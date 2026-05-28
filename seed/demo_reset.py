"""v8 Phase 7: deterministic demo state for the Marsh client portal pitch.

Single command (``python -m seed demo-reset``) returns the database
to Act 1 of the seven-act demo storyboard.

State produced:
  - marsh-demo tenant + Marsh broker row + marsh admin user (BROKER)
  - acme-demo tenant   + Acme Industries (NAICS 51, $180M)
  - northwind-demo tenant + Northwind Health (NAICS 62, $95M)
  - pioneer-demo tenant + Pioneer Manufacturing (NAICS 31, $320M)
  - One cyber submission per client, with a hand-tuned ModelVersion
    + Quote (Acme at score ~685 / tier 4 / REFER for the demo, the
    other two at clean states)
  - For Acme: an open referral in AWAITING_BROKER state with a single
    underwriter -> broker message ("please confirm MFA status")
  - Cohort pool: 60 synthetic entities per (cyber x NAICS x band)
    cohort for the three demo bands -- inserted directly into
    cohort_membership so percentile lookups are meaningful

Cohort-pool entities skip the full workflow on purpose: they are
fodder, not production submissions. The three demo entities ARE
attached to model_versions / quotes / referrals so the demo flow
exercises production read paths.

Live demo entry point: ``python -m seed demo-reset``.
"""
from __future__ import annotations

import logging
import math
import os
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.api.auth.permissions import DEFAULT_ROLES
from infrastructure.db.config import DATABASE_URL_SYNC
from infrastructure.db.models import (
    Broker,
    CohortMembership,
    DecisionType,
    MessageDirection,
    ModelVersionRecord,
    Quote,
    QuoteStatus,
    Referral,
    ReferralMessage,
    ReferralStatus,
    Role,
    Submission,
    SubmissionStatus,
    Tenant,
    User,
)

logger = logging.getLogger("dsi.seed.demo_reset")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEMO_PASSWORD_ENV = "DSI_DEMO_PASSWORD"
DEMO_PASSWORD_DEFAULT = "demo-pass-2026"
DEMO_RNG_SEED_ENV = "DSI_DEMO_RNG_SEED"
DEMO_RNG_SEED_DEFAULT = 42

MARSH_TENANT_SLUG = "marsh-demo"
MARSH_BROKER_SLUG = "marsh"


# Each demo client has multiple coverages so the portal demonstrates
# aggregation + drilldown across a real-feeling book of policies.
# Each coverage entry below becomes one Submission + ModelVersion + Quote.
#
# Schema per coverage:
#   coverage / configuration  -- production config key (must resolve via
#                                infrastructure.models.compiler.get_config)
#   policy_label / limit      -- portal-facing label + limit
#   composite_score           -- TARGET composite the synthetic signal
#                                generator aims for. Chosen so the
#                                production-scored result lands in the
#                                tier band that produces the desired
#                                tier (see tier_bands -> 800-1000=T1,
#                                650-799=T2, 500-649=T3, 350-499=T4).
#                                The actual stored composite may drift
#                                by ~10 points around the target due
#                                to the production scorer's weighting.
#   tier                      -- expected production tier; asserted in
#                                tests, used for narrative reference.
#   drag_modifier_signal_ids  -- signals scored LOW in the synthetic
#                                input so they drive real signal_modifier
#                                drags through the production scorer.
#                                These show up in impact_breakdown
#                                drags on the Signal Pulse card.
#   open_query                -- pre-staged underwriter query; when
#                                present, direct_query_responses[signal]
#                                is set to False, so the production
#                                query_evaluator produces a real
#                                query_modifier drag and (for cyber
#                                MFA) the configured tier override.
#
# All numeric fields downstream (base_premium, premium_after_modifiers,
# final_premium, decision, modifiers_applied, peer_percentile) are
# COMPUTED by the production pipeline -- not stored on the spec.
# The seed records them on the ModelVersion exactly as the pipeline
# returns them so cohort analytics, Signal Pulse, and impact breakdown
# all flow through real DSI logic.
DEMO_CLIENT_TENANTS = [
    {
        "slug": "acme-demo",
        "name": "Acme Industries Tenant",
        "user_email": "client.acme@demo.dsi",
        "user_full_name": "Acme Client",
        "entity_name": "Acme Industries",
        "naics": "5112",
        "naics_section": "51",
        "revenue": 180_000_000,
        "revenue_band": "50-250M",
        "coverages": [
            # CYBER -- the narrative anchor, REFER tier with MFA query.
            # Composite target 425 sits in the production T4 band
            # (350-499). The open MFA query also fires the cyber_general
            # config's mfa_enabled query_condition (override=4) so the
            # tier override path is exercised end-to-end.
            {
                "coverage": "cyber",
                "configuration": "cyber_general",
                "policy_label": "Cyber — Primary",
                "limit": 10_000_000,
                "composite_score": 425.0,
                "tier": 4,
                "drag_modifier_signal_ids": [
                    "mfa_enabled", "security_training", "incident_response_plan",
                ],
                "open_query": {
                    "body": (
                        "Please confirm MFA status across administrative accounts. "
                        "If MFA is deployed, attach evidence (policy screenshot or "
                        "IT attestation)."
                    ),
                    "signal": "mfa_enabled",
                    "reasons": ["MFA absent on admin accounts"],
                },
            },
            # PI -- professional indemnity, preferred terms. T2 band 650-799.
            {
                "coverage": "pi",
                "configuration": "pi_general",
                "policy_label": "Professional Indemnity — Primary",
                "limit": 5_000_000,
                "composite_score": 750.0,
                "tier": 2,
                "drag_modifier_signal_ids": [],
            },
            # D&O -- directors and officers, standard (T3 band 500-649).
            {
                "coverage": "do",
                "configuration": "do_general",
                "policy_label": "D&O Liability — Primary",
                "limit": 15_000_000,
                "composite_score": 580.0,
                "tier": 3,
                "drag_modifier_signal_ids": [],
            },
            # PROPERTY -- preferred (T2 band).
            {
                "coverage": "property",
                "configuration": "property_general",
                "policy_label": "Property — All Risk",
                "limit": 40_000_000,
                "composite_score": 740.0,
                "tier": 2,
                "drag_modifier_signal_ids": [],
            },
        ],
    },
    {
        "slug": "northwind-demo",
        "name": "Northwind Health Tenant",
        "user_email": "client.northwind@demo.dsi",
        "user_full_name": "Northwind Client",
        "entity_name": "Northwind Health",
        "naics": "6221",
        "naics_section": "62",
        "revenue": 95_000_000,
        "revenue_band": "50-250M",
        "coverages": [
            # Cyber preferred T2 -- clean profile for the healthcare anchor.
            {
                "coverage": "cyber",
                "configuration": "cyber_general",
                "policy_label": "Cyber — Primary",
                "limit": 5_000_000,
                "composite_score": 730.0,
                "tier": 2,
                "drag_modifier_signal_ids": [],
            },
            # Medical professional liability -- T3 with staffing query.
            {
                "coverage": "medprof",
                "configuration": "medprof_hospital",
                "policy_label": "Medical Professional Liability",
                "limit": 10_000_000,
                "composite_score": 580.0,
                "tier": 3,
                "drag_modifier_signal_ids": ["clinical_governance"],
                "open_query": {
                    "body": (
                        "Please share the most recent nurse-to-patient ratio "
                        "report for the inpatient wards and confirm any open "
                        "regulatory observations from the last 12 months."
                    ),
                    "signal": "clinical_governance",
                    "reasons": ["Staffing ratio confirmation required"],
                },
            },
            # PI T3 -- moderate score reflecting the elevated tier.
            {
                "coverage": "pi",
                "configuration": "pi_general",
                "policy_label": "Professional Indemnity",
                "limit": 5_000_000,
                "composite_score": 580.0,
                "tier": 3,
                "drag_modifier_signal_ids": [],
            },
            # Property T2 -- non-CAT, preferred.
            {
                "coverage": "property",
                "configuration": "property_general",
                "policy_label": "Property — All Risk",
                "limit": 25_000_000,
                "composite_score": 730.0,
                "tier": 2,
                "drag_modifier_signal_ids": [],
            },
        ],
    },
    {
        "slug": "pioneer-demo",
        "name": "Pioneer Manufacturing Tenant",
        "user_email": "client.pioneer@demo.dsi",
        "user_full_name": "Pioneer Client",
        "entity_name": "Pioneer Manufacturing",
        "naics": "3261",
        "naics_section": "31",
        "revenue": 320_000_000,
        "revenue_band": "250M-1B",
        "coverages": [
            # Cyber T3 -- the manufacturing peer is in elevated band.
            {
                "coverage": "cyber",
                "configuration": "cyber_general",
                "policy_label": "Cyber — Primary",
                "limit": 10_000_000,
                "composite_score": 580.0,
                "tier": 3,
                "drag_modifier_signal_ids": [],
            },
            # General liability T4 with loss-history query.
            {
                "coverage": "casualty",
                "configuration": "casualty_gl",
                "policy_label": "General Liability — Primary",
                "limit": 5_000_000,
                "composite_score": 425.0,
                "tier": 4,
                "drag_modifier_signal_ids": ["loss_history", "safety_program"],
                "open_query": {
                    "body": (
                        "We see two open GL claims from the last 36 months. "
                        "Please share loss-control measures implemented since "
                        "and any updated safety-programme attestation."
                    ),
                    "signal": "loss_history",
                    "reasons": ["Open GL claims require remediation evidence"],
                },
            },
            # Product liability T3.
            {
                "coverage": "prodlib",
                "configuration": "prodlib_consumer_goods",
                "policy_label": "Product Liability",
                "limit": 10_000_000,
                "composite_score": 580.0,
                "tier": 3,
                "drag_modifier_signal_ids": [],
            },
            # CAT-exposed property T4 with hurricane-protection query.
            {
                "coverage": "property",
                "configuration": "property_cat_exposed",
                "policy_label": "Property — CAT Exposed (Gulf Coast)",
                "limit": 55_000_000,
                "composite_score": 425.0,
                "tier": 4,
                "drag_modifier_signal_ids": ["wind_mitigation", "flood_proofing"],
                "open_query": {
                    "body": (
                        "Gulf Coast site requires named-storm mitigation. "
                        "Please share most recent wind-mitigation inspection, "
                        "roof-cover age, and any flood-proofing in place at "
                        "the warehouse footprint."
                    ),
                    "signal": "wind_mitigation",
                    "reasons": ["CAT zone — mitigation evidence required"],
                },
            },
        ],
    },
]

MARSH_USERS = [
    ("marsh.admin@demo.dsi", "Marsh Admin", "BROKER"),
]

# Cohort pool target: N synthetic peers per (coverage, naics, band) cohort
# the demo touches. Sized to comfortably exceed MIN_COHORT_SIZE (10) so
# percentile + mean + median all hydrate, and large enough that the
# percentile lookup doesn't snap to coarse quantiles for the demo
# policies.
COHORT_POOL_PER_BAND = 50

# Per-coverage cohort score distributions. The mean reflects the line's
# market state -- hardening lines (property, medprof) have lower mean
# scores (more risks need attention); softening lines (cyber, D&O) have
# higher mean. Std-dev controls how dramatically a demo policy stands out
# in its cohort.
#
# Tuned so the demo's hand-picked composite_scores (see
# DEMO_CLIENT_TENANTS) land at narratively-accurate percentile bands:
#   - Acme cyber (685) at ~25th percentile of its cohort
#   - Acme PI (762)   at ~top-decile
#   - Pioneer property CAT (654) at bottom of its cohort
COHORT_DISTRIBUTIONS: dict[str, tuple[float, float]] = {
    # softening lines -- mean above 720
    "do":       (740.0, 45.0),
    "cyber":    (720.0, 50.0),
    # flat lines -- mean around 710
    "pi":       (710.0, 50.0),
    "prodlib":  (700.0, 50.0),
    "casualty": (700.0, 50.0),
    # hardening lines -- mean below 700
    "property": (680.0, 55.0),
    "medprof":  (680.0, 55.0),
}
COHORT_DISTRIBUTION_DEFAULT: tuple[float, float] = (700.0, 50.0)


def _enumerate_demo_cohorts() -> list[tuple[str, str, str]]:
    """Every (coverage, naics_section, revenue_band) the demo book touches.

    Drives cohort fodder seeding -- every cohort a demo policy belongs
    to gets ~COHORT_POOL_PER_BAND peers so peer percentile, mean, and
    median all populate on the client + broker portals.
    """
    seen: set[tuple[str, str, str]] = set()
    for t in DEMO_CLIENT_TENANTS:
        naics_section = t["naics_section"]
        revenue_band = t["revenue_band"]
        for cov in t["coverages"]:
            seen.add((cov["coverage"], naics_section, revenue_band))
    return sorted(seen)


# ---------------------------------------------------------------------------
# Session helper
# ---------------------------------------------------------------------------


def _session() -> Session:
    from sqlalchemy import create_engine

    engine = create_engine(DATABASE_URL_SYNC)
    return sessionmaker(bind=engine, autoflush=False)()


def _hash_password(pw: str) -> str:
    from infrastructure.api.auth.jwt_auth import hash_password

    return hash_password(pw)


# ---------------------------------------------------------------------------
# Tear-down
# ---------------------------------------------------------------------------


def _wipe_existing_demo_state(db: Session) -> None:
    """Idempotency: remove anything left by a prior reset."""
    demo_slugs = [MARSH_TENANT_SLUG] + [t["slug"] for t in DEMO_CLIENT_TENANTS]
    # Pull tenant IDs we need to clear
    tenants = db.execute(
        select(Tenant).where(Tenant.slug.in_(demo_slugs))
    ).scalars().all()
    if not tenants:
        # Still drop any orphan cohort_pool rows
        db.execute(delete(CohortMembership).where(
            CohortMembership.entity_key.like("cohort_pool_%")
        ))
        return

    tenant_ids = [t.id for t in tenants]

    # Submissions belonging to demo users
    user_rows = db.execute(
        select(User.id).where(User.tenant_id.in_(tenant_ids))
    ).scalars().all()

    if user_rows:
        # Submissions and their model_versions / quotes / referrals will
        # cascade via FK constraints where defined; submissions don't
        # cascade-delete model_versions because models.py declares the
        # relationship with cascade="all, delete-orphan" -- ORM-level.
        sub_rows = db.execute(
            select(Submission).where(Submission.created_by.in_(user_rows))
        ).scalars().all()
        for sub in sub_rows:
            db.delete(sub)
        db.flush()

    # Cohort membership for the demo entities
    entity_keys = [
        t["entity_name"].strip().lower() for t in DEMO_CLIENT_TENANTS
    ]
    db.execute(
        delete(CohortMembership).where(
            CohortMembership.entity_key.in_(entity_keys)
        )
    )

    # Cohort pool entries (synthetic peer fodder)
    db.execute(
        delete(CohortMembership).where(
            CohortMembership.entity_key.like("cohort_pool_%")
        )
    )

    # Brokers, users, roles, tenants
    for tenant in tenants:
        db.execute(delete(User).where(User.tenant_id == tenant.id))
        db.execute(delete(Broker).where(Broker.tenant_id == tenant.id))
        db.execute(delete(Role).where(Role.tenant_id == tenant.id))
        db.delete(tenant)

    db.flush()


# ---------------------------------------------------------------------------
# Seed building blocks
# ---------------------------------------------------------------------------


def _ensure_tenant(db: Session, *, slug: str, name: str) -> Tenant:
    tenant = db.execute(
        select(Tenant).where(Tenant.slug == slug)
    ).scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(name=name, slug=slug, sso_provider="NONE", is_active=True)
        db.add(tenant)
        db.flush()
    return tenant


def _ensure_roles(db: Session, tenant: Tenant) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for role_name, perms in DEFAULT_ROLES.items():
        role = db.execute(
            select(Role).where(Role.tenant_id == tenant.id, Role.name == role_name)
        ).scalar_one_or_none()
        if role is None:
            role = Role(
                tenant_id=tenant.id,
                name=role_name,
                permissions=[p.value for p in perms],
                is_system_role=True,
                description=f"Seeded {role_name} role",
            )
            db.add(role)
            db.flush()
        roles[role_name] = role
    return roles


def _ensure_user(
    db: Session, *, email: str, full_name: str, tenant: Tenant,
    role: Role, password: str, broker: Optional[Broker] = None,
) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=_hash_password(password),
            tenant_id=tenant.id,
            role_id=role.id,
            broker_id=(broker.id if broker is not None else None),
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.tenant_id = tenant.id
        user.role_id = role.id
        user.broker_id = broker.id if broker is not None else None
        user.is_active = True
        user.hashed_password = _hash_password(password)
        db.flush()
    return user


def _ensure_broker(
    db: Session, *, tenant: Tenant, slug: str, name: str,
) -> Broker:
    broker = db.execute(
        select(Broker).where(Broker.slug == slug)
    ).scalar_one_or_none()
    if broker is None:
        broker = Broker(
            tenant_id=tenant.id, slug=slug, name=name, is_active=True,
        )
        db.add(broker)
        db.flush()
    return broker


# ---------------------------------------------------------------------------
# Cohort pool
# ---------------------------------------------------------------------------


def _seed_cohort_pool(db: Session, rng: random.Random) -> int:
    """Insert synthetic membership rows for every (coverage, naics, band)
    cohort the demo touches.

    These are peer fodder -- they don't carry model_version_id linkages.
    The cohort percentile lookup in layers/cohort/service.py reads
    composite_score from cohort_membership directly, so plain stubs are
    enough to make peer comparison, percentile rank, and cohort mean /
    median populate across the portal.

    Score distributions are per-coverage (see COHORT_DISTRIBUTIONS),
    chosen so:
      - Hardening lines (property, medprof) have lower cohort means --
        the demo policy on a hardening line lands in a tougher cohort.
      - Softening lines (cyber, D&O) have higher means.
      - Each demo policy's composite_score lands at a percentile that
        matches its narrative tier (Acme cyber at REFER tier ~ 25th
        pct, Pioneer CAT property at tier 4 ~ bottom-15th, etc.)

    entity_keys use the cohort_pool_ prefix so the wipe routine can
    find them on every demo-reset.
    """
    inserted = 0
    for coverage, naics_section, revenue_band in _enumerate_demo_cohorts():
        cohort_id = f"{coverage}:{naics_section}:{revenue_band}"
        mean, stddev = COHORT_DISTRIBUTIONS.get(
            coverage, COHORT_DISTRIBUTION_DEFAULT,
        )
        for i in range(COHORT_POOL_PER_BAND):
            score = max(100.0, min(1000.0, rng.gauss(mean, stddev)))
            entity_key = f"cohort_pool_{cohort_id.replace(':', '_')}_{i}"
            membership = CohortMembership(
                entity_key=entity_key,
                coverage=coverage,
                cohort_id=cohort_id,
                composite_score=round(score, 2),
                naics_section=naics_section,
                revenue_band=revenue_band,
                model_version_id=None,
            )
            db.add(membership)
            inserted += 1
        db.flush()
    return inserted


# ---------------------------------------------------------------------------
# Production scoring pipeline
# ---------------------------------------------------------------------------
#
# Demo submissions flow through the same scoring + pricing chain as a
# real submission via the API: build synthetic SignalOutput +
# CategoricalOutput inputs targeted at the desired tier band, then run
# the production ModelScorer + QueryEvaluator + ModelPricer to compute
# the final composite, tier, decision, premium, and impact_breakdown.
#
# Inputs that we still set deterministically per demo coverage:
#   - composite_score (TARGET) -- drives the default signal score and
#     is the average value the synthetic SignalOutputs aggregate to
#   - drag_modifier_signal_ids -- specific signals scored low (15.0)
#     so the scorer produces real impact_breakdown drag entries
#   - open_query[signal] -- if present, the matching direct_query_response
#     is set to False so the query_evaluator produces a real query
#     modifier (and on cyber_general, the mfa_enabled query_condition
#     triggers a tier override)
#
# Outputs that come from the production pipeline (NOT hardcoded):
#   - actual composite, final_tier, tier_label
#   - signal_modifiers + query_modifiers (Signal Pulse drivers)
#   - base_premium, premium_after_modifiers, final_premium
#   - decision (APPROVE / REFER / DECLINE from the tier band action)

from dataclasses import asdict
from typing import Any

from infrastructure.models.compiler import get_config as _get_compiled_config
from layers.risk.pricer import ModelPricer
from layers.risk.query_evaluator import QueryEvaluator
from layers.risk.scorer import ModelScorer
from layers.risk.types import (
    CategoricalOutput,
    SignalOutput,
    utcnow as _types_utcnow,
)

# Module-level singletons -- production code holds these once and
# reuses across calls.
_scorer = ModelScorer()
_pricer = ModelPricer()
_query_evaluator = QueryEvaluator()

# Score injected into "drag" signal slots. Sits comfortably below the
# 35 floor that most cyber/property conditions trigger on.
_DRAG_SIGNAL_SCORE = 15.0


def _build_signal_outputs_for_target(
    config: Any,
    target_composite: float,
    drag_signal_ids: list[str],
    rng: random.Random,
) -> list[SignalOutput]:
    """Synthetic SignalOutput list biased toward a target composite.

    Most signals get a jittered score equal to target_composite / 10
    (config scoring is on 0-100 per signal, aggregated to 0-1000
    composite). Signals named in drag_signal_ids get a forced low
    score so they fire as drags through the scorer's signal-condition
    evaluator.
    """
    default_per_signal = max(5.0, min(95.0, target_composite / 10.0))
    drags = set(drag_signal_ids)

    outputs: list[SignalOutput] = []
    for sd in config.signal_registry:
        if not sd.three_layer_assessment:
            continue
        tla = sd.three_layer_assessment
        if sd.id in drags:
            raw = _DRAG_SIGNAL_SCORE
        else:
            raw = max(5.0, min(95.0, rng.gauss(default_per_signal, 5.0)))
        weight = tla.risk.weight if tla.risk else 0.0
        outputs.append(SignalOutput(
            signal_id=sd.id,
            signal_name=sd.id.replace("_", " ").title(),
            group_id=tla.group_id,
            raw_score=raw,
            confidence=round(rng.uniform(0.78, 0.95), 2),
            weighted_score=raw * weight,
            weight=weight,
            data_sources=["seed"],
            extracted_at=_types_utcnow(),
            execution_time_ms=round(rng.uniform(60, 240), 1),
        ))
    return outputs


def _build_categorical_outputs(
    config: Any, naics_section: str, revenue_band: str,
) -> list[CategoricalOutput]:
    """Categorical inputs the production pricer needs (industry, size,
    geography). Pulled from the demo client's metadata so production
    industry / size factors fire correctly."""
    industry_for_naics = {
        "51": "TECHNOLOGY",
        "62": "HEALTHCARE",
        "31": "MANUFACTURING", "32": "MANUFACTURING", "33": "MANUFACTURING",
        "21": "ENERGY", "22": "ENERGY",
        "52": "FINANCIAL_SERVICES",
        "53": "REAL_ESTATE",
        "23": "CONSTRUCTION",
    }
    size_for_revenue_band = {
        "0-10M":   "MICRO",
        "10-50M":  "SMALL",
        "50-250M": "MEDIUM",
        "250M-1B": "LARGE",
        "1B+":     "ENTERPRISE",
    }
    metadata = {
        "industry_classification": industry_for_naics.get(naics_section, "OTHER"),
        "size_band":                size_for_revenue_band.get(revenue_band, "MEDIUM"),
        "geography":                "US",
    }
    outputs: list[CategoricalOutput] = []
    for sd in config.signal_registry:
        if not sd.categories:
            continue
        cat_def = sd.categories
        cat_group = next(
            (cg for cg in config.groups.categories if cg.id == cat_def.group_id),
            None,
        )
        default_cat = cat_group.default_cat if cat_group else "OTHER"
        group_name = cat_group.label if cat_group else cat_def.group_id

        # Decide which category value applies. metadata.X is the source
        # field for the three categorical groups we care about; fall
        # back to default for anything else.
        selected = None
        if cat_def.source:
            selected = metadata.get(cat_def.source.replace("metadata.", ""))
        if selected is None:
            selected = metadata.get(cat_def.group_id)
        if selected is None:
            selected = default_cat

        # Find modifier from features
        modifier = 1.0
        label = selected
        for feat in cat_def.features:
            if feat.cat == selected:
                modifier = feat.applied if feat.applied is not None else 1.0
                label = feat.label or selected
                break
        else:
            # No matching feature: try default_cat
            for feat in cat_def.features:
                if feat.cat == default_cat:
                    modifier = feat.applied if feat.applied is not None else 1.0
                    label = feat.label or default_cat
                    selected = default_cat
                    break

        outputs.append(CategoricalOutput(
            group_id=cat_def.group_id,
            group_name=group_name,
            category=selected,
            label=label,
            modifier=modifier,
            confidence=0.92,
            extracted_at=_types_utcnow(),
        ))
    return outputs


def _modifier_to_dict(m: Any) -> dict:
    """AppliedModifier dataclasses + plain dicts both flow through here."""
    if isinstance(m, dict):
        return m
    try:
        return asdict(m)
    except TypeError:
        # Pydantic / non-dataclass fallback
        return dict(m) if hasattr(m, "__iter__") else {"raw": str(m)}


def run_synthetic_assessment(
    *,
    coverage: str,
    configuration: str,
    target_composite: float,
    drag_signal_ids: list[str],
    direct_query_responses: dict[str, bool],
    naics_section: str,
    revenue_band: str,
    naics: str,
    revenue: int,
    limit: int,
    rng: random.Random,
) -> dict[str, Any]:
    """Run the production scoring + pricing chain for a synthetic
    submission and return everything needed to populate a
    ModelVersionRecord.

    Determinism: with a fixed rng seed the output is stable across
    runs. Production tier-band rules govern the resulting tier and
    decision.
    """
    config = _get_compiled_config(coverage, configuration)

    signal_outputs = _build_signal_outputs_for_target(
        config, target_composite, drag_signal_ids, rng,
    )
    categorical_outputs = _build_categorical_outputs(
        config, naics_section, revenue_band,
    )

    composite, group_scores, confidence, signal_coverage = (
        _scorer.calculate_composite(signal_outputs=signal_outputs, config=config)
    )
    (signal_conditions, signal_tier_overrides, signal_referrals,
     signal_notes, signal_modifiers) = _scorer.evaluate_signal_conditions(
        signal_outputs=signal_outputs, group_scores=group_scores, config=config,
    )

    query_result = _query_evaluator.evaluate_queries(
        responses=direct_query_responses, config=config,
    )

    all_modifiers = signal_modifiers + query_result.modifiers

    submission_data = {
        "naics": naics, "revenue": revenue, "limit": limit,
    }
    pricing = _pricer.price_submission(
        pure_composite_score=composite,
        signal_tier_overrides=signal_tier_overrides,
        query_tier_overrides=query_result.tier_overrides,
        query_modifiers=all_modifiers,
        categorical_outputs=categorical_outputs,
        submission_data=submission_data,
        config=config,
    )

    final_tier = pricing.final_tier
    tier_band = config.get_tier_band(final_tier)
    action = (
        tier_band.interpretation.action.value
        if tier_band and tier_band.interpretation
        else "APPROVE"
    )
    if action == "DECLINE":
        decision = DecisionType.DECLINE
    elif action == "REFER" or signal_referrals or query_result.referrals:
        decision = DecisionType.REFER
    else:
        decision = DecisionType.APPROVE

    return {
        "composite": composite,
        "confidence": confidence,
        "signal_coverage": signal_coverage,
        "score_based_tier": pricing.score_based_tier
            if hasattr(pricing, "score_based_tier")
            else config.get_tier_for_score(composite),
        "final_tier": final_tier,
        "tier_label": tier_band.label if tier_band else "STANDARD",
        "base_premium": pricing.base_premium,
        "premium_after_modifiers": pricing.premium_after_modifiers,
        "final_premium": pricing.final_premium,
        "modifiers_applied": [_modifier_to_dict(m) for m in pricing.modifiers_applied],
        "decision": decision,
        "auto_approve": decision == DecisionType.APPROVE,
        "group_scores": dict(group_scores or {}),
        "signal_referrals": list(signal_referrals or []),
        "query_referrals": list(query_result.referrals or []),
    }


def _seed_demo_submission(
    db: Session, *, client_spec: dict, coverage_spec: dict,
    marsh_broker: Broker, client_user: User, underwriter_user: User,
    rng: random.Random,
) -> tuple[Submission, ModelVersionRecord, Quote, Optional[Referral]]:
    """Create submission + model_version + quote + referral for one
    coverage, scored through the production pipeline.

    The coverage_spec carries TARGETS (composite_score, tier,
    drag_modifier_signal_ids, open_query). The pipeline produces the
    actual composite, tier, modifiers, premium, and decision. Demo
    storyboard stability comes from deterministic RNG (DEMO_RNG_SEED).
    """
    from infrastructure.db.repositories import generate_id

    now = datetime.now(timezone.utc)
    coverage = coverage_spec["coverage"]
    configuration = coverage_spec["configuration"]
    limit = int(coverage_spec.get("limit", 10_000_000))

    # If there's an open underwriter query for a specific signal, set
    # the matching direct_query_response to False so the production
    # query_evaluator produces a real query modifier (and on cyber the
    # mfa_enabled query_condition triggers a tier override).
    open_query = coverage_spec.get("open_query")
    direct_query_responses: dict[str, bool] = {}
    if open_query is not None and open_query.get("signal"):
        direct_query_responses[open_query["signal"]] = False

    submission = Submission(
        submission_code=generate_id("sub"),
        entity_name=client_spec["entity_name"],
        domain_hint=None,
        country_hint="US",
        coverage=coverage,
        configuration=configuration,
        status=SubmissionStatus.READY,
        submission_data={
            "naics": client_spec["naics"],
            "revenue": client_spec["revenue"],
            "policy_label": coverage_spec.get("policy_label", coverage.capitalize()),
            "limit": limit,
        },
        direct_query_responses=direct_query_responses,
        broker_id=marsh_broker.id,
        created_by=client_user.id,
        created_at=now,
        updated_at=now,
        processing_completed_at=now,
    )
    db.add(submission)
    db.flush()

    # ----- production scoring + pricing -----
    result = run_synthetic_assessment(
        coverage=coverage,
        configuration=configuration,
        target_composite=float(coverage_spec["composite_score"]),
        drag_signal_ids=coverage_spec.get("drag_modifier_signal_ids", []),
        direct_query_responses=direct_query_responses,
        naics_section=client_spec["naics_section"],
        revenue_band=client_spec["revenue_band"],
        naics=client_spec["naics"],
        revenue=int(client_spec["revenue"]),
        limit=limit,
        rng=rng,
    )

    cohort_id = f"{coverage}:{client_spec['naics_section']}:{client_spec['revenue_band']}"

    mv = ModelVersionRecord(
        version_code=generate_id("mv"),
        submission_id=submission.id,
        version_number=1,
        version_type="initial",
        is_latest=True,
        config_hash="demo",
        coverage=coverage,
        configuration_name=configuration,
        pure_composite_score=result["composite"],
        final_composite_score=result["composite"],
        confidence=result["confidence"],
        signal_coverage=result["signal_coverage"],
        score_based_tier=result["score_based_tier"],
        final_tier=result["final_tier"],
        tier_label=result["tier_label"],
        base_premium=result["base_premium"],
        premium_after_modifiers=result["premium_after_modifiers"],
        final_premium=result["final_premium"],
        modifiers_applied=result["modifiers_applied"],
        decision=result["decision"],
        auto_approve=result["auto_approve"],
        peer_cohort_id=cohort_id,
        peer_cohort_size=None,
        created_at=now,
    )
    db.add(mv)
    db.flush()

    # Cohort membership for this real entity. The composite is now the
    # PRODUCTION-COMPUTED value, not a hardcoded one -- so the entity's
    # position in its peer cohort reflects how the scorer actually
    # rated it.
    membership = CohortMembership(
        entity_key=client_spec["entity_name"].strip().lower(),
        coverage=coverage,
        cohort_id=cohort_id,
        composite_score=result["composite"],
        naics_section=client_spec["naics_section"],
        revenue_band=client_spec["revenue_band"],
        model_version_id=mv.id,
    )
    db.add(membership)
    db.flush()

    # Cohort stats include this entity itself.
    cohort_scores = db.execute(
        select(CohortMembership.composite_score).where(
            CohortMembership.cohort_id == cohort_id
        )
    ).scalars().all()
    from layers.cohort.service import (
        cohort_stats_from_scores,
        percentile_from_scores,
    )

    pct = percentile_from_scores(cohort_scores, result["composite"])
    stats = cohort_stats_from_scores(cohort_id, cohort_scores)
    mv.peer_percentile_rank = pct
    mv.peer_cohort_size = len(cohort_scores)
    if stats is not None:
        mv.peer_cohort_mean_score = stats.mean
        mv.peer_cohort_median_score = stats.median
    db.flush()

    quote = Quote(
        quote_code=generate_id("quo"),
        submission_id=submission.id,
        model_version_id=mv.id,
        status=QuoteStatus.READY,
        recommended_premium=result["final_premium"],
        recommended_limit=float(limit),
        created_at=now,
        updated_at=now,
    )
    db.add(quote)
    db.flush()

    referral: Optional[Referral] = None
    open_query = coverage_spec.get("open_query")
    if open_query is not None:
        referral = Referral(
            referral_code=generate_id("ref"),
            quote_id=quote.id,
            status=ReferralStatus.AWAITING_BROKER,
            awaiting_party="broker",
            reasons=open_query.get("reasons", ["Underwriter query pending"]),
            priority=3,
            created_at=now,
            updated_at=now,
        )
        db.add(referral)
        db.flush()

        # Pre-stage the underwriter -> broker query
        query_msg = ReferralMessage(
            referral_id=referral.id,
            direction=MessageDirection.UNDERWRITER_TO_BROKER.value,
            author_user_id=underwriter_user.id,
            body=open_query["body"],
            request_signal_evidence=open_query.get("signal"),
            created_at=now,
        )
        db.add(query_msg)
        db.flush()

    return submission, mv, quote, referral


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def reset_demo_state(db: Session, *, password: str, rng_seed: int) -> dict:
    """Wipe + reseed deterministic demo state.

    Returns a small dict summarising what was created. The caller can
    log this or feed it to a smoke test for verification.
    """
    rng = random.Random(rng_seed)

    logger.info("[demo-reset] wiping prior demo state")
    _wipe_existing_demo_state(db)
    db.flush()

    logger.info("[demo-reset] seeding cohort pool")
    cohort_inserted = _seed_cohort_pool(db, rng)

    logger.info("[demo-reset] seeding Marsh tenant + broker")
    marsh_tenant = _ensure_tenant(
        db, slug=MARSH_TENANT_SLUG, name="Marsh Demo Tenant",
    )
    _ensure_roles(db, marsh_tenant)
    marsh_broker = _ensure_broker(
        db, tenant=marsh_tenant, slug=MARSH_BROKER_SLUG, name="Marsh",
    )
    marsh_broker_role = db.execute(
        select(Role).where(
            Role.tenant_id == marsh_tenant.id, Role.name == "BROKER",
        )
    ).scalar_one()
    for email, full_name, _role_name in MARSH_USERS:
        _ensure_user(
            db, email=email, full_name=full_name,
            tenant=marsh_tenant, role=marsh_broker_role,
            password=password, broker=marsh_broker,
        )

    # A carrier-side underwriter for the demo (used to author the
    # pre-staged MFA query on Acme's referral). Lives in the existing
    # dsi-demo tenant if present, otherwise on Marsh tenant as a
    # convenience role attached to the seed.
    underwriter = _resolve_demo_underwriter(db, marsh_tenant, password)

    summary = {
        "marsh_tenant_id": str(marsh_tenant.id),
        "marsh_broker_id": str(marsh_broker.id),
        "cohort_pool_rows": cohort_inserted,
        "clients": [],
    }

    for client_spec in DEMO_CLIENT_TENANTS:
        logger.info("[demo-reset] seeding client %s", client_spec["entity_name"])
        client_tenant = _ensure_tenant(
            db, slug=client_spec["slug"], name=client_spec["name"],
        )
        roles = _ensure_roles(db, client_tenant)
        client_user = _ensure_user(
            db,
            email=client_spec["user_email"],
            full_name=client_spec["user_full_name"],
            tenant=client_tenant,
            role=roles["CLIENT"],
            password=password,
        )

        coverages_summary: list[dict] = []
        for coverage_spec in client_spec.get("coverages", []):
            submission, mv, quote, referral = _seed_demo_submission(
                db,
                client_spec=client_spec,
                coverage_spec=coverage_spec,
                marsh_broker=marsh_broker,
                client_user=client_user,
                underwriter_user=underwriter,
                rng=rng,
            )
            coverages_summary.append({
                "coverage": coverage_spec["coverage"],
                "policy_label": coverage_spec.get("policy_label"),
                "submission_code": submission.submission_code,
                "quote_code": quote.quote_code,
                "composite_score": mv.final_composite_score,
                "tier": mv.final_tier,
                "peer_percentile_rank": mv.peer_percentile_rank,
                "referral_code": referral.referral_code if referral else None,
                "referral_state": referral.status.value if referral else None,
            })

        summary["clients"].append({
            "entity_name": client_spec["entity_name"],
            "coverages": coverages_summary,
        })

    db.commit()
    logger.info("[demo-reset] complete: %s clients, %s total policies",
                len(summary["clients"]),
                sum(len(c["coverages"]) for c in summary["clients"]))
    return summary


def _resolve_demo_underwriter(
    db: Session, fallback_tenant: Tenant, password: str,
) -> User:
    """Find the existing dsi-demo UNDERWRITER user, or seed one on Marsh tenant.

    The pre-staged MFA query needs an author_user_id; this gives one.
    """
    uw = db.execute(
        select(User).where(User.email == "uw@dsi.local")
    ).scalar_one_or_none()
    if uw is not None:
        return uw

    roles = _ensure_roles(db, fallback_tenant)
    return _ensure_user(
        db,
        email="demo.underwriter@demo.dsi",
        full_name="Demo Underwriter",
        tenant=fallback_tenant,
        role=roles["UNDERWRITER"],
        password=password,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def run(*, password: Optional[str] = None, rng_seed: Optional[int] = None) -> int:
    pw = password or os.environ.get(DEMO_PASSWORD_ENV, DEMO_PASSWORD_DEFAULT)
    seed = rng_seed if rng_seed is not None else int(
        os.environ.get(DEMO_RNG_SEED_ENV, DEMO_RNG_SEED_DEFAULT)
    )
    db = _session()
    try:
        reset_demo_state(db, password=pw, rng_seed=seed)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0

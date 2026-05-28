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
# `open_query` controls whether to pre-stage an underwriter MFA-style
# question; queries are scattered across coverages and clients so the
# Communications page has meaningful volume.
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
            {
                "coverage": "cyber",
                "configuration": "cyber_general",
                "policy_label": "Cyber — Primary",
                "limit": 10_000_000,
                "composite_score": 685.0,
                "tier": 4,
                "base_premium": 165_000.0,
                "decision": DecisionType.REFER,
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
            # PI -- professional indemnity, preferred terms.
            {
                "coverage": "pi",
                "configuration": "pi_general",
                "policy_label": "Professional Indemnity — Primary",
                "limit": 5_000_000,
                "composite_score": 762.0,
                "tier": 2,
                "base_premium": 88_000.0,
                "decision": DecisionType.APPROVE,
                "drag_modifier_signal_ids": [],
            },
            # D&O -- directors and officers, standard.
            {
                "coverage": "do",
                "configuration": "do_general",
                "policy_label": "D&O Liability — Primary",
                "limit": 15_000_000,
                "composite_score": 718.0,
                "tier": 3,
                "base_premium": 134_000.0,
                "decision": DecisionType.APPROVE,
                "drag_modifier_signal_ids": [],
            },
            # PROPERTY -- preferred.
            {
                "coverage": "property",
                "configuration": "property_general",
                "policy_label": "Property — All Risk",
                "limit": 40_000_000,
                "composite_score": 741.0,
                "tier": 2,
                "base_premium": 95_000.0,
                "decision": DecisionType.APPROVE,
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
            {
                "coverage": "cyber",
                "configuration": "cyber_general",
                "policy_label": "Cyber — Primary",
                "limit": 5_000_000,
                "composite_score": 735.0,
                "tier": 2,
                "base_premium": 121_000.0,
                "decision": DecisionType.APPROVE,
                "drag_modifier_signal_ids": [],
            },
            # Medical professional liability -- an open query about staffing.
            {
                "coverage": "medprof",
                "configuration": "medprof_hospital",
                "policy_label": "Medical Professional Liability",
                "limit": 10_000_000,
                "composite_score": 689.0,
                "tier": 3,
                "base_premium": 220_000.0,
                "decision": DecisionType.REFER,
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
            {
                "coverage": "pi",
                "configuration": "pi_general",
                "policy_label": "Professional Indemnity",
                "limit": 5_000_000,
                "composite_score": 711.0,
                "tier": 3,
                "base_premium": 64_000.0,
                "decision": DecisionType.APPROVE,
                "drag_modifier_signal_ids": [],
            },
            {
                "coverage": "property",
                "configuration": "property_general",
                "policy_label": "Property — All Risk",
                "limit": 25_000_000,
                "composite_score": 728.0,
                "tier": 2,
                "base_premium": 72_000.0,
                "decision": DecisionType.APPROVE,
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
            {
                "coverage": "cyber",
                "configuration": "cyber_general",
                "policy_label": "Cyber — Primary",
                "limit": 10_000_000,
                "composite_score": 712.0,
                "tier": 3,
                "base_premium": 168_000.0,
                "decision": DecisionType.APPROVE,
                "drag_modifier_signal_ids": [],
            },
            # General liability with loss-history query.
            {
                "coverage": "casualty",
                "configuration": "casualty_gl",
                "policy_label": "General Liability — Primary",
                "limit": 5_000_000,
                "composite_score": 671.0,
                "tier": 4,
                "base_premium": 240_000.0,
                "decision": DecisionType.REFER,
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
            {
                "coverage": "prodlib",
                "configuration": "prodlib_consumer_goods",
                "policy_label": "Product Liability",
                "limit": 10_000_000,
                "composite_score": 705.0,
                "tier": 3,
                "base_premium": 195_000.0,
                "decision": DecisionType.APPROVE,
                "drag_modifier_signal_ids": [],
            },
            # CAT-exposed property with hurricane-protection query.
            {
                "coverage": "property",
                "configuration": "property_cat_exposed",
                "policy_label": "Property — CAT Exposed (Gulf Coast)",
                "limit": 55_000_000,
                "composite_score": 654.0,
                "tier": 4,
                "base_premium": 410_000.0,
                "decision": DecisionType.REFER,
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
# Demo submissions
# ---------------------------------------------------------------------------


def _build_drag_modifiers(
    drag_signal_ids: list[str], base_premium: float,
) -> tuple[list[dict], float]:
    """Construct modifier audit rows that produce realistic drags.

    Each drag signal contributes a 1.08x factor. Returns a list of
    AppliedModifier-shaped dicts ready for JSONB serialisation, plus
    the final premium after all modifiers.
    """
    current = base_premium
    modifiers: list[dict] = []
    for sig_id in drag_signal_ids:
        factor = 1.08
        before = current
        after = current * factor
        modifiers.append({
            "source": "direct_query",
            "source_id": sig_id,
            "name": f"Direct query drag: {sig_id}",
            "factor": factor,
            "premium_before": round(before, 2),
            "premium_after": round(after, 2),
        })
        current = after
    return modifiers, round(current, 2)


def _seed_demo_submission(
    db: Session, *, client_spec: dict, coverage_spec: dict,
    marsh_broker: Broker, client_user: User, underwriter_user: User,
) -> tuple[Submission, ModelVersionRecord, Quote, Optional[Referral]]:
    """Create submission + model_version + quote + referral for one coverage.

    Hand-tuned to land at the configured composite_score / tier / premium
    so the demo storyboard reads consistently every time.
    """
    from infrastructure.db.repositories import generate_id

    now = datetime.now(timezone.utc)
    coverage = coverage_spec["coverage"]
    configuration = coverage_spec["configuration"]
    base_premium = float(coverage_spec["base_premium"])
    tier = int(coverage_spec["tier"])

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
            # Surfaced on the client portal as the policy label for this
            # submission. Not used by the workflow; carrier UI shows
            # entity_name elsewhere.
            "policy_label": coverage_spec.get("policy_label", coverage.capitalize()),
            "limit": coverage_spec.get("limit"),
        },
        direct_query_responses={},
        broker_id=marsh_broker.id,
        created_by=client_user.id,
        created_at=now,
        updated_at=now,
        processing_completed_at=now,
    )
    db.add(submission)
    db.flush()

    modifiers, post_modifier_premium = _build_drag_modifiers(
        coverage_spec.get("drag_modifier_signal_ids", []), base_premium,
    )

    # Cohort id only meaningful for cyber demo path; other coverages
    # still get a cohort_id stamped for symmetry, but peer stats won't
    # render because the cohort pool only contains cyber entries.
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
        pure_composite_score=coverage_spec["composite_score"],
        final_composite_score=coverage_spec["composite_score"],
        confidence=0.85,
        signal_coverage=0.95,
        score_based_tier=tier,
        final_tier=tier,
        tier_label={1: "PREFERRED", 2: "PREFERRED", 3: "STANDARD", 4: "REFER", 5: "DECLINE"}.get(tier, "STANDARD"),
        base_premium=base_premium,
        premium_after_modifiers=post_modifier_premium,
        final_premium=post_modifier_premium,
        modifiers_applied=modifiers,
        decision=coverage_spec["decision"],
        auto_approve=(coverage_spec["decision"] == DecisionType.APPROVE),
        # v8 peer cohort fields -- populated from the cohort pool below
        peer_cohort_id=cohort_id,
        peer_cohort_size=None,
        created_at=now,
    )
    db.add(mv)
    db.flush()

    # Cohort membership for this real entity. Unique per (entity_key, coverage)
    # so the same entity in multiple coverages produces one row each.
    membership = CohortMembership(
        entity_key=client_spec["entity_name"].strip().lower(),
        coverage=coverage,
        cohort_id=cohort_id,
        composite_score=coverage_spec["composite_score"],
        naics_section=client_spec["naics_section"],
        revenue_band=client_spec["revenue_band"],
        model_version_id=mv.id,
    )
    db.add(membership)
    db.flush()

    # Compute and persist percentile on MV after the entity's membership
    # row is in place so the cohort includes itself.
    cohort_scores = db.execute(
        select(CohortMembership.composite_score).where(
            CohortMembership.cohort_id == cohort_id
        )
    ).scalars().all()
    from layers.cohort.service import (
        cohort_stats_from_scores,
        percentile_from_scores,
    )

    pct = percentile_from_scores(cohort_scores, coverage_spec["composite_score"])
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
        recommended_premium=post_modifier_premium,
        recommended_limit=float(coverage_spec.get("limit", 10_000_000)),
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

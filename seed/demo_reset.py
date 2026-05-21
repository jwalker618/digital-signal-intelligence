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
        # Acme is the demo's narrative anchor -- below cohort mean
        # with MFA / training / IR gaps to remediate
        "composite_score": 685.0,
        "tier": 4,
        "base_premium": 165_000.0,
        "final_premium": 165_000.0,
        "decision": DecisionType.REFER,
        "open_referral": True,
        "drag_modifier_signal_ids": ["mfa_enabled", "security_training", "incident_response_plan"],
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
        "composite_score": 735.0,
        "tier": 2,
        "base_premium": 142_000.0,
        "final_premium": 121_000.0,
        "decision": DecisionType.APPROVE,
        "open_referral": False,
        "drag_modifier_signal_ids": [],
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
        "composite_score": 712.0,
        "tier": 3,
        "base_premium": 220_000.0,
        "final_premium": 218_000.0,
        "decision": DecisionType.APPROVE,
        "open_referral": False,
        "drag_modifier_signal_ids": [],
    },
]

MARSH_USERS = [
    ("marsh.admin@demo.dsi", "Marsh Admin", "BROKER"),
]

# Cohort pool target: 60 entities per cohort, distribution N(720, 50).
COHORT_POOL_PER_BAND = 60
COHORT_POOL_DISTRIBUTION_MEAN = 720.0
COHORT_POOL_DISTRIBUTION_STDDEV = 50.0


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
    """Insert ~60 synthetic membership rows per demo cohort.

    These don't have model_version_id linkages -- they are peer
    fodder. Score distribution is N(720, 50); entity_keys use the
    cohort_pool_ prefix so wipe can find them.
    """
    target_cohorts = {
        f"cyber:{t['naics_section']}:{t['revenue_band']}": (
            t["naics_section"],
            t["revenue_band"],
        )
        for t in DEMO_CLIENT_TENANTS
    }

    inserted = 0
    for cohort_id, (naics_section, revenue_band) in target_cohorts.items():
        for i in range(COHORT_POOL_PER_BAND):
            score = max(
                100.0,
                min(
                    1000.0,
                    rng.gauss(COHORT_POOL_DISTRIBUTION_MEAN, COHORT_POOL_DISTRIBUTION_STDDEV),
                ),
            )
            entity_key = f"cohort_pool_{cohort_id.replace(':', '_')}_{i}"
            membership = CohortMembership(
                entity_key=entity_key,
                coverage="cyber",
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
    db: Session, *, spec: dict, marsh_broker: Broker,
    client_user: User, underwriter_user: User,
) -> tuple[Submission, ModelVersionRecord, Quote, Optional[Referral]]:
    """Create submission + model_version + quote + referral for one demo client.

    Hand-tuned to land at the configured composite_score / tier / premium
    so the demo storyboard reads consistently every time.
    """
    from infrastructure.db.repositories import generate_id

    now = datetime.now(timezone.utc)

    submission = Submission(
        submission_code=generate_id("sub"),
        entity_name=spec["entity_name"],
        domain_hint=None,
        country_hint="US",
        coverage="cyber",
        configuration="cyber_general",
        status=SubmissionStatus.READY,
        submission_data={
            "naics": spec["naics"],
            "revenue": spec["revenue"],
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
        spec["drag_modifier_signal_ids"], spec["base_premium"],
    )

    cohort_id = f"cyber:{spec['naics_section']}:{spec['revenue_band']}"

    mv = ModelVersionRecord(
        version_code=generate_id("mv"),
        submission_id=submission.id,
        version_number=1,
        version_type="initial",
        is_latest=True,
        config_hash="demo",
        coverage="cyber",
        configuration_name="cyber_general",
        pure_composite_score=spec["composite_score"],
        final_composite_score=spec["composite_score"],
        confidence=0.85,
        signal_coverage=0.95,
        score_based_tier=spec["tier"],
        final_tier=spec["tier"],
        tier_label={2: "PREFERRED", 3: "STANDARD", 4: "REFER"}.get(spec["tier"], "STANDARD"),
        base_premium=spec["base_premium"],
        premium_after_modifiers=post_modifier_premium,
        final_premium=post_modifier_premium,
        modifiers_applied=modifiers,
        decision=spec["decision"],
        auto_approve=(spec["decision"] == DecisionType.APPROVE),
        # v8 peer cohort fields
        peer_cohort_id=cohort_id,
        peer_cohort_size=COHORT_POOL_PER_BAND + 1,
        # percentile will be set below once cohort membership is inserted
        created_at=now,
    )
    db.add(mv)
    db.flush()

    # Cohort membership for this real entity
    membership = CohortMembership(
        entity_key=spec["entity_name"].strip().lower(),
        coverage="cyber",
        cohort_id=cohort_id,
        composite_score=spec["composite_score"],
        naics_section=spec["naics_section"],
        revenue_band=spec["revenue_band"],
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

    pct = percentile_from_scores(cohort_scores, spec["composite_score"])
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
        recommended_limit=10_000_000,
        created_at=now,
        updated_at=now,
    )
    db.add(quote)
    db.flush()

    referral: Optional[Referral] = None
    if spec["open_referral"]:
        referral = Referral(
            referral_code=generate_id("ref"),
            quote_id=quote.id,
            status=ReferralStatus.AWAITING_BROKER,
            awaiting_party="broker",
            reasons=["MFA absent on admin accounts"],
            priority=3,
            created_at=now,
            updated_at=now,
        )
        db.add(referral)
        db.flush()

        # Pre-stage the underwriter -> broker MFA query
        query_msg = ReferralMessage(
            referral_id=referral.id,
            direction=MessageDirection.UNDERWRITER_TO_BROKER.value,
            author_user_id=underwriter_user.id,
            body=(
                "Please confirm MFA status across administrative accounts. "
                "If MFA is deployed, attach evidence (policy screenshot or "
                "IT attestation)."
            ),
            request_signal_evidence="mfa_enabled",
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

    for spec in DEMO_CLIENT_TENANTS:
        logger.info("[demo-reset] seeding client %s", spec["entity_name"])
        client_tenant = _ensure_tenant(
            db, slug=spec["slug"], name=spec["name"],
        )
        roles = _ensure_roles(db, client_tenant)
        client_user = _ensure_user(
            db,
            email=spec["user_email"],
            full_name=spec["user_full_name"],
            tenant=client_tenant,
            role=roles["CLIENT"],
            password=password,
        )

        submission, mv, quote, referral = _seed_demo_submission(
            db,
            spec=spec,
            marsh_broker=marsh_broker,
            client_user=client_user,
            underwriter_user=underwriter,
        )

        summary["clients"].append({
            "entity_name": spec["entity_name"],
            "submission_code": submission.submission_code,
            "quote_code": quote.quote_code,
            "composite_score": mv.final_composite_score,
            "tier": mv.final_tier,
            "peer_percentile_rank": mv.peer_percentile_rank,
            "referral_code": referral.referral_code if referral else None,
            "referral_state": referral.status.value if referral else None,
        })

    db.commit()
    logger.info("[demo-reset] complete: %s", summary)
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

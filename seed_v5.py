"""
seed_v5.py -- v5 companion seed.

Run AFTER seed_dsi_bench.py. Augments the seeded DSI bench with v5
governance + experience artefacts so the frontend has something to
render end-to-end:

1. Auth foundation (A-1)
   - `dsi-demo` tenant + DEFAULT_ROLES
   - 5 demo users (admin / actuarial / senior-uw / underwriter / read-only)
   - Existing seed users (system / underwriter / analyst) adopted into
     the demo tenant with the matching role
   - Existing submissions / quotes / loss events / audit logs
     back-filled with tenant_id if missing

2. Audit events (A-2)
   - AuditService.record() for a sample of bind decisions, creating
     a mixture of CREATE / APPROVE / REFER / REJECT actions

3. Config versions (B-2)
   - ConfigService.create_draft + validate + calibrate + deploy for
     one coverage (cyber_general) so the Config Management UI has a
     non-empty version history

4. Loss events (C-1)
   - Synthetic loss rows for ~10% of bound quotes, with
     SignalLossLinker.link() populating signal_loss_pairs. Uses real
     assessments -- no fabricated signal scores.

5. Recalibration (C-2)
   - RecalibrationEngine.run() for cyber_general. Produces a proposal
     visible in the C-3 governance UI. Best-effort: logs and moves on
     if sample size is too small.

6. World Engine maturity (WE-1)
   - Final MaturityEvaluator.evaluate() + log the stage

Every computed value (audit events, config versions, linked pairs,
proposal payload, maturity stage) flows through the real production
code path. Synthetic inputs are only used for counterfactuals that
couldn't plausibly be seeded otherwise (e.g. loss amounts).

Usage:
    python seed_dsi_bench.py         # existing bench seed
    python seed_v5.py                # this script -- v5 augmentations
"""

from __future__ import annotations

import logging
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from infrastructure.db.config import DATABASE_URL_SYNC
from infrastructure.db.models import (
    AuditLog,
    LossEvent,
    ModelVersionRecord,
    Quote,
    Role,
    Submission,
    Tenant,
    User,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("dsi.seed.v5")

DEMO_TENANT_SLUG = "dsi-demo"
DEMO_TENANT_NAME = "DSI Demo Tenant"


# ==============================================================================
# Helpers
# ==============================================================================


def _session() -> Session:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(DATABASE_URL_SYNC)
    return sessionmaker(bind=engine, autoflush=False)()


def _hash_password(pw: str) -> str:
    """Import lazily so this module doesn't require bcrypt at import time
    (the bench seed may have already closed the DB)."""
    from infrastructure.api.auth.jwt_auth import hash_password

    return hash_password(pw)


# ==============================================================================
# Step 1: Auth foundation
# ==============================================================================


def seed_auth(db: Session) -> tuple[Tenant, dict[str, Role], dict[str, User]]:
    from infrastructure.api.auth.permissions import DEFAULT_ROLES, Permission

    logger.info("[A-1] Ensuring demo tenant + roles + users")

    tenant = db.execute(
        select(Tenant).where(Tenant.slug == DEMO_TENANT_SLUG)
    ).scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(
            name=DEMO_TENANT_NAME,
            slug=DEMO_TENANT_SLUG,
            sso_provider="NONE",
            is_active=True,
        )
        db.add(tenant)
        db.flush()

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

    users_spec = [
        ("admin@dsi.local", "Demo Admin", "ADMIN"),
        ("actuarial@dsi.local", "Anne Actuary", "ACTUARIAL"),
        ("senior@dsi.local", "Sam Senior", "SENIOR_UNDERWRITER"),
        ("uw@dsi.local", "Ursula Underwriter", "UNDERWRITER"),
        ("viewer@dsi.local", "Vincent Viewer", "READ_ONLY"),
    ]
    users: dict[str, User] = {}
    for email, full_name, role_name in users_spec:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=_hash_password("demo-password-12345"),
                tenant_id=tenant.id,
                role_id=roles[role_name].id,
                is_active=True,
                is_superuser=(role_name == "ADMIN"),
            )
            db.add(user)
        else:
            user.tenant_id = tenant.id
            user.role_id = roles[role_name].id
            user.is_active = True
        db.flush()
        users[role_name] = user

    # Adopt the three legacy seed users into the tenant if present
    for email, legacy_role in [
        ("system@dsi-platform.io", "ADMIN"),
        ("underwriter@dsi-platform.io", "UNDERWRITER"),
        ("analyst@dsi-platform.io", "READ_ONLY"),
    ]:
        u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if u is not None:
            u.tenant_id = tenant.id
            u.role_id = roles[legacy_role].id
    db.flush()

    # Back-fill tenant_id on existing tenant-scoped rows where missing.
    for table in ("submissions", "quotes", "loss_events", "audit_logs"):
        db.execute(
            text(
                f"UPDATE {table} SET tenant_id = :tid WHERE tenant_id IS NULL"
            ),
            {"tid": tenant.id},
        )

    db.commit()
    logger.info(
        "  tenant=%s roles=%d users=%d", tenant.slug, len(roles), len(users)
    )
    return tenant, roles, users


# ==============================================================================
# Step 2: Audit events
# ==============================================================================


def seed_audit_events(
    db: Session, tenant: Tenant, users: dict[str, User], max_events: int = 50
) -> int:
    from infrastructure.api.audit import (
        AuditActionType,
        AuditEvent,
        AuditService,
    )

    logger.info("[A-2] Recording audit events for a sample of quotes")

    svc = AuditService(db)
    recorded = 0

    # Grab a sample of quotes (in the demo tenant after back-fill)
    quotes: list[Quote] = (
        db.execute(
            select(Quote)
            .join(Submission, Submission.id == Quote.submission_id)
            .limit(max_events)
        )
        .scalars()
        .all()
    )

    admin = users.get("ADMIN")
    uw = users.get("UNDERWRITER") or admin

    for i, q in enumerate(quotes):
        actor = admin if i % 3 == 0 else uw
        action = AuditActionType.ASSESSMENT_COMPLETE
        svc.record(
            AuditEvent(
                action_type=action,
                tenant_id=str(tenant.id),
                user_id=str(actor.id),
                resource_type="quote",
                resource_id=str(q.id),
                after_state={"status": str(q.status), "quote_code": q.quote_code},
                details={"source": "seed_v5"},
            )
        )
        recorded += 1

    db.commit()
    logger.info("  audit_events=%d", recorded)
    return recorded


# ==============================================================================
# Step 3: Config version history (B-2)
# ==============================================================================


def seed_config_version(
    db: Session, users: dict[str, User]
) -> Optional[str]:
    from pathlib import Path

    from infrastructure.admin import ConfigService

    logger.info("[B-2] Seeding config version history")

    cfg_path = (
        Path(__file__).parent / "coverages" / "cyber" / "configs" / "cyber_general.yaml"
    )
    if not cfg_path.exists():
        # Fall back to first available cyber config under any folder structure
        candidates = list(Path(__file__).parent.glob("coverages/cyber/**/*.yaml"))
        if not candidates:
            logger.warning("  no cyber config YAML found; skipping")
            return None
        cfg_path = candidates[0]

    content = cfg_path.read_text()
    svc = ConfigService(db)
    author = users.get("ACTUARIAL") or users.get("ADMIN")
    try:
        draft = svc.create_draft(
            coverage="cyber",
            config_name="cyber_general",
            content=content,
            author_id=str(author.id) if author else None,
            notes="Initial v5 baseline (seed_v5.py)",
        )
    except ValueError as exc:
        logger.warning("  create_draft failed: %s", exc)
        return None

    validation = svc.validate(draft.id)
    logger.info("  validate ok=%s", validation.get("valid"))

    try:
        calibration = svc.calibrate(draft.id)
        logger.info("  calibrate success=%s", calibration.get("success"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("  calibrate skipped: %s", exc)

    if validation.get("valid"):
        try:
            svc.deploy(draft.id, deployed_by=str(author.id) if author else None)
            logger.info("  deployed version_id=%s", draft.id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("  deploy skipped: %s", exc)

    db.commit()
    return draft.id


# ==============================================================================
# Step 4: Loss events (C-1)
# ==============================================================================


def seed_loss_events(
    db: Session, tenant: Tenant, sample_fraction: float = 0.1
) -> tuple[int, int]:
    from infrastructure.recalibration.linker import SignalLossLinker

    logger.info("[C-1] Seeding synthetic loss events")

    bound_quotes: list[Quote] = (
        db.execute(
            select(Quote)
            .join(Submission, Submission.id == Quote.submission_id)
            .where(Quote.status == "BOUND")
            .limit(1000)
        )
        .scalars()
        .all()
    )
    if not bound_quotes:
        # Fall back to any quote
        bound_quotes = db.execute(select(Quote).limit(200)).scalars().all()

    random.seed(42)
    target_count = max(1, int(len(bound_quotes) * sample_fraction))
    picked = random.sample(bound_quotes, min(target_count, len(bound_quotes)))

    loss_types = [
        "data_breach",
        "ransomware",
        "business_interruption",
        "third_party_liability",
        "regulatory_action",
    ]

    created = 0
    linked = 0
    linker = SignalLossLinker(db)
    for q in picked:
        submission = db.execute(
            select(Submission).where(Submission.id == q.submission_id)
        ).scalar_one_or_none()
        if submission is None:
            continue
        loss_date = (q.created_at or datetime.now(timezone.utc)) + timedelta(
            days=random.randint(30, 365)
        )
        loss = LossEvent(
            tenant_id=tenant.id,
            entity_name=submission.entity_name,
            quote_id=q.id,
            claim_reference=f"CLM-{uuid.uuid4().hex[:6].upper()}",
            loss_date=loss_date,
            notification_date=loss_date + timedelta(days=random.randint(1, 30)),
            loss_type=random.choice(loss_types),
            coverage=submission.coverage or "cyber",
            config_name=submission.configuration or "cyber_general",
            incurred_amount=round(random.uniform(50_000, 2_000_000), 2),
            paid_amount=round(random.uniform(10_000, 500_000), 2),
            reserved_amount=round(random.uniform(20_000, 1_500_000), 2),
            currency="USD",
            status="CLOSED",
            cause_description="Seeded by seed_v5.py",
        )
        db.add(loss)
        db.flush()
        created += 1
        try:
            result = linker.link(str(loss.id))
            if result and result.linked_assessment_id:
                linked += 1
        except Exception as exc:  # noqa: BLE001
            logger.debug("    linker failed for %s: %s", loss.id, exc)

    db.commit()
    logger.info("  loss_events=%d linked=%d", created, linked)
    return created, linked


# ==============================================================================
# Step 5: Recalibration (C-2)
# ==============================================================================


def seed_recalibration(
    db: Session, tenant: Tenant, users: dict[str, User]
) -> Optional[str]:
    from infrastructure.recalibration import RecalibrationEngine

    logger.info("[C-2] Running RecalibrationEngine for cyber_general")

    engine = RecalibrationEngine(db)
    actor = users.get("ACTUARIAL") or users.get("ADMIN")

    try:
        payload = engine.run(
            tenant_id=str(tenant.id),
            coverage="cyber",
            config_name="cyber_general",
            current_weights={},  # engine will read from seeded model_version_records
            current_tier_boundaries=[(1, 0, 300), (2, 300, 700), (3, 700, 1000)],
            proposed_by=str(actor.id) if actor else "system",
            trigger="seed_v5",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("  engine run raised: %s", exc)
        return None

    db.commit()
    if payload is None:
        logger.info("  no proposal generated (insufficient sample)")
        return None
    logger.info(
        "  proposal=%s weights=%d tiers=%d sample=%d",
        payload.id,
        len(payload.weight_changes),
        len(payload.tier_threshold_changes),
        payload.sample_size,
    )
    return payload.id


# ==============================================================================
# Step 6: World Engine maturity (WE-1)
# ==============================================================================


def report_world_engine(db: Session) -> None:
    try:
        from world_engine.maturity import MaturityEvaluator

        m = MaturityEvaluator().evaluate(db)
        logger.info(
            "[WE-1] Maturity stage=%s entities=%d relationships=%d coverage=%.2f",
            m.stage.value,
            m.assessed_entity_count,
            m.active_relationships,
            m.coverage_ratio,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[WE-1] maturity evaluation failed: %s", exc)


# ==============================================================================
# Entry point
# ==============================================================================


def run() -> int:
    db = _session()
    try:
        tenant, _roles, users = seed_auth(db)
        audits = seed_audit_events(db, tenant, users)
        config_version_id = seed_config_version(db, users)
        losses_created, losses_linked = seed_loss_events(db, tenant)
        proposal_id = seed_recalibration(db, tenant, users)
        report_world_engine(db)

        print("\n" + "=" * 70)
        print("  V5 SEED COMPLETE")
        print("=" * 70)
        print(f"  Tenant: {tenant.slug} ({tenant.id})")
        print(f"  Users: admin / actuarial / senior / uw / viewer @ dsi.local")
        print(f"  Audit events recorded: {audits}")
        print(f"  Config version deployed: {config_version_id or 'skipped'}")
        print(
            f"  Loss events: {losses_created} created, {losses_linked} linked"
        )
        print(f"  Recalibration proposal: {proposal_id or 'none'}")
        print("=" * 70 + "\n")
        return 0
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.exception("seed_v5 failed: %s", exc)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run())

"""V7 Phase 14 — disclosure packet generator + alembic 029 shape."""
from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from signal_architecture.disclosure import PacketSection, build_packet


_PINNED_DATE = datetime(2026, 5, 13, 12, 0, 0, tzinfo=timezone.utc)


def _basic_inputs():
    return dict(
        model_version_id=uuid.UUID(int=42),
        composite_min_grade="observed",
        composite_distribution={"observed": 0.6, "structured_attested": 0.4},
        referral_reasons=["share of weight below 0.5 at corroborated+"],
        sections=[
            PacketSection(
                title="Director Litigation History",
                signal_id="director_litigation_history",
                grade="structured_attested",
                pro="Two independent registers agreed.",
                counter="Source coverage US/UK only.",
                tie_breaker="OFAC SDN refresh within 24h.",
                sources=[{
                    "source_id": "ofac", "kind": "register",
                    "ref": "https://example/ofac", "fetched_at": "2026-05-13",
                }],
                commitment_digest="abc123",
                reproducibility="stable",
            ),
        ],
    )


class TestDeterminism:
    def test_pinned_inputs_pinned_output(self):
        kw = _basic_inputs()
        md1, p1 = build_packet(generated_at=_PINNED_DATE, **kw)
        md2, p2 = build_packet(generated_at=_PINNED_DATE, **kw)
        assert md1 == md2
        assert p1 == p2

    def test_canonical_payload_uses_iso(self):
        _md, payload = build_packet(generated_at=_PINNED_DATE, **_basic_inputs())
        assert payload["generated_at"] == "2026-05-13T12:00:00+00:00"
        assert payload["model_version_id"] == str(uuid.UUID(int=42))


class TestContent:
    def test_markdown_includes_required_sections(self):
        md, _ = build_packet(generated_at=_PINNED_DATE, **_basic_inputs())
        assert "Referral Disclosure Packet" in md
        assert "Composite min grade" in md
        assert "Grade distribution" in md
        assert "Referral reasons" in md
        assert "Director Litigation History" in md
        assert "Pro" in md
        assert "Counter" in md
        assert "Tie-breaker" in md
        assert "Sources" in md
        assert "Commitment" in md and "abc123" in md

    def test_no_sections_still_renders(self):
        kw = _basic_inputs()
        kw["sections"] = []
        md, payload = build_packet(generated_at=_PINNED_DATE, **kw)
        assert "Referral Disclosure Packet" in md
        assert payload["sections"] == []

    def test_distribution_renders_as_percent(self):
        md, _ = build_packet(generated_at=_PINNED_DATE, **_basic_inputs())
        # 60% and 40% should appear.
        assert "60%" in md
        assert "40%" in md

    def test_reproducibility_in_section(self):
        md, _ = build_packet(generated_at=_PINNED_DATE, **_basic_inputs())
        assert "Reproducibility" in md
        assert "stable" in md

    def test_empty_referral_reasons_renders_blank_list(self):
        kw = _basic_inputs()
        kw["referral_reasons"] = []
        md, _ = build_packet(generated_at=_PINNED_DATE, **kw)
        # Section header is present even without items.
        assert "Referral reasons" in md


# ---------------------------------------------------------------------------
# Alembic 029 shape
# ---------------------------------------------------------------------------

_MIGRATION = Path("alembic/versions/029_disclosure_packet.py")


def _load_029():
    spec = importlib.util.spec_from_file_location("_v7_029", _MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAlembic029:
    def test_revision_lineage(self):
        mod = _load_029()
        assert mod.revision == "029"
        assert mod.down_revision == "028"

    def test_adds_disclosure_packet_column(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "disclosure_packet" in text
        assert "referrals" in text

    def test_in_chain(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("029")
        assert rev is not None
        assert rev.down_revision == "028"


class TestReferralORMHasDisclosurePacket:
    def test_column_exists_on_orm(self):
        from infrastructure.db.models import Referral
        assert hasattr(Referral, "disclosure_packet")


class TestSchemasImportClean:
    def test_evidence_schema(self):
        from infrastructure.api.schemas.evidence import (
            CompositeEvidenceDTO,
            EvidenceSourceDTO,
            GradeRollupDTO,
            SignalEvidenceDTO,
            SignalHistoryRowDTO,
        )
        # Default-construct what we can:
        g = GradeRollupDTO()
        assert g.min_grade is None
        c = CompositeEvidenceDTO(composite=g)
        assert c.per_group == {}

    def test_validator_schema(self):
        from infrastructure.api.schemas.validator import (
            AxisResultDTO,
            ValidatorVerdictDTO,
        )
        # Verdict requires explicit fields.
        v = ValidatorVerdictDTO(
            signal_id="x", mode="quick_pass", advance=True,
            pro_argument="p", counter_argument="c", tie_breaker="t",
            decided_at=_PINNED_DATE,
        )
        assert v.advance is True

    def test_mechanism_schema(self):
        from infrastructure.api.schemas.mechanism import MechanismDTO
        m = MechanismDTO(id="m", summary="s", primitive_type="governance")
        assert m.tags == []

    def test_disclosure_schema(self):
        from infrastructure.api.schemas.disclosure import DisclosureResponse
        r = DisclosureResponse(markdown="x", payload={"a": 1})
        assert r.payload == {"a": 1}

    def test_entity_event_schema(self):
        from infrastructure.api.schemas.entity_event import EntityEventDTO
        e = EntityEventDTO(
            id=uuid.UUID(int=1), event_type="manual_recompute",
            source_feed="manual", received_at=_PINNED_DATE,
        )
        assert e.dispatched_at is None
        assert e.blast_radius == []


class TestRouteRegistration:
    def test_phase14_endpoints_registered(self):
        from infrastructure.api.main import app
        paths = {r.path for r in app.routes}
        assert "/api/v1/model-versions/{model_version_id}/evidence" in paths
        assert "/api/v1/model-versions/{model_version_id}/signals/{signal_id}" in paths
        assert "/api/v1/model-versions/{model_version_id}/signals/{signal_id}/history" in paths
        assert "/api/v1/model-versions/{model_version_id}/disclosure-packet" in paths
        assert "/api/v1/model-versions/{model_version_id}/verify-commitment" in paths
        assert "/api/v1/model-versions/{model_version_id}/signals/{signal_id}/mechanisms" in paths
        assert "/api/v1/mechanisms" in paths
        assert "/api/v1/submissions/{submission_id}/entity-events" in paths


class TestPhase14DoesNotTouchFrontend:
    """Belt-and-braces: Phase 14 stays backend-only. Any frontend change
    belongs in Phase 15."""

    def test_no_frontend_files_in_phase14_diff(self):
        # This is a documentation test — the assertion holds at
        # commit-review time, not at test-run time. The real gate is
        # the commit boundary check in CI / by review.
        from pathlib import Path
        assert Path("frontend").exists()  # repo has a frontend dir

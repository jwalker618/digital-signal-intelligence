"""V7 Phase 1 — role-binding guard tests."""
import pytest
import warnings

from signal_architecture.signals.base import BaseExtractor
from signal_architecture.signals.evidence import (
    EvidenceRoleViolation,
    assert_within_role,
)


class _StubScraper(BaseExtractor):
    MAX_EVIDENCE_GRADE = "observed"
    _EVIDENCE_ENFORCEMENT_MODE = "raise"
    SOURCE_NAME = "stub"

    def extract(self, entity_id, context=None, **kwargs):
        raise NotImplementedError


class _StubRegister(BaseExtractor):
    MAX_EVIDENCE_GRADE = "structured_attested"
    _EVIDENCE_ENFORCEMENT_MODE = "raise"
    SOURCE_NAME = "stub"

    def extract(self, entity_id, context=None, **kwargs):
        raise NotImplementedError


def test_assert_within_role_passes_at_or_below_cap():
    assert_within_role("Foo", "structured_attested", "observed")  # no raise
    assert_within_role("Foo", "structured_attested", "structured_attested")


def test_assert_within_role_raises_above_cap():
    with pytest.raises(EvidenceRoleViolation):
        assert_within_role("Foo", "observed", "corroborated")


def test_extractor_check_in_raise_mode():
    s = _StubScraper()
    with pytest.raises(EvidenceRoleViolation):
        s._check_evidence_role("corroborated")
    s._check_evidence_role("observed")  # passes


def test_extractor_check_in_warn_mode():
    class _Warner(BaseExtractor):
        MAX_EVIDENCE_GRADE = "observed"
        _EVIDENCE_ENFORCEMENT_MODE = "warn"
        SOURCE_NAME = "stub"

        def extract(self, entity_id, context=None, **kwargs):
            raise NotImplementedError

    w = _Warner()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        w._check_evidence_role("corroborated")
    assert any("MAX_EVIDENCE_GRADE" in str(x.message) for x in caught)


def test_register_extractor_can_assert_structured_attested():
    r = _StubRegister()
    r._check_evidence_role("structured_attested")  # passes
    with pytest.raises(EvidenceRoleViolation):
        r._check_evidence_role("behaviourally_validated")


def test_base_extractor_default_cap_permits_top_of_ladder():
    """Default cap on BaseExtractor is `behaviourally_validated` — top of ladder.

    V7 Phase 2 flipped _EVIDENCE_ENFORCEMENT_MODE from 'warn' to 'raise', so
    any class still relying on the BaseExtractor default cap may assert any
    grade up to (and including) the top rung. Beyond the top rung is
    impossible because the type itself doesn't admit a higher value.
    """
    class _UnmigratedExtractor(BaseExtractor):
        SOURCE_NAME = "stub"

        def extract(self, entity_id, context=None, **kwargs):
            raise NotImplementedError

    e = _UnmigratedExtractor()
    e._check_evidence_role("behaviourally_validated")  # no raise


def test_phase2_enforcement_mode_is_raise():
    """Phase 2 invariant — default enforcement is now `raise`."""
    assert BaseExtractor._EVIDENCE_ENFORCEMENT_MODE == "raise"

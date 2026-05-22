"""v8 Phase 4 -- verify the cyber config parses with signal_remediation.

Loads coverages/cyber/config.yaml via the production compiler path and
asserts every authored remediation block is well-formed per the
SignalRemediation schema. This is the canary test that catches a typo
in the YAML before it reaches a demo.
"""
from __future__ import annotations

import pytest

from infrastructure.models.compiler import get_config
from infrastructure.models.config_schema import (
    RemediationEffort,
    SignalRemediation,
)


# Signals that MUST have an authored remediation entry in cyber_general.
# These are the demo-relevant drag signals (Acme's MFA gap, security
# training, IR plan are the demo storyboard).
_REQUIRED_REMEDIATION_SIGNALS: set[str] = {
    "mfa_enabled",
    "security_training",
    "incident_response_plan",
    "edr_deployed",
    "immutable_backups",
    "recent_incident",
    "tls_configuration",
    "security_headers",
    "email_authentication",
    "dnssec_status",
    "software_currency",
    "cve_exposure",
    "waf_presence",
}


@pytest.fixture(scope="module")
def cyber_config():
    """Load cyber_general via the production compiler."""
    return get_config("cyber", "cyber_general")


class TestCyberRemediationLoads:
    def test_signal_remediation_present(self, cyber_config):
        assert cyber_config.signal_remediation is not None
        assert isinstance(cyber_config.signal_remediation, dict)

    def test_remediation_count_at_least_demo_required(self, cyber_config):
        assert len(cyber_config.signal_remediation) >= len(_REQUIRED_REMEDIATION_SIGNALS)


class TestRequiredSignalsCovered:
    @pytest.mark.parametrize("signal_id", sorted(_REQUIRED_REMEDIATION_SIGNALS))
    def test_signal_has_remediation(self, cyber_config, signal_id):
        assert signal_id in cyber_config.signal_remediation, (
            f"cyber_general signal_remediation must cover {signal_id} "
            f"(used in v8 demo)"
        )


class TestRemediationShape:
    def test_every_entry_is_typed(self, cyber_config):
        for sig_id, rem in cyber_config.signal_remediation.items():
            assert isinstance(rem, SignalRemediation), f"{sig_id} -> {type(rem)}"

    def test_every_entry_has_valid_effort(self, cyber_config):
        for sig_id, rem in cyber_config.signal_remediation.items():
            assert rem.effort in {
                RemediationEffort.LOW,
                RemediationEffort.MEDIUM,
                RemediationEffort.HIGH,
            }, f"{sig_id} has invalid effort {rem.effort}"

    def test_headlines_within_length_cap(self, cyber_config):
        for sig_id, rem in cyber_config.signal_remediation.items():
            assert 0 < len(rem.headline) <= 120, (
                f"{sig_id}: headline length {len(rem.headline)} out of bounds"
            )

    def test_descriptions_within_length_cap(self, cyber_config):
        for sig_id, rem in cyber_config.signal_remediation.items():
            assert 0 < len(rem.description) <= 600, (
                f"{sig_id}: description length {len(rem.description)} out of bounds"
            )

    def test_costs_non_negative(self, cyber_config):
        for sig_id, rem in cyber_config.signal_remediation.items():
            assert rem.typical_cost_usd >= 0, f"{sig_id} has negative cost"

    def test_evidence_required_non_empty(self, cyber_config):
        for sig_id, rem in cyber_config.signal_remediation.items():
            assert rem.evidence_required.strip(), f"{sig_id} has empty evidence_required"


class TestNonCyberCoveragesNoBlockOk:
    """Other coverages may omit signal_remediation entirely -- they parse
    cleanly via Optional[Dict[...]] = None default."""

    def test_casualty_gl_loads_without_remediation(self):
        # casualty has no signal_remediation block authored yet; should be None.
        cfg = get_config("casualty", "casualty_gl")
        # Either None or a dict -- both valid. What matters is parse success.
        assert cfg.signal_remediation is None or isinstance(cfg.signal_remediation, dict)

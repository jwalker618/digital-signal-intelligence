"""
Unit Tests for DSI Multiplexer (Phase V4)

Tests the multi-configuration racing and optimal selection functionality.
"""

import pytest
from typing import Any, Dict, List

from signal_architecture.multiplexer import (
    DSIMultiplexer,
    ConfigArbiter,
    MultiplexerConfig,
    ConfigCandidate,
    CandidateResult,
    MultiplexerResult,
    RoutingConstraint,
    ConstraintOperator,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_configs():
    """Sample configuration data for testing."""
    return [
        {
            "cyber_general": {
                "metadata": {
                    "name": "Cyber General",
                    "product_types": ["cyber_liability"],
                    "applicable_markets": ["us", "uk"],
                    "model_specificity": 1,
                    "routing_constraints": [],
                },
                "signal_registry": [
                    {"id": "sig_a", "inference_utility_function": "func_a"},
                    {"id": "sig_b", "inference_utility_function": "func_b"},
                ],
            }
        },
        {
            "cyber_tech": {
                "metadata": {
                    "name": "Cyber Tech",
                    "product_types": ["cyber_liability"],
                    "applicable_markets": ["us"],
                    "model_specificity": 2,
                    "routing_constraints": [
                        {"field": "industry", "operator": "==", "value": "tech"},
                    ],
                },
                "signal_registry": [
                    {"id": "sig_a", "inference_utility_function": "func_a"},
                    {"id": "sig_c", "inference_utility_function": "func_c"},
                ],
            }
        },
        {
            "cyber_sme": {
                "metadata": {
                    "name": "Cyber SME",
                    "product_types": ["cyber_liability"],
                    "applicable_markets": ["us", "uk"],
                    "model_specificity": 2,
                    "routing_constraints": [
                        {"field": "revenue", "operator": "<", "value": 50000000},
                    ],
                },
                "signal_registry": [
                    {"id": "sig_a", "inference_utility_function": "func_a"},
                    {"id": "sig_d", "inference_utility_function": "func_d"},
                ],
            }
        },
    ]


@pytest.fixture
def multiplexer(sample_configs):
    """Create a multiplexer with sample configs."""
    def loader(coverage_id):
        if coverage_id == "cyber":
            return sample_configs
        return []

    return DSIMultiplexer(config_loader=loader)


@pytest.fixture
def arbiter():
    """Create an arbiter with default config."""
    return ConfigArbiter()


# =============================================================================
# DSIMultiplexer Tests
# =============================================================================

class TestDSIMultiplexer:
    """Tests for DSIMultiplexer class."""

    def test_identify_candidates_all_match(self, multiplexer):
        """Test candidate identification when all configs match."""
        user_input = {
            "product_type": "cyber_liability",
            "market": "us",
        }

        candidates = multiplexer.identify_candidates("cyber", user_input)

        # All 3 configs match product_type and market
        # But cyber_tech requires industry=tech, cyber_sme requires revenue<50M
        # Since these fields are missing and required_in_input=False (default),
        # they should pass
        assert len(candidates) == 3

    def test_identify_candidates_market_filter(self, multiplexer):
        """Test that market filter works."""
        user_input = {
            "product_type": "cyber_liability",
            "market": "uk",
        }

        candidates = multiplexer.identify_candidates("cyber", user_input)

        # cyber_tech only supports "us", so should be excluded
        assert len(candidates) == 2
        config_ids = [c.config_id for c in candidates]
        assert "cyber_general" in config_ids
        assert "cyber_sme" in config_ids
        assert "cyber_tech" not in config_ids

    def test_identify_candidates_routing_constraint(self, multiplexer):
        """Test routing constraint filtering."""
        user_input = {
            "product_type": "cyber_liability",
            "market": "us",
            "revenue": 100000000,  # 100M - fails SME constraint
        }

        candidates = multiplexer.identify_candidates("cyber", user_input)

        # cyber_sme should be excluded (revenue >= 50M)
        config_ids = [c.config_id for c in candidates]
        assert "cyber_sme" not in config_ids
        assert "cyber_general" in config_ids

    def test_optimize_signals_deduplication(self, multiplexer):
        """Test signal deduplication across candidates."""
        candidates = [
            ConfigCandidate(
                coverage_id="cyber",
                config_id="cyber_general",
                config={
                    "signal_registry": [
                        {"id": "sig_a", "inference_utility_function": "func_a"},
                        {"id": "sig_b", "inference_utility_function": "func_b"},
                    ]
                },
                model_specificity=1,
                routing_constraints=[],
            ),
            ConfigCandidate(
                coverage_id="cyber",
                config_id="cyber_tech",
                config={
                    "signal_registry": [
                        {"id": "sig_a", "inference_utility_function": "func_a"},
                        {"id": "sig_c", "inference_utility_function": "func_c"},
                    ]
                },
                model_specificity=2,
                routing_constraints=[],
            ),
        ]

        signal_map = multiplexer.optimize_signals(candidates)

        # Should have 3 unique signals (sig_a, sig_b, sig_c)
        assert len(signal_map) == 3
        assert "sig_a" in signal_map
        assert "sig_b" in signal_map
        assert "sig_c" in signal_map


class TestConstraintEvaluation:
    """Tests for routing constraint evaluation."""

    def test_less_than_passes(self, multiplexer):
        """Test < constraint passing."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LT,
                value=50000000,
            )
        ]

        assert multiplexer._check_constraints(constraints, {"revenue": 10000000})
        assert not multiplexer._check_constraints(constraints, {"revenue": 50000000})
        assert not multiplexer._check_constraints(constraints, {"revenue": 100000000})

    def test_greater_than_or_equal_passes(self, multiplexer):
        """Test >= constraint passing."""
        constraints = [
            RoutingConstraint(
                field="employees",
                operator=ConstraintOperator.GTE,
                value=1000,
            )
        ]

        assert multiplexer._check_constraints(constraints, {"employees": 1000})
        assert multiplexer._check_constraints(constraints, {"employees": 5000})
        assert not multiplexer._check_constraints(constraints, {"employees": 500})

    def test_missing_field_not_required(self, multiplexer):
        """Test missing field with required_in_input=False."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LT,
                value=50000000,
                required_in_input=False,
            )
        ]

        # Missing field should pass when not required
        assert multiplexer._check_constraints(constraints, {})

    def test_missing_field_required(self, multiplexer):
        """Test missing field with required_in_input=True."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LT,
                value=50000000,
                required_in_input=True,
            )
        ]

        # Missing field should fail when required
        assert not multiplexer._check_constraints(constraints, {})


# =============================================================================
# ConfigArbiter Tests
# =============================================================================

class TestConfigArbiter:
    """Tests for ConfigArbiter class."""

    def test_select_valid_over_declined(self, arbiter):
        """Test that valid results are preferred over declined."""
        results = [
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_general",
                model_specificity=1,
                composite_score=500,
                tier=3,
                tier_label="STANDARD",
                decision="DECLINE",
                signal_completeness=0.9,
                signals_returned=9,
                signals_defined=10,
            ),
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_tech",
                model_specificity=2,
                composite_score=600,
                tier=2,
                tier_label="PREFERRED",
                decision="APPROVE",
                signal_completeness=0.8,
                signals_returned=8,
                signals_defined=10,
            ),
        ]

        winner = arbiter.select_best_outcome(results)

        assert winner is not None
        assert winner.config_id == "cyber_tech"
        assert winner.decision == "APPROVE"

    def test_prefer_higher_confidence(self, arbiter):
        """Test that higher confidence results are preferred."""
        results = [
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_general",
                model_specificity=1,
                composite_score=600,
                tier=2,
                tier_label="PREFERRED",
                decision="APPROVE",
                signal_completeness=0.5,  # Low confidence
                signals_returned=5,
                signals_defined=10,
            ),
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_tech",
                model_specificity=2,
                composite_score=500,
                tier=3,
                tier_label="STANDARD",
                decision="APPROVE",
                signal_completeness=0.9,  # High confidence
                signals_returned=9,
                signals_defined=10,
            ),
        ]

        winner = arbiter.select_best_outcome(results)

        assert winner is not None
        assert winner.config_id == "cyber_tech"
        assert winner.signal_completeness == 0.9

    def test_prefer_higher_specificity_when_confidence_equal(self, arbiter):
        """Test that higher specificity wins when confidence is equal."""
        results = [
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_general",
                model_specificity=1,
                composite_score=500,
                tier=3,
                tier_label="STANDARD",
                decision="APPROVE",
                signal_completeness=0.85,
                signals_returned=17,
                signals_defined=20,
            ),
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_tech",
                model_specificity=2,
                composite_score=500,
                tier=3,
                tier_label="STANDARD",
                decision="APPROVE",
                signal_completeness=0.85,
                signals_returned=17,
                signals_defined=20,
            ),
        ]

        winner = arbiter.select_best_outcome(results)

        assert winner is not None
        assert winner.config_id == "cyber_tech"
        assert winner.model_specificity == 2

    def test_all_declined_returns_most_specific(self, arbiter):
        """Test that when all decline, most specific is returned."""
        results = [
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_general",
                model_specificity=1,
                composite_score=100,
                tier=5,
                tier_label="DECLINE",
                decision="DECLINE",
                signal_completeness=0.9,
                signals_returned=9,
                signals_defined=10,
            ),
            CandidateResult(
                coverage_id="cyber",
                config_id="cyber_tech",
                model_specificity=2,
                composite_score=100,
                tier=5,
                tier_label="DECLINE",
                decision="DECLINE",
                signal_completeness=0.9,
                signals_returned=9,
                signals_defined=10,
            ),
        ]

        winner = arbiter.select_best_outcome(results)

        assert winner is not None
        assert winner.config_id == "cyber_tech"  # Higher specificity
        assert winner.decision == "DECLINE"

    def test_empty_results_returns_none(self, arbiter):
        """Test that empty results returns None."""
        winner = arbiter.select_best_outcome([])
        assert winner is None

    def test_arbitrate_updates_multiplexer_result(self, arbiter):
        """Test that arbitrate() updates the MultiplexerResult."""
        candidate = CandidateResult(
            coverage_id="cyber",
            config_id="cyber_general",
            model_specificity=1,
            composite_score=500,
            tier=3,
            tier_label="STANDARD",
            decision="APPROVE",
            signal_completeness=0.9,
            signals_returned=9,
            signals_defined=10,
        )

        mux_result = MultiplexerResult(
            entity_id="test-entity",
            coverage_id="cyber",
            candidates_evaluated=1,
            candidate_results=[candidate],
        )

        updated = arbiter.arbitrate(mux_result)

        assert updated.selected_config_id == "cyber_general"
        assert updated.selected_result == candidate
        assert updated.has_winner is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestMultiplexerIntegration:
    """Integration tests for the full multiplexer flow."""

    def test_full_execute_flow(self, multiplexer):
        """Test full execute flow with candidates."""
        import asyncio

        user_input = {
            "client_name": "Test Corp",
            "product_type": "cyber_liability",
            "market": "us",
        }

        result = asyncio.get_event_loop().run_until_complete(
            multiplexer.execute(
                coverage_id="cyber",
                user_input=user_input,
                entity_id="test-corp",
            )
        )

        assert result.entity_id == "test-corp"
        assert result.coverage_id == "cyber"
        assert result.candidates_evaluated >= 1
        assert len(result.candidate_results) >= 1

    def test_execute_no_candidates(self, multiplexer):
        """Test execute with no matching candidates."""
        import asyncio

        user_input = {
            "client_name": "Test Corp",
            "product_type": "unknown_product",  # No config matches this
            "market": "us",
        }

        result = asyncio.get_event_loop().run_until_complete(
            multiplexer.execute(
                coverage_id="cyber",
                user_input=user_input,
            )
        )

        assert result.candidates_evaluated == 0
        assert len(result.candidate_results) == 0

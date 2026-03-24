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
# Phase V4.1: Enhanced Constraint Tests
# =============================================================================

class TestConstraintTypeCoercion:
    """Tests for type coercion in constraint evaluation (Phase V4.1)."""

    def test_string_to_number_coercion(self, multiplexer):
        """Test that string values are coerced to numbers for comparison."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LTE,
                value=50000000,  # int target
            )
        ]

        # String input should be coerced to float for comparison
        assert multiplexer._check_constraints(constraints, {"revenue": "40000000"})
        assert multiplexer._check_constraints(constraints, {"revenue": "50000000"})
        assert not multiplexer._check_constraints(constraints, {"revenue": "60000000"})

    def test_number_to_string_target_coercion(self, multiplexer):
        """Test that string target values are coerced to numbers."""
        constraints = [
            RoutingConstraint(
                field="limit",
                operator=ConstraintOperator.GT,
                value="5000000",  # string target
            )
        ]

        # Numeric input with string target
        assert multiplexer._check_constraints(constraints, {"limit": 10000000})
        assert not multiplexer._check_constraints(constraints, {"limit": 5000000})
        assert not multiplexer._check_constraints(constraints, {"limit": 1000000})

    def test_invalid_string_conversion_fails(self, multiplexer):
        """Test that invalid string conversion fails safely."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LT,
                value=50000000,
            )
        ]

        # Non-numeric string should fail
        assert not multiplexer._check_constraints(constraints, {"revenue": "not_a_number"})
        assert not multiplexer._check_constraints(constraints, {"revenue": "fifty million"})

    def test_float_coercion_precision(self, multiplexer):
        """Test float coercion handles decimal values."""
        constraints = [
            RoutingConstraint(
                field="rate",
                operator=ConstraintOperator.LTE,
                value=0.05,
            )
        ]

        assert multiplexer._check_constraints(constraints, {"rate": "0.03"})
        assert multiplexer._check_constraints(constraints, {"rate": "0.05"})
        assert not multiplexer._check_constraints(constraints, {"rate": "0.06"})


class TestConstraintBoundaryValues:
    """Tests for boundary value handling in constraints (Phase V4.1)."""

    def test_less_than_or_equal_boundary(self, multiplexer):
        """Test <= constraint at exact boundary."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LTE,
                value=50000000,
            )
        ]

        # At boundary
        assert multiplexer._check_constraints(constraints, {"revenue": 50000000})
        # Just below
        assert multiplexer._check_constraints(constraints, {"revenue": 49999999})
        # Just above
        assert not multiplexer._check_constraints(constraints, {"revenue": 50000001})

    def test_greater_than_or_equal_boundary(self, multiplexer):
        """Test >= constraint at exact boundary."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.GTE,
                value=50000000,
            )
        ]

        # At boundary
        assert multiplexer._check_constraints(constraints, {"revenue": 50000000})
        # Just above
        assert multiplexer._check_constraints(constraints, {"revenue": 50000001})
        # Just below
        assert not multiplexer._check_constraints(constraints, {"revenue": 49999999})

    def test_less_than_boundary(self, multiplexer):
        """Test < constraint at exact boundary."""
        constraints = [
            RoutingConstraint(
                field="limit",
                operator=ConstraintOperator.LT,
                value=5000000,
            )
        ]

        # At boundary (should fail for strict <)
        assert not multiplexer._check_constraints(constraints, {"limit": 5000000})
        # Just below
        assert multiplexer._check_constraints(constraints, {"limit": 4999999})
        # Just above
        assert not multiplexer._check_constraints(constraints, {"limit": 5000001})

    def test_greater_than_boundary(self, multiplexer):
        """Test > constraint at exact boundary."""
        constraints = [
            RoutingConstraint(
                field="employees",
                operator=ConstraintOperator.GT,
                value=1000,
            )
        ]

        # At boundary (should fail for strict >)
        assert not multiplexer._check_constraints(constraints, {"employees": 1000})
        # Just above
        assert multiplexer._check_constraints(constraints, {"employees": 1001})
        # Just below
        assert not multiplexer._check_constraints(constraints, {"employees": 999})


class TestConstraintOperators:
    """Tests for all constraint operators (Phase V4.1)."""

    def test_equality_operator(self, multiplexer):
        """Test == operator for exact matches."""
        constraints = [
            RoutingConstraint(
                field="industry",
                operator=ConstraintOperator.EQ,
                value="tech",
            )
        ]

        assert multiplexer._check_constraints(constraints, {"industry": "tech"})
        assert not multiplexer._check_constraints(constraints, {"industry": "healthcare"})
        assert not multiplexer._check_constraints(constraints, {"industry": "TECH"})  # Case sensitive

    def test_not_equal_operator(self, multiplexer):
        """Test != operator for exclusion."""
        constraints = [
            RoutingConstraint(
                field="status",
                operator=ConstraintOperator.NEQ,
                value="blocked",
            )
        ]

        assert multiplexer._check_constraints(constraints, {"status": "active"})
        assert multiplexer._check_constraints(constraints, {"status": "pending"})
        assert not multiplexer._check_constraints(constraints, {"status": "blocked"})

    def test_numeric_equality(self, multiplexer):
        """Test == operator with numeric values."""
        constraints = [
            RoutingConstraint(
                field="tier",
                operator=ConstraintOperator.EQ,
                value=2,
            )
        ]

        assert multiplexer._check_constraints(constraints, {"tier": 2})
        assert not multiplexer._check_constraints(constraints, {"tier": 1})
        assert not multiplexer._check_constraints(constraints, {"tier": 3})


class TestMultipleConstraints:
    """Tests for multiple constraint evaluation (AND logic) (Phase V4.1)."""

    def test_multiple_constraints_all_pass(self, multiplexer):
        """Test that all constraints must pass (AND logic)."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LTE,
                value=50000000,
            ),
            RoutingConstraint(
                field="limit",
                operator=ConstraintOperator.LTE,
                value=5000000,
            ),
        ]

        # Both pass
        assert multiplexer._check_constraints(
            constraints, {"revenue": 40000000, "limit": 3000000}
        )
        # Both at boundary
        assert multiplexer._check_constraints(
            constraints, {"revenue": 50000000, "limit": 5000000}
        )

    def test_multiple_constraints_one_fails(self, multiplexer):
        """Test that if any constraint fails, the check fails."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LTE,
                value=50000000,
            ),
            RoutingConstraint(
                field="limit",
                operator=ConstraintOperator.LTE,
                value=5000000,
            ),
        ]

        # First fails
        assert not multiplexer._check_constraints(
            constraints, {"revenue": 60000000, "limit": 3000000}
        )
        # Second fails
        assert not multiplexer._check_constraints(
            constraints, {"revenue": 40000000, "limit": 10000000}
        )
        # Both fail
        assert not multiplexer._check_constraints(
            constraints, {"revenue": 60000000, "limit": 10000000}
        )

    def test_multiple_constraints_mixed_required(self, multiplexer):
        """Test multiple constraints with different required_in_input settings."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LTE,
                value=50000000,
                required_in_input=True,  # Required
            ),
            RoutingConstraint(
                field="employees",
                operator=ConstraintOperator.LTE,
                value=500,
                required_in_input=False,  # Optional
            ),
        ]

        # Both present and pass
        assert multiplexer._check_constraints(
            constraints, {"revenue": 40000000, "employees": 200}
        )
        # Only required present
        assert multiplexer._check_constraints(
            constraints, {"revenue": 40000000}
        )
        # Required missing - fails
        assert not multiplexer._check_constraints(
            constraints, {"employees": 200}
        )
        # Both present, one fails
        assert not multiplexer._check_constraints(
            constraints, {"revenue": 40000000, "employees": 1000}
        )

    def test_empty_constraints_always_passes(self, multiplexer):
        """Test that empty constraint list always passes."""
        assert multiplexer._check_constraints([], {})
        assert multiplexer._check_constraints([], {"revenue": 100000000})

    def test_three_constraint_chain(self, multiplexer):
        """Test chain of three constraints mimicking SME model profile."""
        constraints = [
            RoutingConstraint(
                field="revenue",
                operator=ConstraintOperator.LTE,
                value=50000000,
                required_in_input=True,
            ),
            RoutingConstraint(
                field="limit",
                operator=ConstraintOperator.LTE,
                value=5000000,
                required_in_input=True,
            ),
            RoutingConstraint(
                field="employees",
                operator=ConstraintOperator.LTE,
                value=500,
                required_in_input=False,
            ),
        ]

        # Perfect SME candidate
        assert multiplexer._check_constraints(
            constraints, {"revenue": 25000000, "limit": 2000000, "employees": 100}
        )
        # SME candidate without optional field
        assert multiplexer._check_constraints(
            constraints, {"revenue": 25000000, "limit": 2000000}
        )
        # Too large (revenue exceeds)
        assert not multiplexer._check_constraints(
            constraints, {"revenue": 75000000, "limit": 2000000, "employees": 100}
        )
        # Missing required field
        assert not multiplexer._check_constraints(
            constraints, {"revenue": 25000000, "employees": 100}
        )


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

        result = asyncio.run(
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

        result = asyncio.run(
            multiplexer.execute(
                coverage_id="cyber",
                user_input=user_input,
            )
        )

        assert result.candidates_evaluated == 0
        assert len(result.candidate_results) == 0

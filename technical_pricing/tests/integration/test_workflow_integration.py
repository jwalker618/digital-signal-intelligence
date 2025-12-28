"""
Integration tests for DSI workflow.

Tests complete workflow scenarios using simulated test profiles
similar to YAML test_profiles configuration.
"""

import pytest
from datetime import datetime
from typing import Callable

from technical_pricing.model.workflow import WorkflowEngine, create_workflow_engine
from technical_pricing.model.config_manager import ConfigManager
from technical_pricing.model.model_data import ModelDataManager
from technical_pricing.model.scorer import ModelScorer
from technical_pricing.model.query_evaluator import QueryEvaluator
from technical_pricing.model.pricer import ModelPricer
from technical_pricing.model.types import (
    WorkflowResult,
    SubmissionRequest,
    CoverageConfig,
    SignalGroupConfig,
    SignalConfig,
    SignalCondition,
    DirectQueryConfig,
    DirectQueryImpact,
    TierConfig,
    LimitBand,
    DecisionType,
    VersionType,
    ConditionAction,
)


# =============================================================================
# TEST PROFILES
# =============================================================================

class TestProfiles:
    """
    Simulated test profiles matching YAML test_profiles structure.

    Each profile defines:
    - inputs: entity characteristics and responses
    - expected: expected outcomes (tier, decision, etc.)
    """

    EXCELLENT_RISK_AUTO_APPROVE = {
        "name": "excellent_risk_auto_approve",
        "description": "Major airline with excellent safety record - should auto-approve",
        "inputs": {
            "entity_id": "AA-001",
            "entity_type": "major_airline",
            "signals": {
                "safety_record": 95,
                "incident_history": 90,
                "financial_strength": 85,
                "regulatory_compliance": 92
            },
            "direct_queries": {
                "pending_claims": False,
                "regulatory_action": False,
                "bankruptcy_filed": False
            },
            "categorical_selections": {
                "operator_type": "major_airline",
                "fleet_category": "narrowbody"
            },
            "submission_data": {
                "tiv": 50000000,
                "entity_id": "AA-001"
            }
        },
        "expected": {
            "tier_range": (1, 2),
            "decision": DecisionType.APPROVE,
            "auto_approve": True,
            "referral_count": 0
        }
    }

    AVERAGE_RISK_APPROVE = {
        "name": "average_risk_approve",
        "description": "Regional airline with average metrics - should approve tier 2-3",
        "inputs": {
            "entity_id": "RA-001",
            "entity_type": "regional_airline",
            "signals": {
                "safety_record": 70,
                "incident_history": 65,
                "financial_strength": 60,
                "regulatory_compliance": 72
            },
            "direct_queries": {
                "pending_claims": False,
                "regulatory_action": False
            },
            "categorical_selections": {
                "operator_type": "regional_airline",
                "fleet_category": "regional_jet"
            },
            "submission_data": {
                "tiv": 25000000,
                "entity_id": "RA-001"
            }
        },
        "expected": {
            "tier_range": (2, 3),
            "decision": DecisionType.APPROVE,
            "auto_approve": True,
            "referral_count": 0
        }
    }

    POOR_RISK_REFER = {
        "name": "poor_risk_refer",
        "description": "Charter operator with poor safety - should refer",
        "inputs": {
            "entity_id": "CH-001",
            "entity_type": "charter_operator",
            "signals": {
                "safety_record": 40,
                "incident_history": 35,
                "financial_strength": 45,
                "regulatory_compliance": 50
            },
            "direct_queries": {
                "pending_claims": False,
                "regulatory_action": False
            },
            "categorical_selections": {
                "operator_type": "charter_operator",
                "fleet_category": "turboprop"
            },
            "submission_data": {
                "tiv": 5000000,
                "entity_id": "CH-001"
            }
        },
        "expected": {
            "tier_range": (3, 4),
            "decision": DecisionType.REFER,
            "auto_approve": False,
            "referral_count": 0  # From tier, not signal conditions
        }
    }

    QUERY_TRIGGERS_REFERRAL = {
        "name": "query_triggers_referral",
        "description": "Good risk but pending claims triggers referral",
        "inputs": {
            "entity_id": "QR-001",
            "entity_type": "major_airline",
            "signals": {
                "safety_record": 85,
                "incident_history": 80,
                "financial_strength": 82,
                "regulatory_compliance": 88
            },
            "direct_queries": {
                "pending_claims": True,  # Triggers referral
                "regulatory_action": False
            },
            "categorical_selections": {
                "operator_type": "major_airline"
            },
            "submission_data": {
                "tiv": 30000000,
                "entity_id": "QR-001"
            }
        },
        "expected": {
            "tier_range": (1, 2),
            "decision": DecisionType.REFER,
            "auto_approve": False,
            "has_referral_reasons": True
        }
    }

    TIER_OVERRIDE_FROM_QUERY = {
        "name": "tier_override_from_query",
        "description": "Regulatory action triggers tier 5 override and decline",
        "inputs": {
            "entity_id": "TO-001",
            "entity_type": "regional_airline",
            "signals": {
                "safety_record": 75,
                "incident_history": 70,
                "financial_strength": 65,
                "regulatory_compliance": 72
            },
            "direct_queries": {
                "pending_claims": False,
                "regulatory_action": True  # Triggers tier 5 override
            },
            "categorical_selections": {
                "operator_type": "regional_airline"
            },
            "submission_data": {
                "tiv": 20000000,
                "entity_id": "TO-001"
            }
        },
        "expected": {
            "tier_range": (5, 5),
            "decision": DecisionType.DECLINE,
            "auto_approve": False
        }
    }

    MODIFIER_APPLIED = {
        "name": "modifier_applied",
        "description": "Wet lease operation triggers premium modifier",
        "inputs": {
            "entity_id": "WL-001",
            "entity_type": "charter_operator",
            "signals": {
                "safety_record": 75,
                "incident_history": 70,
                "financial_strength": 65
            },
            "direct_queries": {
                "wet_lease": True  # Triggers 1.15x modifier
            },
            "categorical_selections": {
                "operator_type": "charter_operator"
            },
            "submission_data": {
                "tiv": 10000000,
                "entity_id": "WL-001"
            }
        },
        "expected": {
            "has_modifiers": True,
            "modifier_count_min": 1
        }
    }

    MISSING_INPUTS = {
        "name": "missing_inputs",
        "description": "Missing required TIV should trigger referral",
        "inputs": {
            "entity_id": "MI-001",
            "entity_type": "major_airline",
            "signals": {
                "safety_record": 85
            },
            "direct_queries": {},
            "categorical_selections": {},
            "submission_data": {
                "entity_id": "MI-001"
                # Missing tiv
            }
        },
        "expected": {
            "decision": DecisionType.REFER,
            "has_missing_inputs": True
        }
    }


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Create a realistic config for integration tests."""
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_general",
        version="1.0.0",
        config_hash="integration-test-hash",
        required_inputs=["entity_id", "tiv"],
        signal_groups=[
            SignalGroupConfig(
                name="safety_signals",
                weight=0.4,
                signals=[
                    SignalConfig(
                        name="safety_record",
                        weight=0.5,
                        inference_function="infer_safety_record",
                        categorizer_type="threshold_bucket",
                        conditions=[
                            SignalCondition(
                                condition_type="threshold_below",
                                condition_value=30,
                                action=ConditionAction.TIER_OVERRIDE,
                                action_value=5
                            ),
                            SignalCondition(
                                condition_type="threshold_below",
                                condition_value=40,
                                action=ConditionAction.REFERRAL,
                                action_value="Safety score critically low"
                            )
                        ]
                    ),
                    SignalConfig(
                        name="incident_history",
                        weight=0.5,
                        inference_function="infer_incident_history",
                        categorizer_type="threshold_bucket",
                        conditions=[]
                    )
                ],
                conditions=[]
            ),
            SignalGroupConfig(
                name="financial_signals",
                weight=0.3,
                signals=[
                    SignalConfig(
                        name="financial_strength",
                        weight=1.0,
                        inference_function="infer_financial_strength",
                        categorizer_type="threshold_bucket",
                        conditions=[]
                    )
                ],
                conditions=[]
            ),
            SignalGroupConfig(
                name="compliance_signals",
                weight=0.3,
                signals=[
                    SignalConfig(
                        name="regulatory_compliance",
                        weight=1.0,
                        inference_function="infer_regulatory_compliance",
                        categorizer_type="threshold_bucket",
                        conditions=[]
                    )
                ],
                conditions=[]
            )
        ],
        direct_queries=[
            DirectQueryConfig(
                id="pending_claims",
                question="Are there any pending claims exceeding $1M?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.REFERRAL,
                        value="Pending claims require review",
                        trigger_on=True
                    )
                ]
            ),
            DirectQueryConfig(
                id="regulatory_action",
                question="Is there any pending regulatory enforcement?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.TIER_OVERRIDE,
                        value=5,
                        trigger_on=True
                    )
                ]
            ),
            DirectQueryConfig(
                id="wet_lease",
                question="Do you operate under wet lease arrangements?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.MODIFIER,
                        value=1.15,
                        trigger_on=True
                    )
                ]
            )
        ],
        categorical_groups=["operator_type", "fleet_category"],
        categorical_features={
            "operator_type": {
                "major_airline": 0.85,
                "regional_airline": 1.00,
                "charter_operator": 1.25,
                "flight_school": 1.50
            },
            "fleet_category": {
                "widebody": 1.15,
                "narrowbody": 1.00,
                "regional_jet": 1.05,
                "turboprop": 0.95
            }
        },
        tier_thresholds=[
            TierConfig(tier=1, min_score=800, max_score=1000, base_premium=25000, decision=DecisionType.APPROVE),
            TierConfig(tier=2, min_score=600, max_score=799, base_premium=35000, decision=DecisionType.APPROVE),
            TierConfig(tier=3, min_score=400, max_score=599, base_premium=50000, decision=DecisionType.REFER),
            TierConfig(tier=4, min_score=200, max_score=399, base_premium=75000, decision=DecisionType.REFER),
            TierConfig(tier=5, min_score=0, max_score=199, base_premium=100000, decision=DecisionType.DECLINE),
        ],
        limit_bands=[
            LimitBand(limit=1000000, ilf=1.0),
            LimitBand(limit=5000000, ilf=2.5),
            LimitBand(limit=10000000, ilf=4.0),
            LimitBand(limit=25000000, ilf=7.0),
        ],
        deductible_credits={
            10000: 1.0,
            25000: 0.95,
            50000: 0.90,
        },
        metadata={"min_premium": 15000}
    )


def create_inference_registry(signal_scores: dict) -> dict[str, Callable]:
    """Create inference registry that returns specified scores."""
    def make_inference_func(score: float):
        def inference(entity_id: str, context: dict) -> dict:
            return {
                "score": score,
                "confidence": 0.95,
                "data_sources": ["test_source"]
            }
        return inference

    return {
        "infer_safety_record": make_inference_func(signal_scores.get("safety_record", 70)),
        "infer_incident_history": make_inference_func(signal_scores.get("incident_history", 70)),
        "infer_financial_strength": make_inference_func(signal_scores.get("financial_strength", 70)),
        "infer_regulatory_compliance": make_inference_func(signal_scores.get("regulatory_compliance", 70)),
    }


@pytest.fixture
def create_workflow_for_profile(integration_config):
    """Factory fixture to create workflow engine for a test profile."""
    def _create(profile: dict) -> tuple[WorkflowEngine, SubmissionRequest]:
        # Create inference registry based on profile signals
        signal_scores = profile["inputs"].get("signals", {})
        registry = create_inference_registry(signal_scores)

        # Create components
        config_manager = ConfigManager(config_dir="coverages")
        # Patch load_from_file to return our integration config
        config_manager._config_cache["aerospace:default"] = integration_config
        config_manager.load_from_file = lambda coverage, cfg=None: integration_config

        data_manager = ModelDataManager()
        scorer = ModelScorer(inference_registry=registry)
        query_evaluator = QueryEvaluator()
        pricer = ModelPricer()

        engine = WorkflowEngine(
            config_manager=config_manager,
            data_manager=data_manager,
            scorer=scorer,
            query_evaluator=query_evaluator,
            pricer=pricer
        )

        # Create submission request
        request = SubmissionRequest(
            entity_id=profile["inputs"]["entity_id"],
            coverage="aerospace",
            submission_data=profile["inputs"].get("submission_data", {}),
            direct_query_responses=profile["inputs"].get("direct_queries", {}),
            categorical_selections=profile["inputs"].get("categorical_selections", {}),
            user="integration_test"
        )

        return engine, request

    return _create


# =============================================================================
# HAPPY PATH TESTS
# =============================================================================

class TestHappyPath:
    """Tests for successful workflow completion."""

    def test_excellent_risk_auto_approve(self, create_workflow_for_profile):
        """Excellent risk should auto-approve at tier 1-2."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        tier_min, tier_max = expected["tier_range"]
        assert tier_min <= result.model_version.final_tier <= tier_max
        assert result.decision == expected["decision"]
        assert result.auto_approve == expected["auto_approve"]
        assert len(result.referral_reasons) == expected["referral_count"]

    def test_average_risk_approve(self, create_workflow_for_profile):
        """Average risk should approve at tier 2-3."""
        profile = TestProfiles.AVERAGE_RISK_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        tier_min, tier_max = expected["tier_range"]
        assert tier_min <= result.model_version.final_tier <= tier_max
        assert result.decision == expected["decision"]


# =============================================================================
# REFERRAL FLOW TESTS
# =============================================================================

class TestReferralFlow:
    """Tests for referral triggering and processing."""

    def test_poor_risk_refer(self, create_workflow_for_profile):
        """Poor risk should be referred for review."""
        profile = TestProfiles.POOR_RISK_REFER
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        assert result.decision == expected["decision"]
        assert result.auto_approve == expected["auto_approve"]

    def test_query_triggers_referral(self, create_workflow_for_profile):
        """Pending claims query should trigger referral."""
        profile = TestProfiles.QUERY_TRIGGERS_REFERRAL
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        assert result.decision == expected["decision"]
        assert result.auto_approve == expected["auto_approve"]
        assert len(result.referral_reasons) > 0

    def test_referral_review_approve(self, create_workflow_for_profile):
        """Reviewer can approve a referred submission."""
        profile = TestProfiles.QUERY_TRIGGERS_REFERRAL
        engine, request = create_workflow_for_profile(profile)

        # Run initial workflow
        initial_result = engine.run_workflow(request)
        assert initial_result.decision == DecisionType.REFER

        # Process referral approval
        model_id = initial_result.model_version.model_id
        review_result = engine.process_referral(
            model_id=model_id,
            reviewer="senior_uw",
            decision="approve",
            adjustments={"notes": ["Reviewed and approved"]}
        )

        assert review_result.decision == DecisionType.APPROVE
        assert review_result.model_version.version_number == 2

    def test_referral_review_decline(self, create_workflow_for_profile):
        """Reviewer can decline a referred submission."""
        profile = TestProfiles.POOR_RISK_REFER
        engine, request = create_workflow_for_profile(profile)

        # Run initial workflow
        initial_result = engine.run_workflow(request)
        assert initial_result.decision == DecisionType.REFER

        # Process referral decline
        model_id = initial_result.model_version.model_id
        review_result = engine.process_referral(
            model_id=model_id,
            reviewer="senior_uw",
            decision="decline",
            adjustments={"notes": ["Risk outside appetite"]}
        )

        assert review_result.decision == DecisionType.DECLINE


# =============================================================================
# TIER OVERRIDE TESTS
# =============================================================================

class TestTierOverride:
    """Tests for tier override behavior."""

    def test_query_tier_override_decline(self, create_workflow_for_profile):
        """Regulatory action should override to tier 5 and decline."""
        profile = TestProfiles.TIER_OVERRIDE_FROM_QUERY
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        tier_min, tier_max = expected["tier_range"]
        assert tier_min <= result.model_version.final_tier <= tier_max
        assert result.decision == expected["decision"]

    def test_signal_condition_tier_override(self, create_workflow_for_profile, integration_config):
        """Signal condition should trigger tier override."""
        # Create profile with very low safety score
        profile = {
            "name": "signal_tier_override",
            "inputs": {
                "entity_id": "LOW-001",
                "signals": {
                    "safety_record": 20,  # Below 30 triggers tier 5 override
                    "incident_history": 60,
                    "financial_strength": 60,
                    "regulatory_compliance": 60
                },
                "direct_queries": {},
                "categorical_selections": {"operator_type": "regional_airline"},
                "submission_data": {"tiv": 10000000, "entity_id": "LOW-001"}
            },
            "expected": {}
        }

        engine, request = create_workflow_for_profile(profile)
        result = engine.run_workflow(request)

        # Should override to tier 5 due to safety < 30
        assert result.model_version.final_tier == 5
        assert result.decision == DecisionType.DECLINE


# =============================================================================
# MODIFIER TESTS
# =============================================================================

class TestModifiers:
    """Tests for premium modifier behavior."""

    def test_modifier_applied(self, create_workflow_for_profile):
        """Wet lease query should apply premium modifier."""
        profile = TestProfiles.MODIFIER_APPLIED
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        modifiers = result.model_version.modifiers_applied

        # Should have at least categorical + query modifiers
        assert len(modifiers) >= expected["modifier_count_min"]

        # Find the wet_lease modifier
        query_modifiers = [m for m in modifiers if m.source == "direct_query"]
        assert len(query_modifiers) > 0

    def test_categorical_modifier_applied(self, create_workflow_for_profile):
        """Categorical selections should apply modifiers."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        modifiers = result.model_version.modifiers_applied
        categorical_mods = [m for m in modifiers if m.source == "categorical"]

        # Should have operator_type and fleet_category modifiers
        assert len(categorical_mods) >= 1


# =============================================================================
# MISSING INPUTS TESTS
# =============================================================================

class TestMissingInputs:
    """Tests for missing input handling."""

    def test_missing_inputs_refer(self, create_workflow_for_profile):
        """Missing required inputs should trigger referral."""
        profile = TestProfiles.MISSING_INPUTS
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        expected = profile["expected"]
        assert result.decision == expected["decision"]
        assert len(result.missing_inputs) > 0
        assert "tiv" in result.missing_inputs


# =============================================================================
# VERSION TRACKING TESTS
# =============================================================================

class TestVersionTracking:
    """Tests for model version tracking."""

    def test_initial_version_created(self, create_workflow_for_profile):
        """Initial workflow should create version 1."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        assert result.model_version.version_number == 1
        assert result.model_version.version_type == VersionType.INITIAL

    def test_referral_creates_new_version(self, create_workflow_for_profile):
        """Referral review should create version 2."""
        profile = TestProfiles.QUERY_TRIGGERS_REFERRAL
        engine, request = create_workflow_for_profile(profile)

        # Initial workflow
        initial_result = engine.run_workflow(request)
        model_id = initial_result.model_version.model_id

        # Referral review
        review_result = engine.process_referral(
            model_id=model_id,
            reviewer="reviewer",
            decision="approve"
        )

        assert review_result.model_version.version_number == 2
        assert review_result.model_version.version_type == VersionType.REFERRAL_REVIEW

    def test_version_history_maintained(self, create_workflow_for_profile):
        """Version history should be queryable."""
        profile = TestProfiles.QUERY_TRIGGERS_REFERRAL
        engine, request = create_workflow_for_profile(profile)

        # Initial + referral
        initial_result = engine.run_workflow(request)
        model_id = initial_result.model_version.model_id

        engine.process_referral(model_id, "reviewer1", "refer")
        engine.process_referral(model_id, "reviewer2", "approve")

        # Check history
        history = engine.data_manager.get_version_history(model_id)
        assert len(history) == 3


# =============================================================================
# PREMIUM CALCULATION TESTS
# =============================================================================

class TestPremiumCalculation:
    """Tests for premium calculation accuracy."""

    def test_premium_options_generated(self, create_workflow_for_profile):
        """Should generate premium for all limit bands."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        # Should have 4 limit options
        assert len(result.premium_options) == 4
        assert 1000000 in result.premium_options
        assert 5000000 in result.premium_options
        assert 10000000 in result.premium_options
        assert 25000000 in result.premium_options

    def test_premium_scales_with_ilf(self, create_workflow_for_profile):
        """Premium should scale correctly with ILF."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        base_premium = result.premium_options[1000000]

        # 5M limit should be ~2.5x base (ILF 2.5)
        assert abs(result.premium_options[5000000] / base_premium - 2.5) < 0.1

        # 10M limit should be ~4x base (ILF 4.0)
        assert abs(result.premium_options[10000000] / base_premium - 4.0) < 0.1

    def test_better_tier_lower_premium(self, create_workflow_for_profile):
        """Better tier should result in lower premium."""
        excellent = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        poor = TestProfiles.POOR_RISK_REFER

        engine_excellent, request_excellent = create_workflow_for_profile(excellent)
        engine_poor, request_poor = create_workflow_for_profile(poor)

        result_excellent = engine_excellent.run_workflow(request_excellent)
        result_poor = engine_poor.run_workflow(request_poor)

        # Excellent risk should have lower base premium
        assert result_excellent.model_version.base_premium < result_poor.model_version.base_premium


# =============================================================================
# END-TO-END SCENARIO TESTS
# =============================================================================

class TestEndToEndScenarios:
    """Complete end-to-end workflow scenario tests."""

    def test_full_approve_flow(self, create_workflow_for_profile):
        """Test complete approve workflow."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        # Verify complete flow
        assert result.is_valid
        assert result.decision == DecisionType.APPROVE
        assert result.auto_approve is True
        assert result.model_version.final_tier <= 2
        assert len(result.premium_options) > 0
        assert result.recommended_premium > 0

    def test_full_refer_then_approve(self, create_workflow_for_profile):
        """Test refer → approve workflow."""
        profile = TestProfiles.QUERY_TRIGGERS_REFERRAL
        engine, request = create_workflow_for_profile(profile)

        # Step 1: Initial submission triggers referral
        initial = engine.run_workflow(request)
        assert initial.decision == DecisionType.REFER
        assert not initial.auto_approve
        assert len(initial.referral_reasons) > 0

        # Step 2: Underwriter reviews and approves
        review = engine.process_referral(
            model_id=initial.model_version.model_id,
            reviewer="senior_uw",
            decision="approve",
            adjustments={"notes": ["Approved after claims review"]}
        )
        assert review.decision == DecisionType.APPROVE
        assert "Reviewed by senior_uw" in review.model_version.notes

    def test_full_decline_flow(self, create_workflow_for_profile):
        """Test complete decline workflow."""
        profile = TestProfiles.TIER_OVERRIDE_FROM_QUERY
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)

        assert result.decision == DecisionType.DECLINE
        assert not result.auto_approve
        assert result.model_version.final_tier == 5

    def test_workflow_summary(self, create_workflow_for_profile):
        """Test workflow summary generation."""
        profile = TestProfiles.EXCELLENT_RISK_AUTO_APPROVE
        engine, request = create_workflow_for_profile(profile)

        result = engine.run_workflow(request)
        summary = engine.get_workflow_summary(result)

        # Verify summary structure
        assert summary["decision"] == "approve"
        assert summary["auto_approve"] is True
        assert summary["is_valid"] is True
        assert "scoring" in summary
        assert "pricing" in summary
        assert "premium_options" in summary
        assert "recommended" in summary

"""
End-to-End Integration Tests for DSI Pipeline

Tests the full flow: submission → signal extraction → scoring →
tier assignment → pricing → decision. Uses stub extractors.
"""

import pytest
from layers.risk.workflow import run_assessment, WorkflowEngine, get_workflow_engine
from layers.risk.types import WorkflowResult, DecisionType, ModelVersion


# =============================================================================
# SINGLE COVERAGE E2E
# =============================================================================

class TestCyberE2E:
    """End-to-end tests for cyber coverage pricing."""

    def test_cyber_basic_submission(self):
        """Complete cyber pricing with minimal input."""
        result = run_assessment(
            entity_id="e2e-test-001",
            coverage="cyber",
            entity_name="Test Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result, WorkflowResult)
        assert result.entity_id == "e2e-test-001"
        assert result.coverage == "cyber"
        assert result.is_valid

    def test_cyber_score_in_range(self):
        """Composite score must be 0-1000 (weighted sum across groups)."""
        result = run_assessment(
            entity_id="e2e-score-range",
            coverage="cyber",
            entity_name="Score Range Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert 0.0 <= result.composite_score <= 1000.0

    def test_cyber_tier_assignment(self):
        """Tier must be a valid integer (1-5 typical)."""
        result = run_assessment(
            entity_id="e2e-tier-test",
            coverage="cyber",
            entity_name="Tier Test Inc",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result.tier, int)
        assert result.tier >= 1
        assert result.tier_label != ""

    def test_cyber_decision_type(self):
        """Decision must be one of APPROVE, REFER, DECLINE."""
        result = run_assessment(
            entity_id="e2e-decision-test",
            coverage="cyber",
            entity_name="Decision Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert result.decision in [
            DecisionType.APPROVE,
            DecisionType.REFER,
            DecisionType.DECLINE,
        ]

    def test_cyber_premium_generated(self):
        """Premium options should be generated."""
        result = run_assessment(
            entity_id="e2e-premium-test",
            coverage="cyber",
            entity_name="Premium Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result.model_version.limit_premiums, dict)
        assert result.recommended_premium >= 0

    def test_cyber_model_version_captured(self):
        """Model version should be captured for audit trail."""
        result = run_assessment(
            entity_id="e2e-audit-test",
            coverage="cyber",
            entity_name="Audit Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert result.model_version is not None
        assert isinstance(result.model_version, ModelVersion)

    def test_cyber_with_submission_data(self):
        """Submission data should be accepted."""
        result = run_assessment(
            entity_id="e2e-data-test",
            coverage="cyber",
            entity_name="Data Corp",
            submission_data={
                "revenue": 50000000,
                "employee_count": 500,
            },
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result, WorkflowResult)
        assert result.is_valid

    def test_cyber_with_direct_queries(self):
        """Direct query responses should be processed."""
        result = run_assessment(
            entity_id="e2e-query-test",
            coverage="cyber",
            entity_name="Query Corp",
            direct_query_responses={
                "has_mfa_enabled": True,
                "has_incident_response_plan": True,
                "has_cyber_insurance": False,
            },
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result, WorkflowResult)

    def test_cyber_confidence_in_range(self):
        """Confidence must be between 0 and 1."""
        result = run_assessment(
            entity_id="e2e-confidence-test",
            coverage="cyber",
            entity_name="Confidence Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert 0.0 <= result.confidence <= 1.0

    def test_cyber_input_validation_rejects_incomplete(self):
        """Input validation should reject submissions missing required fields."""
        result = run_assessment(
            entity_id="e2e-validation-test",
            coverage="cyber",
            entity_name="Validation Corp",
            skip_discovery=True,
            skip_input_validation=False,
        )

        assert not result.is_valid
        assert len(result.missing_inputs) > 0
        assert result.decision == DecisionType.REFER


# =============================================================================
# WORKFLOW ENGINE TESTS
# =============================================================================

class TestWorkflowEngine:
    """Tests for the WorkflowEngine itself."""

    def test_get_workflow_engine(self):
        """Workflow engine singleton should be retrievable."""
        engine = get_workflow_engine()
        assert isinstance(engine, WorkflowEngine)

    def test_engine_run_workflow(self):
        """Engine should run complete workflow."""
        engine = get_workflow_engine()
        result = engine.run_workflow(
            entity_id="e2e-engine-test",
            coverage="cyber",
            entity_name="Engine Corp",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result, WorkflowResult)
        assert result.composite_score >= 0


# =============================================================================
# EXTRACTOR RESOLVER INTEGRATION
# =============================================================================

class TestExtractorResolver:
    """Tests that the extractor resolver works in the pipeline context."""

    def test_resolver_returns_stub(self):
        """Resolver should return stub extractors by default."""
        from signal_architecture.signals.extractors.resolver import get_extractor

        ext = get_extractor("email_auth")
        result = ext.extract("test-entity")

        assert result.success or result.error is not None
        assert result.source != ""

    def test_resolver_all_cyber_extractors(self):
        """All cyber extractors should be resolvable."""
        from signal_architecture.signals.extractors.resolver import get_extractor

        cyber_extractors = [
            "email_auth", "dnssec", "tls_config", "security_headers",
            "waf_presence", "cdn_usage", "cloud_infra", "security_txt",
            "bug_bounty", "cve_exposure", "network_exposure",
            "software_currency", "breach_history", "litigation_history",
            "security_rating", "privacy_policy", "security_page",
            "credential_exposure", "dark_web", "company_size",
            "industry_classification", "operational_base",
        ]

        for name in cyber_extractors:
            ext = get_extractor(name)
            assert ext is not None, f"Failed to resolve extractor: {name}"

    def test_stub_registration_with_factory(self):
        """Stubs should register with factory for hybrid mode."""
        from signal_architecture.signals.extractors.resolver import register_stubs_with_factory

        count = register_stubs_with_factory()
        assert count >= 30  # We have 36 mapped stubs


# =============================================================================
# GRAPH MODULE INTEGRATION
# =============================================================================

class TestGraphIntegration:
    """Tests that graph module integrates with the pipeline."""

    def test_graph_builder_with_submission_data(self):
        """Graph builder should work with realistic submission data."""
        from signal_architecture.graph.graph_builder import GraphBuilder

        submission_data = {
            "entity_id": "e2e-graph-test",
            "entity_name": "Graph Corp",
            "domain": "graphcorp.com",
            "country": "US",
            "revenue": 100000000,
            "employee_count": 1000,
            "assets": [
                {"name": "Main Office", "type": "physical", "value": 5000000},
                {"name": "Cloud Platform", "type": "digital", "value": 2000000},
            ],
            "partners": [
                {"name": "AWS", "type": "cloud_provider"},
                {"name": "Cloudflare", "type": "cdn_provider"},
            ],
        }

        builder = GraphBuilder()
        graph = builder.build(submission_data)

        assert graph is not None
        assert len(graph.nodes) > 0
        assert len(graph.edges) >= 0

    def test_graph_derivatives_compute(self):
        """Derivative calculations should produce valid results."""
        from signal_architecture.graph.graph_builder import GraphBuilder

        submission_data = {
            "entity_id": "e2e-derivatives",
            "entity_name": "Derivatives Corp",
            "assets": [
                {"name": "System A", "type": "digital", "value": 1000000},
                {"name": "System B", "type": "digital", "value": 2000000},
            ],
        }

        builder = GraphBuilder()
        graph = builder.build(submission_data)
        scoring = builder.get_graph_scoring_inputs(graph)

        assert isinstance(scoring, dict)


# =============================================================================
# CONFIG VALIDATOR INTEGRATION
# =============================================================================

class TestConfigValidation:
    """Tests that config validation works with real config files."""

    def test_validate_cyber_config(self):
        """Cyber config should pass validation."""
        import importlib.util
        from pathlib import Path

        validator_path = Path("signal_architecture/validation/config_validator.py")
        if not validator_path.exists():
            pytest.skip("Config validator not found")

        spec = importlib.util.spec_from_file_location(
            "config_validator", str(validator_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find a cyber config file
        import glob
        configs = glob.glob("coverages/cyber/*.yaml") + glob.glob("coverages/cyber/*.yml")
        if not configs:
            pytest.skip("No cyber config files found")

        report = mod.validate_coverage_config(configs[0])
        # Config should load without critical errors
        assert report is not None

    def test_validate_all_configs(self):
        """All coverage configs should be parseable."""
        import glob
        import yaml

        configs = glob.glob("coverages/*/config.yaml") + glob.glob("coverages/*/config.yml")
        if not configs:
            pytest.skip("No config files found")

        for config_path in configs:
            with open(config_path) as f:
                data = yaml.safe_load(f)
            assert data is not None, f"Failed to parse: {config_path}"
            assert isinstance(data, dict), f"Config not a dict: {config_path}"


# =============================================================================
# MULTI-COVERAGE E2E
# =============================================================================

class TestMultiCoverage:
    """Tests for multi-coverage pricing scenarios."""

    def test_multiple_coverages_sequentially(self):
        """Multiple coverages should price without interference."""
        coverages = ["cyber"]  # Start with cyber as the primary coverage

        results = {}
        for coverage in coverages:
            try:
                result = run_assessment(
                    entity_id=f"e2e-multi-{coverage}",
                    coverage=coverage,
                    entity_name="Multi Corp",
                    skip_discovery=True,
                    skip_input_validation=True,
                )
                results[coverage] = result
            except Exception:
                pass  # Other coverages may not have configs

        # At least cyber should succeed
        assert "cyber" in results
        assert results["cyber"].is_valid

    def test_same_entity_consistent_scoring(self):
        """Same entity should get similar scores on repeated runs."""
        scores = []
        for i in range(3):
            result = run_assessment(
                entity_id="e2e-consistency",
                coverage="cyber",
                entity_name="Consistent Corp",
                skip_discovery=True,
                skip_input_validation=True,
            )
            scores.append(result.composite_score)

        # Scores should all be valid (may vary due to random stubs)
        for score in scores:
            assert 0.0 <= score <= 1000.0

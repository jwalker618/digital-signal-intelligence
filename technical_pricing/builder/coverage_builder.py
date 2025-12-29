"""
DSI Coverage Builder (Phase 13)

LLM-assisted coverage creation with validation.
"""

import logging
import time
import yaml
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .types import (
    BuildProgress,
    BuildStage,
    CoverageBuildResult,
    CoverageSpec,
    GeneratedCode,
    IndustryAnalysis,
    SignalSelection,
    ValidationResult,
)
from .signal_library import SignalLibrary
from .validator import ConfigValidator


logger = logging.getLogger("dsi.builder")


class CoverageBuilder:
    """
    LLM-assisted coverage building.

    Creates complete coverage configurations from
    high-level specifications using AI assistance.
    """

    def __init__(
        self,
        llm_client: Optional[Callable] = None,
        signal_library: Optional[SignalLibrary] = None,
        validator: Optional[ConfigValidator] = None,
        output_dir: str = "technical_pricing/coverages",
    ):
        """
        Initialize CoverageBuilder.

        Args:
            llm_client: LLM client for AI assistance
            signal_library: Signal library for recommendations
            validator: Configuration validator
            output_dir: Directory for generated coverages
        """
        self.llm_client = llm_client
        self.signal_library = signal_library or SignalLibrary()
        self.validator = validator or ConfigValidator()
        self.output_dir = output_dir

        self._progress_callbacks: List[Callable] = []

    def on_progress(self, callback: Callable[[BuildProgress], None]) -> None:
        """Register progress callback."""
        self._progress_callbacks.append(callback)

    def _update_progress(self, stage: BuildStage, progress: float, message: str) -> None:
        """Update progress and notify callbacks."""
        bp = BuildProgress(stage=stage, progress=progress, message=message)
        for callback in self._progress_callbacks:
            try:
                callback(bp)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def create_coverage(
        self,
        spec: CoverageSpec,
    ) -> CoverageBuildResult:
        """
        Create a complete coverage from specification.

        Steps:
        1. Analyze industry requirements
        2. Select and configure signals
        3. Generate configuration
        4. Validate and test
        5. Generate code stubs

        Args:
            spec: Coverage specification

        Returns:
            CoverageBuildResult with generated files
        """
        start_time = time.time()
        warnings: List[str] = []
        human_review: List[str] = []

        try:
            # Step 1: Analyze industry
            self._update_progress(BuildStage.ANALYSIS, 0.1, "Analyzing industry...")
            analysis = await self.analyze_industry(spec.industry, spec.example_companies)

            # Step 2: Select signals
            self._update_progress(BuildStage.SIGNAL_SELECTION, 0.3, "Selecting signals...")
            selections = await self.select_signals(analysis, spec)

            if len(selections) < spec.min_signals:
                warnings.append(
                    f"Only {len(selections)} signals selected, below minimum of {spec.min_signals}"
                )
                human_review.append("Review signal selection - below minimum count")

            # Step 3: Generate configuration
            self._update_progress(BuildStage.CONFIG_GENERATION, 0.5, "Generating configuration...")
            config_yaml = await self.generate_config(spec, selections)

            # Step 4: Validate
            self._update_progress(BuildStage.VALIDATION, 0.7, "Validating configuration...")
            validation = await self.validate_config(config_yaml)

            if not validation.valid:
                human_review.extend([
                    f"Validation error: {i.message}"
                    for i in validation.issues
                    if i.severity.value == "error"
                ])

            # Step 5: Generate code stubs for new signals
            self._update_progress(BuildStage.CODE_GENERATION, 0.9, "Generating code stubs...")
            new_signals = [s.signal_id for s in selections if self._is_new_signal(s)]
            generated = await self.generate_stubs(spec, new_signals)

            # Calculate output path
            config_path = f"{self.output_dir}/{spec.name.lower().replace(' ', '_')}/config.yaml"

            # Complete
            self._update_progress(BuildStage.COMPLETE, 1.0, "Build complete")

            duration = time.time() - start_time

            return CoverageBuildResult(
                success=validation.valid or validation.error_count == 0,
                coverage_name=spec.name,
                config_yaml=config_yaml,
                config_path=config_path,
                generated_files=generated.files,
                validation_results=validation,
                warnings=warnings + validation.warnings,
                human_review_required=human_review,
                build_duration_seconds=duration,
            )

        except Exception as e:
            logger.error(f"Coverage build failed: {e}")
            return CoverageBuildResult(
                success=False,
                coverage_name=spec.name,
                config_yaml="",
                config_path="",
                warnings=[str(e)],
                human_review_required=["Build failed - manual intervention required"],
            )

    async def analyze_industry(
        self,
        description: str,
        examples: Optional[List[str]] = None,
    ) -> IndustryAnalysis:
        """
        Analyze industry to identify risk factors and signals.

        Args:
            description: Industry description
            examples: Example companies

        Returns:
            IndustryAnalysis with recommendations
        """
        logger.info(f"Analyzing industry: {description}")

        # Use signal library for industry-specific recommendations
        profile = self.signal_library.get_industry_profile(description)

        if profile:
            return IndustryAnalysis(
                industry=description,
                key_risk_factors=profile.risk_focus,
                relevant_categories=profile.primary_groups + profile.secondary_groups,
                specific_considerations=[],
                confidence=0.9,
            )

        # Fallback to generic analysis
        risk_factors = self._identify_risk_factors(description)
        categories = self._identify_categories(description)

        return IndustryAnalysis(
            industry=description,
            key_risk_factors=risk_factors,
            relevant_categories=categories,
            specific_considerations=[],
            confidence=0.7,
        )

    async def select_signals(
        self,
        analysis: IndustryAnalysis,
        spec: CoverageSpec,
    ) -> List[SignalSelection]:
        """
        Select signals based on industry analysis.

        Args:
            analysis: Industry analysis
            spec: Coverage specification

        Returns:
            List of selected signals with configurations
        """
        logger.info(f"Selecting signals for {analysis.industry}")

        selections: List[SignalSelection] = []

        # Get recommendations from library
        recommendations = self.signal_library.get_signals_for_industry(
            analysis.industry
        )

        # Select top signals
        for rec in recommendations[:spec.max_signals]:
            selections.append(SignalSelection(
                signal_id=rec.signal_id,
                signal_name=rec.signal_name,
                group_id=rec.group_id,
                weight=rec.suggested_weight,
                direction="positive",
                enabled=True,
            ))

        # Normalize weights
        total_weight = sum(s.weight for s in selections)
        if total_weight > 0:
            for s in selections:
                s.weight = round(s.weight / total_weight, 4)

        return selections

    async def generate_config(
        self,
        spec: CoverageSpec,
        selections: List[SignalSelection],
    ) -> str:
        """
        Generate complete YAML configuration.

        Args:
            spec: Coverage specification
            selections: Selected signals

        Returns:
            YAML configuration string
        """
        logger.info(f"Generating config for {spec.name}")

        # Build configuration structure
        config = {
            "coverage": {
                "id": spec.name.lower().replace(" ", "_"),
                "name": spec.name,
                "description": spec.description,
                "locale": spec.locale,
                "industry": spec.industry,
                "version": "1.0.0",
            },
            "signal_groups": self._build_signal_groups(selections),
            "scoring": {
                "composite_method": "weighted_average",
                "scale": {"min": 300, "max": 850},
            },
            "tiers": self._build_tier_config(spec.tier_strategy),
            "premium": {
                "base_rate": 0.005,
                "tier_factors": {
                    "1": 0.7,
                    "2": 1.0,
                    "3": 1.3,
                    "4": 1.7,
                    "5": 2.5,
                },
            },
            "direct_queries": self._build_direct_queries(spec),
        }

        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    async def validate_config(
        self,
        config_yaml: str,
    ) -> ValidationResult:
        """
        Validate generated configuration.

        Args:
            config_yaml: YAML configuration

        Returns:
            ValidationResult with any issues
        """
        logger.info("Validating configuration...")

        return self.validator.validate_yaml(config_yaml)

    async def generate_stubs(
        self,
        spec: CoverageSpec,
        new_signals: List[str],
    ) -> GeneratedCode:
        """
        Generate code stubs for new signals.

        Args:
            spec: Coverage specification
            new_signals: Signals requiring new implementation

        Returns:
            GeneratedCode with file contents
        """
        logger.info(f"Generating stubs for {len(new_signals)} new signals")

        files: Dict[str, str] = {}
        coverage_id = spec.name.lower().replace(" ", "_")

        # Generate extractor stub
        if new_signals:
            extractor_content = self._generate_extractor_stub(coverage_id, new_signals)
            files[f"signals/{coverage_id}/extractors.py"] = extractor_content

            # Generate aggregator stub
            aggregator_content = self._generate_aggregator_stub(coverage_id, new_signals)
            files[f"signals/{coverage_id}/aggregators.py"] = aggregator_content

        # Generate test stub
        test_content = self._generate_test_stub(coverage_id, new_signals)
        files[f"tests/unit/test_{coverage_id}.py"] = test_content

        return GeneratedCode(files=files)

    def _build_signal_groups(
        self,
        selections: List[SignalSelection],
    ) -> Dict[str, Any]:
        """Build signal groups from selections."""
        groups: Dict[str, Dict[str, Any]] = {}

        for selection in selections:
            if selection.group_id not in groups:
                groups[selection.group_id] = {
                    "weight": 0.0,
                    "signals": [],
                }

            groups[selection.group_id]["weight"] += selection.weight
            groups[selection.group_id]["signals"].append({
                "id": selection.signal_id,
                "name": selection.signal_name,
                "weight": selection.weight,
                "direction": selection.direction,
            })

        return groups

    def _build_tier_config(self, strategy: str) -> Dict[str, Any]:
        """Build tier configuration."""
        if strategy == "conservative":
            return {
                "1": {"min_score": 800, "label": "PREFERRED", "decision": "approve"},
                "2": {"min_score": 720, "label": "STANDARD", "decision": "approve"},
                "3": {"min_score": 650, "label": "STANDARD_PLUS", "decision": "approve"},
                "4": {"min_score": 550, "label": "ELEVATED", "decision": "refer"},
                "5": {"min_score": 0, "label": "HIGH_RISK", "decision": "refer"},
            }
        elif strategy == "aggressive":
            return {
                "1": {"min_score": 750, "label": "PREFERRED", "decision": "approve"},
                "2": {"min_score": 650, "label": "STANDARD", "decision": "approve"},
                "3": {"min_score": 550, "label": "STANDARD_PLUS", "decision": "approve"},
                "4": {"min_score": 400, "label": "ELEVATED", "decision": "approve"},
                "5": {"min_score": 0, "label": "HIGH_RISK", "decision": "refer"},
            }
        else:  # standard
            return {
                "1": {"min_score": 780, "label": "PREFERRED", "decision": "approve"},
                "2": {"min_score": 680, "label": "STANDARD", "decision": "approve"},
                "3": {"min_score": 580, "label": "STANDARD_PLUS", "decision": "approve"},
                "4": {"min_score": 480, "label": "ELEVATED", "decision": "refer"},
                "5": {"min_score": 0, "label": "HIGH_RISK", "decision": "refer"},
            }

    def _build_direct_queries(self, spec: CoverageSpec) -> List[Dict[str, Any]]:
        """Build direct queries based on spec."""
        queries = [
            {
                "id": "claims_history",
                "question": "Has the insured had any claims in the past 5 years?",
                "type": "boolean",
                "impact": "tier_adjustment",
            },
            {
                "id": "prior_coverage",
                "question": "Does the insured have prior coverage?",
                "type": "boolean",
                "impact": "underwriting",
            },
        ]

        # Add industry-specific queries
        if "financial" in spec.industry.lower():
            queries.append({
                "id": "regulatory_actions",
                "question": "Any regulatory actions in the past 3 years?",
                "type": "boolean",
                "impact": "tier_adjustment",
            })

        if "technology" in spec.industry.lower() or "cyber" in spec.name.lower():
            queries.append({
                "id": "data_breach",
                "question": "Has the insured experienced a data breach?",
                "type": "boolean",
                "impact": "tier_adjustment",
            })

        return queries

    def _identify_risk_factors(self, industry: str) -> List[str]:
        """Identify risk factors for industry."""
        industry_lower = industry.lower()

        factors = ["operational_risk", "market_risk", "compliance_risk"]

        if "financial" in industry_lower:
            factors.extend(["credit_risk", "liquidity_risk", "regulatory_risk"])
        elif "technology" in industry_lower:
            factors.extend(["cyber_risk", "ip_risk", "obsolescence_risk"])
        elif "healthcare" in industry_lower:
            factors.extend(["patient_safety", "regulatory_compliance", "data_privacy"])
        elif "manufacturing" in industry_lower:
            factors.extend(["supply_chain_risk", "product_liability", "environmental_risk"])

        return factors

    def _identify_categories(self, industry: str) -> List[str]:
        """Identify signal categories for industry."""
        categories = [
            "technical_infrastructure",
            "corporate_footprint",
            "financial_health",
        ]

        industry_lower = industry.lower()

        if "financial" in industry_lower:
            categories.extend(["regulatory_compliance", "fraud_prevention"])
        elif "technology" in industry_lower:
            categories.extend(["security_posture", "innovation_capacity"])

        return categories

    def _is_new_signal(self, selection: SignalSelection) -> bool:
        """Check if signal requires new implementation."""
        # Check if signal exists in library
        return not self.signal_library.has_signal(selection.signal_id)

    def _generate_extractor_stub(
        self,
        coverage_id: str,
        signals: List[str],
    ) -> str:
        """Generate extractor stub code."""
        signal_methods = "\n\n".join([
            f'''    async def extract_{sig}(self, entity_id: str) -> Dict[str, Any]:
        """Extract {sig} signal data."""
        # TODO: Implement extraction logic
        return {{"score": 75, "confidence": 0.8}}'''
            for sig in signals
        ])

        return f'''"""
{coverage_id.title()} Signal Extractors

Auto-generated stubs - implement extraction logic.
"""

from typing import Any, Dict


class {coverage_id.title().replace("_", "")}Extractor:
    """Extractor for {coverage_id} coverage signals."""

{signal_methods}
'''

    def _generate_aggregator_stub(
        self,
        coverage_id: str,
        signals: List[str],
    ) -> str:
        """Generate aggregator stub code."""
        return f'''"""
{coverage_id.title()} Signal Aggregators

Auto-generated stubs - implement aggregation logic.
"""

from typing import Any, Dict, List


class {coverage_id.title().replace("_", "")}Aggregator:
    """Aggregator for {coverage_id} coverage signals."""

    def aggregate(self, raw_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate raw signal data."""
        # TODO: Implement aggregation logic
        return {{"composite_score": 750}}
'''

    def _generate_test_stub(
        self,
        coverage_id: str,
        signals: List[str],
    ) -> str:
        """Generate test stub code."""
        return f'''"""
Tests for {coverage_id.title()} Coverage

Auto-generated test stubs.
"""

import pytest


class Test{coverage_id.title().replace("_", "")}Coverage:
    """Tests for {coverage_id} coverage."""

    def test_config_loads(self):
        """Should load coverage configuration."""
        # TODO: Implement test
        assert True

    def test_signal_extraction(self):
        """Should extract signals correctly."""
        # TODO: Implement test
        assert True

    def test_tier_assignment(self):
        """Should assign correct tier."""
        # TODO: Implement test
        assert True
'''

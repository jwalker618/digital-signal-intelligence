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
        output_dir: str = "coverages",
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

        # Build v2.0 configuration structure
        coverage_id = spec.name.lower().replace(" ", "_")
        config_name = f"{coverage_id}_general"

        inner_config = {
            "metadata": {
                "name": f"DSI {spec.name} Model",
                "description": spec.description,
                "version": "2.0.0",
                "applicable_markets": [spec.locale] if spec.locale else ["us"],
                "minimum_viable_input": ["client name (domain optional)", "Limit in USD"],
                "min_premium": 5000,
                "default_currency": "USD",
            },
            "direct_queries": self._build_direct_queries(spec),
            "signal_groups": self._build_signal_groups_v2(selections),
            "signal_features": self._build_signal_features_v2(selections),
            "tier_thresholds": {"tiers": self._build_tier_config(spec.tier_strategy)},
            "loss_tier_bands": self._build_loss_tier_bands(),
            "exposure_tier_bands": self._build_exposure_tier_bands(),
            "limit_bandings": [
                {"id": 1, "limit": 1000000, "deductible": 25000},
                {"id": 2, "limit": 5000000, "deductible": 50000},
                {"id": 3, "limit": 10000000, "deductible": 100000},
            ],
        }

        config = {coverage_id: {config_name: inner_config}}

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
        """Build signal groups from selections (v1.0 compat)."""
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

    def _build_signal_groups_v2(
        self,
        selections: List[SignalSelection],
    ) -> List[Dict[str, Any]]:
        """Build v2.0 signal groups with score_conditions."""
        groups_map: Dict[str, Dict[str, Any]] = {}

        for selection in selections:
            if selection.group_id not in groups_map:
                groups_map[selection.group_id] = {
                    "id": selection.group_id,
                    "name": selection.group_id.replace("_", " ").title(),
                    "description": f"Signal group: {selection.group_id}",
                    "weight": 0.0,
                    "test_scores": {"excellent": 85, "average": 65, "poor": 35},
                    "score_conditions": [
                        {
                            "threshold": 20,
                            "comparison": "<=",
                            "action": "MODIFIER",
                            "applied": 0.90,
                            "note": f"Excellent {selection.group_id} - modifier applied",
                        }
                    ],
                }
            groups_map[selection.group_id]["weight"] += selection.weight

        return list(groups_map.values())

    def _build_signal_features_v2(
        self,
        selections: List[SignalSelection],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Build v2.0 signal features grouped by group_id."""
        features: Dict[str, List[Dict[str, Any]]] = {}

        for selection in selections:
            if selection.group_id not in features:
                features[selection.group_id] = []

            features[selection.group_id].append({
                "id": selection.signal_id,
                "name": selection.signal_name,
                "description": f"Signal: {selection.signal_name}",
                "weight": selection.weight,
                "inference_utility_function": f"{selection.signal_id}_basefunction",
            })

        return features

    def _build_tier_config(self, strategy: str) -> List[Dict[str, Any]]:
        """Build v2.0 tier configuration with application blocks."""
        base_premiums = {
            "conservative": [5000, 8000, 12000, 20000, 35000],
            "aggressive": [4000, 6000, 9000, 15000, 28000],
            "standard": [5000, 7500, 11000, 18000, 30000],
        }
        thresholds = {
            "conservative": [(800, 1000), (720, 799), (650, 719), (550, 649), (0, 549)],
            "aggressive": [(750, 1000), (650, 749), (550, 649), (400, 549), (0, 399)],
            "standard": [(780, 1000), (680, 779), (580, 679), (480, 579), (0, 479)],
        }
        labels = ["PREFERRED", "STANDARD_PLUS", "STANDARD", "SUBSTANDARD", "DECLINE"]
        approvals = [True, True, False, False, False]
        declines = [False, False, False, False, True]

        strat = strategy if strategy in base_premiums else "standard"
        premiums = base_premiums[strat]
        scores = thresholds[strat]

        tiers = []
        for i in range(5):
            tiers.append({
                "id": i + 1,
                "label": labels[i],
                "min_score": scores[i][0],
                "max_score": scores[i][1],
                "description": f"Tier {i + 1} - {labels[i]}",
                "auto_approve": approvals[i],
                "auto_decline": declines[i],
                "application": {
                    "method": "PREMIUM_BASE",
                    "applied": premiums[i],
                },
            })
        return tiers

    def _build_loss_tier_bands(self) -> Dict[str, Any]:
        """Build v2.0 loss tier bands with frequency/severity modifiers."""
        return {
            "bands": [
                {"id": 1, "label": "VERY_LOW", "interpretation": {
                    "bands": {"min": 80, "max": 100},
                    "application": {"frequency_modifier": 0.70, "severity_modifier": 0.80}}},
                {"id": 2, "label": "LOW", "interpretation": {
                    "bands": {"min": 60, "max": 79},
                    "application": {"frequency_modifier": 0.85, "severity_modifier": 0.90}}},
                {"id": 3, "label": "MODERATE", "interpretation": {
                    "bands": {"min": 40, "max": 59},
                    "application": {"frequency_modifier": 1.00, "severity_modifier": 1.00}}},
                {"id": 4, "label": "HIGH", "interpretation": {
                    "bands": {"min": 20, "max": 39},
                    "application": {"frequency_modifier": 1.25, "severity_modifier": 1.20}}},
                {"id": 5, "label": "VERY_HIGH", "interpretation": {
                    "bands": {"min": 0, "max": 19},
                    "application": {"frequency_modifier": 1.60, "severity_modifier": 1.50}}},
            ],
            "constraints": {"floor": 0.55, "cap": 1.60},
        }

    def _build_exposure_tier_bands(self) -> Dict[str, Any]:
        """Build v2.0 exposure tier bands."""
        return {
            "bands": [
                {"id": 1, "label": "SMALL", "interpretation": {
                    "bands": {"min": 0, "max": 10000000},
                    "application": {"method": "MODIFIER", "applied": 0.85}}},
                {"id": 2, "label": "MEDIUM", "interpretation": {
                    "bands": {"min": 10000001, "max": 50000000},
                    "application": {"method": "MODIFIER", "applied": 1.00}}},
                {"id": 3, "label": "LARGE", "interpretation": {
                    "bands": {"min": 50000001, "max": 250000000},
                    "application": {"method": "MODIFIER", "applied": 1.15}}},
                {"id": 4, "label": "VERY_LARGE", "interpretation": {
                    "bands": {"min": 250000001, "max": None},
                    "application": {"method": "MODIFIER", "applied": 1.35}}},
            ],
        }

    def _build_direct_queries(self, spec: CoverageSpec) -> List[Dict[str, Any]]:
        """Build v2.0 direct queries based on spec."""
        queries = [
            {
                "id": "claims_history",
                "question": "Has the insured had any claims in the past 5 years?",
                "bands": [
                    {"return": True, "action": "REFER", "override": None, "modifier": None,
                     "note": "Prior claims - review required"},
                ],
            },
            {
                "id": "prior_coverage",
                "question": "Does the insured have prior coverage?",
                "bands": [
                    {"return": False, "action": "FLAG", "override": None, "modifier": None,
                     "note": "No prior coverage"},
                ],
            },
        ]

        # Add industry-specific queries
        if "financial" in spec.industry.lower():
            queries.append({
                "id": "regulatory_actions",
                "question": "Any regulatory actions in the past 3 years?",
                "bands": [
                    {"return": True, "action": "REFER", "override": 4, "modifier": None,
                     "note": "Regulatory actions - elevated risk"},
                ],
            })

        if "technology" in spec.industry.lower() or "cyber" in spec.name.lower():
            queries.append({
                "id": "data_breach",
                "question": "Has the insured experienced a data breach?",
                "bands": [
                    {"return": True, "action": "REFER", "override": 4, "modifier": None,
                     "note": "Prior data breach - review required"},
                ],
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

"""
DSI Coverage Builder (Phase 13 → v2.2 Overhaul)

Generates v2.2 compliant coverage configurations matching the canonical
schema used by existing coverages (cyber, D&O, etc.).

Version History:
- v2.0: Original schema with signal_registry, groups, tier_bands
- v2.1: Added V4 multiplexer support (model_specificity, routing_constraints)
- v2.2: Added V5 pricing anchors (base_limit_reference, base_deductible_reference,
        deductible_factors, BUNDLED/DECOUPLED modes)

Output structure:
  coverage_id:
    coverage_id_general:
      metadata: {..., model_specificity, routing_constraints}
      direct_queries: [...]
      signal_registry: [...]
      groups: {categories: [...], three_layer_assessment: [...]}
      risk_tier_bands: {bands: [...]}
      loss_tier_bands: {bands: [...], constraints: {...}}
      exposure: {size: {...}, complexity: {...}}
      limit_bandings: [...] | limit_configuration: {...}
      pricing: {..., base_limit_reference, base_deductible_reference, deductible_factors}

Constraints:
- score_conditions actions: FLAG | MODIFIER | REFER (DECLINE is tier-level only)
- score_conditions are banded (plural, list of multiple conditions)
- score_conditions do NOT apply to tier bands
- Signals defined once in signal_registry with group_id reference
- anchor_limit in ilf_curve SHOULD match base_limit_reference (ILF = 1.0 here)
- base_deductible_reference MUST have factor 1.00 in deductible_factors
"""

import logging
import time
import yaml
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
    Coverage configuration builder producing v2.2 compliant YAML.

    Generates complete coverage configs from high-level specifications.
    Configs match the canonical schema used by existing DSI coverages.

    V2.2 Features:
    - Phase V4: model_specificity, routing_constraints for multiplexer support
    - Phase V5: Pricing anchors, deductible_factors, BUNDLED/DECOUPLED modes
    """

    def __init__(
        self,
        llm_client: Optional[Callable] = None,
        signal_library: Optional[SignalLibrary] = None,
        validator: Optional[ConfigValidator] = None,
        output_dir: str = "coverages",
    ):
        self.llm_client = llm_client
        self.signal_library = signal_library or SignalLibrary()
        self.validator = validator or ConfigValidator()
        self.output_dir = output_dir
        self._progress_callbacks: List[Callable] = []

    def on_progress(self, callback: Callable[[BuildProgress], None]) -> None:
        """Register progress callback."""
        self._progress_callbacks.append(callback)

    def _update_progress(self, stage: BuildStage, progress: float, message: str) -> None:
        bp = BuildProgress(stage=stage, progress=progress, message=message)
        for callback in self._progress_callbacks:
            try:
                callback(bp)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def create_coverage(self, spec: CoverageSpec) -> CoverageBuildResult:
        """
        Create a complete v2.2 coverage from specification.

        Steps:
        1. Analyze industry requirements
        2. Select and configure signals
        3. Generate v2.2 configuration (with V4/V5 features)
        4. Validate against v2.2 schema
        5. Generate code stubs
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

            # Step 3: Generate v2.2 configuration
            self._update_progress(BuildStage.CONFIG_GENERATION, 0.5, "Generating v2.2 configuration...")
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

            # Step 5: Generate code stubs
            self._update_progress(BuildStage.CODE_GENERATION, 0.9, "Generating code stubs...")
            new_signals = [s.signal_id for s in selections if self._is_new_signal(s)]
            generated = await self.generate_stubs(spec, new_signals)

            config_path = f"{self.output_dir}/{spec.name.lower().replace(' ', '_')}/config.yaml"
            self._update_progress(BuildStage.COMPLETE, 1.0, "Build complete")

            return CoverageBuildResult(
                success=validation.valid or validation.error_count == 0,
                coverage_name=spec.name,
                config_yaml=config_yaml,
                config_path=config_path,
                generated_files=generated.files,
                validation_results=validation,
                warnings=warnings + validation.warnings,
                human_review_required=human_review,
                build_duration_seconds=time.time() - start_time,
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
        """Analyze industry to identify risk factors and signals."""
        logger.info(f"Analyzing industry: {description}")

        profile = self.signal_library.get_industry_profile(description)

        if profile:
            return IndustryAnalysis(
                industry=description,
                key_risk_factors=profile.risk_focus,
                relevant_categories=profile.primary_groups + profile.secondary_groups,
                specific_considerations=[],
                confidence=0.9,
            )

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
        spec: CoverageSpec
    ) -> List[SignalSelection]:
        """LLM-assisted signal selection strictly bounded by the SignalLibrary."""
        logger.info(f"Selecting signals for {analysis.industry}")

        # 1. Fetch the absolute truth from the library
        available_signals = self.signal_library.get_signals_for_industry(analysis.industry)
        
        # 2. If no LLM, fallback to static top N (Your current logic)
        if not self.llm_client:
            selections = [
                SignalSelection(
                    signal_id=rec.signal_id,
                    signal_name=rec.signal_name,
                    group_id=rec.group_id,
                    weight=rec.suggested_weight,
                    proxy_tier=rec.proxy_tier,
                )
                for rec in available_signals[:spec.max_signals]
            ]
            return self._normalize_signal_weights(selections)

        # 3. The LLM Hook: Bound the LLM strictly to the available signals
        prompt = f"""
        You are an elite Actuarial AI for DSI. Select between {spec.min_signals} and {spec.max_signals} signals 
        for a '{spec.name}' coverage in the '{spec.industry}' sector.
        
        CRITICAL RULE: You may ONLY select signals from this exact approved list:
        {[s.signal_id for s in available_signals]}
        
        Return a JSON array of selected signal IDs and their relative importance.
        """
        
        # Normalize weights so they equal 1.0 within their group.
        groups: Dict[str, List[SignalSelection]] = {}
        for s in selections:
            groups.setdefault(s.group_id, []).append(s)

        for group_signals in groups.values():
            total = sum(s.weight for s in group_signals)
            if total > 0:
                for s in group_signals:
                    s.weight = round(s.weight / total, 4)

        return selections
    
    def _normalize_signal_weights(self, selections: List[SignalSelection]) -> List[SignalSelection]:
        """Normalize weights so they equal 1.0 within each group."""
        groups: Dict[str, List[SignalSelection]] = {}
        for s in selections:
            groups.setdefault(s.group_id, []).append(s)

        for group_signals in groups.values():
            total = sum(s.weight for s in group_signals)
            if total > 0:
                for s in group_signals:
                    s.weight = round(s.weight / total, 4)

        return selections

    async def generate_config(
        self,
        spec: CoverageSpec,
        selections: List[SignalSelection],
    ) -> str:
        """Generate complete v2.2 compliant YAML configuration."""
        logger.info(f"Generating v2.2 config for {spec.name}")

        coverage_id = spec.name.lower().replace(" ", "_")
        config_name = f"{coverage_id}_general"

        inner_config = {
            "metadata": self._build_metadata(spec),
            "direct_queries": self._build_direct_queries(spec),
            "signal_registry": self._build_signal_registry(selections),
            "groups": self._build_groups(selections, spec.industry),
            "risk_tier_bands": self._build_risk_tier_bands(spec.tier_strategy),
            "loss_tier_bands": self._build_loss_tier_bands(),
            "exposure": self._build_exposure(),
        }

        inner_config["limit_configuration"] = self._build_limit_configuration(spec)

        inner_config["pricing"] = self._build_pricing(spec)

        config = {coverage_id: {config_name: inner_config}}

        return yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)

    async def validate_config(self, config_yaml: str) -> ValidationResult:
        """Validate generated configuration against v2.2 schema."""
        return self.validator.validate_yaml(config_yaml)

    async def generate_stubs(
        self,
        spec: CoverageSpec,
        new_signals: List[str],
    ) -> GeneratedCode:
        """Generate code stubs for new signals."""
        logger.info(f"Generating stubs for {len(new_signals)} new signals")

        files: Dict[str, str] = {}
        coverage_id = spec.name.lower().replace(" ", "_")

        if new_signals:
            files[f"signals/{coverage_id}/extractors.py"] = self._generate_extractor_stub(
                coverage_id, new_signals
            )
            files[f"signals/{coverage_id}/aggregators.py"] = self._generate_aggregator_stub(
                coverage_id, new_signals
            )

        files[f"tests/unit/test_{coverage_id}.py"] = self._generate_test_stub(
            coverage_id, new_signals
        )

        return GeneratedCode(files=files)

    # =========================================================================
    # V2.2 CONFIG BUILDERS
    # =========================================================================

    def _build_metadata(self, spec: CoverageSpec) -> Dict[str, Any]:
        """Build metadata section with V4 multiplexer support."""
        return {
            "name": f"DSI {spec.name} Technical Pricing Model",
            "description": spec.description,
            "version": "2.2.0",
            "product_types": spec.product_types or [spec.name.lower().replace(" ", "_")],
            "applicable_markets": spec.applicable_markets,
            "minimum_viable_input": ["client name (domain optional)", "Limit in USD"],
            "min_premium": spec.min_premium,
            "default_currency": spec.default_currency,
            # V4 Multiplexer support
            "model_specificity": spec.model_specificity,
            "routing_constraints": spec.routing_constraints,
        }

    def _build_direct_queries(self, spec: CoverageSpec) -> List[Dict[str, Any]]:
        """Build v2.0 direct queries with query_condition (not bands)."""
        queries = [
            {
                "id": "claims_history",
                "question": "Has the insured had any claims in the past 5 years?",
                "query_condition": [
                    {"return": True, "action": "REFER", "override": None,
                     "applied": None, "note": "Prior claims - review required"},
                ],
            },
            {
                "id": "prior_coverage",
                "question": "Does the insured have prior coverage?",
                "query_condition": [
                    {"return": False, "action": "FLAG", "override": None,
                     "applied": None, "note": "No prior coverage"},
                ],
            },
        ]

        industry_lower = spec.industry.lower()

        if "financial" in industry_lower:
            queries.append({
                "id": "regulatory_actions",
                "question": "Any regulatory actions in the past 3 years?",
                "query_condition": [
                    {"return": True, "action": "REFER", "override": 4,
                     "applied": None, "note": "Regulatory actions - elevated risk"},
                ],
            })

        if "technology" in industry_lower or "cyber" in spec.name.lower():
            queries.extend([
                {
                    "id": "mfa_enabled",
                    "question": "Is multi-factor authentication enabled for all remote access?",
                    "query_condition": [
                        {"return": False, "action": "FLAG", "override": None,
                         "applied": None, "note": "MFA not enabled - increased ransomware risk"},
                    ],
                },
                {
                    "id": "data_breach",
                    "question": "Has the insured experienced a data breach in the past 3 years?",
                    "query_condition": [
                        {"return": True, "action": "REFER", "override": 4,
                         "applied": None, "note": "Recent data breach - requires manual review"},
                    ],
                },
                {
                    "id": "edr_deployed",
                    "question": "Is endpoint detection and response (EDR) deployed on all endpoints?",
                    "query_condition": [
                        {"return": False, "action": "FLAG", "override": None,
                         "applied": None, "note": "No EDR - reduced threat detection"},
                    ],
                },
            ])

        if "healthcare" in industry_lower:
            queries.append({
                "id": "phi_handler",
                "question": "Do you process Protected Health Information (PHI)?",
                "query_condition": [
                    {"return": True, "action": "MODIFIER", "override": None,
                     "applied": 1.25, "note": "PHI handler - HIPAA exposure"},
                ],
            })

        if "casualty" in spec.name.lower() or "liability" in industry_lower:
            queries.append({
                "id": "prior_litigation",
                "question": "Any material litigation in the past 5 years?",
                "query_condition": [
                    {"return": True, "action": "REFER", "override": 4,
                     "applied": None, "note": "Prior litigation - underwriter review required"},
                ],
            })

        return queries

    def _build_signal_registry(self, selections: List[SignalSelection]) -> List[Dict[str, Any]]:
        """
        Build v2.0 signal_registry.

        Each signal is defined once with group_id reference.
        Categorical signals use 'categories' block.
        Three-layer assessment signals use 'three_layer_assessment' block.
        """
        registry: List[Dict[str, Any]] = []

        for sel in selections:
            if not sel.enabled:
                continue

            inference_fn = sel.inference_function or f"{sel.signal_id}_basefunction"

            if sel.is_categorical and sel.categories:
                # Categorical signal
                entry = {
                    "id": sel.signal_id,
                    "inference_utility_function": inference_fn,
                    "proxy_tier": sel.proxy_tier,
                    "categories": {
                        "group_id": sel.group_id,
                        "features": sel.categories,
                    },
                }
            else:
                # Three-layer assessment signal
                tla: Dict[str, Any] = {"group_id": sel.group_id}

                # Risk dimension
                risk_block: Dict[str, Any] = {
                    "correlation_direction": sel.direction,
                    "weight": round(sel.weight, 4),
                }
                # Add score_conditions for high-weight signals
                if sel.weight >= 0.15:
                    risk_block["score_conditions"] = [
                        {
                            "threshold": 30,
                            "comparison": "<=",
                            "action": "FLAG",
                            "note": f"Low {sel.signal_name.lower()} score",
                        },
                    ]
                tla["risk"] = risk_block

                # Loss dimension (for signals with weight >= 0.10)
                if sel.weight >= 0.10:
                    tla["loss"] = {
                        "frequency": {
                            "correlation_direction": "negative" if sel.direction == "positive" else "positive",
                            "weight": round(sel.weight * 0.7, 4),
                        },
                        "severity": {
                            "correlation_direction": "negative" if sel.direction == "positive" else "positive",
                            "weight": round(sel.weight * 0.3, 4),
                        },
                    }

                # Exposure dimension (for infrastructure/footprint signals)
                if sel.group_id in ("technical_infrastructure", "corporate_footprint", "network_authority"):
                    tla["exposure"] = {
                        "size": {
                            "correlation_direction": sel.direction,
                            "weight": round(sel.weight * 0.5, 4),
                        },
                    }

                entry = {
                    "id": sel.signal_id,
                    "inference_utility_function": inference_fn,
                    "proxy_tier": sel.proxy_tier,
                    "three_layer_assessment": tla,
                }

            registry.append(entry)

        return registry

    def _build_groups(self, selections: List[SignalSelection], industry: str) -> Dict[str, Any]:
        """Build v2.0 groups section using strict SignalLibrary weighting."""
        tla_groups: Dict[str, Dict[str, Any]] = {}
        categorical_groups: List[Dict[str, Any]] = []

        # Get the source of truth for weighting
        profile = self.signal_library.get_industry_profile(industry)
        
        for sel in selections:
            if not sel.enabled: continue
            if sel.is_categorical:
                if not any(c["id"] == sel.group_id for c in categorical_groups):
                    categorical_groups.append({
                        "id": sel.group_id,
                        "label": sel.group_id.replace("_", " ").title(),
                        "impact": "MODIFIER",
                        "default_cat": "OTHER",
                    })
            else:
                if sel.group_id not in tla_groups:
                    tla_groups[sel.group_id] = {
                        "id": sel.group_id,
                        "risk": {"weight": 0.0},
                        "loss": {"weight": 0.0},
                        "exposure": {"weight": 0.0},
                    }

        # Dynamically apply weights from the IndustryProfile
        group_count = len(tla_groups)
        if group_count > 0:
            remaining_weight = 1.0
            
            # 1. Apply library-defined explicit adjustments first
            if profile and profile.weight_adjustments:
                for gid, custom_weight in profile.weight_adjustments.items():
                    if gid in tla_groups:
                        tla_groups[gid]["risk"]["weight"] = custom_weight
                        tla_groups[gid]["loss"]["weight"] = custom_weight
                        tla_groups[gid]["exposure"]["weight"] = custom_weight
                        remaining_weight -= custom_weight
            
            # 2. Distribute remaining weight evenly to unspecified groups
            unweighted_groups = [g for g, d in tla_groups.items() if d["risk"]["weight"] == 0.0]
            if unweighted_groups and remaining_weight > 0:
                even_split = round(remaining_weight / len(unweighted_groups), 4)
                for gid in unweighted_groups:
                    tla_groups[gid]["risk"]["weight"] = even_split
                    tla_groups[gid]["loss"]["weight"] = even_split
                    tla_groups[gid]["exposure"]["weight"] = even_split

            # Identify high-weight groups for score conditions
            avg_weight = 1.0 / max(len(tla_groups), 1)
            high_weight_groups = {
                gid for gid, d in tla_groups.items()
                if d["risk"]["weight"] >= avg_weight
            }

            # Add score_conditions at group level for key groups
            for gid, group in tla_groups.items():
                if gid in high_weight_groups:
                    group["risk"]["score_conditions"] = [
                        {
                            "threshold": 30,
                            "comparison": "<=",
                            "action": "REFER",
                            "override": 5,
                            "note": f"Critical deficiencies in {gid.replace('_', ' ')}",
                        },
                        {
                            "threshold": 45,
                            "comparison": "<=",
                            "action": "REFER",
                            "override": 4,
                            "note": f"Significant concerns in {gid.replace('_', ' ')}",
                        },
                    ]
                    group["loss"]["score_conditions"] = [
                        {
                            "threshold": 30,
                            "comparison": "<=",
                            "action": "MODIFIER",
                            "applied": 1.20,
                            "note": f"Poor {gid.replace('_', ' ')} - loss loading",
                        },
                    ]
        
        # If no categorical signals were selected, add defaults
        if not categorical_groups:
            categorical_groups = [
                {
                    "id": "industry_classification",
                    "label": "Industry Classification",
                    "description": "Industry classification derived from public records",
                    "impact": "MODIFIER",
                    "default_cat": "OTHER",
                },
                {
                    "id": "size_band",
                    "label": "Size Band",
                    "description": "Company size classification",
                    "impact": "MODIFIER",
                    "default_cat": "OTHER",
                },
                {
                    "id": "geography",
                    "label": "Geography",
                    "description": "Primary operational geography",
                    "impact": "MODIFIER",
                    "default_cat": "OTHER",
                },
            ]

        return {
            "categories": categorical_groups,
            "three_layer_assessment": list(tla_groups.values()),
        }
 
    def _build_risk_tier_bands(self, strategy: str) -> Dict[str, Any]:
        """
        Build v2.0 risk_tier_bands with interpretation blocks.

        Scale: 0-1000 composite risk score.
        DECLINE is tier-level action only.
        """
        strategies = {
            "conservative": {
                "bands": [(800, 1000), (650, 799), (500, 649), (350, 499), (0, 349)],
                "premiums": [8000, 12000, 18000, 30000, 50000],
            },
            "aggressive": {
                "bands": [(750, 1000), (600, 749), (450, 599), (300, 449), (0, 299)],
                "premiums": [6000, 10000, 15000, 25000, 45000],
            },
            "standard": {
                "bands": [(800, 1000), (650, 799), (500, 649), (350, 499), (0, 349)],
                "premiums": [8000, 12000, 18000, 30000, 50000],
            },
        }
        labels = ["PREFERRED", "STANDARD_PLUS", "STANDARD", "SUBSTANDARD", "DECLINE"]
        descriptions = [
            "Excellent risk - automatic approval, preferred pricing",
            "Good risk - automatic approval, standard pricing",
            "Average risk - may require referral",
            "Elevated risk - requires senior review",
            "Unacceptable risk - decline",
        ]
        actions = ["APPROVE", "APPROVE", "REFER", "REFER", "DECLINE"]

        strat = strategies.get(strategy, strategies["standard"])
        bands = []
        for i in range(5):
            bands.append({
                "id": i + 1,
                "label": labels[i],
                "description": descriptions[i],
                "interpretation": {
                    "bands": {"min": strat["bands"][i][0], "max": strat["bands"][i][1]},
                    "action": actions[i],
                    "application": {"method": "PREMIUM_BASE", "applied": strat["premiums"][i]},
                },
            })

        return {"bands": bands}

    def _build_loss_tier_bands(self) -> Dict[str, Any]:
        """Build v2.0 loss_tier_bands with frequency/severity modifiers. Scale: 0-100."""
        return {
            "bands": [
                {
                    "id": 1, "label": "VERY_LOW",
                    "description": "Very low risk of loss",
                    "interpretation": {
                        "bands": {"min": 80, "max": 100},
                        "application": {"frequency_modifier": 0.70, "severity_modifier": 0.80},
                    },
                },
                {
                    "id": 2, "label": "LOW",
                    "description": "Low risk of loss",
                    "interpretation": {
                        "bands": {"min": 60, "max": 79},
                        "application": {"frequency_modifier": 0.85, "severity_modifier": 0.90},
                    },
                },
                {
                    "id": 3, "label": "MODERATE",
                    "description": "Moderate risk of loss",
                    "interpretation": {
                        "bands": {"min": 40, "max": 59},
                        "application": {"frequency_modifier": 1.00, "severity_modifier": 1.00},
                    },
                },
                {
                    "id": 4, "label": "ELEVATED",
                    "description": "Elevated risk of loss",
                    "interpretation": {
                        "bands": {"min": 20, "max": 39},
                        "application": {"frequency_modifier": 1.15, "severity_modifier": 1.15},
                    },
                },
                {
                    "id": 5, "label": "HIGH",
                    "description": "High risk of loss",
                    "interpretation": {
                        "bands": {"min": 0, "max": 19},
                        "application": {"frequency_modifier": 1.35, "severity_modifier": 1.40},
                    },
                },
            ],
            "constraints": {"floor": 0.55, "cap": 1.60},
        }

    def _build_exposure(self) -> Dict[str, Any]:
        """Build v2.0 nested exposure with size and complexity dimensions. Scale: 0-100."""
        return {
            "size": {
                "weight": 0.60,
                "bands": [
                    {
                        "id": 1, "label": "MICRO",
                        "description": "Micro exposure value ($0 - $1M)",
                        "interpretation": {
                            "bands": {"min": 0, "max": 20},
                            "application": {
                                "method": "MODIFIER", "applied": 0.50,
                                "implied_thresholds": {"min": 0, "max": 1000000},
                            },
                        },
                    },
                    {
                        "id": 2, "label": "SMALL",
                        "description": "Small exposure value ($1M - $10M)",
                        "interpretation": {
                            "bands": {"min": 21, "max": 40},
                            "application": {
                                "method": "MODIFIER", "applied": 0.75,
                                "implied_thresholds": {"min": 1000000, "max": 10000000},
                            },
                        },
                    },
                    {
                        "id": 3, "label": "MEDIUM",
                        "description": "Medium exposure value ($10M - $50M)",
                        "interpretation": {
                            "bands": {"min": 41, "max": 60},
                            "application": {
                                "method": "MODIFIER", "applied": 1.00,
                                "implied_thresholds": {"min": 10000000, "max": 50000000},
                            },
                        },
                    },
                    {
                        "id": 4, "label": "LARGE",
                        "description": "Large exposure value ($50M - $250M)",
                        "interpretation": {
                            "bands": {"min": 61, "max": 80},
                            "application": {
                                "method": "MODIFIER", "applied": 1.50,
                                "implied_thresholds": {"min": 50000000, "max": 250000000},
                            },
                        },
                    },
                    {
                        "id": 5, "label": "VERY_LARGE",
                        "description": "Very large exposure value ($250M+)",
                        "interpretation": {
                            "bands": {"min": 81, "max": 100},
                            "application": {
                                "method": "MODIFIER", "applied": 2.50,
                                "implied_thresholds": {"min": 250000000, "max": 1000000000},
                            },
                        },
                    },
                ],
            },
            "complexity": {
                "weight": 0.40,
                "bands": [
                    {
                        "id": 1, "label": "SIMPLE",
                        "description": "Simple operational complexity",
                        "interpretation": {
                            "bands": {"min": 0, "max": 20},
                            "application": {"method": "MODIFIER", "applied": 0.85},
                        },
                    },
                    {
                        "id": 2, "label": "MODERATE",
                        "description": "Moderate operational complexity",
                        "interpretation": {
                            "bands": {"min": 21, "max": 40},
                            "application": {"method": "MODIFIER", "applied": 0.95},
                        },
                    },
                    {
                        "id": 3, "label": "COMPLEX",
                        "description": "Complex operations",
                        "interpretation": {
                            "bands": {"min": 41, "max": 60},
                            "application": {"method": "MODIFIER", "applied": 1.10},
                        },
                    },
                    {
                        "id": 4, "label": "HIGHLY_COMPLEX",
                        "description": "Highly complex operations",
                        "interpretation": {
                            "bands": {"min": 61, "max": 80},
                            "application": {"method": "MODIFIER", "applied": 1.30},
                        },
                    },
                    {
                        "id": 5, "label": "EXTREMELY_COMPLEX",
                        "description": "Extremely complex operations",
                        "interpretation": {
                            "bands": {"min": 81, "max": 100},
                            "application": {"method": "MODIFIER", "applied": 1.60},
                        },
                    },
                ],
            },
        }

    def _build_limit_bandings(self, spec: CoverageSpec) -> List[Dict[str, Any]]:
        """Build standard limit/deductible combinations for BUNDLED mode."""
        # Use base_deductible_reference as the anchor point
        base_ded = spec.base_deductible_reference
        return [
            {"id": 1, "limit": 1000000, "deductible": int(base_ded * 0.5)},  # 25k if base=50k
            {"id": 2, "limit": 5000000, "deductible": base_ded},             # 50k anchor
            {"id": 3, "limit": 10000000, "deductible": int(base_ded * 2)},   # 100k
            {"id": 4, "limit": 25000000, "deductible": int(base_ded * 5)},   # 250k
            {"id": 5, "limit": 50000000, "deductible": int(base_ded * 10)},  # 500k
        ]

    def _build_limit_configuration(self, spec: CoverageSpec) -> Dict[str, Any]:
        """Build polymorphic limit configuration for V5 (BUNDLED or DECOUPLED)."""
        if spec.pricing_mode == "DECOUPLED":
            config = {
                "type": "DECOUPLED",
                "valid_deductibles": spec.valid_deductibles or [25000, 50000, 100000, 250000, 500000],
            }
            # Prefer programmatic min/max over hard-coded valid_limits
            if spec.min_limit is not None and spec.max_limit is not None:
                config["min_limit"] = spec.min_limit
                config["max_limit"] = spec.max_limit
            else:
                config["valid_limits"] = spec.valid_limits or [1000000, 5000000, 10000000, 25000000, 50000000]
            return config
        else:
            # BUNDLED Mode (SME Menu Pricing)
            base_ded = spec.base_deductible_reference
            return {
                "type": "BUNDLED",
                "packages": [
                    {"id": 1, "label": "STARTER", "limit": 1000000, "deductible": int(base_ded * 0.5)},
                    {"id": 2, "label": "STANDARD", "limit": 5000000, "deductible": base_ded}, # Anchor
                    {"id": 3, "label": "ENHANCED", "limit": 10000000, "deductible": int(base_ded * 2)},
                    {"id": 4, "label": "PREMIUM", "limit": 25000000, "deductible": int(base_ded * 5)},
                ]
            }
    
    def _build_pricing(self, spec: CoverageSpec) -> Dict[str, Any]:
        """Build pricing section with V5 anchors, ILF curve, and deductible factors."""
        pricing = {
            "base_limit_reference": spec.base_limit_reference,
            "base_deductible_reference": spec.base_deductible_reference,
            "by_product_type": {},

        }
        
        # Phase 5: Curves must be nested by product type
        products = spec.product_types if spec.product_types else [spec.name.lower().replace(" ", "_")]
        for product in products:
            pricing["by_product_type"][product] = {
                "ilf_curve": self._build_ilf_curve(spec),
                "deductible_factors": self._build_deductible_factors(spec)
            }
            
        return pricing
  
    def _build_ilf_curve(self, spec: CoverageSpec) -> Dict[str, Any]:
        """Build parametric ILF curve configuration.

        Generates anchor_limit + curve + params format. Uniform anchor
        normalisation (ILF = raw(L) / raw(anchor)) is applied at runtime
        by the ILFCurve engine — the builder only needs to specify the
        curve shape and parameters.
        """
        anchor = spec.ilf_anchor_limit or spec.base_limit_reference

        # Use spec-level overrides if provided, otherwise sensible defaults
        curve_type = spec.ilf_curve_type
        params = dict(spec.ilf_params) if spec.ilf_params else {}

        if not params:
            # Default params by curve type
            if curve_type == "bounded_exponential":
                params = {"max_ilf": 4.5, "k": 0.025, "cap": 8.0}
            elif curve_type == "power":
                params = {"alpha": 0.45, "cap": 6.0}
            elif curve_type == "logarithmic":
                params = {"a": 0.8, "b": 0.15, "cap": 3.5}
            elif curve_type == "pareto":
                params = {"alpha": 0.5, "cap": 12.0}
            elif curve_type == "iso_pareto":
                params = {"q": 2.0, "b": 25000.0, "cap": 5.0}

        return {
            "anchor_limit": anchor,
            "curve": curve_type,
            "params": params,
        }

    def _build_deductible_factors(self, spec: CoverageSpec) -> List[Dict[str, Any]]:
        """
        Build deductible factor table with anchor = 1.00.

        The anchor deductible (base_deductible_reference) has factor 1.00.
        Lower deductibles have factors > 1.00 (premium loading).
        Higher deductibles have factors < 1.00 (premium credit).
        """
        anchor = spec.base_deductible_reference
        return [
            {"deductible": int(anchor * 0.5), "factor": 1.15},   # 25k: +15%
            {"deductible": anchor, "factor": 1.00},               # 50k: anchor
            {"deductible": int(anchor * 2), "factor": 0.85},      # 100k: -15%
            {"deductible": int(anchor * 5), "factor": 0.70},      # 250k: -30%
            {"deductible": int(anchor * 10), "factor": 0.55},     # 500k: -45%
        ]

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _identify_risk_factors(self, industry: str) -> List[str]:
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
        categories = ["technical_infrastructure", "corporate_footprint", "financial_health"]
        industry_lower = industry.lower()
        if "financial" in industry_lower:
            categories.extend(["regulatory_compliance", "governance"])
        elif "technology" in industry_lower:
            categories.extend(["cyber_security", "network_authority"])
        return categories

    def _is_new_signal(self, selection: SignalSelection) -> bool:
        return not self.signal_library.has_signal(selection.signal_id)

    def _generate_extractor_stub(self, coverage_id: str, signals: List[str]) -> str:
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

    def _generate_aggregator_stub(self, coverage_id: str, signals: List[str]) -> str:
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

    def _generate_test_stub(self, coverage_id: str, signals: List[str]) -> str:
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

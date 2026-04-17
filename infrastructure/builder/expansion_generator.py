"""
DSI Coverage Expansion Generator

Takes an ExpansionSpec (structured YAML) and generates:
1. Complete v2.2/v2.3 config YAML sub-configurations
2. Signal extractor stubs
3. Signal aggregator stubs
4. Inference function registrations
5. __init__.py module updates

This replaces the manual, multi-session process of transcribing phase docs
into config YAML and signal architecture code.
"""

import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .expansion_types import (
    CategoryFeature,
    ConfigurationSpec,
    DirectQuerySpec,
    ExposureBands,
    ExpansionResult,
    ExpansionSpec,
    GroupWeights,
    LimitConfiguration,
    LimitConfigType,
    LossTierBands,
    PricingSpec,
    ProductPricing,
    QueryCondition,
    RiskTierBands,
    RoutingConstraint,
    SignalGroupSpec,
    SignalSpec,
    SignalType,
    ThreeLayerWeights,
)


# =============================================================================
# YAML GENERATION
# =============================================================================

class ConfigYAMLGenerator:
    """Generates v2.2/v2.3 compliant config YAML from expansion spec."""

    def __init__(self, spec: ExpansionSpec, existing_config: Optional[Dict] = None):
        self.spec = spec
        self.existing_config = existing_config or {}

    def generate(self) -> str:
        """Generate complete config YAML for all configurations in the spec."""
        # Build all sub-configurations
        sub_configs = {}
        for config in self.spec.configurations:
            sub_configs[config.id] = self._build_sub_config(config)

        # If existing config provided, merge new sub-configs into it
        if self.existing_config:
            root = dict(self.existing_config)
            coverage_key = self.spec.coverage_key
            if coverage_key in root:
                root[coverage_key].update(sub_configs)
            else:
                root[coverage_key] = sub_configs
        else:
            root = {self.spec.coverage_key: sub_configs}

        return self._dump_yaml(root)

    def generate_new_configs_only(self) -> str:
        """Generate YAML for only the new sub-configurations (for appending)."""
        lines = []
        for config in self.spec.configurations:
            sub_config = self._build_sub_config(config)
            config_yaml = self._dump_yaml({config.id: sub_config})
            # Indent by 2 spaces (sub-configuration level)
            indented = "\n".join(
                f"  {line}" if line.strip() else line
                for line in config_yaml.split("\n")
            )
            comment = f"  # {'=' * 75}\n  # {config.name.upper()}\n  # {'=' * 75}"
            lines.append(f"\n{comment}\n{indented}")
        return "\n".join(lines)

    def _build_sub_config(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build a complete sub-configuration dict."""
        return {
            "metadata": self._build_metadata(config),
            "direct_queries": self._build_direct_queries(config),
            "signal_registry": self._build_signal_registry(config),
            "groups": self._build_groups(config),
            "risk_tier_bands": self._build_risk_tier_bands(config),
            "loss_tier_bands": self._build_loss_tier_bands(config),
            "exposure": self._build_exposure(config),
            "limit_configuration": self._build_limit_configuration(config),
            "pricing": self._build_pricing(config),
            "guardrails": self._build_guardrails(config),
        }

    def _build_metadata(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build metadata section."""
        product_types = config.product_types or self.spec.default_product_types
        markets = config.applicable_markets or self.spec.default_markets
        min_premium = config.min_premium or self.spec.default_min_premium
        mvi = config.minimum_viable_input or self.spec.default_minimum_viable_input

        meta = {
            "name": config.name,
            "description": config.description,
            "version": self.spec.version,
            "product_types": product_types,
            "applicable_markets": markets,
            "minimum_viable_input": {"required": mvi} if mvi else {},
            "min_premium": min_premium,
            "default_currency": self.spec.default_currency,
            "model_specificity": config.model_specificity,
            "routing_constraints": [
                {
                    "field": rc.field,
                    "operator": rc.operator.lower() if rc.operator.upper() == "IN" else rc.operator,
                    "value": rc.value,
                    "required_in_input": rc.required_in_input,
                }
                for rc in config.routing_constraints
            ],
        }
        return meta

    def _build_direct_queries(self, config: ConfigurationSpec) -> List[Dict]:
        """Build direct queries section."""
        queries = []
        for dq in config.direct_queries:
            query = {
                "id": dq.id,
                "question": dq.question,
                "query_condition": [
                    {
                        "return": cond.return_value,
                        "action": cond.action,
                        "override": cond.override,
                        "applied": cond.applied,
                        "note": cond.note,
                    }
                    for cond in dq.conditions
                ],
            }
            queries.append(query)
        return queries

    def _build_signal_registry(self, config: ConfigurationSpec) -> List[Dict]:
        """Build signal registry section from spec signals."""
        registry = []

        # Collect all signals for this config
        all_signals = self._collect_signals_for_config(config)

        for signal in all_signals:
            entry = {
                "id": signal.id,
                "inference_utility_function": f"{signal.id}_basefunction",
                "proxy_tier": signal.proxy_tier,
            }

            if signal.signal_type == SignalType.CATEGORICAL:
                entry["categories"] = {
                    "group_id": signal.group_id,
                    "source": signal.category_source or f"metadata.{signal.id}",
                    "features": [
                        {"cat": f.cat, "label": f.label, "applied": f.applied}
                        for f in (signal.categories or [])
                    ],
                }
            else:
                tla = signal.three_layer or ThreeLayerWeights()
                three_layer = {
                    "group_id": signal.group_id,
                    "risk": {
                        "correlation_direction": tla.risk_direction,
                        "weight": tla.risk_weight,
                    },
                }
                # Add loss sub-dimensions if weights are non-zero
                loss = {}
                if tla.loss_frequency_weight > 0:
                    loss["frequency"] = {
                        "correlation_direction": tla.loss_frequency_direction,
                        "weight": tla.loss_frequency_weight,
                    }
                if tla.loss_severity_weight > 0:
                    loss["severity"] = {
                        "correlation_direction": tla.loss_severity_direction,
                        "weight": tla.loss_severity_weight,
                    }
                if loss:
                    three_layer["loss"] = loss

                # Add exposure sub-dimensions if weights are non-zero
                exposure = {}
                if tla.exposure_size_weight > 0:
                    exposure["size"] = {
                        "correlation_direction": tla.exposure_size_direction,
                        "weight": tla.exposure_size_weight,
                    }
                if tla.exposure_complexity_weight > 0:
                    exposure["complexity"] = {
                        "correlation_direction": tla.exposure_complexity_direction,
                        "weight": tla.exposure_complexity_weight,
                    }
                if exposure:
                    three_layer["exposure"] = exposure

                # Add score conditions if present
                if tla.score_conditions:
                    three_layer["risk"]["score_conditions"] = tla.score_conditions

                entry["three_layer_assessment"] = three_layer

            registry.append(entry)

        return registry

    def _collect_signals_for_config(self, config: ConfigurationSpec) -> List[SignalSpec]:
        """Collect all signals that belong to this config."""
        signals = []

        # Gather signals from new groups that are referenced by this config's group_weights
        group_ids = {gw.group_id for gw in config.group_weights}
        group_ids.update(config.category_groups)

        for group in self.spec.new_signal_groups:
            if group.id in group_ids:
                for sig in group.signals:
                    if sig.id not in config.exclude_signals:
                        signals.append(sig)

        # Add explicitly listed additional signals
        all_new_signals = {}
        for group in self.spec.new_signal_groups:
            for sig in group.signals:
                all_new_signals[sig.id] = sig

        for sig_id in config.additional_signals:
            if sig_id in all_new_signals and sig_id not in [s.id for s in signals]:
                signals.append(all_new_signals[sig_id])

        return signals

    def _build_groups(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build groups section."""
        categories = []
        three_layer = []

        # Category groups
        for group in self.spec.new_signal_groups:
            if group.group_type == "categories" and group.id in config.category_groups:
                categories.append({
                    "id": group.id,
                    "label": group.label,
                    "description": group.description,
                    "impact": "MODIFIER",
                    "default_cat": "OTHER",
                })

        # Also include new_category_groups from spec
        for cg in self.spec.new_category_groups:
            if cg.get("id") in config.category_groups:
                categories.append(cg)

        # Three-layer assessment groups
        for gw in config.group_weights:
            # Find the group spec if it exists in new groups
            group_spec = None
            for g in self.spec.new_signal_groups:
                if g.id == gw.group_id and g.group_type == "three_layer_assessment":
                    group_spec = g
                    break

            entry = {
                "id": gw.group_id,
                "label": group_spec.label if group_spec else gw.group_id.replace("_", " ").title(),
                "description": group_spec.description if group_spec else "",
                "risk": {"weight": gw.risk_weight},
                "loss": {"weight": gw.loss_weight},
                "exposure": {"weight": gw.exposure_weight},
            }

            if gw.score_conditions:
                entry["risk"]["score_conditions"] = gw.score_conditions

            three_layer.append(entry)

        result = {}
        if categories:
            result["categories"] = categories
        if three_layer:
            result["three_layer_assessment"] = three_layer
        return result

    def _build_risk_tier_bands(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build risk tier bands section."""
        bands = config.risk_tier_bands or self.spec.default_risk_tier_bands or RiskTierBands()

        return {
            "bands": [
                {
                    "id": 1,
                    "label": "PREFERRED",
                    "description": "Excellent risk - automatic approval, preferred pricing",
                    "interpretation": {
                        "bands": {"min": bands.preferred_min, "max": 1000},
                        "action": "APPROVE",
                        "application": {
                            "method": bands.method,
                            "applied": bands.preferred_rate,
                            "basis": bands.basis,
                        },
                    },
                },
                {
                    "id": 2,
                    "label": "STANDARD_PLUS",
                    "description": "Good risk - automatic approval, standard pricing",
                    "interpretation": {
                        "bands": {"min": bands.standard_plus_min, "max": bands.preferred_min - 1},
                        "action": "APPROVE",
                        "application": {
                            "method": bands.method,
                            "applied": bands.standard_plus_rate,
                            "basis": bands.basis,
                        },
                    },
                },
                {
                    "id": 3,
                    "label": "STANDARD",
                    "description": "Average risk - may require referral",
                    "interpretation": {
                        "bands": {"min": bands.standard_min, "max": bands.standard_plus_min - 1},
                        "action": "REFER",
                        "application": {
                            "method": bands.method,
                            "applied": bands.standard_rate,
                            "basis": bands.basis,
                        },
                    },
                },
                {
                    "id": 4,
                    "label": "SUBSTANDARD",
                    "description": "Elevated risk - requires senior review",
                    "interpretation": {
                        "bands": {"min": bands.substandard_min, "max": bands.standard_min - 1},
                        "action": "REFER",
                        "application": {
                            "method": bands.method,
                            "applied": bands.substandard_rate,
                            "basis": bands.basis,
                        },
                    },
                },
                {
                    "id": 5,
                    "label": "DECLINE",
                    "description": "Unacceptable risk - decline",
                    "interpretation": {
                        "bands": {"min": 0, "max": bands.substandard_min - 1},
                        "action": "DECLINE",
                        "application": {
                            "method": bands.method,
                            "applied": bands.decline_rate,
                            "basis": bands.basis,
                        },
                    },
                },
            ]
        }

    def _build_loss_tier_bands(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build loss tier bands section."""
        bands = config.loss_tier_bands or self.spec.default_loss_tier_bands or LossTierBands()

        return {
            "bands": [
                {
                    "id": 1, "label": "VERY_LOW",
                    "description": "Very low risk of loss",
                    "interpretation": {
                        "bands": {"min": 80, "max": 100},
                        "application": {
                            "frequency_modifier": bands.very_low_freq,
                            "severity_modifier": bands.very_low_sev,
                        },
                    },
                },
                {
                    "id": 2, "label": "LOW",
                    "description": "Low risk of loss",
                    "interpretation": {
                        "bands": {"min": 60, "max": 79},
                        "application": {
                            "frequency_modifier": bands.low_freq,
                            "severity_modifier": bands.low_sev,
                        },
                    },
                },
                {
                    "id": 3, "label": "MODERATE",
                    "description": "Moderate risk of loss",
                    "interpretation": {
                        "bands": {"min": 40, "max": 59},
                        "application": {
                            "frequency_modifier": bands.moderate_freq,
                            "severity_modifier": bands.moderate_sev,
                        },
                    },
                },
                {
                    "id": 4, "label": "ELEVATED",
                    "description": "Elevated risk of loss",
                    "interpretation": {
                        "bands": {"min": 20, "max": 39},
                        "application": {
                            "frequency_modifier": bands.elevated_freq,
                            "severity_modifier": bands.elevated_sev,
                        },
                    },
                },
                {
                    "id": 5, "label": "HIGH",
                    "description": "High risk of loss",
                    "interpretation": {
                        "bands": {"min": 0, "max": 19},
                        "application": {
                            "frequency_modifier": bands.high_freq,
                            "severity_modifier": bands.high_sev,
                        },
                    },
                },
            ],
            "constraints": {"floor": bands.floor, "cap": bands.cap},
        }

    def _build_exposure(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build exposure section."""
        bands = config.exposure_bands or self.spec.default_exposure_bands or ExposureBands()

        # Standard score bands for 5 tiers
        score_ranges = [
            (0, 20), (21, 40), (41, 60), (61, 80), (81, 100),
        ]

        size_bands = []
        for i, threshold in enumerate(bands.size_thresholds):
            prev_max = bands.size_thresholds[i - 1]["max_value"] if i > 0 else 0
            size_bands.append({
                "id": i + 1,
                "label": threshold["label"],
                "description": f"{threshold['label'].replace('_', ' ').title()} exposure value",
                "interpretation": {
                    "bands": {"min": score_ranges[i][0], "max": score_ranges[i][1]},
                    "application": {
                        "method": "MODIFIER",
                        "applied": threshold["applied"],
                        "implied_thresholds": {
                            "min": prev_max,
                            "max": threshold["max_value"],
                        },
                    },
                },
            })

        complexity_labels = ["Simple", "Moderate", "Complex", "Highly complex", "Extremely complex"]
        complexity_bands = []
        for i, mod in enumerate(bands.complexity_modifiers):
            complexity_bands.append({
                "id": i + 1,
                "label": mod["label"],
                "description": f"{complexity_labels[i]} operational complexity",
                "interpretation": {
                    "bands": {"min": score_ranges[i][0], "max": score_ranges[i][1]},
                    "application": {
                        "method": "MODIFIER",
                        "applied": mod["applied"],
                    },
                },
            })

        return {
            "size": {"weight": bands.size_weight, "bands": size_bands},
            "complexity": {"weight": bands.complexity_weight, "bands": complexity_bands},
        }

    def _build_limit_configuration(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build limit configuration section."""
        lc = config.limit_configuration or self.spec.default_limit_configuration or LimitConfiguration()

        result = {"type": lc.type.value}

        if lc.type == LimitConfigType.DECOUPLED:
            if lc.min_limit is not None and lc.max_limit is not None:
                result["min_limit"] = lc.min_limit
                result["max_limit"] = lc.max_limit
            elif lc.valid_limits:
                result["valid_limits"] = lc.valid_limits
            result["valid_deductibles"] = lc.valid_deductibles
        elif lc.type == LimitConfigType.BUNDLED and lc.packages:
            result["packages"] = lc.packages

        return result

    def _build_pricing(self, config: ConfigurationSpec) -> Dict[str, Any]:
        """Build pricing section."""
        pricing = config.pricing or self.spec.default_pricing or PricingSpec()

        by_product = {}
        for pp in pricing.by_product_type:
            ilf = pp.ilf_curve
            if ilf.anchor_limit is not None and ilf.curve is not None:
                # Parametric mode — use directly
                ilf_dict = {
                    "anchor_limit": ilf.anchor_limit,
                    "curve": ilf.curve,
                    "params": ilf.params or {},
                }
            else:
                # Table-based mode — convert to parametric (production schema
                # requires anchor_limit/curve/params, not base_limit/factors)
                ilf_dict = {
                    "anchor_limit": ilf.base_limit,
                    "curve": "bounded_exponential",
                    "params": {"max_ilf": 5.0, "k": 0.02},
                }
            entry = {
                "ilf_curve": ilf_dict,
                "deductible_factors": pp.deductible_factors,
            }
            by_product[pp.product_type] = entry

        return {
            "base_limit_reference": pricing.base_limit_reference,
            "base_deductible_reference": pricing.base_deductible_reference,
            "by_product_type": by_product,

        }

    def _build_guardrails(self, config) -> Dict[str, Any]:
        """Build guardrails section from config or defaults."""
        from infrastructure.builder.expansion_types import GuardrailsSpec
        gs = config.guardrails or GuardrailsSpec()
        return {
            "modifier_floor": gs.modifier_floor,
            "modifier_cap": gs.modifier_cap,
            "max_premium_to_limit_ratio": gs.max_premium_to_limit_ratio,
            "max_premium_to_revenue_ratio": gs.max_premium_to_revenue_ratio,
            "max_ilf_factor": gs.max_ilf_factor,
        }

    def _dump_yaml(self, data: Dict) -> str:
        """Dump dict to YAML string with clean formatting."""
        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )


# =============================================================================
# SIGNAL CODE GENERATION
# =============================================================================

class SignalCodeGenerator:
    """Generates signal architecture code from expansion spec."""

    def __init__(self, spec: ExpansionSpec):
        self.spec = spec
        self.coverage_dir = spec.coverage_line.replace(" ", "_").lower()

    def generate_all(self) -> Dict[str, str]:
        """Generate all signal code files. Returns {relative_path: content}."""
        files = {}

        # Collect all new signals across all groups
        all_signals = []
        for group in self.spec.new_signal_groups:
            all_signals.extend(group.signals)

        if not all_signals:
            return files

        phase_name = self.spec.phase.replace(" ", "_").lower()

        # 1. Extractor stubs
        extractor_path = (
            f"signal_architecture/signals/extractors/stubs/"
            f"{self.coverage_dir}/{phase_name}_extractors.py"
        )
        files[extractor_path] = self._generate_extractors(all_signals)

        # 2. Aggregator stubs
        aggregator_path = (
            f"signal_architecture/signals/aggregators/implementations/"
            f"{self.coverage_dir}/{phase_name}_aggregators.py"
        )
        files[aggregator_path] = self._generate_aggregators(all_signals)

        # 3. Inference functions
        inference_path = (
            f"signal_architecture/signals/inference/functions/"
            f"{self.coverage_dir}/{phase_name}_signals.py"
        )
        files[inference_path] = self._generate_inference_functions(all_signals)

        return files

    def _generate_extractors(self, signals: List[SignalSpec]) -> str:
        """Generate extractor stub classes."""
        lines = [
            '"""',
            f"DSI {self.spec.description} — Extractor Stubs",
            f"",
            f"Auto-generated by CoverageExpansionGenerator from {self.spec.phase}.",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            '"""',
            "",
            "from signal_architecture.signals.extractors.base import StubExtractor",
            "",
            "",
            "# TTL constants",
            "TTL_DAILY = 86400",
            "TTL_WEEKLY = 604800",
            "TTL_MONTHLY = 2592000",
            "",
        ]

        ttl_map = {"DAILY": "TTL_DAILY", "WEEKLY": "TTL_WEEKLY", "MONTHLY": "TTL_MONTHLY"}

        # Group signals by their group_id for organization
        by_group = {}
        for sig in signals:
            by_group.setdefault(sig.group_id, []).append(sig)

        for group_id, group_signals in by_group.items():
            lines.append(f"# {'=' * 70}")
            lines.append(f"# {group_id.upper().replace('_', ' ')} SIGNALS")
            lines.append(f"# {'=' * 70}")
            lines.append("")

            for sig in group_signals:
                class_name = self._to_class_name(sig.id) + "Extractor"
                ttl = ttl_map.get(sig.ttl, "TTL_WEEKLY")

                lines.append(f"class {class_name}(StubExtractor):")
                lines.append(f'    """Extract {sig.name} signal — {sig.description}"""')
                lines.append(f'    SOURCE_NAME = "{sig.id}"')
                lines.append(f"    DEFAULT_TTL_SECONDS = {ttl}")
                lines.append("")
                lines.append("    async def _do_extract(self, entity_id: str, context: dict) -> dict:")
                lines.append("        data = {")
                lines.append(f'            "query_timestamp": self._now_iso(),')
                lines.append(f'            "entity_id": entity_id,')
                lines.append(f'            "data": {{')

                # Generate stub data fields based on signal type
                if sig.signal_type == SignalType.CATEGORICAL:
                    cats = [f.cat for f in (sig.categories or [])]
                    cats_str = ", ".join(f'"{c}"' for c in cats[:5])
                    lines.append(f'                "{sig.id}": self._random_choice([{cats_str}]),')
                else:
                    lines.append(f'                "{sig.id}_score": self._random_float(0, 100),')

                # Add any explicitly defined extractor fields
                for field_name, field_type in sig.extractor_fields.items():
                    if field_type == "float":
                        lines.append(f'                "{field_name}": self._random_float(0, 100),')
                    elif field_type == "int":
                        lines.append(f'                "{field_name}": self._random_int(0, 100),')
                    elif field_type == "bool":
                        lines.append(f'                "{field_name}": self._random_bool(),')
                    else:
                        lines.append(f'                "{field_name}": self._random_choice(["A", "B", "C"]),')

                lines.append("            },")
                lines.append("        }")
                lines.append("        return self._create_success_result(data)")
                lines.append("")
                lines.append("")

        return "\n".join(lines)

    def _generate_aggregators(self, signals: List[SignalSpec]) -> str:
        """Generate aggregator stub classes using factory pattern."""
        lines = [
            '"""',
            f"DSI {self.spec.description} — Aggregator Stubs",
            f"",
            f"Auto-generated by CoverageExpansionGenerator from {self.spec.phase}.",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            '"""',
            "",
            "from signal_architecture.signals.aggregators.base import ProductionAggregator",
            "",
            "",
            "def _simple_agg(signal_id, score_key, default=50.0):",
            '    """Factory: creates a score-passthrough aggregator."""',
            "",
            "    class Agg(ProductionAggregator):",
            '        SOURCE_NAME = signal_id',
            "",
            "        async def _do_aggregate(self, extractor_results):",
            '            raw = self._get_primary_data(extractor_results, "data")',
            "            val = self._normalize_float(raw.get(score_key), default)",
            "            return self._create_success_result({score_key: round(val, 1)}, extractor_results)",
            "",
            "    Agg.__name__ = Agg.__qualname__ = f'{_to_class(signal_id)}Aggregator'",
            "    return Agg",
            "",
            "",
            "def _categorical_agg(signal_id, cat_key, default='OTHER'):",
            '    """Factory: creates a categorical aggregator."""',
            "",
            "    class Agg(ProductionAggregator):",
            '        SOURCE_NAME = signal_id',
            "",
            "        async def _do_aggregate(self, extractor_results):",
            '            raw = self._get_primary_data(extractor_results, "data")',
            "            val = raw.get(cat_key, default)",
            "            return self._create_success_result({cat_key: val}, extractor_results)",
            "",
            "    Agg.__name__ = Agg.__qualname__ = f'{_to_class(signal_id)}Aggregator'",
            "    return Agg",
            "",
            "",
            "def _to_class(signal_id):",
            '    """Convert signal_id to PascalCase class name."""',
            "    return ''.join(part.capitalize() for part in signal_id.split('_'))",
            "",
            "",
            "# =============================================================================",
            "# AGGREGATOR DEFINITIONS",
            "# =============================================================================",
            "",
        ]

        for sig in signals:
            class_name = self._to_class_name(sig.id) + "Aggregator"
            if sig.signal_type == SignalType.CATEGORICAL:
                lines.append(
                    f'{class_name} = _categorical_agg("{sig.id}", "{sig.id}")'
                )
            else:
                lines.append(
                    f'{class_name} = _simple_agg("{sig.id}", "{sig.id}_score")'
                )

        lines.append("")
        return "\n".join(lines)

    def _generate_inference_functions(self, signals: List[SignalSpec]) -> str:
        """Generate inference function registrations.

        V6/E10 — generator no longer emits imports from the stub
        `extractors.stubs` or `aggregators.implementations` packages.
        New phase files register neutral stand-ins; real extractor
        wiring lands via the D-series production extractors (Stage 6).
        """
        phase_name = self.spec.phase.replace(" ", "_").lower()
        phase_prefix = phase_name.replace("phase_", "p")

        lines = [
            '"""',
            f"DSI {self.spec.description} — Inference Functions",
            f"",
            f"Auto-generated by CoverageExpansionGenerator from {self.spec.phase}.",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"",
            f"V6/E10 — neutral stand-ins; real extractor wiring lands via",
            f"the D-series production extractors (Stage 6).",
            '"""',
            "",
            "from signal_architecture.signals.inference.registry import register_inference_function",
            "from signal_architecture.signals.types import SignalResult",
            "",
            "",
            "# V6/E10 neutral stand-ins.",
            "async def _run_pipeline(signal_id, *args, default=50.0, **kwargs):",
            "    return SignalResult(signal_id=signal_id, score=float(default),",
            "                        confidence=0.5, execution_time_ms=0.0)",
            "",
            "",
            'async def _run_categorical(signal_id, *args, default="OTHER", **kwargs):',
            "    return SignalResult(signal_id=signal_id, category=default,",
            "                        confidence=0.5, execution_time_ms=0.0)",
            "",
            "",
            '# =============================================================================',
            '# REGISTERED INFERENCE FUNCTIONS',
            '# =============================================================================',
            '',
        ]

        # Generate registered functions
        for i, sig in enumerate(signals, 1):
            func_name = f"{phase_prefix}_{i:02d}"
            yaml_fn = f"{sig.id}_basefunction"

            lines.append(f'@register_inference_function("{yaml_fn}")')
            lines.append(f"async def {func_name}(entity_id, context):")
            lines.append(f'    """{sig.name}"""')

            if sig.signal_type == SignalType.CATEGORICAL:
                lines.append(
                    f'    return await _run_categorical("{sig.id}", entity_id, context)'
                )
            else:
                lines.append(
                    f'    return await _run_pipeline("{sig.id}", entity_id, context)'
                )

            lines.append("")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _to_class_name(signal_id: str) -> str:
        """Convert signal_id to PascalCase."""
        return "".join(part.capitalize() for part in signal_id.split("_"))


# =============================================================================
# SPEC LOADER (YAML -> ExpansionSpec)
# =============================================================================

def load_expansion_spec(yaml_path: str) -> ExpansionSpec:
    """Load an ExpansionSpec from a YAML file."""
    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    spec = ExpansionSpec(
        coverage_line=raw["coverage_line"],
        coverage_key=raw["coverage_key"],
        phase=raw["phase"],
        description=raw["description"],
        version=raw.get("version", "2.3.0"),
        default_product_types=raw.get("default_product_types", []),
        default_markets=raw.get("default_markets", ["us", "uk", "eu", "apac"]),
        default_currency=raw.get("default_currency", "USD"),
        default_min_premium=raw.get("default_min_premium", 25000),
        default_minimum_viable_input=raw.get("default_minimum_viable_input", []),
        routing_field=raw.get("routing_field", ""),
    )

    # Parse new signal groups
    for group_raw in raw.get("new_signal_groups", []):
        group = SignalGroupSpec(
            id=group_raw["id"],
            label=group_raw["label"],
            description=group_raw.get("description", ""),
            group_type=group_raw.get("group_type", "three_layer_assessment"),
        )
        for sig_raw in group_raw.get("signals", []):
            sig = _parse_signal(sig_raw)
            group.signals.append(sig)
        spec.new_signal_groups.append(group)

    # Parse new category groups
    spec.new_category_groups = raw.get("new_category_groups", [])

    # Parse default tier bands
    if "default_risk_tier_bands" in raw:
        spec.default_risk_tier_bands = _parse_risk_tier_bands(raw["default_risk_tier_bands"])
    if "default_loss_tier_bands" in raw:
        spec.default_loss_tier_bands = _parse_loss_tier_bands(raw["default_loss_tier_bands"])
    if "default_exposure_bands" in raw:
        spec.default_exposure_bands = _parse_exposure_bands(raw["default_exposure_bands"])
    if "default_limit_configuration" in raw:
        spec.default_limit_configuration = _parse_limit_config(raw["default_limit_configuration"])
    if "default_pricing" in raw:
        spec.default_pricing = _parse_pricing(raw["default_pricing"])

    # Parse configurations
    for conf_raw in raw.get("configurations", []):
        conf = _parse_configuration(conf_raw)
        spec.configurations.append(conf)

    return spec


def _parse_signal(raw: Dict) -> SignalSpec:
    """Parse a signal from raw YAML dict."""
    sig = SignalSpec(
        id=raw["id"],
        name=raw.get("name", raw["id"].replace("_", " ").title()),
        description=raw.get("description", ""),
        group_id=raw["group_id"],
        proxy_tier=raw.get("proxy_tier", "INFERRED_PROXY"),
        signal_type=SignalType(raw.get("signal_type", "three_layer")),
        ttl=raw.get("ttl", "WEEKLY"),
        extractor_fields=raw.get("extractor_fields", {}),
    )

    if sig.signal_type == SignalType.CATEGORICAL:
        sig.category_source = raw.get("category_source")
        sig.categories = [
            CategoryFeature(cat=c["cat"], label=c["label"], applied=c["applied"])
            for c in raw.get("categories", [])
        ]
    else:
        tla_raw = raw.get("three_layer", {})
        sig.three_layer = ThreeLayerWeights(
            risk_direction=tla_raw.get("risk_direction", "positive"),
            risk_weight=tla_raw.get("risk_weight", 0.0),
            loss_frequency_direction=tla_raw.get("loss_frequency_direction", "positive"),
            loss_frequency_weight=tla_raw.get("loss_frequency_weight", 0.0),
            loss_severity_direction=tla_raw.get("loss_severity_direction", "positive"),
            loss_severity_weight=tla_raw.get("loss_severity_weight", 0.0),
            exposure_size_direction=tla_raw.get("exposure_size_direction", "positive"),
            exposure_size_weight=tla_raw.get("exposure_size_weight", 0.0),
            exposure_complexity_direction=tla_raw.get("exposure_complexity_direction", "positive"),
            exposure_complexity_weight=tla_raw.get("exposure_complexity_weight", 0.0),
            score_conditions=tla_raw.get("score_conditions", []),
        )

    return sig


def _parse_risk_tier_bands(raw: Dict) -> RiskTierBands:
    return RiskTierBands(**{k: v for k, v in raw.items()})


def _parse_loss_tier_bands(raw: Dict) -> LossTierBands:
    return LossTierBands(**{k: v for k, v in raw.items()})


def _parse_exposure_bands(raw: Dict) -> ExposureBands:
    bands = ExposureBands()
    if "size_weight" in raw:
        bands.size_weight = raw["size_weight"]
    if "complexity_weight" in raw:
        bands.complexity_weight = raw["complexity_weight"]
    if "size_thresholds" in raw:
        bands.size_thresholds = raw["size_thresholds"]
    if "complexity_modifiers" in raw:
        bands.complexity_modifiers = raw["complexity_modifiers"]
    return bands


def _parse_limit_config(raw: Dict) -> LimitConfiguration:
    return LimitConfiguration(
        type=LimitConfigType(raw.get("type", "DECOUPLED")),
        valid_limits=raw.get("valid_limits", []),
        valid_deductibles=raw.get("valid_deductibles", []),
        packages=raw.get("packages"),
    )


def _parse_pricing(raw: Dict) -> PricingSpec:
    pricing = PricingSpec(
        base_limit_reference=raw.get("base_limit_reference", 10_000_000),
        base_deductible_reference=raw.get("base_deductible_reference", 50_000),

    )
    for pt_raw in raw.get("by_product_type", []):
        from .expansion_types import ILFCurve
        ilf_raw = pt_raw.get("ilf_curve", {})
        ilf = ILFCurve(
            base_limit=ilf_raw.get("base_limit", 10_000_000),
            factors=ilf_raw.get("factors", []),
        )
        pp = ProductPricing(
            product_type=pt_raw["product_type"],
            ilf_curve=ilf,
            deductible_factors=pt_raw.get("deductible_factors", []),
            curve_type=pt_raw.get("curve_type", "standard"),
        )
        pricing.by_product_type.append(pp)
    return pricing


def _parse_configuration(raw: Dict) -> ConfigurationSpec:
    """Parse a configuration from raw YAML dict."""
    conf = ConfigurationSpec(
        id=raw["id"],
        name=raw.get("name", raw["id"].replace("_", " ").title()),
        description=raw.get("description", ""),
        model_specificity=raw.get("model_specificity", 2),
        min_premium=raw.get("min_premium"),
        product_types=raw.get("product_types"),
        applicable_markets=raw.get("applicable_markets"),
        minimum_viable_input=raw.get("minimum_viable_input"),
        inherit_signals_from=raw.get("inherit_signals_from"),
        additional_signals=raw.get("additional_signals", []),
        exclude_signals=raw.get("exclude_signals", []),
        signal_overrides=raw.get("signal_overrides", {}),
        category_groups=raw.get("category_groups", []),
    )

    # Routing constraints
    for rc_raw in raw.get("routing_constraints", []):
        conf.routing_constraints.append(RoutingConstraint(
            field=rc_raw["field"],
            operator=rc_raw["operator"],
            value=rc_raw["value"],
            required_in_input=rc_raw.get("required_in_input", False),
        ))

    # Direct queries
    for dq_raw in raw.get("direct_queries", []):
        dq = DirectQuerySpec(
            id=dq_raw["id"],
            question=dq_raw["question"],
        )
        for cond_raw in dq_raw.get("conditions", []):
            dq.conditions.append(QueryCondition(
                return_value=cond_raw.get("return", True),
                action=cond_raw.get("action", "REFER"),
                override=cond_raw.get("override"),
                applied=cond_raw.get("applied"),
                note=cond_raw.get("note", ""),
            ))
        conf.direct_queries.append(dq)

    # Group weights
    for gw_raw in raw.get("group_weights", []):
        conf.group_weights.append(GroupWeights(
            group_id=gw_raw["group_id"],
            risk_weight=gw_raw.get("risk_weight", 0.0),
            loss_weight=gw_raw.get("loss_weight", 0.0),
            exposure_weight=gw_raw.get("exposure_weight", 0.0),
            score_conditions=gw_raw.get("score_conditions", []),
        ))

    # Tier bands (optional overrides)
    if "risk_tier_bands" in raw:
        conf.risk_tier_bands = _parse_risk_tier_bands(raw["risk_tier_bands"])
    if "loss_tier_bands" in raw:
        conf.loss_tier_bands = _parse_loss_tier_bands(raw["loss_tier_bands"])
    if "exposure_bands" in raw:
        conf.exposure_bands = _parse_exposure_bands(raw["exposure_bands"])
    if "limit_configuration" in raw:
        conf.limit_configuration = _parse_limit_config(raw["limit_configuration"])
    if "pricing" in raw:
        conf.pricing = _parse_pricing(raw["pricing"])
    if "guardrails" in raw:
        from infrastructure.builder.expansion_types import GuardrailsSpec
        gr = raw["guardrails"]
        conf.guardrails = GuardrailsSpec(
            modifier_floor=gr.get("modifier_floor", 0.10),
            modifier_cap=gr.get("modifier_cap", 2.50),
            max_premium_to_limit_ratio=gr.get("max_premium_to_limit_ratio", 0.35),
            max_premium_to_revenue_ratio=gr.get("max_premium_to_revenue_ratio", 0.01),
            max_ilf_factor=gr.get("max_ilf_factor", 10.0),
        )

    return conf


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class CoverageExpansionGenerator:
    """Main orchestrator for coverage expansion generation.

    Usage:
        spec = load_expansion_spec("phase_6_spec.yaml")
        generator = CoverageExpansionGenerator(spec)
        result = generator.generate()
    """

    def __init__(
        self,
        spec: ExpansionSpec,
        existing_config_path: Optional[str] = None,
        output_dir: str = ".",
    ):
        self.spec = spec
        self.output_dir = Path(output_dir)
        self.existing_config = None

        if existing_config_path and Path(existing_config_path).exists():
            with open(existing_config_path) as f:
                self.existing_config = yaml.safe_load(f)

    def generate(self, write: bool = False, dry_run: bool = False) -> ExpansionResult:
        """Run the full expansion generation pipeline."""
        result = ExpansionResult(success=True)

        # 1. Validate the spec
        errors = self._validate_spec()
        if errors:
            result.validation_errors = errors
            result.success = False
            return result

        # 2. Generate config YAML
        yaml_gen = ConfigYAMLGenerator(self.spec, self.existing_config)
        if self.existing_config:
            result.config_yaml = yaml_gen.generate()
        else:
            result.config_yaml = yaml_gen.generate_new_configs_only()

        # 3. Generate signal code
        code_gen = SignalCodeGenerator(self.spec)
        result.generated_files = code_gen.generate_all()

        # 4. Collect stats
        result.stats = {
            "configurations_generated": len(self.spec.configurations),
            "new_signal_groups": len(self.spec.new_signal_groups),
            "new_signals": sum(len(g.signals) for g in self.spec.new_signal_groups),
            "config_yaml_lines": len(result.config_yaml.splitlines()),
            "code_files_generated": len(result.generated_files),
            "total_code_lines": sum(
                len(content.splitlines()) for content in result.generated_files.values()
            ),
        }

        # 5. Generate __init__.py updates for new signal modules
        init_updates = self._generate_init_updates(result.generated_files)
        if init_updates:
            result.generated_files.update(init_updates)
            result.stats["init_files_updated"] = len(init_updates)

        # 6. Write files if requested
        if write and not dry_run:
            self._write_files(result)
            # 7. Post-write verification
            verification = self._verify_generation(result)
            if verification:
                result.stats["verification_warnings"] = verification

        return result

    def _validate_spec(self) -> List[str]:
        """Validate the expansion spec for completeness and consistency."""
        errors = []

        if not self.spec.coverage_line:
            errors.append("coverage_line is required")
        if not self.spec.coverage_key:
            errors.append("coverage_key is required")
        if not self.spec.configurations:
            errors.append("At least one configuration is required")

        # Check group weight consistency
        for config in self.spec.configurations:
            total_risk = sum(gw.risk_weight for gw in config.group_weights)
            total_loss = sum(gw.loss_weight for gw in config.group_weights)
            total_exposure = sum(gw.exposure_weight for gw in config.group_weights)

            if config.group_weights:
                if abs(total_risk - 1.0) > 0.05:
                    errors.append(
                        f"{config.id}: risk weights sum to {total_risk:.2f} (should be ~1.0)"
                    )
                if abs(total_loss - 1.0) > 0.05:
                    errors.append(
                        f"{config.id}: loss weights sum to {total_loss:.2f} (should be ~1.0)"
                    )
                if abs(total_exposure - 1.0) > 0.05:
                    errors.append(
                        f"{config.id}: exposure weights sum to {total_exposure:.2f} (should be ~1.0)"
                    )

        # Check signal group references
        defined_groups = {g.id for g in self.spec.new_signal_groups}
        for config in self.spec.configurations:
            for gw in config.group_weights:
                if gw.group_id not in defined_groups:
                    # Not an error — could reference existing groups from _general config
                    pass

        return errors

    def _generate_init_updates(self, generated_files: Dict[str, str]) -> Dict[str, str]:
        """Generate __init__.py updates to register new signal modules.

        For each directory containing generated signal files, ensures the
        directory's __init__.py imports the new module.
        """
        init_updates: Dict[str, str] = {}

        for rel_path in generated_files:
            if not rel_path.endswith(".py") or "__init__" in rel_path:
                continue

            dir_path = self.output_dir / Path(rel_path).parent
            init_path = dir_path / "__init__.py"
            module_name = Path(rel_path).stem

            # Build the import line
            import_line = f"from . import {module_name}"

            if init_path.exists():
                existing = init_path.read_text()
                if import_line not in existing and module_name not in existing:
                    # Append import to existing __init__.py
                    rel_init = str(Path(rel_path).parent / "__init__.py")
                    updated = existing.rstrip() + f"\n{import_line}\n"
                    init_updates[rel_init] = updated
            else:
                # Create new __init__.py with the import
                rel_init = str(Path(rel_path).parent / "__init__.py")
                init_updates[rel_init] = f'"""{Path(rel_path).parent.name} — auto-generated."""\n{import_line}\n'

        return init_updates

    def _verify_generation(self, result: ExpansionResult) -> List[str]:
        """Post-write verification: file existence, signal registration, and smoke test."""
        warnings = []

        # 1. Check all generated files exist on disk
        for rel_path in result.generated_files:
            full_path = self.output_dir / rel_path
            if not full_path.exists():
                warnings.append(f"Generated file not found on disk: {rel_path}")

        # 2. Verify signal count matches spec
        expected_signals = sum(len(g.signals) for g in self.spec.new_signal_groups)
        if expected_signals > 0:
            actual_signals = 0
            for rel_path, content in result.generated_files.items():
                if "inference" in rel_path and rel_path.endswith(".py"):
                    actual_signals += content.count("def infer_")

            if actual_signals != expected_signals:
                warnings.append(
                    f"Signal count mismatch: spec defines {expected_signals} signals, "
                    f"but {actual_signals} inference functions generated"
                )

        # 3. Verify config YAML is valid and parseable
        if result.config_yaml:
            try:
                parsed = yaml.safe_load(result.config_yaml)
                if parsed is None:
                    warnings.append("Generated config YAML is empty")
                else:
                    config_count = len(parsed) if isinstance(parsed, dict) else 0
                    expected_configs = len(self.spec.configurations)
                    if config_count != expected_configs:
                        warnings.append(
                            f"Config count mismatch: spec defines {expected_configs} configs, "
                            f"but YAML contains {config_count}"
                        )
            except yaml.YAMLError as e:
                warnings.append(f"Generated config YAML is invalid: {e}")

        # 4. Signal registration verification — check each new signal appears
        #    in the config YAML's signal_registry for at least one config
        if result.config_yaml and expected_signals > 0:
            config_yaml_content = result.config_yaml
            for group in self.spec.new_signal_groups:
                for signal in group.signals:
                    if signal.id not in config_yaml_content:
                        warnings.append(
                            f"Signal '{signal.id}' defined in spec but not found "
                            f"in generated config YAML signal_registry"
                        )

        # 5. Smoke test — try to import generated Python modules
        for rel_path, content in result.generated_files.items():
            if not rel_path.endswith(".py") or "__init__" in rel_path:
                continue
            full_path = self.output_dir / rel_path
            if not full_path.exists():
                continue
            try:
                import ast
                ast.parse(content, filename=rel_path)
            except SyntaxError as e:
                warnings.append(
                    f"Syntax error in generated file {rel_path}: "
                    f"line {e.lineno}: {e.msg}"
                )

        # 6. Schema validation — try loading generated YAML through Pydantic
        if result.config_yaml:
            try:
                parsed = yaml.safe_load(result.config_yaml)
                if parsed and isinstance(parsed, dict):
                    from infrastructure.models.config_schema import CoverageConfig
                    coverage_key = self.spec.coverage_key
                    for config_id, config_data in parsed.items():
                        try:
                            CoverageConfig(
                                coverage_id=coverage_key,
                                config_id=config_id,
                                **config_data,
                            )
                        except Exception as e:
                            warnings.append(
                                f"Schema validation failed for {config_id}: {e}"
                            )
            except Exception:
                pass  # YAML parse errors already caught above

        return warnings

    def _write_files(self, result: ExpansionResult):
        """Write generated files to disk with proper incremental merging.

        Config YAML: If existing config exists, merge new configs into it
        (preserving existing configs). If not, create new file.
        Signal code: Write to appropriate directories, creating parents.
        __init__.py: Merge imports into existing files or create new ones.
        """
        coverage_dir = self.spec.coverage_line.replace(" ", "_").lower()
        config_path = self.output_dir / "coverages" / coverage_dir / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if self.existing_config:
            # Incremental merge: load existing, add new configs, write combined
            new_configs = yaml.safe_load(result.config_yaml) or {}
            merged = dict(self.existing_config)  # copy existing
            for config_id, config_data in new_configs.items():
                if config_id in merged:
                    # Config already exists — update it
                    merged[config_id] = config_data
                else:
                    # New config — add it
                    merged[config_id] = config_data
            config_path.write_text(yaml.dump(
                merged, default_flow_style=False, sort_keys=False, allow_unicode=True,
            ))
        else:
            # No existing config — write the generated YAML directly
            config_path.write_text(result.config_yaml)

        # Write code files (including __init__.py updates)
        for rel_path, content in result.generated_files.items():
            full_path = self.output_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

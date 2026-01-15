"""
Exposure Rules Engine (Phase 17)

Evaluates auto-apply rules for exposure-based decisions.
Triggers referrals, flags, and pricing adjustments.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .types import (
    ExposureConfig,
    ExposureResult,
    ComplexityResult,
    ExposureBand,
    ComplexityCategory,
    ProxyTier,
    ExposureRuleResult,
    ExposureDecision,
)


class ExposureRulesEngine:
    """
    Evaluate auto-apply rules for exposure decisions.

    Rules can trigger:
    - Referrals: Send to underwriter for review
    - Flags: Add notes for underwriter attention
    - Modifiers: Apply pricing adjustments

    Rules are configured in YAML and evaluated against
    exposure and complexity results.

    Usage:
        engine = ExposureRulesEngine(config)
        decision = engine.evaluate(exposure_result, complexity_result)
    """

    def __init__(self, config: ExposureConfig):
        """
        Initialize rules engine.

        Args:
            config: Exposure configuration from YAML
        """
        self.config = config
        self._rules = config.auto_apply_rules

    def evaluate(
        self,
        exposure: ExposureResult,
        complexity: ComplexityResult
    ) -> ExposureDecision:
        """
        Evaluate all rules against exposure and complexity results.

        Args:
            exposure: ExposureResult from scorer
            complexity: ComplexityResult from complexity scorer

        Returns:
            ExposureDecision with referral triggers, flags, and modifiers
        """
        rule_results = []
        referral_reasons = []
        flags = []
        notes = []

        # Build context for rule evaluation
        context = self._build_context(exposure, complexity)

        # Evaluate each configured rule
        for rule in self._rules:
            result = self._evaluate_rule(rule, context)
            rule_results.append(result)

            if result.triggered:
                if rule.get("action") == "refer":
                    referral_reasons.append(result.reason)
                elif rule.get("action") == "flag":
                    flags.append(result.reason)
                elif rule.get("action") == "note":
                    notes.append(result.reason)

        # Add built-in rules
        builtin_decision = self._evaluate_builtin_rules(exposure, complexity)

        # Merge results
        referral_reasons.extend(builtin_decision.referral_reasons)
        flags.extend(builtin_decision.flags)
        notes.extend(builtin_decision.notes)

        # Calculate combined modifier
        combined_modifier = exposure.exposure_modifier * complexity.complexity_modifier

        return ExposureDecision(
            should_refer=len(referral_reasons) > 0,
            referral_reasons=referral_reasons,
            flags=flags,
            notes=notes,
            exposure_modifier=exposure.exposure_modifier,
            complexity_modifier=complexity.complexity_modifier,
            combined_modifier=combined_modifier,
            rule_results=rule_results,
        )

    def _build_context(
        self,
        exposure: ExposureResult,
        complexity: ComplexityResult
    ) -> Dict[str, Any]:
        """Build context dictionary for rule evaluation."""
        return {
            # Exposure fields
            "exposure_score": exposure.score,
            "exposure_band": exposure.band.value,
            "exposure_confidence": exposure.confidence,
            "exposure_proxy_tier": exposure.proxy_tier.value,
            "implied_tiv_low": exposure.implied_tiv_low,
            "implied_tiv_high": exposure.implied_tiv_high,
            "exposure_modifier": exposure.exposure_modifier,
            "cohort_prior_applied": exposure.cohort_prior_applied,

            # Complexity fields
            "complexity_score": complexity.score,
            "complexity_category": complexity.category.value,
            "complexity_confidence": complexity.confidence,
            "geographic_score": complexity.geographic_score,
            "structural_score": complexity.structural_score,
            "technical_score": complexity.technical_score,
            "regulatory_score": complexity.regulatory_score,
            "complexity_modifier": complexity.complexity_modifier,

            # Combined
            "combined_modifier": exposure.exposure_modifier * complexity.complexity_modifier,
        }

    def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ExposureRuleResult:
        """
        Evaluate a single rule against context.

        Args:
            rule: Rule configuration dict with condition, action, reason
            context: Context dictionary with exposure/complexity values

        Returns:
            ExposureRuleResult
        """
        rule_id = rule.get("id", "unnamed")
        condition = rule.get("condition", "")
        action = rule.get("action", "flag")
        reason = rule.get("reason", "Rule triggered")

        try:
            # Safe evaluation of condition
            triggered = self._safe_eval_condition(condition, context)
        except Exception as e:
            # Log error but don't crash
            triggered = False
            reason = f"Rule evaluation error: {str(e)}"

        return ExposureRuleResult(
            rule_id=rule_id,
            condition=condition,
            action=action,
            triggered=triggered,
            reason=reason if triggered else "",
            modifier=rule.get("modifier"),
        )

    def _safe_eval_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Safely evaluate a condition string.

        Supports simple comparisons like:
        - "exposure_band == 'very_large'"
        - "exposure_confidence < 0.5"
        - "combined_modifier > 2.0"

        Args:
            condition: Condition expression string
            context: Variable values

        Returns:
            Boolean result of condition evaluation
        """
        if not condition:
            return False

        # Parse simple conditions
        # Supported operators: ==, !=, <, <=, >, >=, and, or

        # Handle 'and' conditions
        if " and " in condition:
            parts = condition.split(" and ")
            return all(self._safe_eval_condition(p.strip(), context) for p in parts)

        # Handle 'or' conditions
        if " or " in condition:
            parts = condition.split(" or ")
            return any(self._safe_eval_condition(p.strip(), context) for p in parts)

        # Handle comparison operators
        operators = ["==", "!=", "<=", ">=", "<", ">"]

        for op in operators:
            if op in condition:
                parts = condition.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    # Get left value from context
                    left_val = context.get(left, left)

                    # Parse right value
                    right_val = self._parse_value(right)

                    # Compare
                    return self._compare(left_val, right_val, op)

        return False

    def _parse_value(self, value_str: str) -> Any:
        """Parse a value string to appropriate type."""
        value_str = value_str.strip()

        # String literal
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        return value_str

    def _compare(self, left: Any, right: Any, op: str) -> bool:
        """Compare two values with operator."""
        try:
            if op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == "<":
                return left < right
            elif op == "<=":
                return left <= right
            elif op == ">":
                return left > right
            elif op == ">=":
                return left >= right
        except (TypeError, ValueError):
            return False

        return False

    def _evaluate_builtin_rules(
        self,
        exposure: ExposureResult,
        complexity: ComplexityResult
    ) -> ExposureDecision:
        """
        Evaluate built-in rules that always apply.

        These are hardcoded rules that apply regardless of config.
        """
        referral_reasons = []
        flags = []
        notes = []

        # Rule: High exposure + low confidence = refer
        if exposure.band in [ExposureBand.LARGE, ExposureBand.VERY_LARGE]:
            if exposure.confidence < 0.5:
                referral_reasons.append(
                    f"High exposure ({exposure.band.value}) with low confidence ({exposure.confidence:.2f}) - manual verification required"
                )

        # Rule: Unknown proxy tier with non-micro exposure = flag
        if exposure.proxy_tier == ProxyTier.UNKNOWN:
            if exposure.band not in [ExposureBand.MICRO]:
                flags.append("Exposure estimation based on insufficient data")

        # Rule: Very large exposure = note
        if exposure.band == ExposureBand.VERY_LARGE:
            notes.append(
                f"Very large exposure estimated (TIV range: ${exposure.implied_tiv_low/1e6:.0f}M - ${exposure.implied_tiv_high/1e6:.0f}M)"
            )

        # Rule: High complexity with high exposure = flag
        if complexity.category in [ComplexityCategory.HIGHLY_COMPLEX, ComplexityCategory.EXTREMELY_COMPLEX]:
            if exposure.band in [ExposureBand.LARGE, ExposureBand.VERY_LARGE]:
                flags.append("High complexity combined with large exposure - aggregation risk")

        # Rule: Cohort prior applied = note
        if exposure.cohort_prior_applied:
            notes.append(
                f"Exposure estimate includes cohort prior (cohort: {exposure.cohort_name or 'unknown'})"
            )

        return ExposureDecision(
            should_refer=len(referral_reasons) > 0,
            referral_reasons=referral_reasons,
            flags=flags,
            notes=notes,
        )

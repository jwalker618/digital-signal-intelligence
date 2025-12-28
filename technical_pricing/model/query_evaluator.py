"""
DSI Model Layer - Query Evaluator (Phase 4)

Executes Step 7 of the workflow:
- Evaluate responses to direct queries (boolean questions)
- Trigger impacts: tier override, referral, note, modifier

Direct queries are OPTIONAL per DSI principles - the model must work
without them. They provide additional risk signals when available.
"""

import logging
from typing import Dict, List, Optional, Any

from .types import (
    CoverageConfig,
    DirectQueryConfig,
    QueryEvaluationResult,
    TriggeredCondition,
    ConditionAction,
)


logger = logging.getLogger("dsi.query_evaluator")


class QueryEvaluator:
    """
    Evaluates direct query responses (Step 7).

    Direct queries can trigger:
    - Tier override: Force to specific tier
    - Referral: Set auto_approve = false
    - Note: Post note for underwriter
    - Modifier: Premium modifier applied after base premium
    """

    def evaluate_queries(
        self,
        responses: Dict[str, bool],
        config: CoverageConfig
    ) -> QueryEvaluationResult:
        """
        Step 7: Evaluate all direct query responses.

        Args:
            responses: Map of query_id -> boolean response
            config: Coverage configuration with query definitions

        Returns:
            QueryEvaluationResult with all triggered impacts
        """
        conditions: List[TriggeredCondition] = []
        tier_overrides: List[int] = []
        referrals: List[str] = []
        notes: List[str] = []
        modifiers: List[Dict[str, Any]] = []

        for query_config in config.direct_queries:
            query_id = query_config.id
            response = responses.get(query_id)

            # Skip if no response provided (queries are optional)
            if response is None:
                logger.debug(f"Query '{query_id}' not answered, skipping")
                continue

            # Evaluate each impact band for this query
            for impact in query_config.impacts:
                # Check if the response triggers this impact
                if response == impact.trigger_value:
                    triggered_condition = self._create_triggered_condition(
                        query_config, impact, response
                    )
                    conditions.append(triggered_condition)

                    # Collect the specific impact
                    if impact.action == "DECLINE":
                        tier_overrides.append(impact.tier_override or 5)
                        notes.append(impact.note or f"Query {query_id} triggered decline")

                    elif impact.action == "REFER":
                        referrals.append(impact.note or f"Query {query_id} requires referral")

                    elif impact.action == "MODIFIER":
                        if impact.modifier is not None:
                            modifiers.append({
                                "source": "direct_query",
                                "source_id": query_id,
                                "name": query_config.question[:50],
                                "factor": impact.modifier,
                            })
                        if impact.note:
                            notes.append(impact.note)

                    elif impact.tier_override is not None:
                        tier_overrides.append(impact.tier_override)
                        if impact.note:
                            notes.append(impact.note)

                    elif impact.note:
                        notes.append(impact.note)

        logger.debug(
            f"Evaluated {len(responses)} query responses: "
            f"{len(tier_overrides)} tier overrides, "
            f"{len(referrals)} referrals, "
            f"{len(modifiers)} modifiers, "
            f"{len(notes)} notes"
        )

        return QueryEvaluationResult(
            conditions_triggered=conditions,
            tier_overrides=tier_overrides,
            referrals=referrals,
            notes=notes,
            modifiers=modifiers,
        )

    def _create_triggered_condition(
        self,
        query_config: DirectQueryConfig,
        impact,  # DirectQueryImpact
        response: bool
    ) -> TriggeredCondition:
        """
        Create a TriggeredCondition from a query impact.

        Args:
            query_config: The query configuration
            impact: The triggered impact
            response: The response that triggered it

        Returns:
            TriggeredCondition record
        """
        # Determine the action type
        if impact.action == "DECLINE":
            action = ConditionAction.TIER_OVERRIDE
            action_value = impact.tier_override or 5
        elif impact.action == "REFER":
            action = ConditionAction.REFERRAL
            action_value = impact.note or "Referral required"
        elif impact.action == "MODIFIER":
            action = ConditionAction.MODIFIER
            action_value = impact.modifier
        elif impact.tier_override is not None:
            action = ConditionAction.TIER_OVERRIDE
            action_value = impact.tier_override
        else:
            action = ConditionAction.NOTE
            action_value = impact.note or ""

        return TriggeredCondition(
            source_type="direct_query",
            source_id=query_config.id,
            source_name=query_config.question,
            score=None,
            response=response,
            action=action,
            action_value=action_value,
            note=impact.note or "",
        )

    def get_unanswered_queries(
        self,
        responses: Dict[str, bool],
        config: CoverageConfig
    ) -> List[DirectQueryConfig]:
        """
        Get list of queries that haven't been answered.

        Useful for showing which optional queries are pending.

        Args:
            responses: Map of query_id -> response
            config: Coverage configuration

        Returns:
            List of unanswered DirectQueryConfig
        """
        answered_ids = set(responses.keys())

        return [
            query for query in config.direct_queries
            if query.id not in answered_ids
        ]

    def get_critical_queries(
        self,
        config: CoverageConfig
    ) -> List[DirectQueryConfig]:
        """
        Get queries that can trigger decline or severe tier override.

        These are the most impactful queries that should be prioritized.

        Args:
            config: Coverage configuration

        Returns:
            List of critical DirectQueryConfig
        """
        critical_queries = []

        for query in config.direct_queries:
            is_critical = False
            for impact in query.impacts:
                if impact.action == "DECLINE":
                    is_critical = True
                elif impact.tier_override is not None and impact.tier_override >= 4:
                    is_critical = True

            if is_critical:
                critical_queries.append(query)

        return critical_queries

    def summarize_query_impacts(
        self,
        result: QueryEvaluationResult
    ) -> Dict[str, Any]:
        """
        Create a summary of query evaluation results.

        Args:
            result: QueryEvaluationResult

        Returns:
            Summary dictionary for reporting
        """
        return {
            "conditions_count": len(result.conditions_triggered),
            "has_tier_override": len(result.tier_overrides) > 0,
            "max_tier_override": max(result.tier_overrides) if result.tier_overrides else None,
            "requires_referral": len(result.referrals) > 0,
            "referral_reasons": result.referrals,
            "has_modifiers": len(result.modifiers) > 0,
            "modifier_count": len(result.modifiers),
            "total_modifier_factor": self._calculate_total_modifier(result.modifiers),
            "notes": result.notes,
        }

    def _calculate_total_modifier(
        self,
        modifiers: List[Dict[str, Any]]
    ) -> float:
        """Calculate combined modifier factor."""
        total = 1.0
        for mod in modifiers:
            total *= mod.get("factor", 1.0)
        return total


# Singleton instance for convenience
_default_evaluator: Optional[QueryEvaluator] = None


def get_query_evaluator() -> QueryEvaluator:
    """Get the default QueryEvaluator instance."""
    global _default_evaluator
    if _default_evaluator is None:
        _default_evaluator = QueryEvaluator()
    return _default_evaluator

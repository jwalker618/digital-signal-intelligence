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

from infrastructure.models.config_schema import (
    CoverageConfig,
    DirectQuery,
    QueryCondition,
    ScoreConditionAction,
)

from .types import (
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
            config: Coverage configuration (Pydantic compiled)

        Returns:
            QueryEvaluationResult with all triggered impacts
        """
        conditions: List[TriggeredCondition] = []
        tier_overrides: List[int] = []
        referrals: List[str] = []
        notes: List[str] = []
        modifiers: List[Dict[str, Any]] = []

        for query in config.direct_queries:
            query_id = query.id
            response = responses.get(query_id)

            # Skip if no response provided (queries are optional)
            if response is None:
                logger.debug(f"Query '{query_id}' not answered, skipping")
                continue

            # Evaluate each condition for this query
            for qc in query.query_condition:
                # Check if the response triggers this condition
                if response == qc.return_value:
                    triggered_condition = self._create_triggered_condition(
                        query, qc, response
                    )
                    conditions.append(triggered_condition)

                    # Collect the specific impact based on action type
                    if qc.action == ScoreConditionAction.REFER:
                        if qc.override is not None:
                            tier_overrides.append(qc.override)
                        referrals.append(
                            qc.note or f"Query {query_id} requires referral"
                        )

                    elif qc.action == ScoreConditionAction.MODIFIER:
                        if qc.applied is not None:
                            modifiers.append({
                                "source": "direct_query",
                                "source_id": query_id,
                                "name": query.question[:50],
                                "factor": qc.applied,
                            })
                        if qc.note:
                            notes.append(qc.note)

                    elif qc.action == ScoreConditionAction.FLAG:
                        notes.append(
                            qc.note or f"Query {query_id} flagged"
                        )

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
        query: DirectQuery,
        qc: QueryCondition,
        response: bool,
    ) -> TriggeredCondition:
        """
        Create a TriggeredCondition from a query condition.

        Args:
            query: The DirectQuery definition
            qc: The triggered QueryCondition
            response: The response that triggered it

        Returns:
            TriggeredCondition record
        """
        # Map ScoreConditionAction to internal ConditionAction
        action_map = {
            ScoreConditionAction.REFER: ConditionAction.REFER,
            ScoreConditionAction.MODIFIER: ConditionAction.MODIFIER,
            ScoreConditionAction.FLAG: ConditionAction.FLAG,
        }
        action = action_map.get(qc.action, ConditionAction.NOTE)

        if qc.action == ScoreConditionAction.REFER:
            action_value = qc.override or qc.note or "Referral required"
        elif qc.action == ScoreConditionAction.MODIFIER:
            action_value = qc.applied
        elif qc.action == ScoreConditionAction.FLAG:
            action_value = qc.note or ""
        else:
            action_value = qc.note or ""

        return TriggeredCondition(
            source_type="direct_query",
            source_id=query.id,
            source_name=query.question,
            score=None,
            response=response,
            action=action,
            action_value=action_value,
            note=qc.note or "",
        )

    def get_unanswered_queries(
        self,
        responses: Dict[str, bool],
        config: CoverageConfig
    ) -> List[DirectQuery]:
        """
        Get list of queries that haven't been answered.

        Useful for showing which optional queries are pending.

        Args:
            responses: Map of query_id -> response
            config: Coverage configuration (Pydantic compiled)

        Returns:
            List of unanswered DirectQuery
        """
        answered_ids = set(responses.keys())

        return [
            query for query in config.direct_queries
            if query.id not in answered_ids
        ]

    def get_critical_queries(
        self,
        config: CoverageConfig
    ) -> List[DirectQuery]:
        """
        Get queries that can trigger severe tier override (REFER with override >= 4).

        These are the most impactful queries that should be prioritized.

        Args:
            config: Coverage configuration (Pydantic compiled)

        Returns:
            List of critical DirectQuery
        """
        critical_queries = []

        for query in config.direct_queries:
            is_critical = False
            for qc in query.query_condition:
                if qc.action == ScoreConditionAction.REFER:
                    if qc.override is not None and qc.override >= 4:
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

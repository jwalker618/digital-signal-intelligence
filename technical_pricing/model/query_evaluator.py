"""
DSI Query Evaluator

Evaluates direct query responses (Step 7).

Direct queries are boolean questions that can trigger:
- (a) Tier override
- (b) Referral
- (c) Note
- (d) Modifier (ONLY direct queries can define modifiers)

This is the key difference from signal conditions (Step 6),
which cannot define modifiers.
"""

from .types import (
    CoverageConfig,
    DirectQueryConfig,
    DirectQueryImpact,
    QueryEvaluationResult,
    ConditionAction,
)


class QueryEvaluator:
    """
    Evaluates direct query responses.
    
    Direct queries are optional boolean questions that allow
    additional underwriting control beyond signal-based scoring.
    """
    
    def evaluate_queries(
        self,
        responses: dict[str, bool],
        config: CoverageConfig
    ) -> QueryEvaluationResult:
        """
        Evaluate all direct query responses (Step 7).
        
        Args:
            responses: Dict mapping query_id to boolean response
            config: Coverage configuration
        
        Returns:
            QueryEvaluationResult with tier overrides, referrals, notes, and modifiers
        """
        result = QueryEvaluationResult()
        
        for query in config.direct_queries:
            # Get response for this query
            response = responses.get(query.id)
            
            # Track evaluation for audit
            query_eval = {
                'id': query.id,
                'question': query.question,
                'response': response,
                'impacts_triggered': []
            }
            
            # Skip if no response provided
            if response is None:
                query_eval['skipped'] = True
                result.queries_evaluated.append(query_eval)
                continue
            
            # Evaluate each impact
            for impact in query.impacts:
                if self._should_trigger(impact, response):
                    triggered = {
                        'impact_type': impact.impact_type.value,
                        'value': impact.value,
                        'trigger_on': impact.trigger_on
                    }
                    query_eval['impacts_triggered'].append(triggered)
                    
                    # Apply the impact
                    self._apply_impact(
                        impact=impact,
                        query=query,
                        result=result
                    )
            
            result.queries_evaluated.append(query_eval)
        
        return result
    
    def _should_trigger(self, impact: DirectQueryImpact, response: bool) -> bool:
        """
        Determine if an impact should trigger based on response.
        
        trigger_on=True means impact fires when response is True
        trigger_on=False means impact fires when response is False
        """
        return response == impact.trigger_on
    
    def _apply_impact(
        self,
        impact: DirectQueryImpact,
        query: DirectQueryConfig,
        result: QueryEvaluationResult
    ) -> None:
        """Apply a triggered impact to the result"""
        
        if impact.impact_type == ConditionAction.TIER_OVERRIDE:
            result.tier_overrides.append(int(impact.value))
        
        elif impact.impact_type == ConditionAction.REFERRAL:
            reason = impact.value or f"Query '{query.id}' triggered referral"
            result.referrals.append(str(reason))
        
        elif impact.impact_type == ConditionAction.NOTE:
            note = impact.value or f"Note from query '{query.id}'"
            result.notes.append(str(note))
        
        elif impact.impact_type == ConditionAction.MODIFIER:
            # Direct queries CAN define modifiers
            modifier = {
                'name': f"query_{query.id}",
                'factor': float(impact.value),
                'source': 'direct_query',
                'query_id': query.id
            }
            result.modifiers.append(modifier)
    
    def validate_responses(
        self,
        responses: dict[str, bool],
        config: CoverageConfig
    ) -> tuple[bool, list[str]]:
        """
        Validate query responses against configuration.
        
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check for unknown query IDs
        valid_ids = {q.id for q in config.direct_queries}
        for query_id in responses:
            if query_id not in valid_ids:
                errors.append(f"Unknown query ID: {query_id}")
        
        # Check response types
        for query_id, response in responses.items():
            if not isinstance(response, bool):
                errors.append(f"Query '{query_id}' response must be boolean, got {type(response).__name__}")
        
        return (len(errors) == 0, errors)
    
    def get_required_queries(self, config: CoverageConfig) -> list[dict]:
        """
        Get list of queries that should be answered.
        
        Returns list of {id, question} dicts.
        """
        return [
            {'id': q.id, 'question': q.question}
            for q in config.direct_queries
        ]
    
    def summarize_impacts(self, result: QueryEvaluationResult) -> dict:
        """
        Summarize the impacts from query evaluation for reporting.
        """
        return {
            'total_queries': len(result.queries_evaluated),
            'queries_with_impacts': sum(
                1 for q in result.queries_evaluated
                if q.get('impacts_triggered')
            ),
            'tier_overrides': len(result.tier_overrides),
            'referrals': len(result.referrals),
            'notes': len(result.notes),
            'modifiers': len(result.modifiers),
            'modifier_total': self._calculate_modifier_total(result.modifiers)
        }
    
    def _calculate_modifier_total(self, modifiers: list[dict]) -> float:
        """Calculate combined modifier factor"""
        if not modifiers:
            return 1.0
        
        # Modifiers are multiplicative
        total = 1.0
        for mod in modifiers:
            total *= mod.get('factor', 1.0)
        return total

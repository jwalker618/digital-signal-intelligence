"""
DSI Multiplexer Integration (Phase V4)

Bridges the Multiplexer with the existing MultiCoverageOrchestrator.
Provides a unified entry point for multi-configuration racing within
multi-coverage orchestration.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from .broker import DSIMultiplexer
from .arbiter import ConfigArbiter
from .types import (
    MultiplexerConfig,
    MultiplexerResult,
    CandidateResult,
)


logger = logging.getLogger("dsi.multiplexer.integration")


class MultiplexedWorkflow:
    """
    Workflow wrapper that uses the multiplexer for configuration selection.

    This class can be passed to MultiCoverageOrchestrator as the workflow_factory
    to enable intra-coverage configuration racing.
    """

    def __init__(
        self,
        coverage: str,
        locale: str,
        multiplexer: Optional[DSIMultiplexer] = None,
        arbiter: Optional[ConfigArbiter] = None,
        base_workflow_factory: Optional[Callable] = None,
        shared_cache: Optional[Any] = None,
    ):
        """
        Initialize MultiplexedWorkflow.

        Args:
            coverage: Coverage identifier (e.g., "cyber")
            locale: Locale identifier (e.g., "us")
            multiplexer: DSIMultiplexer instance (created if not provided)
            arbiter: ConfigArbiter instance (created if not provided)
            base_workflow_factory: Factory for creating base workflows
            shared_cache: Shared signal cache for optimization
        """
        self.coverage = coverage
        self.locale = locale
        self.multiplexer = multiplexer or DSIMultiplexer()
        self.arbiter = arbiter or ConfigArbiter()
        self.base_workflow_factory = base_workflow_factory
        self.shared_cache = shared_cache

        # Results storage
        self.multiplexer_result: Optional[MultiplexerResult] = None
        self.selected_config: Optional[str] = None

    def run(
        self,
        entity_name: str,
        domain: Optional[str] = None,
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Run multiplexed workflow.

        Args:
            entity_name: Entity identifier
            domain: Optional domain hint
            submission_data: Submission input data

        Returns:
            Workflow result from selected configuration
        """
        # Build user input
        user_input = submission_data or {}
        user_input["client_name"] = entity_name
        if domain:
            user_input["domain"] = domain
        user_input["market"] = self.locale

        # Run multiplexer (synchronous wrapper for async)
        loop = asyncio.new_event_loop()
        try:
            self.multiplexer_result = loop.run_until_complete(
                self.multiplexer.execute(
                    coverage_id=self.coverage,
                    user_input=user_input,
                    entity_id=entity_name,
                )
            )
        finally:
            loop.close()

        # Arbitrate
        self.multiplexer_result = self.arbiter.arbitrate(self.multiplexer_result)

        # Get selected result
        if self.multiplexer_result.selected_result:
            selected = self.multiplexer_result.selected_result
            self.selected_config = selected.config_id

            # If we have the full result from evaluation, return it
            if selected.full_result:
                return selected.full_result

            # Otherwise build a result from the candidate data
            return self._build_result_from_candidate(selected)

        # No selection - return a placeholder result
        logger.warning(f"No configuration selected for {self.coverage}")
        return self._build_empty_result(entity_name)

    def _build_result_from_candidate(self, candidate: CandidateResult) -> Dict[str, Any]:
        """Build a workflow-compatible result from candidate data."""
        return {
            "entity_id": candidate.coverage_id,
            "coverage": candidate.coverage_id,
            "config_id": candidate.config_id,
            "composite_score": candidate.composite_score,
            "tier": candidate.tier,
            "tier_label": candidate.tier_label,
            "decision": {"action": candidate.decision},
            "referral_reasons": candidate.referral_reasons,
            "pricing": {"final_premium": candidate.recommended_premium},
            "signal_completeness": candidate.signal_completeness,
            "signals_returned": candidate.signals_returned,
            "signals_defined": candidate.signals_defined,
            "multiplexer": {
                "candidates_evaluated": (
                    self.multiplexer_result.candidates_evaluated
                    if self.multiplexer_result else 0
                ),
                "selected_config": candidate.config_id,
                "selection_reason": (
                    self.multiplexer_result.selection_reason
                    if self.multiplexer_result else ""
                ),
            },
        }

    def _build_empty_result(self, entity_name: str) -> Dict[str, Any]:
        """Build an empty result for no-selection case."""
        return {
            "entity_id": entity_name,
            "coverage": self.coverage,
            "config_id": None,
            "composite_score": 0,
            "tier": 3,
            "tier_label": "STANDARD",
            "decision": {"action": "REFER"},
            "referral_reasons": ["No configuration selected by multiplexer"],
            "pricing": {"final_premium": 0},
            "signal_completeness": 0,
            "multiplexer": {
                "candidates_evaluated": (
                    self.multiplexer_result.candidates_evaluated
                    if self.multiplexer_result else 0
                ),
                "selected_config": None,
                "selection_reason": "No valid candidates",
            },
        }


def create_multiplexed_workflow_factory(
    multiplexer: Optional[DSIMultiplexer] = None,
    arbiter: Optional[ConfigArbiter] = None,
    config: Optional[MultiplexerConfig] = None,
) -> Callable:
    """
    Create a workflow factory that uses multiplexer for configuration selection.

    This factory can be passed to MultiCoverageOrchestrator:

        orchestrator = MultiCoverageOrchestrator(
            workflow_factory=create_multiplexed_workflow_factory()
        )

    Args:
        multiplexer: Optional pre-configured multiplexer
        arbiter: Optional pre-configured arbiter
        config: Optional multiplexer configuration

    Returns:
        Factory function compatible with MultiCoverageOrchestrator
    """
    # Create shared instances if not provided
    _config = config or MultiplexerConfig()
    _multiplexer = multiplexer or DSIMultiplexer(config=_config)
    _arbiter = arbiter or ConfigArbiter(config=_config)

    def factory(
        coverage: str,
        locale: str,
        shared_cache: Optional[Any] = None,
        **kwargs,
    ) -> MultiplexedWorkflow:
        """Create a MultiplexedWorkflow for the given coverage/locale."""
        return MultiplexedWorkflow(
            coverage=coverage,
            locale=locale,
            multiplexer=_multiplexer,
            arbiter=_arbiter,
            shared_cache=shared_cache,
        )

    return factory


# Convenience function for standalone usage
async def run_multiplexed_assessment(
    coverage_id: str,
    entity_name: str,
    submission_data: Dict[str, Any],
    config: Optional[MultiplexerConfig] = None,
) -> MultiplexerResult:
    """
    Run a multiplexed assessment for a single coverage.

    This is a convenience function for cases where you want to use the
    multiplexer directly without the full orchestrator.

    Args:
        coverage_id: Coverage identifier (e.g., "cyber")
        entity_name: Entity name
        submission_data: Submission input data
        config: Optional multiplexer configuration

    Returns:
        MultiplexerResult with selected configuration
    """
    _config = config or MultiplexerConfig()
    multiplexer = DSIMultiplexer(config=_config)
    arbiter = ConfigArbiter(config=_config)

    # Build user input
    user_input = submission_data.copy()
    user_input["client_name"] = entity_name

    # Execute
    result = await multiplexer.execute(
        coverage_id=coverage_id,
        user_input=user_input,
        entity_id=entity_name,
    )

    # Arbitrate
    result = arbiter.arbitrate(result)

    return result

"""
DSI Configuration Arbiter (Phase V4)

Selects the optimal configuration from multiplexer results.
Selection hierarchy: validity → confidence → specificity → commercial value.
"""

import logging
from typing import List, Optional

from .types import (
    CandidateResult,
    MultiplexerConfig,
    MultiplexerResult,
)


logger = logging.getLogger("dsi.multiplexer.arbiter")


class ConfigArbiter:
    """
    Selects the best outcome from multiple configuration evaluations.

    Selection Hierarchy:
    1. Validity: Non-DECLINE results preferred
    2. Confidence: High signal completeness (>70%) preferred
    3. Specificity: Higher model_specificity wins (niche > general)
    4. Commercial: Configurable (higher or lower premium)
    """

    def __init__(self, config: Optional[MultiplexerConfig] = None):
        """
        Initialize ConfigArbiter.

        Args:
            config: Multiplexer configuration with arbiter preferences
        """
        self.config = config or MultiplexerConfig()

    def select_best_outcome(
        self,
        results: List[CandidateResult],
    ) -> Optional[CandidateResult]:
        """
        Select the best outcome from candidate results.

        Args:
            results: List of CandidateResult from multiplexer

        Returns:
            Best CandidateResult, or None if no results
        """
        if not results:
            logger.warning("No results to arbitrate")
            return None

        # 1. Filter DECLINE results (unless all declined)
        valid_results = [r for r in results if r.is_valid]

        if not valid_results:
            # All declined - return the most specific decline
            # (provides most detailed reasoning)
            logger.info("All candidates declined, selecting most specific decline")
            return self._select_best_decline(results)

        # 2. Filter low confidence results (unless all low confidence)
        confident_results = [r for r in valid_results if r.is_confident]

        # Use confident results if available, otherwise fall back to all valid
        candidates = confident_results if confident_results else valid_results

        if confident_results:
            logger.info(
                f"Arbitrating {len(confident_results)} confident results "
                f"(filtered {len(valid_results) - len(confident_results)} low-confidence)"
            )
        else:
            logger.warning(
                f"No high-confidence results, arbitrating {len(valid_results)} "
                f"low-confidence valid results"
            )

        # 3. Sort by selection criteria
        sorted_candidates = self._sort_candidates(candidates)

        # 4. Select winner
        winner = sorted_candidates[0]

        logger.info(
            f"Selected {winner.config_id} "
            f"(specificity={winner.model_specificity}, "
            f"completeness={winner.signal_completeness:.0%}, "
            f"premium=${winner.recommended_premium:,.0f})"
        )

        return winner

    def arbitrate(
        self,
        multiplexer_result: MultiplexerResult,
    ) -> MultiplexerResult:
        """
        Perform arbitration on a MultiplexerResult, updating it with winner.

        Args:
            multiplexer_result: Result from DSIMultiplexer.execute()

        Returns:
            Updated MultiplexerResult with selected winner
        """
        winner = self.select_best_outcome(multiplexer_result.candidate_results)

        if winner:
            multiplexer_result.selected_config_id = winner.config_id
            multiplexer_result.selected_result = winner
            multiplexer_result.selection_reason = self._build_selection_reason(
                winner, multiplexer_result.candidate_results
            )
        else:
            multiplexer_result.selection_reason = "No valid candidates"

        return multiplexer_result

    def _sort_candidates(
        self,
        candidates: List[CandidateResult],
    ) -> List[CandidateResult]:
        """
        Sort candidates by selection criteria.

        Sort order (descending priority):
        1. Signal completeness (higher = better)
        2. Model specificity (higher = more niche = better)
        3. Premium (configurable: higher or lower)
        """
        def sort_key(r: CandidateResult) -> tuple:
            # Primary: Confidence (signal completeness)
            confidence = r.signal_completeness

            # Secondary: Specificity
            specificity = r.model_specificity if self.config.prefer_specificity else 0

            # Tertiary: Commercial value
            if self.config.prefer_higher_premium:
                commercial = r.recommended_premium
            else:
                commercial = -r.recommended_premium  # Invert for lower-is-better

            return (confidence, specificity, commercial)

        return sorted(candidates, key=sort_key, reverse=True)

    def _select_best_decline(
        self,
        results: List[CandidateResult],
    ) -> CandidateResult:
        """
        Select the best decline result (most specific reasoning).
        """
        # Sort by specificity descending
        sorted_results = sorted(
            results,
            key=lambda r: r.model_specificity,
            reverse=True,
        )
        return sorted_results[0]

    def _build_selection_reason(
        self,
        winner: CandidateResult,
        all_results: List[CandidateResult],
    ) -> str:
        """Build human-readable selection reason."""
        reasons = []

        # Count categories
        valid_count = sum(1 for r in all_results if r.is_valid)
        confident_count = sum(1 for r in all_results if r.is_valid and r.is_confident)

        if len(all_results) == 1:
            reasons.append("Only candidate")
        else:
            if valid_count < len(all_results):
                reasons.append(
                    f"{len(all_results) - valid_count} declined"
                )

            if confident_count < valid_count:
                reasons.append(
                    f"{valid_count - confident_count} low-confidence filtered"
                )

            if winner.model_specificity > 1:
                reasons.append(
                    f"Highest specificity ({winner.model_specificity})"
                )

            if winner.signal_completeness >= 0.9:
                reasons.append(
                    f"Excellent data coverage ({winner.signal_completeness:.0%})"
                )

        return "; ".join(reasons) if reasons else "Default selection"


def create_arbiter(config: Optional[MultiplexerConfig] = None) -> ConfigArbiter:
    """Factory function to create ConfigArbiter."""
    return ConfigArbiter(config)

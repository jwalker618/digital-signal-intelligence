"""
DSI Multiplexer Types (Phase V4)

Data structures for multi-configuration racing and optimal selection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConstraintOperator(str, Enum):
    """Operators for routing constraints."""
    LT = "<"
    GT = ">"
    LTE = "<="
    GTE = ">="
    EQ = "=="
    NEQ = "!="


@dataclass
class RoutingConstraint:
    """
    A single routing constraint for candidate filtering.

    Evaluated BEFORE signal execution to exclude non-applicable configs.
    """
    field: str                          # Field name from submission input
    operator: ConstraintOperator        # Comparison operator
    value: Any                          # Threshold value
    required_in_input: bool = False     # If True, missing field fails constraint


@dataclass
class ConfigCandidate:
    """
    A configuration that passed routing constraints.

    Represents one entry in the "race".
    """
    coverage_id: str                    # e.g., "cyber"
    config_id: str                      # e.g., "cyber_general"
    config: Dict[str, Any]              # Full configuration dict
    model_specificity: int              # 1-5 specificity score
    routing_constraints: List[RoutingConstraint]

    # Populated after signal execution
    signal_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Extract signal IDs from config."""
        if not self.signal_ids and self.config:
            registry = self.config.get("signal_registry", [])
            self.signal_ids = [s.get("id") for s in registry if s.get("id")]


@dataclass
class SignalPool:
    """
    Shared pool of executed signals across all candidates.

    Signals are executed once and shared to avoid redundant API calls.
    """
    signals: Dict[str, Any] = field(default_factory=dict)  # signal_id -> result
    execution_time_ms: float = 0.0
    errors: Dict[str, str] = field(default_factory=dict)   # signal_id -> error message

    def get(self, signal_id: str) -> Optional[Any]:
        """Get signal result, returns None if not found or errored."""
        if signal_id in self.errors:
            return None
        return self.signals.get(signal_id)

    def has_result(self, signal_id: str) -> bool:
        """Check if signal has a valid result."""
        return signal_id in self.signals and signal_id not in self.errors


@dataclass
class CandidateResult:
    """
    Result from evaluating a single candidate configuration.
    """
    coverage_id: str
    config_id: str
    model_specificity: int

    # Scoring results
    composite_score: float              # 0-1000
    tier: int                           # 1-5
    tier_label: str                     # e.g., "PREFERRED", "STANDARD"

    # Decision
    decision: str                       # "APPROVE", "REFER", "DECLINE"
    referral_reasons: List[str] = field(default_factory=list)

    # Pricing
    recommended_premium: float = 0.0

    # Signal completeness - critical for arbiter
    signal_completeness: float = 0.0    # 0.0 - 1.0
    signals_returned: int = 0
    signals_defined: int = 0

    # Full result for downstream processing
    full_result: Optional[Any] = None

    @property
    def is_valid(self) -> bool:
        """Check if result is valid (not declined)."""
        return self.decision != "DECLINE"

    @property
    def is_confident(self) -> bool:
        """Check if result has high confidence (>70% signals returned)."""
        return self.signal_completeness >= 0.7


@dataclass
class MultiplexerResult:
    """
    Complete result from multiplexer execution.

    Contains all candidate results and the selected winner.
    """
    # Request info
    entity_id: str
    coverage_id: str

    # Candidates
    candidates_evaluated: int
    candidate_results: List[CandidateResult]

    # Winner selection
    selected_config_id: Optional[str] = None
    selected_result: Optional[CandidateResult] = None
    selection_reason: str = ""

    # Signal pool info
    unique_signals_executed: int = 0
    total_execution_time_ms: float = 0.0

    # Metadata
    multiplexer_version: str = "1.0.0"
    executed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def all_declined(self) -> bool:
        """Check if all candidates declined."""
        return all(not r.is_valid for r in self.candidate_results)

    @property
    def has_winner(self) -> bool:
        """Check if a winner was selected."""
        return self.selected_result is not None


@dataclass
class MultiplexerConfig:
    """
    Configuration for the DSI Multiplexer.
    """
    # Confidence thresholds
    min_signal_completeness: float = 0.7  # Minimum for "confident" result

    # Arbiter preferences
    prefer_specificity: bool = True       # Prefer niche over general
    prefer_higher_premium: bool = True    # Commercial preference

    # Execution limits
    max_candidates: int = 10              # Maximum configs to race
    signal_timeout_ms: float = 30000      # Per-signal timeout

    # Feature flags
    store_all_results: bool = True        # Store non-winners for analysis
    enable_parallel_execution: bool = True

"""
DSI Multiplexer Types (Phase V4 + Cycle 3 Error Handling)

Data structures for multi-configuration racing and optimal selection.
Includes robust ExtractionError logging as per Cycle 3 requirements.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# Cycle 3 Extraction Error Handling
# =============================================================================

class ExtractionErrorType(str, Enum):
    """Types of extraction failures for granular error logging."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PARSING_ERROR = "parsing_error"
    NETWORK_ERROR = "network_error"
    AUTH_ERROR = "auth_error"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN = "unknown"


@dataclass
class ExtractionError(Exception):
    """
    Structured exception for signal extraction failures.

    Cycle 3 Requirement: Log exact failure reasons (Timeout, Rate Limit,
    Parsing Error) to audit_logs before passing None to scoring engine.
    """
    signal_id: str
    error_type: ExtractionErrorType
    message: str
    source: str = ""  # API/service that failed
    entity_id: str = ""
    retry_after: Optional[int] = None  # Seconds until retry (for rate limits)
    raw_error: Optional[str] = None  # Original exception string

    def __str__(self) -> str:
        return f"ExtractionError({self.error_type.value}): {self.message}"

    def to_audit_dict(self) -> Dict[str, Any]:
        """Convert to dict for audit_logs table insertion."""
        return {
            "signal_id": self.signal_id,
            "error_type": self.error_type.value,
            "message": self.message,
            "source": self.source,
            "entity_id": self.entity_id,
            "retry_after": self.retry_after,
            "raw_error": self.raw_error,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @classmethod
    def from_exception(
        cls,
        signal_id: str,
        exc: Exception,
        entity_id: str = "",
        source: str = "",
    ) -> "ExtractionError":
        """
        Create ExtractionError from a raw exception.

        Classifies common exception types into appropriate error types.
        """
        exc_name = type(exc).__name__.lower()
        exc_str = str(exc).lower()

        # Classify the error type
        if "timeout" in exc_name or "timeout" in exc_str:
            error_type = ExtractionErrorType.TIMEOUT
        elif "ratelimit" in exc_name or "rate limit" in exc_str or "429" in exc_str:
            error_type = ExtractionErrorType.RATE_LIMIT
        elif "parse" in exc_name or "json" in exc_name or "decode" in exc_str:
            error_type = ExtractionErrorType.PARSING_ERROR
        elif "connection" in exc_name or "network" in exc_str:
            error_type = ExtractionErrorType.NETWORK_ERROR
        elif "auth" in exc_name or "401" in exc_str or "403" in exc_str:
            error_type = ExtractionErrorType.AUTH_ERROR
        elif "notfound" in exc_name or "404" in exc_str:
            error_type = ExtractionErrorType.NOT_FOUND
        elif "validation" in exc_name:
            error_type = ExtractionErrorType.VALIDATION_ERROR
        else:
            error_type = ExtractionErrorType.UNKNOWN

        return cls(
            signal_id=signal_id,
            error_type=error_type,
            message=str(exc),
            source=source,
            entity_id=entity_id,
            raw_error=f"{type(exc).__name__}: {exc}",
        )


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

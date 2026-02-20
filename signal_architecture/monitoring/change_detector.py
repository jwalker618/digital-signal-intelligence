"""
Change Detection for Signal Monitoring

Detects significant changes in signal values and triggers alerts
when thresholds are breached.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class ChangeType(Enum):
    """Types of signal changes detected."""
    NONE = "none"
    VALUE_CHANGE = "value_change"
    THRESHOLD_BREACH = "threshold_breach"
    MISSING_DATA = "missing_data"
    NEW_DATA = "new_data"
    DEGRADATION = "degradation"
    IMPROVEMENT = "improvement"


@dataclass
class ChangeThresholds:
    """Thresholds for detecting significant changes."""
    # Percentage change that triggers an alert
    percentage_threshold: float = 0.1  # 10%

    # Absolute change threshold (for small values)
    absolute_threshold: float = 0.01

    # Score change that triggers re-evaluation
    score_delta_threshold: float = 50.0  # 50 points on 1000 scale

    # Tier change always triggers alert
    tier_change_triggers_alert: bool = True


@dataclass
class ChangeEvent:
    """Represents a detected change in a signal."""
    entity_id: str
    signal_id: str
    change_type: ChangeType
    previous_value: Any
    current_value: Any
    change_magnitude: float
    detected_at: datetime
    requires_action: bool = False
    suggested_action: Optional[str] = None


class ChangeDetector:
    """
    Detects significant changes in signal values.

    Supports the continuous monitoring requirement by identifying
    changes that may impact risk scores, triggering re-evaluation
    or alerting underwriters.
    """

    def __init__(self, thresholds: Optional[ChangeThresholds] = None):
        self.thresholds = thresholds or ChangeThresholds()
        self._change_history: Dict[str, List[ChangeEvent]] = {}

    def detect(
        self,
        entity_id: str,
        signal_id: str,
        previous_value: Any,
        current_value: Any,
    ) -> ChangeEvent:
        """Detect and classify a change between values."""
        change_type = ChangeType.NONE
        magnitude = 0.0
        requires_action = False
        suggested_action = None

        # Handle missing data cases
        if previous_value is None and current_value is not None:
            change_type = ChangeType.NEW_DATA
            magnitude = 1.0
            suggested_action = "Review new signal data"

        elif previous_value is not None and current_value is None:
            change_type = ChangeType.MISSING_DATA
            magnitude = 1.0
            requires_action = True
            suggested_action = "Investigate data source availability"

        elif previous_value != current_value:
            # Calculate magnitude for numeric values
            if isinstance(previous_value, (int, float)) and isinstance(current_value, (int, float)):
                if previous_value != 0:
                    magnitude = abs(current_value - previous_value) / abs(previous_value)
                else:
                    magnitude = 1.0 if current_value != 0 else 0.0

                # Determine if improvement or degradation (higher = worse for risk)
                if current_value > previous_value:
                    change_type = ChangeType.DEGRADATION
                else:
                    change_type = ChangeType.IMPROVEMENT
            else:
                change_type = ChangeType.VALUE_CHANGE
                magnitude = 1.0  # Non-numeric changes are always significant

            # Check thresholds
            if magnitude >= self.thresholds.percentage_threshold:
                change_type = ChangeType.THRESHOLD_BREACH
                requires_action = True
                suggested_action = "Re-evaluate risk score"

        event = ChangeEvent(
            entity_id=entity_id,
            signal_id=signal_id,
            change_type=change_type,
            previous_value=previous_value,
            current_value=current_value,
            change_magnitude=magnitude,
            detected_at=datetime.utcnow(),
            requires_action=requires_action,
            suggested_action=suggested_action,
        )

        # Store in history
        key = f"{entity_id}:{signal_id}"
        if key not in self._change_history:
            self._change_history[key] = []
        self._change_history[key].append(event)

        return event

    def get_history(
        self,
        entity_id: str,
        signal_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ChangeEvent]:
        """Get change history for an entity/signal."""
        if signal_id:
            key = f"{entity_id}:{signal_id}"
            return self._change_history.get(key, [])[-limit:]

        # Return all signals for entity
        results = []
        for key, events in self._change_history.items():
            if key.startswith(f"{entity_id}:"):
                results.extend(events)
        return sorted(results, key=lambda e: e.detected_at, reverse=True)[:limit]

    def get_actionable_changes(
        self,
        entity_id: Optional[str] = None,
    ) -> List[ChangeEvent]:
        """Get all changes that require action."""
        results = []
        for key, events in self._change_history.items():
            if entity_id and not key.startswith(f"{entity_id}:"):
                continue
            results.extend(e for e in events if e.requires_action)
        return sorted(results, key=lambda e: e.detected_at, reverse=True)

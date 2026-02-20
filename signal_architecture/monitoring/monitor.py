"""
Signal Monitoring Core

Provides continuous monitoring of signal values for entities under coverage,
enabling derivative calculations and performance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio


class MonitoringPriority(Enum):
    """Priority levels for signal refresh scheduling."""
    CRITICAL = 1     # Real-time monitoring (external APIs with high variance)
    HIGH = 2         # Hourly refresh (regulatory data)
    STANDARD = 3     # Daily refresh (corporate records)
    LOW = 4          # Weekly refresh (stable signals)


@dataclass
class MonitoringConfig:
    """Configuration for signal monitoring."""
    entity_id: str
    coverage: str
    signal_ids: List[str]
    refresh_interval_seconds: int = 86400  # Default: daily
    priority: MonitoringPriority = MonitoringPriority.STANDARD
    enabled: bool = True
    max_retries: int = 3
    alert_on_change: bool = True
    change_threshold: float = 0.1  # 10% change triggers alert
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringResult:
    """Result from a monitoring cycle."""
    entity_id: str
    signal_id: str
    previous_value: Any
    current_value: Any
    extracted_at: datetime
    changed: bool
    change_magnitude: Optional[float] = None
    error: Optional[str] = None


class SignalMonitor:
    """
    Continuous signal monitoring for entities.

    Manages scheduled re-extraction of signals to track changes over time,
    supporting derivative calculations (velocity, drift, entropy) and
    performance monitoring as specified in the Vision Paper.
    """

    def __init__(
        self,
        extractor_factory: Optional[Callable] = None,
        time_series_store: Optional["SignalTimeSeries"] = None,
    ):
        self._configs: Dict[str, MonitoringConfig] = {}
        self._extractor_factory = extractor_factory
        self._time_series = time_series_store
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    def register(self, config: MonitoringConfig) -> None:
        """Register an entity for continuous monitoring."""
        self._configs[config.entity_id] = config

    def unregister(self, entity_id: str) -> None:
        """Stop monitoring an entity."""
        if entity_id in self._configs:
            del self._configs[entity_id]
        if entity_id in self._tasks:
            self._tasks[entity_id].cancel()
            del self._tasks[entity_id]

    async def start(self) -> None:
        """Start the monitoring loop."""
        self._running = True
        for entity_id, config in self._configs.items():
            if config.enabled:
                self._tasks[entity_id] = asyncio.create_task(
                    self._monitor_entity(config)
                )

    async def stop(self) -> None:
        """Stop all monitoring tasks."""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()

    async def _monitor_entity(self, config: MonitoringConfig) -> None:
        """Monitor a single entity continuously."""
        while self._running and config.enabled:
            try:
                results = await self._extract_and_compare(config)
                for result in results:
                    if result.changed and self._time_series:
                        await self._time_series.record(
                            entity_id=config.entity_id,
                            signal_id=result.signal_id,
                            value=result.current_value,
                            timestamp=result.extracted_at,
                        )
            except Exception as e:
                # Log error but continue monitoring
                pass

            await asyncio.sleep(config.refresh_interval_seconds)

    async def _extract_and_compare(
        self, config: MonitoringConfig
    ) -> List[MonitoringResult]:
        """Extract signals and compare with previous values."""
        results = []

        for signal_id in config.signal_ids:
            # Get previous value from time series
            previous = None
            if self._time_series:
                previous = await self._time_series.get_latest(
                    config.entity_id, signal_id
                )

            # Extract current value
            current = None
            error = None
            try:
                if self._extractor_factory:
                    extractor = self._extractor_factory(signal_id)
                    current = await extractor.extract(config.entity_id)
            except Exception as e:
                error = str(e)

            # Calculate change
            changed = previous != current
            magnitude = None
            if changed and previous is not None and current is not None:
                try:
                    if isinstance(previous, (int, float)) and isinstance(current, (int, float)):
                        magnitude = abs(current - previous) / abs(previous) if previous != 0 else 1.0
                except Exception:
                    pass

            results.append(MonitoringResult(
                entity_id=config.entity_id,
                signal_id=signal_id,
                previous_value=previous,
                current_value=current,
                extracted_at=datetime.utcnow(),
                changed=changed,
                change_magnitude=magnitude,
                error=error,
            ))

        return results

    def get_monitoring_status(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get monitoring status for an entity."""
        if entity_id not in self._configs:
            return None

        config = self._configs[entity_id]
        return {
            "entity_id": entity_id,
            "coverage": config.coverage,
            "signal_count": len(config.signal_ids),
            "priority": config.priority.name,
            "refresh_interval_seconds": config.refresh_interval_seconds,
            "enabled": config.enabled,
            "running": entity_id in self._tasks and not self._tasks[entity_id].done(),
        }

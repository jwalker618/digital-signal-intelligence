"""
Time Series Storage for Signal Monitoring

Provides temporal storage and aggregation of signal values,
supporting derivative calculations (velocity, drift, entropy)
as specified in the Vision Paper.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import math


@dataclass
class TimeSeriesPoint:
    """A single point in a signal time series."""
    timestamp: datetime
    value: Any
    confidence: float = 1.0
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TimeSeriesStats:
    """Statistical summary of a time series window."""
    count: int
    min_value: float
    max_value: float
    mean: float
    std_dev: float
    first_value: float
    last_value: float
    velocity: float  # Rate of change
    drift: float     # Cumulative directional change
    entropy: float   # Measure of unpredictability


class SignalTimeSeries:
    """
    Time series storage for signal values.

    Supports the Vision Paper requirement for historical signal tracking
    to enable derivative calculations (velocity, drift, entropy).
    """

    def __init__(self, max_history_days: int = 365):
        self._data: Dict[str, List[TimeSeriesPoint]] = defaultdict(list)
        self._max_history = timedelta(days=max_history_days)

    def _key(self, entity_id: str, signal_id: str) -> str:
        return f"{entity_id}:{signal_id}"

    async def record(
        self,
        entity_id: str,
        signal_id: str,
        value: Any,
        timestamp: Optional[datetime] = None,
        confidence: float = 1.0,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a new value in the time series."""
        key = self._key(entity_id, signal_id)
        point = TimeSeriesPoint(
            timestamp=timestamp or datetime.utcnow(),
            value=value,
            confidence=confidence,
            source=source,
            metadata=metadata,
        )
        self._data[key].append(point)

        # Prune old data
        cutoff = datetime.utcnow() - self._max_history
        self._data[key] = [p for p in self._data[key] if p.timestamp > cutoff]

    async def get_latest(
        self,
        entity_id: str,
        signal_id: str,
    ) -> Optional[Any]:
        """Get the most recent value."""
        key = self._key(entity_id, signal_id)
        if key not in self._data or not self._data[key]:
            return None
        return self._data[key][-1].value

    async def get_history(
        self,
        entity_id: str,
        signal_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[TimeSeriesPoint]:
        """Get historical values within a time range."""
        key = self._key(entity_id, signal_id)
        points = self._data.get(key, [])

        if start:
            points = [p for p in points if p.timestamp >= start]
        if end:
            points = [p for p in points if p.timestamp <= end]
        if limit:
            points = points[-limit:]

        return points

    async def get_stats(
        self,
        entity_id: str,
        signal_id: str,
        window_days: int = 30,
    ) -> Optional[TimeSeriesStats]:
        """Calculate statistics for a time window."""
        start = datetime.utcnow() - timedelta(days=window_days)
        points = await self.get_history(entity_id, signal_id, start=start)

        if not points:
            return None

        # Extract numeric values
        numeric_values = []
        for p in points:
            if isinstance(p.value, (int, float)):
                numeric_values.append(p.value)

        if not numeric_values:
            return None

        count = len(numeric_values)
        min_val = min(numeric_values)
        max_val = max(numeric_values)
        mean = sum(numeric_values) / count
        variance = sum((v - mean) ** 2 for v in numeric_values) / count if count > 1 else 0
        std_dev = math.sqrt(variance)

        first_val = numeric_values[0]
        last_val = numeric_values[-1]

        # Calculate derivatives
        velocity = (last_val - first_val) / window_days if window_days > 0 else 0

        # Drift: cumulative directional change
        drift = 0.0
        for i in range(1, len(numeric_values)):
            drift += numeric_values[i] - numeric_values[i-1]

        # Entropy: Shannon entropy approximation
        entropy = self._calculate_entropy(numeric_values)

        return TimeSeriesStats(
            count=count,
            min_value=min_val,
            max_value=max_val,
            mean=mean,
            std_dev=std_dev,
            first_value=first_val,
            last_value=last_val,
            velocity=velocity,
            drift=drift,
            entropy=entropy,
        )

    def _calculate_entropy(self, values: List[float], bins: int = 10) -> float:
        """Calculate Shannon entropy of the value distribution."""
        if not values or len(values) < 2:
            return 0.0

        min_val = min(values)
        max_val = max(values)
        if min_val == max_val:
            return 0.0

        # Create histogram
        bin_width = (max_val - min_val) / bins
        histogram = [0] * bins
        for v in values:
            bin_idx = min(int((v - min_val) / bin_width), bins - 1)
            histogram[bin_idx] += 1

        # Calculate entropy
        n = len(values)
        entropy = 0.0
        for count in histogram:
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)

        return entropy


class TimeSeriesAggregator:
    """
    Aggregates time series data across multiple signals.

    Supports portfolio-level monitoring and trend analysis.
    """

    def __init__(self, time_series: SignalTimeSeries):
        self._ts = time_series

    async def aggregate_entity(
        self,
        entity_id: str,
        signal_ids: List[str],
        window_days: int = 30,
    ) -> Dict[str, TimeSeriesStats]:
        """Aggregate stats for multiple signals of an entity."""
        results = {}
        for signal_id in signal_ids:
            stats = await self._ts.get_stats(entity_id, signal_id, window_days)
            if stats:
                results[signal_id] = stats
        return results

    async def calculate_portfolio_drift(
        self,
        entity_ids: List[str],
        signal_id: str,
        window_days: int = 30,
    ) -> Dict[str, float]:
        """Calculate drift across a portfolio of entities."""
        drifts = {}
        for entity_id in entity_ids:
            stats = await self._ts.get_stats(entity_id, signal_id, window_days)
            if stats:
                drifts[entity_id] = stats.drift
        return drifts

    async def identify_outliers(
        self,
        entity_ids: List[str],
        signal_id: str,
        window_days: int = 30,
        std_threshold: float = 2.0,
    ) -> List[Tuple[str, float]]:
        """Identify entities with unusual signal drift."""
        drifts = await self.calculate_portfolio_drift(entity_ids, signal_id, window_days)

        if not drifts:
            return []

        values = list(drifts.values())
        mean_drift = sum(values) / len(values)
        variance = sum((v - mean_drift) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        outliers = []
        for entity_id, drift in drifts.items():
            if std_dev > 0:
                z_score = (drift - mean_drift) / std_dev
                if abs(z_score) > std_threshold:
                    outliers.append((entity_id, z_score))

        return sorted(outliers, key=lambda x: abs(x[1]), reverse=True)

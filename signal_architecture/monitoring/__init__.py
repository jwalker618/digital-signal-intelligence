"""
DSI Continuous Monitoring Infrastructure

This module provides continuous signal monitoring capabilities for tracking
signal changes over time, supporting the Vision Paper requirement for
derivative calculations (velocity, drift, entropy) based on historical data.

Key Components:
- SignalMonitor: Schedules and tracks signal re-extraction
- ChangeDetector: Identifies significant signal value changes
- AlertManager: Triggers notifications on threshold breaches
- TimeSeriesStore: Manages historical signal data for derivatives
"""

from .monitor import SignalMonitor, MonitoringConfig
from .change_detector import ChangeDetector, ChangeThresholds
from .time_series import SignalTimeSeries, TimeSeriesAggregator

__all__ = [
    "SignalMonitor",
    "MonitoringConfig",
    "ChangeDetector",
    "ChangeThresholds",
    "SignalTimeSeries",
    "TimeSeriesAggregator",
]

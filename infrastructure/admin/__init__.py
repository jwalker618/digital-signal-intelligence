"""
B-1: Admin backend services.

Provides:
- SystemHealthAggregator: unified green/amber/red health across API, DB,
  Redis, World Engine, and extractors.
- ExtractorTracker: per-extractor success/error counters.
- PipelineMetrics: assessment throughput, latency percentiles, failure
  rate. On-demand + hourly snapshots for trend analysis.
"""

from infrastructure.admin.health import SystemHealthAggregator, HealthStatus
from infrastructure.admin.extractor_tracker import ExtractorTracker
from infrastructure.admin.pipeline_metrics import PipelineMetrics

__all__ = [
    "SystemHealthAggregator",
    "HealthStatus",
    "ExtractorTracker",
    "PipelineMetrics",
]

"""
Admin backend services (B-1, B-2).

Provides:
- SystemHealthAggregator: unified green/amber/red health.
- ExtractorTracker: per-extractor success/error counters.
- PipelineMetrics: assessment throughput / latency / failure rate.
- ConfigService: versioned coverage config lifecycle.
- ConfigDiffEngine: structured diff between config versions.
"""

from infrastructure.admin.health import SystemHealthAggregator, HealthStatus
from infrastructure.admin.extractor_tracker import ExtractorTracker
from infrastructure.admin.pipeline_metrics import PipelineMetrics
from infrastructure.admin.config_service import ConfigService, ConfigVersionRow
from infrastructure.admin.config_diff import ConfigDiff, ConfigDiffEngine
from infrastructure.admin.user_service import (
    InvitationService,
    InvitationToken,
    RoleService,
    UserService,
)

__all__ = [
    "SystemHealthAggregator",
    "HealthStatus",
    "ExtractorTracker",
    "PipelineMetrics",
    "ConfigService",
    "ConfigVersionRow",
    "ConfigDiff",
    "ConfigDiffEngine",
    "UserService",
    "RoleService",
    "InvitationService",
    "InvitationToken",
]

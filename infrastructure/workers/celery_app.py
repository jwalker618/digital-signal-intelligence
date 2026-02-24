"""
DSI Celery Application Configuration (Version 4 - Phase 2)

Configures the Celery distributed task queue for continuous signal telemetry.
Signals are refreshed in the background based on their volatility:

- Highly Volatile (CVEs, breaches): Every 12 hours
- Medium Volatility (Security headers): Every 24 hours
- Low Volatility (Financial filings): Every 7-30 days
- Static (Industry classification): On-demand only

Usage:
    # Start worker
    celery -A infrastructure.workers.celery_app worker --loglevel=info

    # Start beat scheduler
    celery -A infrastructure.workers.celery_app beat --loglevel=info
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Queue


# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

# Broker URL (Redis by default)
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "dsi_telemetry",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "infrastructure.workers.telemetry",
    ],
)

# =============================================================================
# TASK CONFIGURATION
# =============================================================================

celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_queues=(
        Queue("high_priority", routing_key="high"),
        Queue("default", routing_key="default"),
        Queue("low_priority", routing_key="low"),
    ),
    task_default_queue="default",
    task_default_routing_key="default",

    # Task execution
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    worker_prefetch_multiplier=4,  # Tasks to prefetch per worker

    # Result expiration
    result_expires=86400,  # 24 hours

    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit

    # Retry configuration
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=3,
)


# =============================================================================
# BEAT SCHEDULE (Periodic Tasks)
# =============================================================================

celery_app.conf.beat_schedule = {
    # Refresh highly volatile signals every 12 hours
    "refresh-high-volatility-signals": {
        "task": "infrastructure.workers.telemetry.batch_refresh_by_volatility",
        "schedule": crontab(minute=0, hour="*/12"),  # Every 12 hours
        "args": ("HIGH",),
        "options": {"queue": "high_priority"},
    },

    # Refresh medium volatility signals daily
    "refresh-medium-volatility-signals": {
        "task": "infrastructure.workers.telemetry.batch_refresh_by_volatility",
        "schedule": crontab(minute=30, hour=3),  # 3:30 AM daily
        "args": ("MEDIUM",),
        "options": {"queue": "default"},
    },

    # Refresh low volatility signals weekly
    "refresh-low-volatility-signals": {
        "task": "infrastructure.workers.telemetry.batch_refresh_by_volatility",
        "schedule": crontab(minute=0, hour=4, day_of_week=1),  # Monday 4 AM
        "args": ("LOW",),
        "options": {"queue": "low_priority"},
    },

    # Cleanup stale signals daily
    "cleanup-stale-signals": {
        "task": "infrastructure.workers.telemetry.cleanup_stale_signals",
        "schedule": crontab(minute=0, hour=2),  # 2 AM daily
        "options": {"queue": "low_priority"},
    },
}


# =============================================================================
# TASK ROUTES
# =============================================================================

celery_app.conf.task_routes = {
    # High priority tasks
    "infrastructure.workers.telemetry.refresh_entity_signal": {"queue": "default"},
    "infrastructure.workers.telemetry.refresh_entity_all_signals": {"queue": "default"},

    # Batch operations on low priority
    "infrastructure.workers.telemetry.batch_refresh_by_volatility": {"queue": "low_priority"},
    "infrastructure.workers.telemetry.cleanup_stale_signals": {"queue": "low_priority"},
}


# =============================================================================
# SIGNAL VOLATILITY CONFIGURATION
# =============================================================================

# Signal volatility classification
# Determines refresh frequency for each signal type
SIGNAL_VOLATILITY = {
    # HIGH - Refresh every 12 hours
    "HIGH": [
        "active_cves",
        "recent_breaches",
        "threat_intelligence",
        "malware_detections",
    ],

    # MEDIUM - Refresh daily
    "MEDIUM": [
        "security_headers",
        "tls_configuration",
        "dns_security",
        "waf_presence",
        "email_security",
    ],

    # LOW - Refresh weekly
    "LOW": [
        "financial_stability",
        "regulatory_filings",
        "governance_structure",
        "audit_findings",
    ],

    # STATIC - Refresh on-demand only
    "STATIC": [
        "industry_classification",
        "company_size",
        "founding_date",
    ],
}


def get_signal_volatility(signal_id: str) -> str:
    """Get volatility classification for a signal."""
    for volatility, signals in SIGNAL_VOLATILITY.items():
        if signal_id in signals:
            return volatility
    return "MEDIUM"  # Default to medium if not classified


def get_refresh_interval_hours(volatility: str) -> int:
    """Get refresh interval in hours for a volatility level."""
    intervals = {
        "HIGH": 12,
        "MEDIUM": 24,
        "LOW": 168,  # 7 days
        "STATIC": 720,  # 30 days (on-demand preferred)
    }
    return intervals.get(volatility, 24)


# =============================================================================
# CONFIG-DRIVEN SIGNAL DISCOVERY (Phase 2)
# =============================================================================

def get_registry_signal_ids(coverage_id: str = None) -> list:
    """
    Discover signal IDs from compiled Pydantic configs.

    If a coverage_id is given, returns signals for that coverage only.
    Otherwise returns the union of all signals across all coverages.

    Args:
        coverage_id: Optional coverage to filter by

    Returns:
        List of signal IDs found in signal_registry
    """
    try:
        from infrastructure.models.compiler import get_compiled_configs, get_config

        if coverage_id:
            config = get_config(coverage_id)
            return [sig.id for sig in config.signal_registry]

        # Union across all coverages
        configs = get_compiled_configs()
        signal_ids = set()
        for coverage in configs.values():
            for config in coverage.configurations.values():
                for sig in config.signal_registry:
                    signal_ids.add(sig.id)
        return sorted(signal_ids)

    except Exception:
        # Fallback to static list if configs not available
        all_signals = []
        for signals in SIGNAL_VOLATILITY.values():
            all_signals.extend(signals)
        return all_signals


def get_inference_function_map(coverage_id: str) -> dict:
    """
    Build a map of signal_id -> inference_utility_function from compiled config.

    Args:
        coverage_id: Coverage to load

    Returns:
        Dict mapping signal_id to its inference function name
    """
    try:
        from infrastructure.models.compiler import get_config

        config = get_config(coverage_id)
        return {
            sig.id: sig.inference_utility_function
            for sig in config.signal_registry
        }
    except Exception:
        return {}

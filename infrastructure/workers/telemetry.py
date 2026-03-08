"""
DSI Telemetry Workers (Version 4 - Phase 2)

Celery tasks for continuous signal extraction and graph maintenance.

The telemetry system transitions from "Point-in-Time" API extraction to a
continuous "Organisational Graph" model:

1. Signal extractors run as background workers
2. Results are stored in the RiskSignal table with timestamps
3. The quoting engine queries pre-populated signals (millisecond response)
4. Stale signals trigger synchronous refresh as fallback

Usage:
    from infrastructure.workers.telemetry import refresh_entity_signal

    # Queue signal refresh
    refresh_entity_signal.delay("entity_123", "security_headers")

    # Refresh all signals for entity
    refresh_entity_all_signals.delay("entity_123")
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .celery_app import (
    celery_app,
    get_signal_volatility,
    get_refresh_interval_hours,
    get_registry_signal_ids,
    SIGNAL_VOLATILITY,
)

logger = logging.getLogger("dsi.telemetry")


# =============================================================================
# CORE TASKS
# =============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_entity_signal(
    self,
    entity_id: str,
    signal_id: str,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Refresh a single signal for an entity.

    This is the core telemetry task. It:
    1. Checks if refresh is needed (based on staleness)
    2. Calls the appropriate extractor
    3. Updates the RiskSignal table with inferred_value
    4. Logs to audit trail

    Args:
        entity_id: Entity identifier
        signal_id: Signal to refresh
        force: Force refresh even if not stale

    Returns:
        Dict with refresh result
    """
    try:
        # Import here to avoid circular dependencies
        from infrastructure.db.session import get_db
        from infrastructure.db.models import SignalCache
        from signal_architecture.signals.inference.registry import get_inference_function
        from signal_architecture.signals.types import InferenceContext

        db = next(get_db())

        # Check if signal exists and is fresh
        existing = db.query(SignalCache).filter_by(
            entity_id=entity_id,
            signal_id=signal_id,
        ).first()

        if existing and not force:
            volatility = get_signal_volatility(signal_id)
            refresh_hours = get_refresh_interval_hours(volatility)
            staleness_threshold = datetime.now(timezone.utc) - timedelta(hours=refresh_hours)

            if existing.extracted_at > staleness_threshold:
                logger.debug(
                    f"Signal {signal_id} for {entity_id} is fresh "
                    f"(extracted {existing.extracted_at}), skipping"
                )
                return {
                    "status": "skipped",
                    "reason": "fresh",
                    "entity_id": entity_id,
                    "signal_id": signal_id,
                    "extracted_at": existing.extracted_at.isoformat(),
                }

        # Get inference function
        try:
            inference_func = get_inference_function(signal_id)
        except Exception as e:
            logger.error(f"Inference function not found for {signal_id}: {e}")
            return {
                "status": "error",
                "error": f"Inference function not found: {signal_id}",
                "entity_id": entity_id,
                "signal_id": signal_id,
            }

        # Execute extraction with coverage context if available
        coverage = ""
        config_name = ""
        try:
            from infrastructure.models.compiler import get_compiled_configs
            configs = get_compiled_configs()
            # Find which coverage this signal belongs to
            for cov_id, cov in configs.items():
                for cfg_id, cfg in cov.configurations.items():
                    for sig in cfg.signal_registry:
                        if sig.id == signal_id:
                            coverage = cov_id
                            config_name = cfg_id
                            break
                    if coverage:
                        break
                if coverage:
                    break
        except Exception:
            pass

        context = InferenceContext(
            configuration={},
            coverage=coverage,
            config_name=config_name,
        )

        result = inference_func(entity_id, context)
        extracted_at = datetime.now(timezone.utc)

        # Update or create signal record
        if existing:
            existing.inferred_value = result.score
            existing.raw_data = result.metadata or {}
            existing.confidence = result.confidence or 0.8
            existing.extracted_at = extracted_at
            existing.source_name = result.metadata.get("extractor", signal_id) if result.metadata else signal_id
            existing.error = result.error
        else:
            new_signal = SignalCache(
                entity_id=entity_id,
                signal_id=signal_id,
                source_name=result.metadata.get("extractor", signal_id) if result.metadata else signal_id,
                inferred_value=result.score,
                raw_data=result.metadata or {},
                confidence=result.confidence or 0.8,
                extracted_at=extracted_at,
                error=result.error,
            )
            db.add(new_signal)

        db.commit()

        logger.info(
            f"Refreshed signal {signal_id} for {entity_id}: "
            f"score={result.score}, confidence={result.confidence}"
        )

        return {
            "status": "success",
            "entity_id": entity_id,
            "signal_id": signal_id,
            "score": result.score,
            "confidence": result.confidence,
            "extracted_at": extracted_at.isoformat(),
        }

    except Exception as exc:
        logger.error(
            f"Signal refresh failed for {entity_id}/{signal_id}: {exc}",
            exc_info=True
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True)
def refresh_entity_all_signals(
    self,
    entity_id: str,
    signal_ids: Optional[List[str]] = None,
    coverage_id: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Refresh all signals for an entity.

    Args:
        entity_id: Entity identifier
        signal_ids: Optional list of signals to refresh (all if None)
        coverage_id: Optional coverage ID to discover signals from config
        force: Force refresh even if not stale

    Returns:
        Dict with summary of refresh results
    """
    # If no signal IDs provided, discover from compiled config or fallback to static
    if signal_ids is None:
        signal_ids = get_registry_signal_ids(coverage_id)
        if not signal_ids:
            signal_ids = []
            for volatility_signals in SIGNAL_VOLATILITY.values():
                signal_ids.extend(volatility_signals)

    results = {
        "entity_id": entity_id,
        "total": len(signal_ids),
        "success": 0,
        "skipped": 0,
        "errors": 0,
        "details": [],
    }

    for signal_id in signal_ids:
        try:
            result = refresh_entity_signal(entity_id, signal_id, force)
            results["details"].append(result)

            if result["status"] == "success":
                results["success"] += 1
            elif result["status"] == "skipped":
                results["skipped"] += 1
            else:
                results["errors"] += 1

        except Exception as e:
            logger.error(f"Failed to refresh {signal_id} for {entity_id}: {e}")
            results["errors"] += 1
            results["details"].append({
                "status": "error",
                "signal_id": signal_id,
                "error": str(e),
            })

    logger.info(
        f"Refreshed {results['success']} signals for {entity_id} "
        f"({results['skipped']} skipped, {results['errors']} errors)"
    )

    return results


@celery_app.task
def schedule_entity_refresh(
    entity_id: str,
    priority: str = "default",
) -> str:
    """
    Schedule a full entity refresh with appropriate priority.

    Args:
        entity_id: Entity to refresh
        priority: Queue priority (high_priority, default, low_priority)

    Returns:
        Task ID of the scheduled refresh
    """
    task = refresh_entity_all_signals.apply_async(
        args=[entity_id],
        kwargs={"force": False},
        queue=priority,
    )
    return task.id


# =============================================================================
# BATCH TASKS
# =============================================================================

@celery_app.task
def batch_refresh_by_volatility(
    volatility: str,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Batch refresh signals by volatility level.

    Called by Celery Beat on schedule to refresh signals that are due.

    Args:
        volatility: Volatility level (HIGH, MEDIUM, LOW, STATIC)
        limit: Maximum entities to process per batch

    Returns:
        Dict with batch processing summary
    """
    from infrastructure.db.session import get_db
    from infrastructure.db.models import SignalCache
    from sqlalchemy import func

    signal_ids = SIGNAL_VOLATILITY.get(volatility, [])
    if not signal_ids:
        return {"status": "skipped", "reason": f"No signals for volatility {volatility}"}

    refresh_hours = get_refresh_interval_hours(volatility)
    staleness_threshold = datetime.now(timezone.utc) - timedelta(hours=refresh_hours)

    db = next(get_db())

    # Find entities with stale signals
    stale_entities = db.query(
        SignalCache.entity_code
    ).filter(
        SignalCache.signal_code.in_(signal_ids),
        SignalCache.extracted_at < staleness_threshold,
    ).group_by(
        SignalCache.entity_code
    ).limit(limit).all()

    entity_ids = [e[0] for e in stale_entities]

    logger.info(
        f"Batch refresh {volatility}: Found {len(entity_ids)} entities with stale signals"
    )

    # Queue refresh tasks
    for entity_id in entity_ids:
        refresh_entity_all_signals.delay(
            entity_id=entity_id,
            signal_ids=signal_ids,
            force=True,
        )

    return {
        "status": "queued",
        "volatility": volatility,
        "entities_queued": len(entity_ids),
        "signals": signal_ids,
    }


@celery_app.task
def cleanup_stale_signals(
    days_threshold: int = 90,
) -> Dict[str, Any]:
    """
    Clean up signal records that haven't been refreshed in a long time.

    Args:
        days_threshold: Days after which signals are considered abandoned

    Returns:
        Dict with cleanup summary
    """
    from infrastructure.db.session import get_db
    from infrastructure.db.models import SignalCache

    threshold = datetime.now(timezone.utc) - timedelta(days=days_threshold)

    db = next(get_db())

    # Count stale records
    stale_count = db.query(SignalCache).filter(
        SignalCache.extracted_at < threshold
    ).count()

    if stale_count == 0:
        return {"status": "skipped", "reason": "No stale signals found"}

    # Delete stale records
    db.query(SignalCache).filter(
        SignalCache.extracted_at < threshold
    ).delete()
    db.commit()

    logger.info(f"Cleaned up {stale_count} stale signal records")

    return {
        "status": "success",
        "deleted_count": stale_count,
        "threshold_date": threshold.isoformat(),
    }


# =============================================================================
# SYNCHRONOUS FALLBACK
# =============================================================================

def synchronous_refresh(
    entity_id: str,
    signal_ids: List[str],
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    """
    Synchronous signal refresh fallback for stale data.

    Used by the quoting engine when cached data is too old.
    This is a blocking operation and should be used sparingly.

    Args:
        entity_id: Entity to refresh
        signal_ids: Signals to refresh
        timeout_seconds: Maximum time to wait

    Returns:
        Dict mapping signal_id to result
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed

    results = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                refresh_entity_signal,
                entity_id,
                signal_id,
                True,  # force=True
            ): signal_id
            for signal_id in signal_ids
        }

        try:
            for future in as_completed(futures, timeout=timeout_seconds):
                signal_id = futures[future]
                try:
                    result = future.result()
                    results[signal_id] = result
                except Exception as e:
                    results[signal_id] = {"status": "error", "error": str(e)}

        except TimeoutError:
            logger.warning(
                f"Synchronous refresh timed out for {entity_id} "
                f"after {timeout_seconds}s"
            )
            # Mark incomplete signals
            for future, signal_id in futures.items():
                if signal_id not in results:
                    results[signal_id] = {"status": "timeout"}

    return results


def check_signal_freshness(
    entity_id: str,
    signal_ids: List[str],
) -> Dict[str, bool]:
    """
    Check if signals are fresh enough for use.

    Args:
        entity_id: Entity to check
        signal_ids: Signals to check

    Returns:
        Dict mapping signal_id to freshness status (True = fresh)
    """
    from infrastructure.db.session import get_db
    from infrastructure.db.models import SignalCache

    db = next(get_db())

    results = {sid: False for sid in signal_ids}

    signals = db.query(SignalCache).filter(
        SignalCache.entity_code == entity_id,
        SignalCache.signal_code.in_(signal_ids),
    ).all()

    now = datetime.now(timezone.utc)

    for signal in signals:
        volatility = get_signal_volatility(signal.signal_code)
        refresh_hours = get_refresh_interval_hours(volatility)
        staleness_threshold = now - timedelta(hours=refresh_hours)

        results[signal.signal_code] = signal.extracted_at > staleness_threshold

    return results

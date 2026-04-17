"""V6/A-deep — derived inference functions for captive.

Scaffolded "+N derived" inference functions per the coverage's
MATURATION_STATUS.md. Each function returns a deterministic score
derived from a stable hash of (entity_id, signal_id) so per-entity
variation is exercised in calibration and tests. Real extractor-
backed bodies land per-signal as the upstream extractors mature.

Score range [30.0, 70.0] — neutral-centered synthetic spread that
matches the SignalResult validation window (0-100).
"""
from __future__ import annotations

import hashlib
from typing import Any

from signal_architecture.signals.inference.registry import register_inference_function
from signal_architecture.signals.types import SignalResult


def _deterministic_score(entity_id: str, signal_id: str) -> float:
    """Deterministic score in [30.0, 70.0]."""
    h = hashlib.sha1(f"{entity_id}|{signal_id}".encode("utf-8")).digest()
    nibble = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
    return 30.0 + 40.0 * nibble


def _deterministic_confidence(entity_id: str, signal_id: str) -> float:
    """Deterministic confidence in [0.50, 0.85]."""
    h = hashlib.sha1(f"{entity_id}:{signal_id}:conf".encode("utf-8")).digest()
    nibble = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
    return 0.50 + 0.35 * nibble


def _padded(signal_id: str, entity_id: str) -> SignalResult:
    return SignalResult(
        signal_id=signal_id,
        score=_deterministic_score(entity_id, signal_id),
        confidence=_deterministic_confidence(entity_id, signal_id),
        execution_time_ms=0.0,
    )



@register_inference_function("captive_derived_01_basefunction")
async def captive_derived_01(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #01 — deterministic synthetic scaffold."""
    return _padded("captive_derived_01", entity_id)


@register_inference_function("captive_derived_02_basefunction")
async def captive_derived_02(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #02 — deterministic synthetic scaffold."""
    return _padded("captive_derived_02", entity_id)


@register_inference_function("captive_derived_03_basefunction")
async def captive_derived_03(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #03 — deterministic synthetic scaffold."""
    return _padded("captive_derived_03", entity_id)


@register_inference_function("captive_derived_04_basefunction")
async def captive_derived_04(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #04 — deterministic synthetic scaffold."""
    return _padded("captive_derived_04", entity_id)


@register_inference_function("captive_derived_05_basefunction")
async def captive_derived_05(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #05 — deterministic synthetic scaffold."""
    return _padded("captive_derived_05", entity_id)


@register_inference_function("captive_derived_06_basefunction")
async def captive_derived_06(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #06 — deterministic synthetic scaffold."""
    return _padded("captive_derived_06", entity_id)


@register_inference_function("captive_derived_07_basefunction")
async def captive_derived_07(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #07 — deterministic synthetic scaffold."""
    return _padded("captive_derived_07", entity_id)


@register_inference_function("captive_derived_08_basefunction")
async def captive_derived_08(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #08 — deterministic synthetic scaffold."""
    return _padded("captive_derived_08", entity_id)


@register_inference_function("captive_derived_09_basefunction")
async def captive_derived_09(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #09 — deterministic synthetic scaffold."""
    return _padded("captive_derived_09", entity_id)


@register_inference_function("captive_derived_10_basefunction")
async def captive_derived_10(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #10 — deterministic synthetic scaffold."""
    return _padded("captive_derived_10", entity_id)


@register_inference_function("captive_derived_11_basefunction")
async def captive_derived_11(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #11 — deterministic synthetic scaffold."""
    return _padded("captive_derived_11", entity_id)


@register_inference_function("captive_derived_12_basefunction")
async def captive_derived_12(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #12 — deterministic synthetic scaffold."""
    return _padded("captive_derived_12", entity_id)


@register_inference_function("captive_derived_13_basefunction")
async def captive_derived_13(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #13 — deterministic synthetic scaffold."""
    return _padded("captive_derived_13", entity_id)


@register_inference_function("captive_derived_14_basefunction")
async def captive_derived_14(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #14 — deterministic synthetic scaffold."""
    return _padded("captive_derived_14", entity_id)


@register_inference_function("captive_derived_15_basefunction")
async def captive_derived_15(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #15 — deterministic synthetic scaffold."""
    return _padded("captive_derived_15", entity_id)


@register_inference_function("captive_derived_16_basefunction")
async def captive_derived_16(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #16 — deterministic synthetic scaffold."""
    return _padded("captive_derived_16", entity_id)


@register_inference_function("captive_derived_17_basefunction")
async def captive_derived_17(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #17 — deterministic synthetic scaffold."""
    return _padded("captive_derived_17", entity_id)


@register_inference_function("captive_derived_18_basefunction")
async def captive_derived_18(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #18 — deterministic synthetic scaffold."""
    return _padded("captive_derived_18", entity_id)


@register_inference_function("captive_derived_19_basefunction")
async def captive_derived_19(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #19 — deterministic synthetic scaffold."""
    return _padded("captive_derived_19", entity_id)


@register_inference_function("captive_derived_20_basefunction")
async def captive_derived_20(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #20 — deterministic synthetic scaffold."""
    return _padded("captive_derived_20", entity_id)


@register_inference_function("captive_derived_21_basefunction")
async def captive_derived_21(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #21 — deterministic synthetic scaffold."""
    return _padded("captive_derived_21", entity_id)


@register_inference_function("captive_derived_22_basefunction")
async def captive_derived_22(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #22 — deterministic synthetic scaffold."""
    return _padded("captive_derived_22", entity_id)


@register_inference_function("captive_derived_23_basefunction")
async def captive_derived_23(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #23 — deterministic synthetic scaffold."""
    return _padded("captive_derived_23", entity_id)


@register_inference_function("captive_derived_24_basefunction")
async def captive_derived_24(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #24 — deterministic synthetic scaffold."""
    return _padded("captive_derived_24", entity_id)


@register_inference_function("captive_derived_25_basefunction")
async def captive_derived_25(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #25 — deterministic synthetic scaffold."""
    return _padded("captive_derived_25", entity_id)


@register_inference_function("captive_derived_26_basefunction")
async def captive_derived_26(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #26 — deterministic synthetic scaffold."""
    return _padded("captive_derived_26", entity_id)


@register_inference_function("captive_derived_27_basefunction")
async def captive_derived_27(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #27 — deterministic synthetic scaffold."""
    return _padded("captive_derived_27", entity_id)


@register_inference_function("captive_derived_28_basefunction")
async def captive_derived_28(entity_id: str, context: Any) -> SignalResult:
    """captive derived signal #28 — deterministic synthetic scaffold."""
    return _padded("captive_derived_28", entity_id)

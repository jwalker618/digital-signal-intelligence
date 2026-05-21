"""V7 Phase 11 — variant loop package."""
from .types import VariantKind, VariantQuery, VariantResult, VARIANT_KINDS
from .prompts import generate_variants_for
from .loop import (
    is_trigger,
    run_variant_loop,
    select_triggers,
)

__all__ = [
    "VariantKind",
    "VariantQuery",
    "VariantResult",
    "VARIANT_KINDS",
    "generate_variants_for",
    "is_trigger",
    "run_variant_loop",
    "select_triggers",
]

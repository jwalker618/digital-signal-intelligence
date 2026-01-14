"""Backwards compatibility shim - re-exports from signals package."""
import signals as _signals
from signals import *
from signals import (
    ExtractorResult,
    SignalResult,
    InferenceContext,
)

# Re-export submodules
from signals import types
from signals import extractors
from signals import aggregators
from signals import categorisers
from signals import inference
from signals import routing

__all__ = _signals.__all__ if hasattr(_signals, '__all__') else []

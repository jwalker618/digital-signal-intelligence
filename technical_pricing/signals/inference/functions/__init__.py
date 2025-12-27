"""
DSI Inference Functions by Coverage Domain

Structure:
    {coverage}/
        __init__.py
        signals.py      - All inference functions for the coverage

Each function:
    - Maps to an `inference_utility_function` in the YAML config
    - Orchestrates: Extractor(s) → Aggregator(s) → Categorizer
    - Returns a SignalResult with score/category and audit trail

Registration:
    Functions are registered via @register_inference_function decorator.
    Import the modules to trigger registration.
"""

# Import all coverage modules to register functions
from . import aerospace
from . import cyber
from . import do
from . import energy
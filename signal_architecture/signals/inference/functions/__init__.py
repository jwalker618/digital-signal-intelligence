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
from . import cross_coverage
from . import medprof  # V6/B1
from . import wc  # V6/B2
from . import prodlib  # V6/B3
from . import env_liab  # V6/B4
from . import construction  # V6/B5
from . import event  # V6/B6
from . import pvt  # V6/B7
from . import teo  # V6/B8
from . import reinsurance  # V6/B9
from . import crop  # V6/B10
"""
DSI Inference Functions by Coverage Domain

Each module contains inference function implementations for a specific coverage:
    - aerospace.py: Aviation signal inference functions
    - cyber.py: Cybersecurity signal inference functions
    - do.py: Directors & Officers signal inference functions
    - energy.py: Energy sector signal inference functions
    - fi.py: Financial Institutions signal inference functions
    - marine.py: Marine/shipping signal inference functions
    - pi.py: Professional Indemnity signal inference functions

Each function:
    - Maps to an `inference_utility_function` in the YAML config
    - Orchestrates: Extractor(s) → Aggregator(s) → Categorizer
    - Returns a SignalResult with score/category and audit trail

Registration:
    Functions are registered via decorator:
    
    @register_inference_function("alliance_membership_basefunction")
    def alliance_membership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
        ...
"""

# Functions will be imported here to trigger registration
# from . import aerospace
# from . import cyber
# etc.

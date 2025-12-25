"""
DSI Technical Pricing Framework

Digital Signal Intelligence (DSI) insurance pricing based on observable
digital signals rather than self-reported documentation.

Packages:
    - signals: Signal processing pipeline (extractors, aggregators, categorizers, inference)
    - coverages: YAML configuration files for each coverage domain
    - model: Model execution, scoring, and pricing logic

Architecture:
    YAML Config → Extractor → Aggregator → Categorizer → Inference → Model Output
    
    1. YAML configs define signals, weights, thresholds, tiers
    2. Extractors fetch raw data (currently stubs)
    3. Aggregators normalize data for scoring
    4. Categorizers apply scoring/categorization logic
    5. Inference functions orchestrate the pipeline per signal
    6. Model combines all signals into composite score and premium

Usage:
    from technical_pricing.signals import (
        ExtractorResult,
        SignalResult,
        InferenceContext,
    )
    from technical_pricing.signals.extractors import StubExtractor
    from technical_pricing.signals.inference import get_inference_function
"""

__version__ = "0.1.0"

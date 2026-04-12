"""WE-3a: Correlation Scanner -- first stage of the discovery pipeline.

Mines the assessment database for pairwise signal correlations and
filters to statistically significant, coverage-agnostic candidates.
"""

from world_engine.scanner.correlation_scanner import CorrelationScanner, ScannerConfig

__all__ = ["CorrelationScanner", "ScannerConfig"]

"""
DSI Core - Python bindings for Rust performance components.

Provides accelerated implementations of:
- Graph computations (PageRank, risk propagation)
- Behavioural derivative calculations
- Configuration validation

Falls back to pure Python implementations when the Rust
extension is not available (e.g., during development).
"""

import sys as _sys

try:
    from dsi_core.dsi_core import graph, derivatives, validation, scoring
    # Register the PyO3 submodules so `import dsi_core.scoring` works.
    _sys.modules[__name__ + ".graph"] = graph
    _sys.modules[__name__ + ".derivatives"] = derivatives
    _sys.modules[__name__ + ".validation"] = validation
    _sys.modules[__name__ + ".scoring"] = scoring
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

__version__ = "0.1.0"
__all__ = ["RUST_AVAILABLE", "graph", "derivatives", "validation", "scoring"]

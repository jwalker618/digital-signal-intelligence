"""
DSI Core - Python bindings for Rust performance components.

Provides accelerated implementations of:
- Graph computations (PageRank, risk propagation)
- Behavioural derivative calculations
- Configuration validation

Falls back to pure Python implementations when the Rust
extension is not available (e.g., during development).
"""

try:
    from dsi_core.dsi_core import graph, derivatives, validation
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

__version__ = "0.1.0"
__all__ = ["RUST_AVAILABLE", "graph", "derivatives", "validation"]

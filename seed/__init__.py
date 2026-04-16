"""DSI seed package (V6/C4).

Consolidates bench, v5 companion, and synthetic-generator seed scripts
behind a single ``python -m seed`` CLI. The legacy root-level scripts
(``seed_dsi_bench.py``, ``seed_v5.py``, ``synthetic_generator.py``)
still exist and emit a ``DeprecationWarning``; they will be deleted in
the C4-final phase (Q4 per V6_Master_Sequence.md) after `python -m seed
init` is proven in CI.

Entry points:

    python -m seed init --tenant dsi-demo --entities 500
    python -m seed bench
    python -m seed v5
    python -m seed synthetic --coverage cyber --n 100
    python -m seed reset --confirm
    python -m seed verify
"""
from __future__ import annotations

__all__ = ["bench", "v5", "synthetic", "reset", "verify", "cli"]

"""DSI seed package (V6/C4-final).

Canonical home for all bench / v5 / synthetic seed logic. Legacy
root-level scripts (``seed_dsi_bench.py``, ``seed_v5.py``,
``synthetic_generator.py``) were removed in V6/C4-final and their
logic moved here verbatim.

Entry points (via ``python -m seed``):

    python -m seed init --tenant dsi-demo --entities 500
    python -m seed bench
    python -m seed v5
    python -m seed synthetic --coverage cyber --n 100
    python -m seed reset --confirm
    python -m seed verify
"""
from __future__ import annotations

__all__ = ["bench", "v5", "synthetic", "reset", "verify", "cli"]

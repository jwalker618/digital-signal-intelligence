"""PyO3 binding shim for `rust/dsi-core` (V6/E1).

Runtime resolution:
- When the compiled `dsi_core` module is importable AND
  ``DSI_USE_RUST_SCORER=true``, ``score()`` calls the Rust
  implementation.
- Otherwise ``score()`` falls back to the pure-Python reference
  scorer in ``layers.risk.scorer``. The reference path stays
  the authoritative semantics; the Rust path is validated against
  it via the nightly parity job documented in
  ``docs/overview/Rust_Core_Decision.md``.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Iterable, Optional

log = logging.getLogger("dsi.rust_bindings")


def _rust_enabled() -> bool:
    return os.environ.get("DSI_USE_RUST_SCORER", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _try_import_rust():
    try:
        import dsi_core as _rust  # type: ignore
        return _rust
    except ImportError:
        return None


def score(
    config_hash: str,
    signals: Iterable[Any],
    *,
    use_rust: Optional[bool] = None,
) -> Any:
    """Score a set of signals into a composite.

    Dispatches to either the Rust-compiled scorer or the reference
    Python scorer. Identical output under the E1 parity contract
    (max abs divergence < 1e-9).

    Args:
        config_hash: The compiled-config hash used by the Rust path for
            lookup-table cache reuse; ignored by the Python fallback.
        signals: Iterable of SignalScore objects.
        use_rust: Force a path (True/False). Defaults to the runtime
            env flag ``DSI_USE_RUST_SCORER``.
    """
    if use_rust is None:
        use_rust = _rust_enabled()

    rust = _try_import_rust() if use_rust else None
    if rust is not None:
        try:
            return rust.score(config_hash, list(signals))
        except Exception as e:  # pragma: no cover — parity suite guards this
            log.warning("Rust scorer failed (%s); falling back to Python.", e)

    from layers.risk.scorer import score as _py_score
    return _py_score(config_hash=config_hash, signals=list(signals))

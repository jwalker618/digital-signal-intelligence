"""V7 — LLM client factory.

Resolves a callable matching the project-wide ``(system, user) -> str``
protocol that the validator, mechanism extractor, and variant loop all
consume. Reads ``DSI_LLM_PROVIDER`` env to pick a backend:

    stub       — always returns ``"{}"`` (default; safe for tests + dev)
    anthropic  — Anthropic Claude via the official SDK
    openai     — OpenAI chat-completions via the official SDK
    callable   — custom path: set DSI_LLM_CALLABLE=dotted.path.to.fn

Backends that need an SDK only import it lazily, so the module loads
without optional deps installed. Callers don't need to know which
backend ran — the protocol stays sealed.
"""
from __future__ import annotations

import importlib
import logging
import os
from typing import Callable, Optional

logger = logging.getLogger("dsi.llm")


# Public type — matches Phase 6 Validator.LLMCallable and the variant
# loop's signature.
LLMClient = Callable[..., str]


# ---------------------------------------------------------------------------
# Stub backend (default)
# ---------------------------------------------------------------------------

def _stub_client(*, system: str, user: str) -> str:
    """Returns an empty JSON object. Downstream parsers degrade gracefully
    (validator -> non-advance failure verdict; mechanism extractor -> None;
    variant loop -> empty queries list). Tests and dev environments use
    this by default.
    """
    return "{}"


# ---------------------------------------------------------------------------
# Anthropic backend (lazy import)
# ---------------------------------------------------------------------------

def _anthropic_client_factory(
    *,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1024,
) -> LLMClient:
    """Bind a configured anthropic client into the protocol shape."""
    import anthropic  # type: ignore  # lazy

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)

    def _call(*, system: str, user: str) -> str:
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Anthropic returns a list of content blocks; concat text blocks.
        parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "".join(parts)

    return _call


# ---------------------------------------------------------------------------
# OpenAI backend (lazy import)
# ---------------------------------------------------------------------------

def _openai_client_factory(
    *,
    model: str = "gpt-4o-mini",
    max_tokens: int = 1024,
) -> LLMClient:
    import openai  # type: ignore  # lazy

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = openai.OpenAI(api_key=api_key)

    def _call(*, system: str, user: str) -> str:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    return _call


# ---------------------------------------------------------------------------
# Custom callable backend
# ---------------------------------------------------------------------------

def _custom_callable_factory(path: str) -> LLMClient:
    """Resolve ``DSI_LLM_CALLABLE`` to an importable callable."""
    module_path, _, attr = path.rpartition(".")
    if not module_path:
        raise RuntimeError(f"DSI_LLM_CALLABLE bad form: {path!r}")
    mod = importlib.import_module(module_path)
    obj = getattr(mod, attr, None)
    if obj is None or not callable(obj):
        raise RuntimeError(f"DSI_LLM_CALLABLE {path!r} is not callable")
    return obj


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

_cached_client: Optional[LLMClient] = None


def get_llm_client(*, force_refresh: bool = False) -> LLMClient:
    """Return the configured LLM callable. Cached per-process.

    Resolution order:
        1. DSI_LLM_PROVIDER=callable + DSI_LLM_CALLABLE=<dotted.path>
        2. DSI_LLM_PROVIDER=anthropic  (requires ANTHROPIC_API_KEY)
        3. DSI_LLM_PROVIDER=openai     (requires OPENAI_API_KEY)
        4. DSI_LLM_PROVIDER=stub (or unset) -> stub client
    """
    global _cached_client
    if _cached_client is not None and not force_refresh:
        return _cached_client

    provider = (os.environ.get("DSI_LLM_PROVIDER") or "stub").lower()

    try:
        if provider == "callable":
            path = os.environ.get("DSI_LLM_CALLABLE", "")
            client = _custom_callable_factory(path)
        elif provider == "anthropic":
            client = _anthropic_client_factory()
        elif provider == "openai":
            client = _openai_client_factory()
        elif provider == "stub":
            client = _stub_client
        else:
            logger.warning(
                "Unknown DSI_LLM_PROVIDER=%r, falling back to stub", provider,
            )
            client = _stub_client
    except Exception as e:  # noqa: BLE001 — never let LLM-factory crash the worker
        logger.warning(
            "LLM provider %r failed to initialise (%s); falling back to stub",
            provider, e,
        )
        client = _stub_client

    _cached_client = client
    return client


def reset_client_cache() -> None:
    """Test hook — clears the cached client so env changes take effect."""
    global _cached_client
    _cached_client = None

"""
DSI Extractor Resolver

Unified entry point for inference functions to obtain extractors through
the production factory. The previous in-package stub fallback
(``stubs.cyber`` / ``stubs.common``) was retired in the V6/E10 stub
retirement — production code must not import the stub fixtures, and the
factory is now the single source of truth.

Usage in inference functions:
    from ....extractors.resolver import get_extractor

    extractor = get_extractor("email_auth")
    result = extractor.extract(entity_id, context=context)
"""

import logging
import os
from typing import Optional

from .production.factory import get_extractor as factory_get_extractor

logger = logging.getLogger(__name__)


def _get_mode() -> str:
    """Get the current extractor mode from environment or factory default."""
    env_mode = os.getenv("DSI_EXTRACTOR_MODE")
    if env_mode:
        return env_mode

    use_stubs = os.getenv("FEATURE_USE_STUBS", "true").lower()
    if use_stubs == "false":
        return "hybrid"

    return "stub"


def get_extractor(name: str, mode: Optional[str] = None):
    """
    Get an extractor instance by name via the production factory.

    Args:
        name: Extractor name (e.g., 'email_auth', 'tls_config')
        mode: Override mode ('stub', 'production', 'hybrid')

    Returns:
        Extractor instance ready to call .extract()
    """
    effective_mode = mode or _get_mode()
    return factory_get_extractor(name, mode=effective_mode)

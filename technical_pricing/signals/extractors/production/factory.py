"""
DSI Signal Architecture - Extractor Factory

Provides a factory for creating extractors that can swap between
stub and production implementations.

Usage:
    from technical_pricing.signals.extractors.production import (
        get_extractor,
        set_default_mode,
        ExtractorFactory,
    )

    # Set default mode (affects all get_extractor calls)
    set_default_mode('production')

    # Get an extractor (uses production if available, falls back to stub)
    extractor = get_extractor('email_auth')
    result = extractor.extract('example.com')

    # Or explicitly request a mode
    stub_extractor = get_extractor('email_auth', mode='stub')
    prod_extractor = get_extractor('email_auth', mode='production')

    # Hybrid mode: use production for some, stub for others
    set_default_mode('hybrid')

Modes:
    - 'stub': Always use stub extractors (default, for testing)
    - 'production': Use production extractors (requires API keys)
    - 'hybrid': Use production where available, fall back to stub
"""

import logging
from typing import Any, Callable, Dict, Optional, Type

from .base import ProductionExtractor
from .config import ExtractorConfig, get_config

logger = logging.getLogger(__name__)

# Type alias for extractor classes
ExtractorClass = Type[ProductionExtractor]


class ExtractorRegistry:
    """
    Registry of available extractors.

    Maps extractor names to their stub and production implementations.
    """

    def __init__(self):
        # Map: extractor_name -> {'stub': StubClass, 'production': ProdClass}
        self._registry: Dict[str, Dict[str, ExtractorClass]] = {}
        # Lazy loader functions for imports
        self._loaders: Dict[str, Callable[[], None]] = {}

    def register_stub(self, name: str, extractor_class: ExtractorClass) -> None:
        """Register a stub extractor implementation."""
        if name not in self._registry:
            self._registry[name] = {}
        self._registry[name]['stub'] = extractor_class
        logger.debug(f"Registered stub extractor: {name}")

    def register_production(self, name: str, extractor_class: ExtractorClass) -> None:
        """Register a production extractor implementation."""
        if name not in self._registry:
            self._registry[name] = {}
        self._registry[name]['production'] = extractor_class
        logger.debug(f"Registered production extractor: {name}")

    def register_loader(self, name: str, loader: Callable[[], None]) -> None:
        """Register a lazy loader for an extractor module."""
        self._loaders[name] = loader

    def get(self, name: str, mode: str) -> Optional[ExtractorClass]:
        """Get an extractor class by name and mode."""
        # Try lazy loading if not registered
        if name not in self._registry and name in self._loaders:
            self._loaders[name]()

        if name not in self._registry:
            return None

        return self._registry[name].get(mode)

    def has_production(self, name: str) -> bool:
        """Check if a production implementation exists."""
        if name in self._loaders and name not in self._registry:
            self._loaders[name]()
        return name in self._registry and 'production' in self._registry[name]

    def has_stub(self, name: str) -> bool:
        """Check if a stub implementation exists."""
        if name in self._loaders and name not in self._registry:
            self._loaders[name]()
        return name in self._registry and 'stub' in self._registry[name]

    def list_extractors(self) -> Dict[str, Dict[str, bool]]:
        """List all registered extractors and their available modes."""
        # Trigger all lazy loaders
        for loader in self._loaders.values():
            try:
                loader()
            except Exception:
                pass

        result = {}
        for name, modes in self._registry.items():
            result[name] = {
                'stub': 'stub' in modes,
                'production': 'production' in modes,
            }
        return result


# Global registry instance
_registry = ExtractorRegistry()

# Default mode
_default_mode = 'stub'


def set_default_mode(mode: str) -> None:
    """
    Set the default extractor mode.

    Args:
        mode: 'stub', 'production', or 'hybrid'
    """
    global _default_mode
    if mode not in ('stub', 'production', 'hybrid'):
        raise ValueError(f"mode must be 'stub', 'production', or 'hybrid', got '{mode}'")
    _default_mode = mode
    logger.info(f"Default extractor mode set to: {mode}")


def get_default_mode() -> str:
    """Get the current default mode."""
    return _default_mode


class ExtractorFactory:
    """
    Factory for creating extractor instances.

    Manages the creation of extractors based on the configured mode,
    handling fallback from production to stub when needed.
    """

    def __init__(
        self,
        config: Optional[ExtractorConfig] = None,
        registry: Optional[ExtractorRegistry] = None,
    ):
        """
        Initialize the factory.

        Args:
            config: Extractor configuration (uses global config if not provided)
            registry: Extractor registry (uses global registry if not provided)
        """
        self.config = config or get_config()
        self.registry = registry or _registry

    def get_extractor(
        self,
        name: str,
        mode: Optional[str] = None,
        **kwargs
    ) -> ProductionExtractor:
        """
        Get an extractor instance.

        Args:
            name: Extractor name (e.g., 'email_auth', 'security_headers')
            mode: Override the default mode ('stub', 'production', 'hybrid')
            **kwargs: Additional arguments to pass to the extractor constructor

        Returns:
            Extractor instance

        Raises:
            ValueError: If no implementation is available
        """
        effective_mode = mode or self.config.mode or _default_mode

        if effective_mode == 'production':
            return self._get_production(name, **kwargs)
        elif effective_mode == 'stub':
            return self._get_stub(name, **kwargs)
        elif effective_mode == 'hybrid':
            return self._get_hybrid(name, **kwargs)
        else:
            raise ValueError(f"Unknown mode: {effective_mode}")

    def _get_production(self, name: str, **kwargs) -> ProductionExtractor:
        """Get production extractor, raise if not available."""
        extractor_class = self.registry.get(name, 'production')
        if extractor_class is None:
            raise ValueError(
                f"No production extractor registered for '{name}'. "
                f"Use mode='stub' or mode='hybrid' to fall back to stub."
            )
        return extractor_class(config=self.config.to_dict(), **kwargs)

    def _get_stub(self, name: str, **kwargs) -> ProductionExtractor:
        """Get stub extractor, raise if not available."""
        extractor_class = self.registry.get(name, 'stub')
        if extractor_class is None:
            raise ValueError(f"No stub extractor registered for '{name}'")
        # Stubs typically don't need config, but pass it anyway
        try:
            return extractor_class(config=self.config.to_dict(), **kwargs)
        except TypeError:
            # Stub might not accept config
            return extractor_class(**kwargs)

    def _get_hybrid(self, name: str, **kwargs) -> ProductionExtractor:
        """Get production if available, otherwise stub."""
        if self.registry.has_production(name):
            try:
                return self._get_production(name, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Failed to create production extractor '{name}': {e}. "
                    f"Falling back to stub."
                )
        return self._get_stub(name, **kwargs)

    def list_available(self) -> Dict[str, Dict[str, bool]]:
        """List all available extractors and their modes."""
        return self.registry.list_extractors()


# Global factory instance
_factory: Optional[ExtractorFactory] = None


def get_factory() -> ExtractorFactory:
    """Get the global extractor factory."""
    global _factory
    if _factory is None:
        _factory = ExtractorFactory()
    return _factory


def get_extractor(
    name: str,
    mode: Optional[str] = None,
    **kwargs
) -> ProductionExtractor:
    """
    Get an extractor instance.

    This is the main entry point for getting extractors.

    Args:
        name: Extractor name (e.g., 'email_auth', 'security_headers')
        mode: Override the default mode ('stub', 'production', 'hybrid')
        **kwargs: Additional arguments for the extractor

    Returns:
        Extractor instance

    Example:
        extractor = get_extractor('email_auth')
        result = extractor.extract('example.com')
    """
    return get_factory().get_extractor(name, mode, **kwargs)


def register_stub(name: str, extractor_class: ExtractorClass) -> None:
    """Register a stub extractor with the global registry."""
    _registry.register_stub(name, extractor_class)


def register_production(name: str, extractor_class: ExtractorClass) -> None:
    """Register a production extractor with the global registry."""
    _registry.register_production(name, extractor_class)


def register_loader(name: str, loader: Callable[[], None]) -> None:
    """Register a lazy loader for an extractor module."""
    _registry.register_loader(name, loader)


# ============================================================================
# Register lazy loaders for extractor modules
# ============================================================================

def _load_dns_extractors():
    """Lazy load DNS extractors."""
    try:
        from .dns import register_all
        register_all()
    except ImportError as e:
        logger.debug(f"Could not load DNS extractors: {e}")


def _load_http_extractors():
    """Lazy load HTTP extractors."""
    try:
        from .http import register_all
        register_all()
    except ImportError as e:
        logger.debug(f"Could not load HTTP extractors: {e}")


def _load_tls_extractors():
    """Lazy load TLS extractors."""
    try:
        from .tls import register_all
        register_all()
    except ImportError as e:
        logger.debug(f"Could not load TLS extractors: {e}")


# Register loaders for known extractor types
_dns_extractors = ['email_auth', 'dnssec', 'dns_records']
_http_extractors = ['security_headers', 'security_txt', 'waf_presence', 'cdn_usage']
_tls_extractors = ['tls_config', 'certificate_info']

for name in _dns_extractors:
    register_loader(name, _load_dns_extractors)

for name in _http_extractors:
    register_loader(name, _load_http_extractors)

for name in _tls_extractors:
    register_loader(name, _load_tls_extractors)

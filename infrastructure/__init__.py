"""
DSI Infrastructure

This package contains support systems and external integrations:
    - api: FastAPI REST API layer (requires 'api' extras)
    - db: Database layer (SQLAlchemy models, repositories)
    - analytics: Performance analytics and reporting
    - builder: LLM coverage builder tools
    - integrations: External integrations (email, documents, webhooks)
"""

__all__ = ["api", "db", "analytics", "builder", "integrations"]


def __getattr__(name):
    """Lazy import submodules to avoid hard dependency on optional packages."""
    if name in __all__:
        import importlib

        try:
            return importlib.import_module(f"infrastructure.{name}")
        except ImportError as e:
            raise ImportError(
                f"infrastructure.{name} requires additional dependencies. "
                f"Install with: pip install digital-signal-intelligence[{name}]"
            ) from e
    raise AttributeError(f"module 'infrastructure' has no attribute {name!r}")

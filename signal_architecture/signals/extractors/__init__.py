"""DSI Extractors — Production extractor package.

V6/E10: the stub package was moved to `tests/fixtures/stub_extractors/`
and is no longer re-exported from this package. Production code
imports directly from `signal_architecture.signals.extractors.production`
or via `signal_architecture.signals.extractors.resolver.get_extractor`.

Test-only code that needs stub fixtures should import directly from
`tests.fixtures.stub_extractors`.
"""

from .base import StubExtractor, utcnow

__all__ = ["StubExtractor", "utcnow"]

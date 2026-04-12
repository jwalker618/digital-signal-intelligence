"""Experience-based recalibration (Workstream C).

C-1 (Loss Data Ingestion) lives here as the data layer. C-2 (Recalibration
Engine) will add analysis modules. C-3 (Governance UI) will consume the
proposal API.
"""

from infrastructure.recalibration.linker import SignalLossLinker, LinkResult

__all__ = ["SignalLossLinker", "LinkResult"]

"""Experience-based recalibration (Workstream C).

C-1: Loss Data Ingestion
C-2: Recalibration Engine
C-3: Governance UI + deployer
"""

from infrastructure.recalibration.linker import SignalLossLinker, LinkResult
from infrastructure.recalibration.signal_analysis import SignalAnalyser
from infrastructure.recalibration.weight_optimiser import WeightOptimiser
from infrastructure.recalibration.tier_analysis import TierAnalyser
from infrastructure.recalibration.impact import ImpactAssessor
from infrastructure.recalibration.proposal import ProposalGenerator
from infrastructure.recalibration.engine import RecalibrationEngine
from infrastructure.recalibration.deployer import (
    DeploymentError,
    DeploymentResult,
    ProposalDeployer,
)
from infrastructure.recalibration.types import (
    Alignment,
    ImpactAssessment,
    ProposalStatus,
    RecalibrationProposalPayload,
    SignalReportCard,
    TierThresholdChange,
    WeightChange,
)

__all__ = [
    "SignalLossLinker",
    "LinkResult",
    "SignalAnalyser",
    "WeightOptimiser",
    "TierAnalyser",
    "ImpactAssessor",
    "ProposalGenerator",
    "RecalibrationEngine",
    "ProposalDeployer",
    "DeploymentResult",
    "DeploymentError",
    "Alignment",
    "ImpactAssessment",
    "ProposalStatus",
    "RecalibrationProposalPayload",
    "SignalReportCard",
    "TierThresholdChange",
    "WeightChange",
]

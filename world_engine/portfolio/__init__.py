"""WE-5: Portfolio Intelligence & Simulation.

Assembles per-entity Organisational Graphs into a Portfolio Graph for a
commercial entity. Detects concentration, feeds concentration into CAF,
evaluates the marginal impact of new submissions, and runs scenario
simulations.
"""

from world_engine.portfolio.types import (
    EntityImpact,
    LossRange,
    MarginalImpactResult,
    MitigationPath,
    PortfolioEdge,
    PortfolioGraph,
    PortfolioNode,
    ScenarioDefinition,
    ScenarioShock,
    SimulationResult,
    SystemicNode,
)
from world_engine.portfolio.graph_builder import PortfolioGraphBuilder
from world_engine.portfolio.concentration import ConcentrationDetector
from world_engine.portfolio.simulation import ScenarioSimulator
from world_engine.portfolio.marginal_impact import MarginalImpactAnalyser
from world_engine.portfolio.caf_enrichment import PortfolioCafEnricher

__all__ = [
    "PortfolioGraph",
    "PortfolioNode",
    "PortfolioEdge",
    "SystemicNode",
    "ScenarioDefinition",
    "ScenarioShock",
    "SimulationResult",
    "EntityImpact",
    "LossRange",
    "MitigationPath",
    "MarginalImpactResult",
    "PortfolioGraphBuilder",
    "ConcentrationDetector",
    "ScenarioSimulator",
    "MarginalImpactAnalyser",
    "PortfolioCafEnricher",
]

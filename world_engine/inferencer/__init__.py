"""WE-3b: Causal Inferencer.

Determines causal direction for correlated signal pairs (Granger causality)
and filters out relationships explained by confounders (partial correlation).
"""

from world_engine.inferencer.granger import CausalInferencer, GrangerConfig
from world_engine.inferencer.confound_control import ConfoundController

__all__ = ["CausalInferencer", "GrangerConfig", "ConfoundController"]

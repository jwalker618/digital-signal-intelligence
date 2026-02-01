"""
Organisational Graph - Propagation Algorithms

Graph operations defined in schemas/organisational_graph.yaml:
  - authority_propagation: PageRank through trust/ownership edges
  - risk_propagation: Weighted propagation through dependency/data_flow edges
  - exposure_aggregation: Weighted sum across jurisdictions/assets
  - cohort_comparison: Z-score based peer comparison
"""

from .algorithms import PropagationEngine

__all__ = ["PropagationEngine"]

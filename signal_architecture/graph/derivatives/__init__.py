"""
Organisational Graph - Behavioural Derivatives

Computed from signal time-series to detect early warning indicators.
These are the "leading indicators" described in the DSI Vision Paper.

Derivatives:
  - entropy: Control decay indicator
  - velocity: Operational overload indicator
  - drift: Peer divergence indicator
  - concentration: Single-point-of-failure indicator
  - fragility: Composite resilience indicator
"""

from .calculator import DerivativeCalculator

__all__ = ["DerivativeCalculator"]

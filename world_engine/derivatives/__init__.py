"""V6/D7 — Behavioural derivatives package.

Velocity + acceleration signals computed over rolling windows from
raw extractor outputs. The hiring velocity derivative is the first
concrete tenant; further derivatives land with Q4 drift + referral
wiring (E6).
"""
from .velocity import (  # noqa: F401
    HiringVelocityComputer,
    VelocityDetection,
    compute_velocity,
)

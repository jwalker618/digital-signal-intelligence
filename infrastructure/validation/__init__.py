"""
DSI Model Configuration Validation Framework (v2.0)

Comprehensive validation of coverage configurations against the
v2.0 master schema. Validates structure, consistency, and correctness.
"""

from .config_validator import ModelConfigValidator, ValidationReport

__all__ = ["ModelConfigValidator", "ValidationReport"]

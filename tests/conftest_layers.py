"""
DSI Technical Pricing Tests - Pytest Configuration

Shared fixtures and configuration for model layer tests.
"""

import pytest
import sys
from pathlib import Path

# Ensure all DSI packages are importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# COMMON FIXTURES
# =============================================================================

@pytest.fixture
def sample_entity_id():
    """Standard test entity ID."""
    return "test-entity-001"


@pytest.fixture
def sample_user():
    """Standard test user."""
    return "test_user"


@pytest.fixture
def sample_submission_data():
    """Standard submission data."""
    return {
        "entity_id": "test-entity-001",
        "tiv": 10000000,
        "revenue": 50000000,
        "fleet_size": 25
    }


@pytest.fixture
def sample_categorical_selections():
    """Standard categorical selections."""
    return {
        "operator_type": "major_airline",
        "fleet_category": "narrowbody"
    }


# =============================================================================
# PYTEST MARKERS
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )

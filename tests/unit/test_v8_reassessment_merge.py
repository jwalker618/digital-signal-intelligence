"""v8 Phase 5 -- re-assessment merge helper (pure function tests).

The full re-assessment path invokes the workflow engine; we don't
exercise that here (it needs a fully configured coverage etc., which
the integration smoke in Phase 7 covers). These tests confirm the
pure merge / coercion logic that prepares the workflow inputs.
"""
from __future__ import annotations

import pytest

from layers.risk.reassessment import (
    UnknownSignalError,
    merge_direct_query_responses,
)


class TestMergeDirectQueryResponses:
    def test_inserts_new_key(self):
        result = merge_direct_query_responses({}, "mfa_enabled", True)
        assert result == {"mfa_enabled": True}

    def test_overrides_existing_key(self):
        existing = {"mfa_enabled": False, "edr_deployed": True}
        result = merge_direct_query_responses(existing, "mfa_enabled", True)
        assert result == {"mfa_enabled": True, "edr_deployed": True}

    def test_existing_none_treated_as_empty(self):
        result = merge_direct_query_responses(None, "mfa_enabled", True)
        assert result == {"mfa_enabled": True}

    def test_does_not_mutate_input(self):
        existing = {"mfa_enabled": False}
        merge_direct_query_responses(existing, "mfa_enabled", True)
        # Input is untouched
        assert existing == {"mfa_enabled": False}

    def test_preserves_other_keys(self):
        existing = {"a": True, "b": False, "c": True}
        result = merge_direct_query_responses(existing, "b", True)
        assert result == {"a": True, "b": True, "c": True}


class TestBoolCoercion:
    """Brokers reply with various truthy / falsy shapes; we coerce to bool."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            (True, True),
            (False, False),
            (1, True),
            (0, False),
            ("true", True),
            ("True", True),
            ("YES", True),
            ("1", True),
            ("y", True),
            ("t", True),
            ("false", False),
            ("no", False),
            ("0", False),
            ("n", False),
            ("f", False),
        ],
    )
    def test_coercion(self, raw, expected):
        result = merge_direct_query_responses({}, "x", raw)
        assert result["x"] is expected
        assert isinstance(result["x"], bool)

    def test_falls_back_to_truthiness_for_unknown(self):
        # Empty list -> False
        result = merge_direct_query_responses({}, "x", [])
        assert result["x"] is False
        # Non-empty list -> True
        result2 = merge_direct_query_responses({}, "x", ["something"])
        assert result2["x"] is True


class TestUnknownSignalError:
    def test_class_exists(self):
        # Sanity: the error type is exported for callers to catch.
        assert issubclass(UnknownSignalError, ValueError)

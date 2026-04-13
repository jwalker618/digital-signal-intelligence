"""B-4: Audit log viewer -- pure helpers (no DB required)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from infrastructure.api.admin.audit_routes import (
    _event_to_dict,
    _stream_csv,
    _stream_json,
)


class TestEventToDict:
    def _fake_audit_row(self):
        row = MagicMock()
        row.id = "abc-123"
        row.tenant_id = "tenant-1"
        row.user_id = "user-1"
        row.session_id = None
        row.request_id = "req-1"
        row.action_type = "LOGIN"
        row.event_type = "login"
        row.event_action = "login"
        row.resource_type = "user"
        row.resource_code = "res-1"
        row.before_state = {"x": 1}
        row.after_state = {"x": 2}
        row.details = {"note": "test"}
        row.ip_address = "10.0.0.1"
        row.user_agent = "curl"
        row.duration_ms = 12.3
        row.created_at = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        return row

    def test_basic_fields(self):
        row = self._fake_audit_row()
        d = _event_to_dict(row)
        assert d["id"] == "abc-123"
        assert d["action_type"] == "LOGIN"
        assert d["resource_type"] == "user"
        assert d["resource_id"] == "res-1"   # renamed from resource_code
        assert d["before_state"] == {"x": 1}
        assert d["created_at"].startswith("2026-04-12")

    def test_none_timestamp(self):
        row = self._fake_audit_row()
        row.created_at = None
        d = _event_to_dict(row)
        assert d["created_at"] is None

    def test_none_tenant_id(self):
        row = self._fake_audit_row()
        row.tenant_id = None
        d = _event_to_dict(row)
        assert d["tenant_id"] is None


class TestCsvStreamChunks:
    """Verify _stream_csv produces valid CSV output with header + one row."""

    def test_single_row_stream(self):
        # Mock AuditService.query to return one event then empty
        row = MagicMock()
        row.id = "abc"
        row.tenant_id = "t"
        row.user_id = "u"
        row.session_id = None
        row.request_id = "r"
        row.action_type = "LOGIN"
        row.event_type = "login"
        row.event_action = "login"
        row.resource_type = "x"
        row.resource_code = "y"
        row.before_state = None
        row.after_state = None
        row.details = None
        row.ip_address = None
        row.user_agent = None
        row.duration_ms = None
        row.created_at = datetime(2026, 4, 12, tzinfo=timezone.utc)

        svc = MagicMock()
        svc.query.side_effect = [
            ([row], None),  # first page
        ]

        chunks = list(_stream_csv(
            svc, "tenant-1",
            None, None, None, None, None, None,
            max_rows=10,
        ))
        assembled = "".join(chunks)
        lines = assembled.splitlines()
        assert lines[0].startswith("id,created_at,action_type")
        assert any("abc" in l for l in lines[1:])


class TestJsonStream:
    def test_json_wraps_array(self):
        svc = MagicMock()
        svc.query.return_value = ([], None)
        chunks = list(_stream_json(
            svc, "tenant-1",
            None, None, None, None, None, None,
            max_rows=10,
        ))
        body = "".join(chunks)
        assert body == "[]"

    def test_json_produces_valid_array_with_commas(self):
        row = MagicMock()
        row.id = "a"
        row.tenant_id = "t"
        row.user_id = None
        row.session_id = None
        row.request_id = None
        row.action_type = "LOGIN"
        row.event_type = "login"
        row.event_action = "login"
        row.resource_type = None
        row.resource_code = None
        row.before_state = None
        row.after_state = None
        row.details = {}
        row.ip_address = None
        row.user_agent = None
        row.duration_ms = None
        row.created_at = datetime(2026, 4, 12, tzinfo=timezone.utc)

        svc = MagicMock()
        svc.query.side_effect = [
            ([row, row], None),
        ]
        chunks = list(_stream_json(
            svc, "tenant-1",
            None, None, None, None, None, None,
            max_rows=10,
        ))
        body = "".join(chunks)
        import json as _json
        parsed = _json.loads(body)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

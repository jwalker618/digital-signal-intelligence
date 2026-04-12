"""C-1d: Loss import parsing tests (no DB required)."""

import json

import pytest

from infrastructure.api.routes.losses import _coerce_types, _parse_import


class TestCoerceTypes:
    def test_empty_strings_dropped(self):
        raw = {"entity_name": "X", "notes": ""}
        out = _coerce_types(raw)
        assert out == {"entity_name": "X"}  # empty notes dropped

    def test_float_fields(self):
        raw = {"incurred_amount": "1234.56", "paid_amount": "0"}
        out = _coerce_types(raw)
        assert out["incurred_amount"] == 1234.56
        assert out["paid_amount"] == 0.0
        assert isinstance(out["incurred_amount"], float)

    def test_date_fields(self):
        raw = {"loss_date": "2026-03-15T00:00:00"}
        out = _coerce_types(raw)
        assert str(out["loss_date"]) == "2026-03-15 00:00:00"

    def test_json_metadata(self):
        raw = {"event_metadata": '{"key": "value"}'}
        out = _coerce_types(raw)
        assert out["event_metadata"] == {"key": "value"}

    def test_passthrough_strings(self):
        raw = {"entity_name": "Acme", "coverage": "cyber"}
        out = _coerce_types(raw)
        assert out == {"entity_name": "Acme", "coverage": "cyber"}


class TestParseImport:
    def test_csv(self):
        content = b"entity_name,coverage,loss_date,loss_type,incurred_amount\n"
        content += b"Acme,cyber,2026-03-15T00:00:00,breach,1000\n"
        content += b"Beta,cyber,2026-04-01T00:00:00,ransomware,5000\n"
        rows = _parse_import(content, "losses.csv")
        assert len(rows) == 2
        assert rows[0]["entity_name"] == "Acme"
        assert rows[0]["incurred_amount"] == 1000.0

    def test_csv_with_bom(self):
        """Excel exports CSVs with a UTF-8 BOM -- we must tolerate it."""
        content = b"\xef\xbb\xbfentity_name,coverage,loss_date,loss_type,incurred_amount\n"
        content += b"Acme,cyber,2026-03-15T00:00:00,breach,1000\n"
        rows = _parse_import(content, "losses.csv")
        assert len(rows) == 1
        assert rows[0]["entity_name"] == "Acme"  # no BOM leakage into first key

    def test_json_array(self):
        data = json.dumps([
            {"entity_name": "Acme", "coverage": "cyber", "loss_date": "2026-03-15T00:00:00",
             "loss_type": "breach", "incurred_amount": 1000},
        ]).encode()
        rows = _parse_import(data, "losses.json")
        assert len(rows) == 1
        assert rows[0]["entity_name"] == "Acme"

    def test_json_non_array_rejected(self):
        data = json.dumps({"entity_name": "Acme"}).encode()
        with pytest.raises(ValueError):
            _parse_import(data, "losses.json")

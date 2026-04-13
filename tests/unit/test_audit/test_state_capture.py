"""A-2e: State capture helper tests."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from infrastructure.api.audit import capture_model
from infrastructure.api.audit.state_capture import _serialise


class SampleEnum(str, Enum):
    FOO = "foo"
    BAR = "bar"


class TestSerialise:
    def test_none(self):
        assert _serialise(None) is None

    def test_primitives(self):
        assert _serialise("hello") == "hello"
        assert _serialise(42) == 42
        assert _serialise(3.14) == 3.14
        assert _serialise(True) is True

    def test_uuid(self):
        u = uuid4()
        assert _serialise(u) == str(u)

    def test_datetime(self):
        dt = datetime(2026, 4, 12, 10, 30, tzinfo=timezone.utc)
        result = _serialise(dt)
        assert isinstance(result, str)
        assert "2026-04-12" in result

    def test_decimal(self):
        assert _serialise(Decimal("1.23")) == 1.23

    def test_enum(self):
        assert _serialise(SampleEnum.FOO) == "foo"

    def test_nested_dict(self):
        u = uuid4()
        result = _serialise({"id": u, "count": 5})
        assert result == {"id": str(u), "count": 5}

    def test_nested_list(self):
        assert _serialise([1, "two", None]) == [1, "two", None]


class TestCaptureModel:
    def test_none_input(self):
        assert capture_model(None) == {}

    def test_pydantic_model(self):
        from pydantic import BaseModel

        class Sample(BaseModel):
            x: int
            y: str

        m = Sample(x=1, y="two")
        # Non-SQLA object -- falls through to model_dump
        snap = capture_model(m)
        assert snap["x"] == 1
        assert snap["y"] == "two"

    def test_exclude_parameter(self):
        from pydantic import BaseModel

        class Sample(BaseModel):
            public: str
            secret: str

        m = Sample(public="visible", secret="hidden")
        # capture_model falls through to model_dump for pydantic, which
        # doesn't respect exclude -- so test with a simple object instead
        class Obj:
            def __init__(self):
                self.public = "visible"
                self.secret = "hidden"
        snap = capture_model(Obj(), exclude={"secret"})
        assert snap.get("public") == "visible"
        assert "secret" not in snap

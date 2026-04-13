"""C-1d: Loss request/response schema validation tests."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from infrastructure.api.routes.losses import (
    LossEventCreate,
    LossEventUpdate,
)


class TestLossEventCreate:
    def test_minimal_valid(self):
        body = LossEventCreate(
            entity_name="Acme",
            coverage="cyber",
            loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            loss_type="data_breach",
            incurred_amount=100.0,
        )
        assert body.entity_name == "Acme"
        assert body.status == "OPEN"
        assert body.currency == "USD"
        assert body.paid_amount == 0.0

    def test_status_normalisation(self):
        body = LossEventCreate(
            entity_name="Acme", coverage="cyber",
            loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            loss_type="x", incurred_amount=1.0, status="open",
        )
        assert body.status == "OPEN"  # uppercase

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            LossEventCreate(
                entity_name="Acme", coverage="cyber",
                loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
                loss_type="x", incurred_amount=1.0, status="INVALID",
            )

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            LossEventCreate(
                entity_name="Acme", coverage="cyber",
                loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
                loss_type="x", incurred_amount=-1.0,
            )

    def test_empty_entity_name_rejected(self):
        with pytest.raises(ValidationError):
            LossEventCreate(
                entity_name="", coverage="cyber",
                loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
                loss_type="x", incurred_amount=1.0,
            )

    def test_currency_length(self):
        # Must be exactly 3 chars
        with pytest.raises(ValidationError):
            LossEventCreate(
                entity_name="A", coverage="cyber",
                loss_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
                loss_type="x", incurred_amount=1.0, currency="US",
            )


class TestLossEventUpdate:
    def test_all_optional(self):
        body = LossEventUpdate()
        assert body.model_dump(exclude_unset=True) == {}

    def test_partial_update(self):
        body = LossEventUpdate(status="CLOSED", paid_amount=100.0)
        dumped = body.model_dump(exclude_unset=True)
        assert dumped == {"status": "CLOSED", "paid_amount": 100.0}

    def test_status_validation(self):
        with pytest.raises(ValidationError):
            LossEventUpdate(status="BOGUS")

    def test_status_normalisation(self):
        body = LossEventUpdate(status="closed")
        assert body.status == "CLOSED"

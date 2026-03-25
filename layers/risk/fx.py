"""
FX Conversion Layer — Currency I/O for Technical Pricing

All technical pricing is performed in USD internally. This module converts
submission monetary values from the submission's currency to USD before
pricing, and converts the output premium back to the original currency.

The FX rate source is pluggable — the default implementation uses static
reference rates suitable for development and testing. Production deployments
should register a live rate provider (ECB, Bloomberg, etc.).

Usage:
    from layers.risk.fx import FXConverter, convert_submission_to_usd

    converter = FXConverter()
    usd_data, fx_context = converter.to_usd(submission_data, source_currency="GBP")
    # ... run pricing in USD ...
    local_premium = converter.from_usd(premium_usd, target_currency="GBP", fx_context=fx_context)

Design principles:
    - All internal pricing, calibration, analytics, and monitoring use USD
    - Currency is an I/O concern — the pricer never sees non-USD values
    - FX context (rate, source, date) is captured for full audit trail
    - No submission is rejected for currency — anything converts
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger("dsi.fx")


# =============================================================================
# CURRENCY ENUM
# =============================================================================

class Currency(str, Enum):
    """ISO 4217 currency codes supported by DSI."""
    USD = "USD"
    GBP = "GBP"
    EUR = "EUR"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    JPY = "JPY"
    SGD = "SGD"
    HKD = "HKD"
    NZD = "NZD"
    SEK = "SEK"
    NOK = "NOK"
    DKK = "DKK"
    ZAR = "ZAR"
    BRL = "BRL"
    MXN = "MXN"
    INR = "INR"
    CNY = "CNY"
    KRW = "KRW"
    AED = "AED"


# =============================================================================
# FX CONTEXT — audit trail for every conversion
# =============================================================================

@dataclass
class FXContext:
    """Captures the FX conversion details for audit trail."""
    source_currency: str
    target_currency: str = "USD"
    rate: float = 1.0               # source → target rate
    inverse_rate: float = 1.0       # target → source rate
    rate_source: str = "static"     # e.g., "ecb_daily", "bloomberg", "static"
    rate_date: str = ""             # ISO date of the rate
    converted_at: str = ""          # ISO timestamp of conversion
    monetary_fields_converted: List[str] = field(default_factory=list)


# =============================================================================
# RATE PROVIDER INTERFACE
# =============================================================================

class FXRateProvider(Protocol):
    """Interface for FX rate providers.

    Implementations should return the rate to convert 1 unit of
    source_currency into target_currency.
    """

    def get_rate(
        self,
        source_currency: str,
        target_currency: str,
        as_of: Optional[date] = None,
    ) -> float:
        ...

    @property
    def source_name(self) -> str:
        ...


# =============================================================================
# STATIC RATE PROVIDER (development / testing)
# =============================================================================

class StaticRateProvider:
    """Static reference rates for development and testing.

    These are approximate mid-market rates and should NOT be used for
    production pricing. Register a live provider for production.
    """

    # Rates: 1 USD = X foreign currency (USD-based cross rates)
    _RATES_PER_USD: Dict[str, float] = {
        "USD": 1.0,
        "GBP": 0.79,
        "EUR": 0.92,
        "CAD": 1.36,
        "AUD": 1.53,
        "CHF": 0.88,
        "JPY": 149.5,
        "SGD": 1.34,
        "HKD": 7.82,
        "NZD": 1.67,
        "SEK": 10.5,
        "NOK": 10.8,
        "DKK": 6.88,
        "ZAR": 18.2,
        "BRL": 5.05,
        "MXN": 17.1,
        "INR": 83.5,
        "CNY": 7.24,
        "KRW": 1330.0,
        "AED": 3.67,
    }

    def get_rate(
        self,
        source_currency: str,
        target_currency: str,
        as_of: Optional[date] = None,
    ) -> float:
        """Return rate to convert 1 source_currency → target_currency."""
        source = source_currency.upper()
        target = target_currency.upper()

        if source == target:
            return 1.0

        # Convert source → USD → target
        source_per_usd = self._RATES_PER_USD.get(source)
        target_per_usd = self._RATES_PER_USD.get(target)

        if source_per_usd is None:
            raise ValueError(f"Unsupported currency: {source}")
        if target_per_usd is None:
            raise ValueError(f"Unsupported currency: {target}")

        # 1 source = (1 / source_per_usd) USD = (target_per_usd / source_per_usd) target
        return target_per_usd / source_per_usd

    @property
    def source_name(self) -> str:
        return "static_reference"


# =============================================================================
# FX CONVERTER
# =============================================================================

# Submission fields that contain monetary values and should be converted
MONETARY_FIELDS = frozenset({
    "limit",
    "deductible",
    "revenue",
    "tiv",
    "hull_value",
    "total_assets",
    "aggregate_limit",
    "min_premium_override",
})


class FXConverter:
    """Converts submission monetary values between currencies.

    All technical pricing runs in USD. This converter:
    1. Converts submission monetary fields from source currency to USD (pre-pricing)
    2. Converts premium outputs from USD back to source currency (post-pricing)
    3. Captures full audit trail in FXContext
    """

    def __init__(self, provider: Optional[FXRateProvider] = None):
        self._provider = provider or StaticRateProvider()

    def to_usd(
        self,
        submission_data: Dict[str, Any],
        source_currency: str,
    ) -> tuple[Dict[str, Any], FXContext]:
        """Convert monetary fields in submission_data from source_currency to USD.

        Args:
            submission_data: Original submission with monetary values in source_currency.
            source_currency: ISO 4217 code (e.g., "GBP", "EUR").

        Returns:
            Tuple of (converted_data, fx_context).
            converted_data is a new dict with monetary fields in USD.
            fx_context captures the conversion details for audit trail.
        """
        source = source_currency.upper()

        if source == "USD":
            return dict(submission_data), FXContext(
                source_currency="USD",
                target_currency="USD",
                rate=1.0,
                inverse_rate=1.0,
                rate_source=self._provider.source_name,
                rate_date=date.today().isoformat(),
                converted_at=datetime.utcnow().isoformat(),
            )

        rate = self._provider.get_rate(source, "USD")
        inverse_rate = self._provider.get_rate("USD", source)

        converted = dict(submission_data)
        fields_converted = []

        for field_name in MONETARY_FIELDS:
            if field_name in converted and isinstance(converted[field_name], (int, float)):
                original = converted[field_name]
                converted[field_name] = round(original * rate, 2)
                fields_converted.append(field_name)

        context = FXContext(
            source_currency=source,
            target_currency="USD",
            rate=rate,
            inverse_rate=inverse_rate,
            rate_source=self._provider.source_name,
            rate_date=date.today().isoformat(),
            converted_at=datetime.utcnow().isoformat(),
            monetary_fields_converted=fields_converted,
        )

        logger.info(
            "FX conversion %s→USD: rate=%.6f, fields=%s",
            source, rate, fields_converted,
        )

        return converted, context

    def from_usd(
        self,
        amount_usd: float,
        target_currency: str,
        fx_context: Optional[FXContext] = None,
    ) -> float:
        """Convert a USD amount to target currency.

        If fx_context is provided, uses the inverse rate captured during
        to_usd() to ensure consistency (same rate for input and output).

        Args:
            amount_usd: Amount in USD.
            target_currency: ISO 4217 code to convert to.
            fx_context: Optional context from to_usd() for rate consistency.

        Returns:
            Amount in target currency.
        """
        target = target_currency.upper()

        if target == "USD":
            return amount_usd

        if fx_context and fx_context.source_currency.upper() == target:
            # Use the inverse rate from the same conversion for consistency
            rate = fx_context.inverse_rate
        else:
            rate = self._provider.get_rate("USD", target)

        return round(amount_usd * rate, 2)


# =============================================================================
# MODULE-LEVEL SINGLETON
# =============================================================================

_default_converter: Optional[FXConverter] = None


def get_fx_converter() -> FXConverter:
    """Get or create the default FX converter."""
    global _default_converter
    if _default_converter is None:
        _default_converter = FXConverter()
    return _default_converter


def set_fx_provider(provider: FXRateProvider) -> None:
    """Register a custom FX rate provider (e.g., for production)."""
    global _default_converter
    _default_converter = FXConverter(provider=provider)

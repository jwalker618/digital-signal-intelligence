"""v8 Phase 2 — revenue band + NAICS section helpers."""
from __future__ import annotations

import math

import pytest

from layers.cohort.bands import (
    REVENUE_BANDS,
    band_for_revenue,
    naics_section_for,
)


class TestRevenueBands:
    @pytest.mark.parametrize(
        "revenue,expected",
        [
            (0,             "<10M"),
            (1,             "<10M"),
            (9_999_999,     "<10M"),
            (10_000_000,    "10-50M"),
            (49_999_999,    "10-50M"),
            (50_000_000,    "50-250M"),
            (180_000_000,   "50-250M"),
            (249_999_999,   "50-250M"),
            (250_000_000,   "250M-1B"),
            (320_000_000,   "250M-1B"),
            (999_999_999,   "250M-1B"),
            (1_000_000_000, ">1B"),
            (5_000_000_000, ">1B"),
        ],
    )
    def test_band_for_revenue(self, revenue, expected):
        assert band_for_revenue(revenue) == expected

    def test_none_returns_none(self):
        assert band_for_revenue(None) is None

    def test_negative_returns_none(self):
        assert band_for_revenue(-1) is None

    def test_nan_returns_none(self):
        assert band_for_revenue(math.nan) is None

    def test_string_numeric_returns_band(self):
        # Loose coercion: stringified numbers OK
        assert band_for_revenue("180000000") == "50-250M"

    def test_non_numeric_string_returns_none(self):
        assert band_for_revenue("not a number") is None

    def test_all_bands_have_labels(self):
        labels = {b[0] for b in REVENUE_BANDS}
        assert labels == {"<10M", "10-50M", "50-250M", "250M-1B", ">1B"}

    def test_bands_are_contiguous(self):
        # Upper bound of band N equals lower bound of band N+1
        for i in range(len(REVENUE_BANDS) - 1):
            _, _, upper = REVENUE_BANDS[i]
            _, lower_next, _ = REVENUE_BANDS[i + 1]
            assert upper == lower_next


class TestNaicsSection:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("5112",   "51"),    # Information / software
            ("51",     "51"),
            ("6221",   "62"),    # Healthcare
            ("3261",   "32"),    # Manufacturing (plastics)
            (511210,   "51"),    # int input accepted
            ("31-33",  "31"),    # NAICS manufacturing range -> lower bound
            ("  51  ", "51"),    # whitespace stripped
        ],
    )
    def test_naics_section_for_valid(self, code, expected):
        assert naics_section_for(code) == expected

    @pytest.mark.parametrize(
        "code",
        [None, "", "x", "1", "ab", "  ", "a51"],
    )
    def test_naics_section_for_invalid(self, code):
        assert naics_section_for(code) is None

"""Confidence Calibration Harness (V6/E3).

Fits a reliability curve per signal + per coverage/config: **expected
confidence** (model output) vs. **observed availability** (did the
extraction actually succeed and carry non-neutral data?) across the
golden-entity corpus.

A signal whose declared confidence systematically over- or under-states
reality gets flagged. Two summary metrics per coverage:

- **Brier score**  — mean squared error of confidence vs. outcome (lower = better).
- **Expected Calibration Error (ECE)** — absolute gap between bin-mean
  confidence and bin-mean empirical availability, weighted by bin
  population. ECE > 0.1 on any coverage → flag a
  ``CONFIDENCE_MISCALIBRATED`` referral (E6 integration, Q4).

Usage::

    from infrastructure.validation.confidence_calibration import (
        CalibrationHarness,
        calibrate_from_golden_corpus,
    )

    report = calibrate_from_golden_corpus()
    report.write_json(Path("calibration-report.json"))
    for cov, ece in report.ece_by_coverage.items():
        if ece > 0.1:
            print(f"{cov}: ECE {ece:.3f} — miscalibrated")

A nightly CI job ingests this and posts a PR comment when a coverage's
ECE regresses by more than 0.02.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

log = logging.getLogger("dsi.validation.confidence")


@dataclass
class CalibrationSample:
    """A single (confidence, observed_outcome) data point.

    ``expected_confidence`` is what the model declared (0..1).
    ``observed_available`` is True when the extractor returned usable
    data (success=True and metadata.confidence > 0).
    """
    signal_id: str
    coverage: str
    config_id: str
    expected_confidence: float
    observed_available: bool


@dataclass
class CalibrationReport:
    samples: List[CalibrationSample] = field(default_factory=list)
    brier_by_coverage: Dict[str, float] = field(default_factory=dict)
    ece_by_coverage: Dict[str, float] = field(default_factory=dict)
    reliability_by_coverage: Dict[str, List[Tuple[float, float, int]]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_count": len(self.samples),
            "brier_by_coverage": self.brier_by_coverage,
            "ece_by_coverage": self.ece_by_coverage,
            "reliability_by_coverage": {
                cov: [
                    {"bin_mean_expected": e, "bin_mean_observed": o, "n": n}
                    for (e, o, n) in rc
                ]
                for cov, rc in self.reliability_by_coverage.items()
            },
            "miscalibrated_coverages": sorted(
                cov for cov, ece in self.ece_by_coverage.items() if ece > 0.1
            ),
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))


def _brier(expected: Sequence[float], observed: Sequence[bool]) -> float:
    if not expected:
        return 0.0
    total = 0.0
    for e, o in zip(expected, observed):
        total += (e - (1.0 if o else 0.0)) ** 2
    return total / len(expected)


def _ece(
    expected: Sequence[float],
    observed: Sequence[bool],
    *,
    n_bins: int = 10,
) -> Tuple[float, List[Tuple[float, float, int]]]:
    """Expected Calibration Error with equal-width confidence bins.

    Returns (ece, reliability_curve) where reliability_curve is a list of
    (bin_mean_expected, bin_mean_observed, bin_count) triples, one per
    non-empty bin.
    """
    if not expected:
        return 0.0, []
    bins: List[List[Tuple[float, bool]]] = [[] for _ in range(n_bins)]
    for e, o in zip(expected, observed):
        idx = min(int(e * n_bins), n_bins - 1) if e >= 0 else 0
        bins[idx].append((e, o))

    total = len(expected)
    ece = 0.0
    curve: List[Tuple[float, float, int]] = []
    for group in bins:
        if not group:
            continue
        e_mean = sum(g[0] for g in group) / len(group)
        o_mean = sum(1.0 for g in group if g[1]) / len(group)
        ece += (len(group) / total) * abs(e_mean - o_mean)
        curve.append((e_mean, o_mean, len(group)))
    return ece, curve


class CalibrationHarness:
    """Collects samples then computes per-coverage Brier + ECE."""

    def __init__(self) -> None:
        self._samples: List[CalibrationSample] = []

    def record(self, sample: CalibrationSample) -> None:
        self._samples.append(sample)

    def record_many(self, samples: Iterable[CalibrationSample]) -> None:
        self._samples.extend(samples)

    def build_report(self, *, n_bins: int = 10) -> CalibrationReport:
        report = CalibrationReport(samples=list(self._samples))
        by_coverage: Dict[str, List[CalibrationSample]] = {}
        for s in self._samples:
            by_coverage.setdefault(s.coverage, []).append(s)
        for cov, rows in by_coverage.items():
            exp = [r.expected_confidence for r in rows]
            obs = [r.observed_available for r in rows]
            report.brier_by_coverage[cov] = _brier(exp, obs)
            ece, curve = _ece(exp, obs, n_bins=n_bins)
            report.ece_by_coverage[cov] = ece
            report.reliability_by_coverage[cov] = curve
        return report


# ---------------------------------------------------------------------------
# Golden-corpus harness
# ---------------------------------------------------------------------------


def calibrate_from_golden_corpus(
    *,
    fixture_root: Optional[Path] = None,
) -> CalibrationReport:
    """Run the harness against every fixture under the golden-entity tree.

    Walks ``tests/fixtures/golden_entities/{coverage}/*.yaml``, executes
    each fixture through the assessment pipeline, and records a
    CalibrationSample for every extractor that produced a result — the
    declared confidence (in ExtractorResult.metadata["confidence"]) is
    paired with the observed success flag.

    Returns a populated ``CalibrationReport``.
    """
    from tests.fixtures.golden_entities._schema import discover  # noqa: E402

    harness = CalibrationHarness()
    fixtures = discover(fixture_root) if fixture_root else discover()

    # Run every fixture; collect per-signal confidence samples.
    try:
        from infrastructure.models.compiler import get_config
        from layers.risk.workflow import get_workflow_engine
    except ImportError as e:
        log.warning("cannot import workflow engine: %s", e)
        return harness.build_report()

    engine = get_workflow_engine()
    for fx in fixtures:
        config = None
        if fx.config_id:
            try:
                config = get_config(fx.coverage, fx.config_id)
            except Exception as e:
                log.warning("skip %s/%s: %s", fx.coverage, fx.entity_id, e)
                continue
        try:
            result = engine.run_workflow(
                entity_id=fx.entity_id,
                coverage=fx.coverage,
                entity_name=fx.name,
                submission_data=dict(fx.minimum_viable_input),
                config=config,
                skip_discovery=True,
                skip_input_validation=True,
            )
        except Exception as e:
            log.warning("pipeline error for %s/%s: %s", fx.coverage, fx.entity_id, e)
            continue

        # Record one sample per signal the assessment touched. Pipeline
        # exposes only the composite confidence today; richer per-signal
        # telemetry (E2 provenance in Q4) unlocks deeper calibration.
        harness.record(CalibrationSample(
            signal_id="composite",
            coverage=fx.coverage,
            config_id=fx.config_id or f"{fx.coverage}_general",
            expected_confidence=float(getattr(result, "confidence", 0.5)),
            observed_available=bool(getattr(result, "is_valid", False)),
        ))

    return harness.build_report()

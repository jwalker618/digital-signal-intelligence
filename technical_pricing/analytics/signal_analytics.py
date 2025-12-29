"""
DSI Signal Analytics (Phase 9)

Signal quality and coverage analysis for monitoring
signal extraction health and performance.
"""

import logging
import statistics
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from .portfolio_types import (
    SignalCoverageReport,
    SignalDistribution,
    SignalDistributions,
    SignalIssue,
)


logger = logging.getLogger("dsi.analytics.signals")


@dataclass
class SignalRecord:
    """Record of signal extraction for analysis."""
    entity_id: str
    model_id: str
    coverage: str
    signal_id: str
    signal_name: str
    group_id: str

    # Extraction result
    extracted: bool = True
    score: Optional[float] = None
    confidence: float = 1.0

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    from_cache: bool = False


# Import dataclass
from dataclasses import dataclass, field


class SignalAnalytics:
    """
    Signal quality and coverage analysis.

    Monitors:
    - Signal extraction coverage (% successfully extracted)
    - Score distributions
    - Quality issues (low coverage, high error rates)
    - Drift detection
    """

    def __init__(self, coverage_threshold: float = 0.80):
        """
        Initialize SignalAnalytics.

        Args:
            coverage_threshold: Minimum acceptable coverage rate
        """
        self.coverage_threshold = coverage_threshold
        self._signal_records: List[SignalRecord] = []

    def record_signals(self, records: List[SignalRecord]) -> None:
        """Record signal extraction data."""
        self._signal_records.extend(records)

    def record_from_model_version(
        self,
        model_version: Any,  # ModelVersion from model.types
    ) -> None:
        """
        Record signals from a completed model version.

        Extracts signal data from a workflow result.
        """
        for output in model_version.signal_outputs:
            self._signal_records.append(SignalRecord(
                entity_id=model_version.entity_id,
                model_id=model_version.model_id,
                coverage=model_version.coverage,
                signal_id=output.signal_id,
                signal_name=output.signal_name,
                group_id=output.group_id,
                extracted=output.error is None,
                score=output.raw_score if output.error is None else None,
                confidence=output.confidence,
                extracted_at=output.extracted_at,
                execution_time_ms=output.execution_time_ms,
                error=output.error,
                from_cache=output.from_cache,
            ))

    def get_signal_coverage(
        self,
        coverage: str,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> SignalCoverageReport:
        """
        Get signal extraction coverage report.

        Args:
            coverage: Coverage type to analyze
            date_range: Period to analyze

        Returns:
            SignalCoverageReport with coverage percentages
        """
        records = self._filter_records(coverage, date_range)

        if not records:
            return SignalCoverageReport(coverage=coverage)

        # Overall coverage
        total = len(records)
        extracted = sum(1 for r in records if r.extracted)
        overall = extracted / total if total > 0 else 0.0

        # By group
        group_stats: Dict[str, Dict[str, int]] = {}
        for r in records:
            if r.group_id not in group_stats:
                group_stats[r.group_id] = {"total": 0, "extracted": 0}
            group_stats[r.group_id]["total"] += 1
            if r.extracted:
                group_stats[r.group_id]["extracted"] += 1

        group_coverage = {
            gid: stats["extracted"] / stats["total"] if stats["total"] > 0 else 0.0
            for gid, stats in group_stats.items()
        }

        # By signal
        signal_stats: Dict[str, Dict[str, int]] = {}
        for r in records:
            if r.signal_id not in signal_stats:
                signal_stats[r.signal_id] = {"total": 0, "extracted": 0}
            signal_stats[r.signal_id]["total"] += 1
            if r.extracted:
                signal_stats[r.signal_id]["extracted"] += 1

        signal_coverage = {
            sid: stats["extracted"] / stats["total"] if stats["total"] > 0 else 0.0
            for sid, stats in signal_stats.items()
        }

        # Identify issues
        low_coverage = [
            sid for sid, cov in signal_coverage.items()
            if cov < self.coverage_threshold
        ]
        failing = [
            sid for sid, cov in signal_coverage.items()
            if cov < 0.5
        ]

        # Get unique model count for sample size
        sample_size = len(set(r.model_id for r in records))

        return SignalCoverageReport(
            coverage=coverage,
            period=self._format_period(date_range),
            sample_size=sample_size,
            overall_coverage=overall,
            group_coverage=group_coverage,
            signal_coverage=signal_coverage,
            low_coverage_signals=low_coverage,
            failing_signals=failing,
        )

    def get_signal_distributions(
        self,
        coverage: str,
        signal_group: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> SignalDistributions:
        """
        Get score distributions by signal.

        Args:
            coverage: Coverage type
            signal_group: Optional group filter
            date_range: Period to analyze

        Returns:
            SignalDistributions with statistics per signal
        """
        records = self._filter_records(coverage, date_range)

        if signal_group:
            records = [r for r in records if r.group_id == signal_group]

        # Group scores by signal
        signal_scores: Dict[str, List[float]] = {}
        signal_names: Dict[str, str] = {}

        for r in records:
            if r.score is not None:
                if r.signal_id not in signal_scores:
                    signal_scores[r.signal_id] = []
                    signal_names[r.signal_id] = r.signal_name
                signal_scores[r.signal_id].append(r.score)

        distributions: Dict[str, SignalDistribution] = {}

        for signal_id, scores in signal_scores.items():
            if len(scores) < 5:
                continue

            sorted_scores = sorted(scores)
            n = len(sorted_scores)

            distributions[signal_id] = SignalDistribution(
                signal_id=signal_id,
                signal_name=signal_names.get(signal_id, signal_id),
                count=n,
                mean=statistics.mean(scores),
                median=statistics.median(scores),
                std_dev=statistics.stdev(scores) if n > 1 else 0.0,
                min_value=min(scores),
                max_value=max(scores),
                p10=sorted_scores[int(n * 0.10)],
                p25=sorted_scores[int(n * 0.25)],
                p75=sorted_scores[int(n * 0.75)],
                p90=sorted_scores[int(n * 0.90)],
                histogram=self._build_histogram(scores),
            )

        return SignalDistributions(
            coverage=coverage,
            group=signal_group,
            distributions=distributions,
        )

    def identify_signal_issues(
        self,
        coverage: str,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> List[SignalIssue]:
        """
        Find signals with quality issues.

        Checks for:
        - Low extraction coverage
        - High error rates
        - Low variance (not discriminating)
        - Drift from historical patterns

        Args:
            coverage: Coverage type
            date_range: Period to analyze

        Returns:
            List of SignalIssue findings
        """
        issues: List[SignalIssue] = []

        coverage_report = self.get_signal_coverage(coverage, date_range)
        distributions = self.get_signal_distributions(coverage, date_range=date_range)

        # Low coverage issues
        for signal_id in coverage_report.low_coverage_signals:
            cov_rate = coverage_report.signal_coverage.get(signal_id, 0.0)
            severity = "critical" if cov_rate < 0.5 else "warning"

            issues.append(SignalIssue(
                signal_id=signal_id,
                issue_type="low_coverage",
                severity=severity,
                description=f"Signal extraction coverage is {cov_rate:.1%}",
                metric_value=cov_rate,
                threshold=self.coverage_threshold,
                recommendation="Check signal extractor, data source availability, or signal definition",
            ))

        # Low variance issues
        for signal_id, dist in distributions.distributions.items():
            if dist.std_dev < 5.0 and dist.count > 20:
                issues.append(SignalIssue(
                    signal_id=signal_id,
                    signal_name=dist.signal_name,
                    issue_type="low_variance",
                    severity="warning",
                    description=f"Signal has very low variance (std={dist.std_dev:.2f})",
                    metric_value=dist.std_dev,
                    threshold=5.0,
                    recommendation="Signal may not be discriminating between risks effectively",
                ))

        # Extreme values (possible data quality issue)
        for signal_id, dist in distributions.distributions.items():
            if dist.max_value > 100 or dist.min_value < 0:
                issues.append(SignalIssue(
                    signal_id=signal_id,
                    signal_name=dist.signal_name,
                    issue_type="value_range",
                    severity="info",
                    description=f"Signal has values outside expected 0-100 range ({dist.min_value:.0f} to {dist.max_value:.0f})",
                    metric_value=dist.max_value,
                    threshold=100.0,
                    recommendation="Verify signal scoring logic",
                ))

        # High error rates
        records = self._filter_records(coverage, date_range)
        error_counts: Dict[str, int] = {}
        total_counts: Dict[str, int] = {}

        for r in records:
            total_counts[r.signal_id] = total_counts.get(r.signal_id, 0) + 1
            if r.error:
                error_counts[r.signal_id] = error_counts.get(r.signal_id, 0) + 1

        for signal_id, error_count in error_counts.items():
            total = total_counts.get(signal_id, 1)
            error_rate = error_count / total

            if error_rate > 0.10:
                issues.append(SignalIssue(
                    signal_id=signal_id,
                    issue_type="high_error_rate",
                    severity="critical" if error_rate > 0.25 else "warning",
                    description=f"Signal has {error_rate:.1%} error rate ({error_count} errors)",
                    metric_value=error_rate,
                    threshold=0.10,
                    recommendation="Check signal extractor logs for common error patterns",
                ))

        return sorted(issues, key=lambda i: (
            0 if i.severity == "critical" else 1 if i.severity == "warning" else 2
        ))

    def get_extraction_performance(
        self,
        coverage: str,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> Dict[str, Any]:
        """
        Get signal extraction performance metrics.

        Returns execution times, cache hit rates, etc.
        """
        records = self._filter_records(coverage, date_range)

        if not records:
            return {"sample_size": 0}

        # Execution times
        exec_times = [r.execution_time_ms for r in records if r.execution_time_ms > 0]

        # Cache stats
        cache_hits = sum(1 for r in records if r.from_cache)
        cache_rate = cache_hits / len(records) if records else 0.0

        # Error rate
        errors = sum(1 for r in records if r.error)
        error_rate = errors / len(records) if records else 0.0

        return {
            "sample_size": len(records),
            "avg_execution_ms": statistics.mean(exec_times) if exec_times else 0.0,
            "p50_execution_ms": statistics.median(exec_times) if exec_times else 0.0,
            "p95_execution_ms": sorted(exec_times)[int(len(exec_times) * 0.95)] if exec_times else 0.0,
            "cache_hit_rate": cache_rate,
            "error_rate": error_rate,
            "total_execution_time_s": sum(exec_times) / 1000 if exec_times else 0.0,
        }

    def _filter_records(
        self,
        coverage: str,
        date_range: Optional[Tuple[date, date]],
    ) -> List[SignalRecord]:
        """Filter signal records by coverage and date."""
        results = [r for r in self._signal_records if r.coverage == coverage]

        if date_range:
            start_date, end_date = date_range
            results = [
                r for r in results
                if start_date <= r.extracted_at.date() <= end_date
            ]

        return results

    def _build_histogram(
        self,
        scores: List[float],
        buckets: int = 10,
    ) -> Dict[str, int]:
        """Build histogram from scores."""
        if not scores:
            return {}

        min_val = min(scores)
        max_val = max(scores)
        range_val = max_val - min_val

        if range_val == 0:
            return {"0-100": len(scores)}

        bucket_size = range_val / buckets
        histogram: Dict[str, int] = {}

        for i in range(buckets):
            low = min_val + i * bucket_size
            high = min_val + (i + 1) * bucket_size
            label = f"{low:.0f}-{high:.0f}"
            histogram[label] = 0

        for score in scores:
            bucket_idx = min(int((score - min_val) / bucket_size), buckets - 1)
            low = min_val + bucket_idx * bucket_size
            high = min_val + (bucket_idx + 1) * bucket_size
            label = f"{low:.0f}-{high:.0f}"
            histogram[label] = histogram.get(label, 0) + 1

        return histogram

    def _format_period(self, date_range: Optional[Tuple[date, date]]) -> str:
        """Format date range as string."""
        if date_range:
            return f"{date_range[0]} to {date_range[1]}"
        return "all"

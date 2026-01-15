"""
Correlation Matrix Manager (Phase 16)

Manages the loss correlation matrix - the empirically-derived
relationships between signals and loss outcomes. This component
requires historical policy + loss data for calibration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

from .types import (
    CorrelationMatrix,
    CorrelationMatrixEntry,
)


class CorrelationMatrixManager:
    """
    Manages the loss correlation matrix - the empirically-derived
    relationships between signals and loss outcomes.

    This component requires historical policy + loss data for calibration.
    Initial implementation uses hypothesized correlations; validation
    requires empirical testing against carrier loss data.
    """

    def __init__(self, coverage: str):
        """
        Initialize matrix manager for a coverage.

        Args:
            coverage: Coverage type (e.g., 'cyber', 'do', 'pi')
        """
        self.coverage = coverage
        self.matrix: Optional[CorrelationMatrix] = None

    def calibrate(
        self,
        policies: List[Dict[str, Any]],
        losses: List[Dict[str, Any]],
        observation_start: datetime,
        observation_end: datetime
    ) -> CorrelationMatrix:
        """
        Calibrate correlation matrix from historical data.

        Args:
            policies: List of policies with signal snapshots at bind
                Each policy should have: policy_id, signals (dict of signal_id -> value)
            losses: List of losses linked to policy IDs
                Each loss should have: policy_id, incurred (amount)
            observation_start: Start of observation period
            observation_end: End of observation period

        Returns:
            Calibrated correlation matrix
        """
        # Link losses to policies
        policy_outcomes = self._link_losses_to_policies(policies, losses)

        # Extract signal IDs from first policy with signals
        signal_ids = []
        for policy in policies:
            if 'signals' in policy and policy['signals']:
                signal_ids = list(policy['signals'].keys())
                break

        if not signal_ids:
            raise ValueError("No signals found in policy data")

        entries = []
        for signal_id in signal_ids:
            entry = self._calculate_signal_correlation(
                signal_id,
                policy_outcomes
            )
            if entry is not None:
                entries.append(entry)

        # Calculate cohort calibrations
        cohort_calibrations = self._calibrate_cohorts(policy_outcomes)

        self.matrix = CorrelationMatrix(
            coverage=self.coverage,
            version=datetime.utcnow().strftime("%Y-%m-%d"),
            created_at=datetime.utcnow(),
            observation_period_start=observation_start,
            observation_period_end=observation_end,
            policy_count=len(policies),
            claim_count=len(losses),
            entries=entries,
            cohort_calibrations=cohort_calibrations
        )

        return self.matrix

    def _link_losses_to_policies(
        self,
        policies: List[Dict[str, Any]],
        losses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Link losses to policies and create outcome records."""
        loss_by_policy: Dict[str, List[Dict[str, Any]]] = {}
        for loss in losses:
            policy_id = loss['policy_id']
            if policy_id not in loss_by_policy:
                loss_by_policy[policy_id] = []
            loss_by_policy[policy_id].append(loss)

        outcomes = []
        for policy in policies:
            policy_id = policy['policy_id']
            policy_losses = loss_by_policy.get(policy_id, [])

            outcomes.append({
                'policy_id': policy_id,
                'signals': policy.get('signals', {}),
                'has_loss': len(policy_losses) > 0,
                'loss_count': len(policy_losses),
                'total_incurred': sum(l.get('incurred', 0) for l in policy_losses),
                'max_severity': max((l.get('incurred', 0) for l in policy_losses), default=0)
            })

        return outcomes

    def _calculate_signal_correlation(
        self,
        signal_id: str,
        outcomes: List[Dict[str, Any]]
    ) -> Optional[CorrelationMatrixEntry]:
        """Calculate correlation for a single signal."""
        # Extract signal values and outcomes
        signal_values: List[float] = []
        has_loss: List[int] = []
        loss_amounts: List[float] = []

        for outcome in outcomes:
            if signal_id in outcome['signals']:
                value = outcome['signals'][signal_id]
                if isinstance(value, (int, float)):
                    signal_values.append(float(value))
                    has_loss.append(1 if outcome['has_loss'] else 0)
                    if outcome['has_loss']:
                        loss_amounts.append(outcome['total_incurred'])

        if len(signal_values) < 30:  # Minimum sample size
            return None

        # Calculate frequency correlation using Pearson correlation
        freq_corr = self._pearson_correlation(signal_values, has_loss)

        # Calculate severity correlation (only for policies with losses)
        sev_corr = 0.0
        if len(loss_amounts) >= 10:
            loss_signal_values = [
                v for v, h in zip(signal_values, has_loss) if h == 1
            ]
            if len(loss_signal_values) == len(loss_amounts):
                sev_corr = self._pearson_correlation(loss_signal_values, loss_amounts)

        # Calculate information value
        iv = self._calculate_information_value(signal_values, has_loss)

        # Assess stability (placeholder - would need multiple time periods)
        stability = 0.8

        return CorrelationMatrixEntry(
            signal_id=signal_id,
            frequency_correlation=freq_corr,
            severity_correlation=sev_corr,
            information_value=iv,
            stability_score=stability,
            sample_size=len(signal_values),
            last_updated=datetime.utcnow(),
            interaction_effects=[]
        )

    def _pearson_correlation(
        self,
        x: List[float],
        y: List[float]
    ) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n < 2 or len(y) != n:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

        sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
        sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)

        denominator = (sum_sq_x * sum_sq_y) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _calculate_information_value(
        self,
        signal_values: List[float],
        outcomes: List[int]
    ) -> float:
        """Calculate information value for predictive power."""
        if not signal_values or not outcomes:
            return 0.0

        # Calculate percentiles for binning
        sorted_values = sorted(signal_values)
        n = len(sorted_values)

        # Create 10 bins based on deciles
        percentile_indices = [int(n * p / 10) for p in range(1, 10)]
        bins = [sorted_values[i] for i in percentile_indices if i < n]

        if not bins:
            return 0.0

        # Assign values to bins
        def get_bin(value: float) -> int:
            for i, threshold in enumerate(bins):
                if value <= threshold:
                    return i
            return len(bins)

        binned = [get_bin(v) for v in signal_values]

        total_good = sum(1 for o in outcomes if o == 0)
        total_bad = sum(1 for o in outcomes if o == 1)

        if total_good == 0 or total_bad == 0:
            return 0.0

        iv = 0.0
        for b in range(len(bins) + 1):
            bin_outcomes = [o for v, o in zip(binned, outcomes) if v == b]
            if not bin_outcomes:
                continue

            good_in_bin = sum(1 for o in bin_outcomes if o == 0)
            bad_in_bin = sum(1 for o in bin_outcomes if o == 1)

            good_pct = good_in_bin / total_good if total_good > 0 else 0
            bad_pct = bad_in_bin / total_bad if total_bad > 0 else 0

            if good_pct > 0 and bad_pct > 0:
                import math
                iv += (good_pct - bad_pct) * math.log(good_pct / bad_pct)

        return abs(iv)

    def _calibrate_cohorts(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calibrate cohort loss experience."""
        # Group by cohort and calculate loss metrics
        # Implementation depends on cohort definition method
        # This is a placeholder for future cohort calibration
        return []

    def get_signal_correlation(
        self,
        signal_id: str
    ) -> Optional[CorrelationMatrixEntry]:
        """Get correlation entry for a signal."""
        if self.matrix is None:
            return None

        for entry in self.matrix.entries:
            if entry.signal_id == signal_id:
                return entry
        return None

    def get_high_correlation_signals(
        self,
        min_correlation: float = 0.2,
        correlation_type: str = 'frequency'
    ) -> List[CorrelationMatrixEntry]:
        """
        Get signals with high correlation to loss.

        Args:
            min_correlation: Minimum absolute correlation value
            correlation_type: 'frequency' or 'severity'

        Returns:
            List of correlation entries sorted by correlation strength
        """
        if self.matrix is None:
            return []

        results = []
        for entry in self.matrix.entries:
            if correlation_type == 'frequency':
                if abs(entry.frequency_correlation) >= min_correlation:
                    results.append(entry)
            elif correlation_type == 'severity':
                if abs(entry.severity_correlation) >= min_correlation:
                    results.append(entry)

        # Sort by absolute correlation strength
        if correlation_type == 'frequency':
            return sorted(results, key=lambda e: abs(e.frequency_correlation), reverse=True)
        else:
            return sorted(results, key=lambda e: abs(e.severity_correlation), reverse=True)

    def get_predictive_signals(
        self,
        min_iv: float = 0.1,
        min_stability: float = 0.7
    ) -> List[CorrelationMatrixEntry]:
        """
        Get signals with high predictive power.

        Args:
            min_iv: Minimum information value
            min_stability: Minimum stability score

        Returns:
            List of predictive signal entries
        """
        if self.matrix is None:
            return []

        results = []
        for entry in self.matrix.entries:
            if entry.information_value >= min_iv and entry.stability_score >= min_stability:
                results.append(entry)

        return sorted(results, key=lambda e: e.information_value, reverse=True)

    def save_matrix(self, filepath: Path) -> None:
        """Save correlation matrix to JSON file."""
        if self.matrix is None:
            raise ValueError("No matrix to save")

        data = {
            'coverage': self.matrix.coverage,
            'version': self.matrix.version,
            'created_at': self.matrix.created_at.isoformat(),
            'observation_period_start': self.matrix.observation_period_start.isoformat(),
            'observation_period_end': self.matrix.observation_period_end.isoformat(),
            'policy_count': self.matrix.policy_count,
            'claim_count': self.matrix.claim_count,
            'entries': [
                {
                    'signal_id': e.signal_id,
                    'frequency_correlation': e.frequency_correlation,
                    'severity_correlation': e.severity_correlation,
                    'information_value': e.information_value,
                    'stability_score': e.stability_score,
                    'sample_size': e.sample_size,
                    'last_updated': e.last_updated.isoformat(),
                    'interaction_effects': e.interaction_effects
                }
                for e in self.matrix.entries
            ],
            'cohort_calibrations': self.matrix.cohort_calibrations
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_matrix(self, filepath: Path) -> CorrelationMatrix:
        """Load correlation matrix from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        entries = [
            CorrelationMatrixEntry(
                signal_id=e['signal_id'],
                frequency_correlation=e['frequency_correlation'],
                severity_correlation=e['severity_correlation'],
                information_value=e['information_value'],
                stability_score=e['stability_score'],
                sample_size=e['sample_size'],
                last_updated=datetime.fromisoformat(e['last_updated']),
                interaction_effects=e.get('interaction_effects', [])
            )
            for e in data['entries']
        ]

        self.matrix = CorrelationMatrix(
            coverage=data['coverage'],
            version=data['version'],
            created_at=datetime.fromisoformat(data['created_at']),
            observation_period_start=datetime.fromisoformat(data['observation_period_start']),
            observation_period_end=datetime.fromisoformat(data['observation_period_end']),
            policy_count=data['policy_count'],
            claim_count=data['claim_count'],
            entries=entries,
            cohort_calibrations=data.get('cohort_calibrations', [])
        )

        return self.matrix

    def get_matrix_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the correlation matrix."""
        if self.matrix is None:
            return {}

        freq_correlations = [e.frequency_correlation for e in self.matrix.entries]
        sev_correlations = [e.severity_correlation for e in self.matrix.entries]
        ivs = [e.information_value for e in self.matrix.entries]

        return {
            'coverage': self.matrix.coverage,
            'version': self.matrix.version,
            'policy_count': self.matrix.policy_count,
            'claim_count': self.matrix.claim_count,
            'signal_count': len(self.matrix.entries),
            'avg_frequency_correlation': sum(freq_correlations) / len(freq_correlations) if freq_correlations else 0,
            'max_frequency_correlation': max(freq_correlations, key=abs) if freq_correlations else 0,
            'avg_severity_correlation': sum(sev_correlations) / len(sev_correlations) if sev_correlations else 0,
            'max_severity_correlation': max(sev_correlations, key=abs) if sev_correlations else 0,
            'avg_information_value': sum(ivs) / len(ivs) if ivs else 0,
            'high_iv_signals': len([iv for iv in ivs if iv >= 0.1]),
        }

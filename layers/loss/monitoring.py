"""
Loss Monitoring Engine (Phase 16)

Continuous monitoring of loss propensity for in-force policies.
Detects deterioration, triggers alerts, and recommends actions.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .types import (
    LossPropensityResult,
    LossPropensityBand,
    TrendDirection,
    DeteriorationAlert,
    MonitoringResult,
    MonitoringConfig,
)
from .scorer import LossCorrelationScorer


class LossMonitoringEngine:
    """
    Continuous monitoring of loss propensity for in-force policies.

    Detects deterioration, triggers alerts, and recommends actions.
    Transforms insurance from point-in-time to continuous risk assessment.
    """

    def __init__(
        self,
        scorer: LossCorrelationScorer,
        config: Optional[MonitoringConfig] = None
    ):
        """
        Initialize monitoring engine.

        Args:
            scorer: LossCorrelationScorer instance for calculations
            config: Monitoring configuration (uses defaults if not provided)
        """
        self.scorer = scorer
        self.config = config or MonitoringConfig()

        # Parse refresh frequency to days
        self.refresh_frequency_days = self._parse_frequency(
            self.config.refresh_frequency
        )

        # Cache of previous results by entity
        self.result_cache: Dict[str, LossPropensityResult] = {}

        # Active alerts by entity
        self.active_alerts: Dict[str, List[DeteriorationAlert]] = {}

    def _parse_frequency(self, frequency: str) -> int:
        """Parse frequency string to number of days."""
        frequency_map = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'semi_annually': 180,
            'annually': 365,
        }
        return frequency_map.get(frequency.lower(), 30)

    def check_entity(
        self,
        entity_id: str,
        signal_outputs: List[Any],
        force_refresh: bool = False
    ) -> MonitoringResult:
        """
        Check an entity's loss propensity and generate alerts.

        Args:
            entity_id: Entity identifier
            signal_outputs: Current signal extraction results
            force_refresh: Force recalculation regardless of cache

        Returns:
            Monitoring result with alerts and recommendations
        """
        previous_result = self.result_cache.get(entity_id)

        # Check if refresh is needed
        refresh_needed = force_refresh or self._needs_refresh(previous_result)

        if not refresh_needed and previous_result is not None:
            return MonitoringResult(
                entity_id=entity_id,
                current_result=previous_result,
                previous_result=None,
                alerts=[],
                refresh_recommended=False,
                next_refresh_date=self._next_refresh_date(previous_result)
            )

        # Calculate new propensity
        current_result = self.scorer.calculate_propensity(
            signal_outputs,
            previous_result
        )

        # Generate alerts
        alerts = self._generate_alerts(entity_id, current_result, previous_result)

        # Update cache
        self.result_cache[entity_id] = current_result

        # Store active alerts
        if alerts:
            self.active_alerts[entity_id] = alerts

        return MonitoringResult(
            entity_id=entity_id,
            current_result=current_result,
            previous_result=previous_result,
            alerts=alerts,
            refresh_recommended=len(alerts) > 0,
            next_refresh_date=self._next_refresh_date(current_result)
        )

    def _needs_refresh(self, previous: Optional[LossPropensityResult]) -> bool:
        """Check if refresh is needed based on time."""
        if previous is None:
            return True

        days_elapsed = (datetime.utcnow() - previous.calculated_at).days
        return days_elapsed >= self.refresh_frequency_days

    def _next_refresh_date(self, result: LossPropensityResult) -> datetime:
        """Calculate next recommended refresh date."""
        base_date = result.calculated_at

        # More frequent refresh for deteriorating risks
        if result.trend_direction == TrendDirection.DETERIORATING:
            days = self.refresh_frequency_days // 2
        elif result.loss_propensity_band in [LossPropensityBand.ELEVATED, LossPropensityBand.HIGH]:
            days = int(self.refresh_frequency_days * 0.75)
        else:
            days = self.refresh_frequency_days

        return base_date + timedelta(days=max(1, days))

    def _generate_alerts(
        self,
        entity_id: str,
        current: LossPropensityResult,
        previous: Optional[LossPropensityResult]
    ) -> List[DeteriorationAlert]:
        """Generate alerts based on changes."""
        alerts = []

        if previous is None:
            # First assessment - check if already in high risk band
            if current.loss_propensity_band == LossPropensityBand.HIGH:
                alerts.append(DeteriorationAlert(
                    entity_id=entity_id,
                    alert_type='warning',
                    current_score=current.loss_propensity_score,
                    previous_score=0.0,
                    score_delta=current.loss_propensity_score,
                    days_elapsed=0,
                    current_band=current.loss_propensity_band.value,
                    previous_band='none',
                    trigger_reason="Initial assessment in high loss propensity band",
                    recommended_action="Immediate underwriter review recommended",
                    created_at=datetime.utcnow()
                ))
            return alerts

        score_delta = current.loss_propensity_score - previous.loss_propensity_score
        days_elapsed = (current.calculated_at - previous.calculated_at).days

        # Check for significant deterioration
        if score_delta >= self.config.deterioration_threshold:
            alert_type = 'critical' if score_delta >= self.config.deterioration_threshold * 1.5 else 'warning'

            alerts.append(DeteriorationAlert(
                entity_id=entity_id,
                alert_type=alert_type,
                current_score=current.loss_propensity_score,
                previous_score=previous.loss_propensity_score,
                score_delta=score_delta,
                days_elapsed=days_elapsed,
                current_band=current.loss_propensity_band.value,
                previous_band=previous.loss_propensity_band.value,
                trigger_reason=f"Loss propensity increased by {score_delta:.1f} points",
                recommended_action=self._get_recommended_action(current, score_delta),
                created_at=datetime.utcnow()
            ))

        # Check for band migration (deterioration)
        if current.loss_propensity_band != previous.loss_propensity_band:
            band_order = ['very_low', 'low', 'moderate', 'elevated', 'high']

            try:
                current_idx = band_order.index(current.loss_propensity_band.value)
                previous_idx = band_order.index(previous.loss_propensity_band.value)

                if current_idx > previous_idx:  # Deteriorated
                    alerts.append(DeteriorationAlert(
                        entity_id=entity_id,
                        alert_type='warning',
                        current_score=current.loss_propensity_score,
                        previous_score=previous.loss_propensity_score,
                        score_delta=score_delta,
                        days_elapsed=days_elapsed,
                        current_band=current.loss_propensity_band.value,
                        previous_band=previous.loss_propensity_band.value,
                        trigger_reason=f"Loss propensity band changed from {previous.loss_propensity_band.value} to {current.loss_propensity_band.value}",
                        recommended_action="Review risk and consider renewal terms adjustment",
                        created_at=datetime.utcnow()
                    ))
            except ValueError:
                pass  # Invalid band value

        # Check for velocity spike
        if self.config.alert_on_velocity_spike:
            if current.combined_score_velocity >= self.config.velocity_spike_threshold:
                alerts.append(DeteriorationAlert(
                    entity_id=entity_id,
                    alert_type='warning',
                    current_score=current.loss_propensity_score,
                    previous_score=previous.loss_propensity_score,
                    score_delta=score_delta,
                    days_elapsed=days_elapsed,
                    current_band=current.loss_propensity_band.value,
                    previous_band=previous.loss_propensity_band.value,
                    trigger_reason=f"Rapid deterioration: {current.combined_score_velocity:.1f} points/month",
                    recommended_action="Monitor closely for continued deterioration",
                    created_at=datetime.utcnow()
                ))

        return alerts

    def _get_recommended_action(
        self,
        result: LossPropensityResult,
        score_delta: float
    ) -> str:
        """Get recommended action based on current state."""
        if result.loss_propensity_band == LossPropensityBand.HIGH:
            return "Immediate underwriter review required. Consider non-renewal or significant terms adjustment."
        elif result.loss_propensity_band == LossPropensityBand.ELEVATED:
            return "Flag for renewal review. Consider risk improvement outreach."
        elif score_delta >= 20:
            return "Significant deterioration detected. Investigate cause and monitor closely."
        else:
            return "Continue standard monitoring. Note change for renewal consideration."

    def get_portfolio_alerts(
        self,
        min_severity: str = 'warning'
    ) -> List[DeteriorationAlert]:
        """
        Get all active alerts across portfolio.

        Args:
            min_severity: Minimum alert severity ('warning' or 'critical')

        Returns:
            List of all active alerts meeting severity threshold
        """
        all_alerts = []

        for entity_id, alerts in self.active_alerts.items():
            for alert in alerts:
                if min_severity == 'warning' or alert.alert_type == 'critical':
                    all_alerts.append(alert)

        # Sort by alert type (critical first) then score delta
        return sorted(
            all_alerts,
            key=lambda a: (0 if a.alert_type == 'critical' else 1, -a.score_delta)
        )

    def get_deteriorating_entities(
        self,
        min_score_delta: float = 10.0
    ) -> List[str]:
        """
        Get list of entities showing deterioration.

        Args:
            min_score_delta: Minimum score increase to be considered deteriorating

        Returns:
            List of entity IDs showing deterioration
        """
        deteriorating = []

        for entity_id, result in self.result_cache.items():
            if result.trend_direction == TrendDirection.DETERIORATING:
                # Check velocity (convert to monthly equivalent)
                if result.combined_score_velocity >= min_score_delta / 30:
                    deteriorating.append(entity_id)

        return deteriorating

    def get_improving_entities(
        self,
        min_score_delta: float = 10.0
    ) -> List[str]:
        """
        Get list of entities showing improvement.

        Args:
            min_score_delta: Minimum score decrease to be considered improving

        Returns:
            List of entity IDs showing improvement
        """
        improving = []

        for entity_id, result in self.result_cache.items():
            if result.trend_direction == TrendDirection.IMPROVING:
                # Check velocity (convert to monthly equivalent)
                if abs(result.combined_score_velocity) >= min_score_delta / 30:
                    improving.append(entity_id)

        return improving

    def get_entities_by_band(
        self,
        band: LossPropensityBand
    ) -> List[str]:
        """
        Get entities in a specific loss propensity band.

        Args:
            band: Loss propensity band to filter by

        Returns:
            List of entity IDs in the specified band
        """
        return [
            entity_id
            for entity_id, result in self.result_cache.items()
            if result.loss_propensity_band == band
        ]

    def get_entities_needing_refresh(self) -> List[str]:
        """
        Get entities due for refresh.

        Returns:
            List of entity IDs needing propensity refresh
        """
        needing_refresh = []
        now = datetime.utcnow()

        for entity_id, result in self.result_cache.items():
            next_refresh = self._next_refresh_date(result)
            if now >= next_refresh:
                needing_refresh.append(entity_id)

        return needing_refresh

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for the monitored portfolio.

        Returns:
            Dictionary with portfolio monitoring statistics
        """
        if not self.result_cache:
            return {
                'entity_count': 0,
                'band_distribution': {},
                'trend_distribution': {},
                'alert_count': 0,
                'critical_alert_count': 0,
            }

        # Band distribution
        band_dist: Dict[str, int] = {}
        for result in self.result_cache.values():
            band = result.loss_propensity_band.value
            band_dist[band] = band_dist.get(band, 0) + 1

        # Trend distribution
        trend_dist: Dict[str, int] = {}
        for result in self.result_cache.values():
            trend = result.trend_direction.value
            trend_dist[trend] = trend_dist.get(trend, 0) + 1

        # Alert counts
        all_alerts = self.get_portfolio_alerts()
        critical_count = len([a for a in all_alerts if a.alert_type == 'critical'])

        # Score statistics
        scores = [r.loss_propensity_score for r in self.result_cache.values()]

        return {
            'entity_count': len(self.result_cache),
            'band_distribution': band_dist,
            'trend_distribution': trend_dist,
            'alert_count': len(all_alerts),
            'critical_alert_count': critical_count,
            'avg_propensity_score': sum(scores) / len(scores) if scores else 0,
            'max_propensity_score': max(scores) if scores else 0,
            'min_propensity_score': min(scores) if scores else 0,
            'deteriorating_count': len(self.get_deteriorating_entities()),
            'improving_count': len(self.get_improving_entities()),
            'needing_refresh_count': len(self.get_entities_needing_refresh()),
        }

    def clear_entity_cache(self, entity_id: str) -> None:
        """Remove an entity from the monitoring cache."""
        if entity_id in self.result_cache:
            del self.result_cache[entity_id]
        if entity_id in self.active_alerts:
            del self.active_alerts[entity_id]

    def clear_all_cache(self) -> None:
        """Clear all cached results and alerts."""
        self.result_cache.clear()
        self.active_alerts.clear()

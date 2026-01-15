"""
Cohort Manager (Phase 17)

Manages cohort priors for exposure estimation.
Used as fallback when direct signals are insufficient.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ExposureConfig,
    ExposureBand,
    CohortPrior,
    CohortPriorConfig,
    CohortMatch,
)


class CohortManager:
    """
    Manage cohort priors for exposure estimation.

    Cohorts provide prior distributions based on:
    - Sector (industry classification)
    - Region (geographic location)
    - Size indicator (employee count band, revenue band)

    When direct exposure signals are insufficient,
    cohort priors provide fallback estimates.

    Usage:
        manager = CohortManager(config)
        match = manager.find_cohort(entity_data)
        prior = manager.get_prior(match.cohort_id)
    """

    def __init__(self, config: ExposureConfig):
        """
        Initialize cohort manager.

        Args:
            config: Exposure configuration from YAML
        """
        self.config = config

        # Convert config priors to CohortPrior objects
        self._priors: Dict[str, CohortPrior] = {}
        for prior_config in config.cohort_priors:
            self._priors[prior_config.cohort_id] = CohortPrior(
                cohort_id=prior_config.cohort_id,
                name=prior_config.name,
                sector=prior_config.sector,
                region=prior_config.region,
                size_indicator=prior_config.size_indicator,
                prior_band=prior_config.prior_band,
                prior_score_mean=prior_config.prior_score,
                prior_score_std=15.0,  # Default uncertainty
                prior_confidence=prior_config.confidence,
            )

        # Build sector and region indexes for fast lookup
        self._by_sector: Dict[str, List[str]] = {}
        self._by_region: Dict[str, List[str]] = {}

        for cohort_id, prior in self._priors.items():
            if prior.sector:
                if prior.sector not in self._by_sector:
                    self._by_sector[prior.sector] = []
                self._by_sector[prior.sector].append(cohort_id)

            if prior.region:
                if prior.region not in self._by_region:
                    self._by_region[prior.region] = []
                self._by_region[prior.region].append(cohort_id)

    def find_cohort(
        self,
        entity_data: Dict[str, Any]
    ) -> Optional[CohortMatch]:
        """
        Find best matching cohort for an entity.

        Args:
            entity_data: Entity information including:
                - sector: Industry classification
                - region: Geographic region
                - size_indicator: Size band if known
                - employee_count_band: Employee count band
                - revenue_band: Revenue band

        Returns:
            CohortMatch with best matching cohort, or None
        """
        sector = entity_data.get("sector", "").upper()
        region = entity_data.get("region", "").upper()
        size_indicator = entity_data.get("size_indicator") or \
                        entity_data.get("employee_count_band") or \
                        entity_data.get("revenue_band")

        candidates = []

        # Find candidates matching sector
        if sector and sector in self._by_sector:
            for cohort_id in self._by_sector[sector]:
                prior = self._priors[cohort_id]
                match_score = self._calculate_match_score(prior, sector, region, size_indicator)
                if match_score > 0:
                    candidates.append((cohort_id, match_score))

        # Find candidates matching region if no sector match
        if not candidates and region and region in self._by_region:
            for cohort_id in self._by_region[region]:
                prior = self._priors[cohort_id]
                match_score = self._calculate_match_score(prior, sector, region, size_indicator)
                if match_score > 0:
                    candidates.append((cohort_id, match_score))

        # Fall back to default cohort
        if not candidates:
            default_cohort = self._get_default_cohort()
            if default_cohort:
                return CohortMatch(
                    cohort_id=default_cohort.cohort_id,
                    cohort_name=default_cohort.name,
                    match_confidence=0.3,
                    match_criteria={"fallback": "default"},
                    prior=default_cohort,
                )
            return None

        # Sort by match score and return best
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_id, best_score = candidates[0]
        prior = self._priors[best_id]

        match_criteria = {}
        if prior.sector and prior.sector.upper() == sector:
            match_criteria["sector"] = sector
        if prior.region and prior.region.upper() == region:
            match_criteria["region"] = region
        if prior.size_indicator and prior.size_indicator == size_indicator:
            match_criteria["size_indicator"] = size_indicator

        return CohortMatch(
            cohort_id=best_id,
            cohort_name=prior.name,
            match_confidence=min(1.0, best_score / 3.0),  # Normalize to 0-1
            match_criteria=match_criteria,
            prior=prior,
        )

    def _calculate_match_score(
        self,
        prior: CohortPrior,
        sector: str,
        region: str,
        size_indicator: Optional[str]
    ) -> float:
        """Calculate match score between prior and entity attributes."""
        score = 0.0

        if prior.sector and prior.sector.upper() == sector:
            score += 1.0

        if prior.region and prior.region.upper() == region:
            score += 0.5

        if prior.size_indicator and prior.size_indicator == size_indicator:
            score += 0.5

        return score

    def _get_default_cohort(self) -> Optional[CohortPrior]:
        """Get default cohort for fallback."""
        for prior in self._priors.values():
            if prior.sector is None and prior.region is None:
                return prior

        # Create a default if none exists
        if not self._priors:
            return CohortPrior(
                cohort_id="default",
                name="Default Cohort",
                sector=None,
                region=None,
                size_indicator=None,
                prior_band=ExposureBand.MEDIUM,
                prior_score_mean=50.0,
                prior_score_std=20.0,
                prior_confidence=0.3,
            )

        return None

    def get_prior(self, cohort_id: str) -> Optional[CohortPrior]:
        """
        Get prior distribution for a cohort.

        Args:
            cohort_id: Cohort identifier

        Returns:
            CohortPrior or None
        """
        return self._priors.get(cohort_id)

    def get_prior_dict(self, cohort_id: str) -> Optional[Dict[str, Any]]:
        """
        Get prior as dictionary for use with scorer.

        Args:
            cohort_id: Cohort identifier

        Returns:
            Dictionary with prior_score, prior_band, confidence
        """
        prior = self.get_prior(cohort_id)
        if not prior:
            return None

        return {
            "cohort_id": prior.cohort_id,
            "name": prior.name,
            "prior_score": prior.prior_score_mean,
            "prior_band": prior.prior_band.value,
            "confidence": prior.prior_confidence,
        }

    def update_prior(
        self,
        cohort_id: str,
        observed_scores: List[float],
        observed_tivs: Optional[List[float]] = None
    ) -> None:
        """
        Update cohort prior with new observations.

        Args:
            cohort_id: Cohort identifier
            observed_scores: List of exposure scores from this cohort
            observed_tivs: Optional list of actual TIVs for calibration
        """
        prior = self._priors.get(cohort_id)
        if not prior:
            return

        if not observed_scores:
            return

        # Calculate observed statistics
        n = len(observed_scores)
        observed_mean = sum(observed_scores) / n
        observed_std = (sum((s - observed_mean) ** 2 for s in observed_scores) / n) ** 0.5 if n > 1 else 15.0

        # Update prior using Bayesian update
        # Weight by sample size vs prior strength
        prior_weight = 10  # Effective sample size of prior
        combined_n = prior_weight + n

        # Posterior mean
        posterior_mean = (prior.prior_score_mean * prior_weight + observed_mean * n) / combined_n

        # Update the prior
        prior.prior_score_mean = posterior_mean
        prior.prior_score_std = observed_std
        prior.sample_count = n
        prior.observed_mean = observed_mean
        prior.observed_std = observed_std
        prior.updated_at = datetime.utcnow()

        # Increase confidence with more data
        prior.prior_confidence = min(0.9, 0.5 + (n / 100))

    def get_all_cohorts(self) -> List[CohortPrior]:
        """Get all cohort priors."""
        return list(self._priors.values())

    def get_cohorts_for_sector(self, sector: str) -> List[CohortPrior]:
        """Get all cohort priors for a sector."""
        sector = sector.upper()
        if sector not in self._by_sector:
            return []
        return [self._priors[cid] for cid in self._by_sector[sector]]

    def add_cohort(self, prior: CohortPrior) -> None:
        """Add a new cohort prior."""
        self._priors[prior.cohort_id] = prior

        if prior.sector:
            if prior.sector not in self._by_sector:
                self._by_sector[prior.sector] = []
            self._by_sector[prior.sector].append(prior.cohort_id)

        if prior.region:
            if prior.region not in self._by_region:
                self._by_region[prior.region] = []
            self._by_region[prior.region].append(prior.cohort_id)

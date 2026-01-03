"""
Routed Signal Functions

Ready-to-use inference functions that leverage the multi-source routing module
for comprehensive, jurisdiction-aware signal extraction.

Each function:
1. Uses the routing module to determine which extractors to call
2. Executes extractors in parallel
3. Normalizes results to a unified schema
4. Converts to a signal score (0-100)

These functions automatically use the entity's locale from InferenceContext
to route to appropriate regional and global data sources.
"""

import time
import logging
from typing import Optional

from ....types import SignalResult, InferenceContext
from ....aggregators.routing_bridges import (
    SanctionsSignalBridge,
    CorporateSignalBridge,
)

logger = logging.getLogger(__name__)


def sanctions_check_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Multi-source sanctions check using jurisdiction-aware routing.

    Checks against appropriate sanctions lists based on entity locale:
    - Global: OpenSanctions, Interpol, FBI, World Bank
    - US: OFAC SDN
    - UK: UK OFSI
    - EU: EU Consolidated Sanctions
    - Asia-Pacific: ADB
    - Americas: IDB
    - Europe/Central Asia: EBRD
    - Africa: AfDB

    Args:
        entity_id: Entity name to check
        context: InferenceContext with locale information

    Returns:
        SignalResult with score (95=clear, 5=confirmed sanctioned)

    Example YAML config:
        signal_features:
          - id: sanctions_exposure
            name: Sanctions Exposure
            weight: 0.15
            inference_utility_function: sanctions_check_routed
            score_conditions:
              - max: 30
                tier_override: 5
                modifier: null
                note: High sanctions risk - possible match
    """
    start_time = time.time()

    try:
        bridge = SanctionsSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        # Determine confidence based on sources
        confidence = data.get('confidence', 0.8)

        return SignalResult(
            signal_id='sanctions_check_routed',
            score=data.get('score', 50),
            confidence=confidence,
            raw_data={
                'risk_level': data.get('risk_level'),
                'total_matches': data.get('total_matches', 0),
                'confirmed_sanctioned': data.get('confirmed_sanctioned', False),
                'highest_match_score': data.get('highest_match_score', 0),
            },
            aggregated_data=data,
            metadata={
                'sources_checked': data.get('sources_checked', []),
                'sources_with_matches': data.get('sources_with_matches', []),
                'locale': data.get('locale'),
                'strategy': data.get('strategy'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"sanctions_check_routed failed: {e}")
        return SignalResult(
            signal_id='sanctions_check_routed',
            score=50,  # Neutral on error
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )


def corporate_registry_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Multi-source corporate registry verification.

    Checks against appropriate registries based on locale:
    - Global: OpenCorporates (145 jurisdictions), GLEIF LEI
    - UK: Companies House
    - Australia: Australian Business Register
    - India: MCA

    Score interpretation:
    - 90+: Found in multiple registries, all details verified
    - 70-89: Found in registry, active status
    - 50-69: Found but limited information
    - 30-49: Not found or inactive
    - <30: Dissolved or concerning status

    Args:
        entity_id: Company name or registration number
        context: InferenceContext with locale

    Returns:
        SignalResult with combined registration score
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='corporate_registry_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'records_found': data.get('records_found', 0),
                'any_active': data.get('any_active', False),
                'lei': data.get('lei'),
            },
            aggregated_data=data,
            metadata={
                'sources_checked': data.get('sources_checked', []),
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"corporate_registry_routed failed: {e}")
        return SignalResult(
            signal_id='corporate_registry_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )


def corporate_status_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Corporate status check - is the company active?

    Returns the status_score component from corporate lookup:
    - 90: Active in registry
    - 50: Status unknown
    - 20: Dissolved/inactive

    Use this when you specifically need the activity status signal
    separate from the full corporate registry check.
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='corporate_status_routed',
            score=data.get('status_score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'any_active': data.get('any_active', False),
                'any_dissolved': data.get('any_dissolved', False),
            },
            aggregated_data=data,
            metadata={
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"corporate_status_routed failed: {e}")
        return SignalResult(
            signal_id='corporate_status_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )


def corporate_age_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Corporate age/establishment check.

    Returns the age_score component:
    - 95: > 10 years old
    - 85: > 5 years old
    - 70: > 2 years old
    - 55: > 1 year old
    - 35: < 1 year old (newly formed)

    Newer companies are generally higher risk in insurance contexts.
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='corporate_age_routed',
            score=data.get('age_score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'primary_record': data.get('primary_record'),
            },
            aggregated_data=data,
            metadata={
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"corporate_age_routed failed: {e}")
        return SignalResult(
            signal_id='corporate_age_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )


def lei_verification_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Legal Entity Identifier (LEI) verification.

    Checks if the entity has a valid LEI via GLEIF.
    Having an LEI indicates:
    - Regulated entity or significant financial participant
    - Verified legal identity
    - Meets ISO 17442 standards

    Score:
    - 90: Has valid LEI
    - 50: No LEI found (not necessarily bad for smaller entities)
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        # LEI-specific scoring
        has_lei = data.get('lei') is not None
        lei_status = data.get('lei_status', '')

        if has_lei and lei_status.upper() in ('ISSUED', 'ACTIVE'):
            score = 90
        elif has_lei:
            score = 70  # Has LEI but status is unclear
        else:
            score = 50  # No LEI - neutral for most entities

        return SignalResult(
            signal_id='lei_verification_routed',
            score=score,
            confidence=data.get('confidence', 0.8),
            raw_data={
                'lei': data.get('lei'),
                'lei_status': lei_status,
            },
            aggregated_data={'lei_score': data.get('lei_score', 50)},
            metadata={
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"lei_verification_routed failed: {e}")
        return SignalResult(
            signal_id='lei_verification_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )

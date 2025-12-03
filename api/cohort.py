"""
Cohort Processing
=================

High-volume cohort processing for portfolio analysis and bulk pricing.
Optimized for processing hundreds or thousands of entities efficiently.
"""

import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
import multiprocessing as mp
from dataclasses import dataclass
import traceback

logger = logging.getLogger(__name__)


@dataclass
class CohortResult:
    """Result from cohort processing."""
    total_entities: int
    successful: int
    failed: int
    duration_seconds: float
    entities_per_second: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class CohortProcessor:
    """Process large cohorts of entities efficiently."""

    def __init__(self, max_workers: Optional[int] = None, use_multiprocessing: bool = True):
        """
        Initialize cohort processor.

        Args:
            max_workers: Maximum number of parallel workers (default: CPU count)
            use_multiprocessing: Use process pool (True) or thread pool (False)
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.use_multiprocessing = use_multiprocessing

    def process_cohort(
        self,
        entities: List[Dict[str, Any]],
        pricing_func: Callable,
        model_name: str,
        chunk_size: int = 100
    ) -> CohortResult:
        """
        Process a cohort of entities.

        Args:
            entities: List of entity data dictionaries
            pricing_func: Pricing function to call
            model_name: Name of the model
            chunk_size: Number of entities to process in each chunk

        Returns:
            CohortResult with processed entities and statistics
        """
        start_time = datetime.now()
        total_entities = len(entities)

        logger.info(f"Processing cohort of {total_entities} entities for {model_name}")

        # Split into chunks for better memory management
        chunks = [entities[i:i + chunk_size] for i in range(0, total_entities, chunk_size)]

        results = []
        errors = []

        # Process chunks
        if self.use_multiprocessing and total_entities > 100:
            # Use multiprocessing for large cohorts
            results, errors = self._process_with_multiprocessing(chunks, pricing_func)
        else:
            # Use threading for smaller cohorts
            results, errors = self._process_with_threading(chunks, pricing_func)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        statistics = self._calculate_statistics(results)

        return CohortResult(
            total_entities=total_entities,
            successful=len(results),
            failed=len(errors),
            duration_seconds=duration,
            entities_per_second=total_entities / duration if duration > 0 else 0,
            results=results,
            errors=errors,
            statistics=statistics
        )

    def _process_with_threading(
        self,
        chunks: List[List[Dict[str, Any]]],
        pricing_func: Callable
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process using thread pool."""
        results = []
        errors = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._process_chunk, chunk, pricing_func): chunk_idx
                for chunk_idx, chunk in enumerate(chunks)
            }

            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_results, chunk_errors = future.result()
                    results.extend(chunk_results)
                    errors.extend(chunk_errors)
                    logger.info(f"Processed chunk {chunk_idx + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx}: {str(e)}")
                    errors.append({
                        'chunk': chunk_idx,
                        'error': str(e)
                    })

        return results, errors

    def _process_with_multiprocessing(
        self,
        chunks: List[List[Dict[str, Any]]],
        pricing_func: Callable
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process using process pool."""
        results = []
        errors = []

        # Note: For production, pricing_func needs to be picklable
        # This works with threading for now
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._process_chunk, chunk, pricing_func): chunk_idx
                for chunk_idx, chunk in enumerate(chunks)
            }

            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_results, chunk_errors = future.result()
                    results.extend(chunk_results)
                    errors.extend(chunk_errors)
                    logger.info(f"Processed chunk {chunk_idx + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx}: {str(e)}")
                    errors.append({
                        'chunk': chunk_idx,
                        'error': str(e)
                    })

        return results, errors

    @staticmethod
    def _process_chunk(
        chunk: List[Dict[str, Any]],
        pricing_func: Callable
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Process a single chunk of entities."""
        results = []
        errors = []

        for idx, entity_data in enumerate(chunk):
            try:
                result = pricing_func(entity_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing entity {idx}: {str(e)}")
                errors.append({
                    'entity': entity_data.get('company_name') or entity_data.get('entity_name', 'unknown'),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })

        return results, errors

    @staticmethod
    def _calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cohort-level statistics."""
        if not results:
            return {}

        # Extract premiums and scores
        premiums = []
        scores = []
        tiers = []

        for result in results:
            if isinstance(result, dict):
                if 'annual_premium' in result:
                    premiums.append(result['annual_premium'])
                if 'composite_score' in result:
                    scores.append(result['composite_score'])
                if 'risk_tier' in result:
                    tier_str = str(result['risk_tier'])
                    # Extract tier number from string like "TIER_1" or just "1"
                    if 'TIER_' in tier_str:
                        tiers.append(int(tier_str.split('_')[-1]))
                    elif tier_str.isdigit():
                        tiers.append(int(tier_str))

        statistics = {
            'count': len(results)
        }

        if premiums:
            statistics['premium'] = {
                'total': sum(premiums),
                'average': sum(premiums) / len(premiums),
                'min': min(premiums),
                'max': max(premiums),
                'median': sorted(premiums)[len(premiums) // 2]
            }

        if scores:
            statistics['scores'] = {
                'average': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'median': sorted(scores)[len(scores) // 2]
            }

        if tiers:
            tier_dist = {i: tiers.count(i) for i in range(1, 6)}
            statistics['tier_distribution'] = tier_dist

        return statistics


class CohortValidator:
    """Validate cohort requests."""

    @staticmethod
    def validate_cohort_request(data: Dict[str, Any], max_cohort_size: int = 10000) -> tuple[bool, str]:
        """
        Validate cohort request structure.

        Args:
            data: Request data
            max_cohort_size: Maximum allowed cohort size

        Returns:
            (is_valid, error_message)
        """
        if 'entities' not in data:
            return False, "Missing 'entities' field in cohort request"

        entities = data['entities']

        if not isinstance(entities, list):
            return False, "'entities' must be a list"

        if len(entities) == 0:
            return False, "Cohort must contain at least one entity"

        if len(entities) > max_cohort_size:
            return False, f"Cohort size {len(entities)} exceeds maximum {max_cohort_size}"

        return True, ""

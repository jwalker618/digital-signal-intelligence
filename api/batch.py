"""
Batch Processing
================

Handles batch quote requests for multiple entities at once.
"""

import logging
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple quote requests in parallel."""

    def __init__(self, max_workers: int = 10):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers

    def process_batch(
        self,
        requests: List[Dict[str, Any]],
        pricing_func: Callable,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Process a batch of pricing requests.

        Args:
            requests: List of quote request dictionaries
            pricing_func: Function to call for each request
            model_name: Name of the model being processed

        Returns:
            Dictionary with results and statistics
        """
        start_time = datetime.now()

        results = []
        errors = []

        # Process requests in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_request = {
                executor.submit(self._process_single, pricing_func, req, idx): (req, idx)
                for idx, req in enumerate(requests)
            }

            # Collect results as they complete
            for future in as_completed(future_to_request):
                req, idx = future_to_request[future]
                try:
                    result = future.result()
                    results.append({
                        'index': idx,
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    logger.error(f"Error processing batch item {idx}: {str(e)}")
                    errors.append({
                        'index': idx,
                        'success': False,
                        'error': str(e),
                        'entity_name': req.get('company_name') or req.get('institution_name') or req.get('entity_name', 'unknown')
                    })

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Sort results by original index
        results.sort(key=lambda x: x['index'])
        errors.sort(key=lambda x: x['index'])

        return {
            'success': True,
            'model': model_name,
            'batch_size': len(requests),
            'successful': len(results),
            'failed': len(errors),
            'duration_seconds': duration,
            'requests_per_second': len(requests) / duration if duration > 0 else 0,
            'results': results,
            'errors': errors,
            'timestamp': end_time.isoformat()
        }

    @staticmethod
    def _process_single(pricing_func: Callable, request_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Process a single request.

        Args:
            pricing_func: Function to call
            request_data: Request data
            index: Request index

        Returns:
            Pricing result
        """
        try:
            return pricing_func(request_data)
        except Exception as e:
            logger.error(f"Error processing request {index}: {str(e)}\n{traceback.format_exc()}")
            raise


class BatchValidator:
    """Validate batch requests."""

    @staticmethod
    def validate_batch_request(data: Dict[str, Any], max_batch_size: int = 100) -> tuple[bool, str]:
        """
        Validate batch request structure.

        Args:
            data: Request data
            max_batch_size: Maximum allowed batch size

        Returns:
            (is_valid, error_message)
        """
        if 'requests' not in data:
            return False, "Missing 'requests' field in batch request"

        requests = data['requests']

        if not isinstance(requests, list):
            return False, "'requests' must be a list"

        if len(requests) == 0:
            return False, "Batch must contain at least one request"

        if len(requests) > max_batch_size:
            return False, f"Batch size {len(requests)} exceeds maximum {max_batch_size}"

        return True, ""

    @staticmethod
    def validate_request_structure(request: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
        """
        Validate individual request structure.

        Args:
            request: Single request data
            required_fields: List of required field names

        Returns:
            (is_valid, error_message)
        """
        for field in required_fields:
            if field not in request:
                return False, f"Missing required field: {field}"

        return True, ""

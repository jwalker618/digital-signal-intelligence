"""
DSI Production Extractor - CFPB Consumer Complaints

Queries the Consumer Financial Protection Bureau's complaint database.
This is a FREE extractor - CFPB data is public.

CFPB Complaint Database:
    - Consumer complaints about financial products/services
    - Data from 2011 to present
    - Updated daily
    - Includes company response and dispute status

API Documentation:
    https://cfpb.github.io/api/ccdb/

Scoring Implications:
    - High complaint volume relative to company size = Concerning
    - Pattern of untimely responses = Negative signal
    - Low/no complaints = Positive signal (for financial services companies)
    - No data = Neutral (may not be in financial services)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class CFPBComplaintsExtractor(ProductionExtractor):
    """
    Extracts CFPB consumer complaint data for a company.

    Uses the CFPB Consumer Complaint Database API to retrieve
    complaint statistics and patterns.

    Output:
        {
            'searched_company': str,
            'company_found': bool,
            'total_complaints': int,
            'complaints_12mo': int,
            'products': {
                'product_name': count,
                ...
            },
            'issues': {
                'issue_name': count,
                ...
            },
            'response_timeliness': {
                'timely': int,
                'untimely': int,
                'timely_rate': float,
            },
            'consumer_disputed': {
                'disputed': int,
                'not_disputed': int,
                'dispute_rate': float,
            },
            'trends': {
                'current_month': int,
                'previous_month': int,
                'trend': str,  # 'increasing', 'decreasing', 'stable'
            },
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "cfpb_complaints"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 2.0  # CFPB is generous
    COST_TIER = "free"

    # CFPB API endpoints
    BASE_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for CFPBComplaintsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search CFPB complaints for a company."""
        company_name = entity_id.strip()

        if not company_name:
            return self._create_error_result("Empty company name provided")

        try:
            # Get aggregate statistics
            stats = self._get_company_stats(company_name)

            if not stats or stats.get('total_complaints', 0) == 0:
                return self._create_success_result({
                    'searched_company': company_name,
                    'company_found': False,
                    'total_complaints': 0,
                    'note': 'No CFPB complaints found for this company',
                })

            # Get additional breakdown
            products = self._get_product_breakdown(company_name)
            issues = self._get_issue_breakdown(company_name)
            response_data = self._get_response_analysis(company_name)
            trends = self._get_trend_data(company_name)

            data = {
                'searched_company': company_name,
                'company_found': True,
                'total_complaints': stats.get('total_complaints', 0),
                'complaints_12mo': stats.get('complaints_12mo', 0),
                'products': products,
                'issues': issues,
                'response_timeliness': response_data.get('timeliness', {}),
                'consumer_disputed': response_data.get('disputed', {}),
                'company_response': response_data.get('responses', {}),
                'trends': trends,
                'date_range': {
                    'earliest': stats.get('earliest_date'),
                    'latest': stats.get('latest_date'),
                },
            }

            return self._create_success_result(data, confidence=0.90)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"CFPB API error: {e}")

    def _get_company_stats(self, company_name: str) -> Dict[str, Any]:
        """Get basic complaint statistics for a company."""
        # Search for complaints
        params = {
            'company': company_name,
            'size': 1,  # We just need the count
            'sort': 'created_date_desc',
        }

        response = requests.get(
            f"{self.BASE_URL}/",
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        response.raise_for_status()

        data = response.json()
        total = data.get('hits', {}).get('total', {})

        if isinstance(total, dict):
            total_count = total.get('value', 0)
        else:
            total_count = total or 0

        # Get date range
        hits = data.get('hits', {}).get('hits', [])
        latest_date = None
        if hits:
            source = hits[0].get('_source', {})
            latest_date = source.get('date_received')

        # Get 12 month count
        twelve_months_ago = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')
        params_12mo = {
            'company': company_name,
            'size': 0,
            'date_received_min': twelve_months_ago,
        }

        response_12mo = requests.get(
            f"{self.BASE_URL}/",
            params=params_12mo,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        data_12mo = response_12mo.json()
        total_12mo = data_12mo.get('hits', {}).get('total', {})
        if isinstance(total_12mo, dict):
            count_12mo = total_12mo.get('value', 0)
        else:
            count_12mo = total_12mo or 0

        return {
            'total_complaints': total_count,
            'complaints_12mo': count_12mo,
            'latest_date': latest_date,
        }

    def _get_product_breakdown(self, company_name: str) -> Dict[str, int]:
        """Get complaints breakdown by product."""
        params = {
            'company': company_name,
            'size': 0,
            'agg': 'product',
        }

        response = requests.get(
            f"{self.BASE_URL}/",
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        response.raise_for_status()

        data = response.json()
        products = {}

        # Parse aggregation results
        aggs = data.get('aggregations', {})
        product_agg = aggs.get('product', {}).get('product', {}).get('buckets', [])

        for bucket in product_agg:
            products[bucket.get('key', 'Unknown')] = bucket.get('doc_count', 0)

        return products

    def _get_issue_breakdown(self, company_name: str) -> Dict[str, int]:
        """Get complaints breakdown by issue."""
        params = {
            'company': company_name,
            'size': 0,
            'agg': 'issue',
        }

        response = requests.get(
            f"{self.BASE_URL}/",
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        response.raise_for_status()

        data = response.json()
        issues = {}

        aggs = data.get('aggregations', {})
        issue_agg = aggs.get('issue', {}).get('issue', {}).get('buckets', [])

        for bucket in issue_agg[:15]:  # Top 15 issues
            issues[bucket.get('key', 'Unknown')] = bucket.get('doc_count', 0)

        return issues

    def _get_response_analysis(self, company_name: str) -> Dict[str, Any]:
        """Analyze company response patterns."""
        # Get timeliness data
        params = {
            'company': company_name,
            'size': 0,
            'agg': 'timely',
        }

        response = requests.get(
            f"{self.BASE_URL}/",
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        response.raise_for_status()

        data = response.json()
        result = {
            'timeliness': {'timely': 0, 'untimely': 0, 'timely_rate': 0.0},
            'disputed': {'disputed': 0, 'not_disputed': 0, 'dispute_rate': 0.0},
            'responses': {},
        }

        aggs = data.get('aggregations', {})

        # Timeliness
        timely_agg = aggs.get('timely', {}).get('timely', {}).get('buckets', [])
        for bucket in timely_agg:
            key = bucket.get('key', '')
            count = bucket.get('doc_count', 0)
            if key.lower() == 'yes':
                result['timeliness']['timely'] = count
            elif key.lower() == 'no':
                result['timeliness']['untimely'] = count

        total_timely = result['timeliness']['timely'] + result['timeliness']['untimely']
        if total_timely > 0:
            result['timeliness']['timely_rate'] = round(
                result['timeliness']['timely'] / total_timely * 100, 1
            )

        # Get dispute data
        params['agg'] = 'consumer_disputed'
        response = requests.get(
            f"{self.BASE_URL}/",
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        dispute_data = response.json()
        dispute_agg = dispute_data.get('aggregations', {}).get(
            'consumer_disputed', {}
        ).get('consumer_disputed', {}).get('buckets', [])

        for bucket in dispute_agg:
            key = bucket.get('key', '')
            count = bucket.get('doc_count', 0)
            if key.lower() in ('yes', 'y'):
                result['disputed']['disputed'] = count
            elif key.lower() in ('no', 'n'):
                result['disputed']['not_disputed'] = count

        total_dispute = result['disputed']['disputed'] + result['disputed']['not_disputed']
        if total_dispute > 0:
            result['disputed']['dispute_rate'] = round(
                result['disputed']['disputed'] / total_dispute * 100, 1
            )

        # Get company response types
        params['agg'] = 'company_response'
        response = requests.get(
            f"{self.BASE_URL}/",
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        resp_data = response.json()
        resp_agg = resp_data.get('aggregations', {}).get(
            'company_response', {}
        ).get('company_response', {}).get('buckets', [])

        for bucket in resp_agg:
            result['responses'][bucket.get('key', 'Unknown')] = bucket.get('doc_count', 0)

        return result

    def _get_trend_data(self, company_name: str) -> Dict[str, Any]:
        """Get trend data for recent months."""
        now = datetime.utcnow()
        current_month_start = now.replace(day=1).strftime('%Y-%m-%d')
        prev_month_end = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        prev_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')

        # Current month
        params_current = {
            'company': company_name,
            'size': 0,
            'date_received_min': current_month_start,
        }

        response_current = requests.get(
            f"{self.BASE_URL}/",
            params=params_current,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        data_current = response_current.json()
        total_current = data_current.get('hits', {}).get('total', {})
        if isinstance(total_current, dict):
            current_count = total_current.get('value', 0)
        else:
            current_count = total_current or 0

        # Previous month
        params_prev = {
            'company': company_name,
            'size': 0,
            'date_received_min': prev_month_start,
            'date_received_max': prev_month_end,
        }

        response_prev = requests.get(
            f"{self.BASE_URL}/",
            params=params_prev,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (complaint-research)'},
        )
        data_prev = response_prev.json()
        total_prev = data_prev.get('hits', {}).get('total', {})
        if isinstance(total_prev, dict):
            prev_count = total_prev.get('value', 0)
        else:
            prev_count = total_prev or 0

        # Determine trend
        if current_count > prev_count * 1.2:
            trend = 'increasing'
        elif current_count < prev_count * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'current_month': current_count,
            'previous_month': prev_count,
            'trend': trend,
            'period': {
                'current': current_month_start,
                'previous': prev_month_start,
            },
        }

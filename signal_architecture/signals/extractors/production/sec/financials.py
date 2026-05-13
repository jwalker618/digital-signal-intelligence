"""
DSI Production Extractor - SEC EDGAR Financials

Extracts financial data from SEC EDGAR company facts.
This is a FREE extractor - SEC EDGAR is a public database.

SEC Company Facts API:
    - Provides XBRL-tagged financial data
    - Historical data back to ~2009
    - Standardized US-GAAP and IFRS concepts

Financial Concepts Extracted:
    - Revenue / Net Sales
    - Net Income
    - Total Assets
    - Total Liabilities
    - Stockholders Equity
    - Operating Income
    - Cash and Cash Equivalents
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class SECFinancialsExtractor(ProductionExtractor):
    """
    Extracts financial data from SEC EDGAR Company Facts.

    Uses the SEC's XBRL-based Company Facts API to retrieve
    standardized financial metrics.

    Output:
        {
            'cik': str,
            'company_name': str,
            'financials': {
                'revenue': {'value': float, 'period': str, 'unit': str},
                'net_income': {...},
                'total_assets': {...},
                'total_liabilities': {...},
                'stockholders_equity': {...},
                'cash': {...},
            },
            'ratios': {
                'debt_to_equity': float,
                'current_ratio': float,
                'profit_margin': float,
            },
            'trends': {
                'revenue_growth': float,  # YoY percentage
                'net_income_growth': float,
            },
            'fiscal_year_end': str,
            'latest_period': str,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "sec_edgar_financials"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 8.0
    COST_TIER = "free"

    # SEC Company Facts API
    COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    # Common XBRL concepts to extract
    REVENUE_CONCEPTS = [
        'Revenues',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'SalesRevenueNet',
        'SalesRevenueGoodsNet',
        'SalesRevenueServicesNet',
    ]

    NET_INCOME_CONCEPTS = [
        'NetIncomeLoss',
        'ProfitLoss',
        'NetIncomeLossAvailableToCommonStockholdersBasic',
    ]

    ASSETS_CONCEPTS = [
        'Assets',
    ]

    LIABILITIES_CONCEPTS = [
        'Liabilities',
        'LiabilitiesAndStockholdersEquity',
    ]

    EQUITY_CONCEPTS = [
        'StockholdersEquity',
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
    ]

    CASH_CONCEPTS = [
        'CashAndCashEquivalentsAtCarryingValue',
        'Cash',
        'CashCashEquivalentsAndShortTermInvestments',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SECFinancialsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 15) if config else 15
        self._user_agent = config.get(
            'sec_user_agent',
            'DSI-Framework/1.0 (contact@example.com)'
        ) if config else 'DSI-Framework/1.0 (contact@example.com)'

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract financial data for a company."""
        # Normalize CIK
        cik = self._normalize_cik(entity_id)

        try:
            facts = self._fetch_company_facts(cik)
        except Exception as e:
            return self._create_error_result(f"Error fetching SEC data: {e}")

        if not facts:
            return self._create_error_result(f"No SEC data found for CIK: {cik}")

        # Parse financial data
        data = self._parse_financials(facts, cik)

        return self._create_success_result(data, confidence=0.90)

    def _normalize_cik(self, entity_id: str) -> str:
        """Normalize entity_id to a 10-digit CIK."""
        # Remove any non-digits
        cik = ''.join(c for c in entity_id if c.isdigit())
        return cik.zfill(10)

    def _fetch_company_facts(self, cik: str) -> Optional[Dict]:
        """Fetch company facts from SEC EDGAR."""
        url = self.COMPANY_FACTS_URL.format(cik=cik)

        response = requests.get(
            url,
            headers={'User-Agent': self._user_agent},
            timeout=self._timeout,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    def _parse_financials(self, facts: Dict, cik: str) -> Dict[str, Any]:
        """Parse company facts into financial metrics."""
        result = {
            'cik': cik,
            'company_name': facts.get('entityName', ''),
            'financials': {},
            'ratios': {},
            'trends': {},
            'fiscal_year_end': None,
            'latest_period': None,
        }

        # Get US-GAAP facts (most common)
        us_gaap = facts.get('facts', {}).get('us-gaap', {})

        # Extract key metrics
        result['financials']['revenue'] = self._get_latest_value(
            us_gaap, self.REVENUE_CONCEPTS, '10-K'
        )
        result['financials']['net_income'] = self._get_latest_value(
            us_gaap, self.NET_INCOME_CONCEPTS, '10-K'
        )
        result['financials']['total_assets'] = self._get_latest_value(
            us_gaap, self.ASSETS_CONCEPTS, '10-K'
        )
        result['financials']['total_liabilities'] = self._get_latest_value(
            us_gaap, self.LIABILITIES_CONCEPTS, '10-K'
        )
        result['financials']['stockholders_equity'] = self._get_latest_value(
            us_gaap, self.EQUITY_CONCEPTS, '10-K'
        )
        result['financials']['cash'] = self._get_latest_value(
            us_gaap, self.CASH_CONCEPTS, '10-K'
        )

        # Calculate ratios
        result['ratios'] = self._calculate_ratios(result['financials'])

        # Calculate trends (YoY growth)
        result['trends'] = self._calculate_trends(us_gaap)

        # Get latest period
        for metric in result['financials'].values():
            if metric and metric.get('period'):
                result['latest_period'] = metric['period']
                break

        return result

    def _get_latest_value(
        self,
        us_gaap: Dict,
        concepts: List[str],
        form_type: str = '10-K'
    ) -> Optional[Dict[str, Any]]:
        """Get the latest value for a financial concept."""
        for concept in concepts:
            if concept not in us_gaap:
                continue

            concept_data = us_gaap[concept]
            units = concept_data.get('units', {})

            # Look for USD values first
            usd_values = units.get('USD', [])
            if not usd_values:
                continue

            # Filter to annual filings and get most recent
            annual_values = [
                v for v in usd_values
                if v.get('form') == form_type and v.get('frame')
            ]

            if not annual_values:
                # Try without form filter
                annual_values = [v for v in usd_values if v.get('frame')]

            if not annual_values:
                continue

            # Sort by end date and get most recent
            annual_values.sort(key=lambda x: x.get('end', ''), reverse=True)
            latest = annual_values[0]

            return {
                'value': latest.get('val'),
                'period': latest.get('frame', '').replace('CY', ''),
                'end_date': latest.get('end'),
                'form': latest.get('form'),
                'unit': 'USD',
                'concept': concept,
            }

        return None

    def _calculate_ratios(self, financials: Dict) -> Dict[str, Optional[float]]:
        """Calculate financial ratios from extracted data."""
        ratios = {
            'debt_to_equity': None,
            'profit_margin': None,
            'return_on_assets': None,
            'return_on_equity': None,
        }

        # Debt to Equity
        liabilities = financials.get('total_liabilities', {}).get('value')
        equity = financials.get('stockholders_equity', {}).get('value')
        if liabilities and equity and equity != 0:
            ratios['debt_to_equity'] = round(liabilities / equity, 2)

        # Profit Margin
        revenue = financials.get('revenue', {}).get('value')
        net_income = financials.get('net_income', {}).get('value')
        if revenue and net_income and revenue != 0:
            ratios['profit_margin'] = round((net_income / revenue) * 100, 2)

        # Return on Assets
        assets = financials.get('total_assets', {}).get('value')
        if assets and net_income and assets != 0:
            ratios['return_on_assets'] = round((net_income / assets) * 100, 2)

        # Return on Equity
        if equity and net_income and equity != 0:
            ratios['return_on_equity'] = round((net_income / equity) * 100, 2)

        return ratios

    def _calculate_trends(self, us_gaap: Dict) -> Dict[str, Optional[float]]:
        """Calculate year-over-year growth trends."""
        trends = {
            'revenue_growth': None,
            'net_income_growth': None,
        }

        # Revenue growth
        revenue_growth = self._get_yoy_growth(us_gaap, self.REVENUE_CONCEPTS)
        if revenue_growth is not None:
            trends['revenue_growth'] = round(revenue_growth, 2)

        # Net income growth
        income_growth = self._get_yoy_growth(us_gaap, self.NET_INCOME_CONCEPTS)
        if income_growth is not None:
            trends['net_income_growth'] = round(income_growth, 2)

        return trends

    def _get_yoy_growth(
        self,
        us_gaap: Dict,
        concepts: List[str]
    ) -> Optional[float]:
        """Calculate year-over-year growth for a concept."""
        for concept in concepts:
            if concept not in us_gaap:
                continue

            units = us_gaap[concept].get('units', {}).get('USD', [])
            if not units:
                continue

            # Get annual values with frames
            annual_values = [
                v for v in units
                if v.get('form') == '10-K' and v.get('frame')
            ]

            if len(annual_values) < 2:
                continue

            # Sort by end date
            annual_values.sort(key=lambda x: x.get('end', ''), reverse=True)

            current = annual_values[0].get('val')
            previous = annual_values[1].get('val')

            if current and previous and previous != 0:
                return ((current - previous) / abs(previous)) * 100

        return None

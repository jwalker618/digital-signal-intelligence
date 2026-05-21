"""
DSI Production Extractor - SEC EDGAR Filings

Extracts company filing information from SEC EDGAR.
This is a FREE extractor - SEC EDGAR is a public database.

SEC EDGAR API:
    - Base URL: https://data.sec.gov/
    - Rate limit: 10 requests per second
    - Requires User-Agent header with contact info

Filing Types:
    - 10-K: Annual report
    - 10-Q: Quarterly report
    - 8-K: Current report (material events)
    - DEF 14A: Proxy statement
    - 4: Insider trading
    - 13F: Institutional holdings
"""

import logging
import re
import time
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


class SECFilingsExtractor(ProductionExtractor):
    """
    Extracts SEC filing information for a company.

    Accepts:
        - Ticker symbol (e.g., 'AAPL')
        - CIK number (e.g., '0000320193' or '320193')
        - Company name (will search)

    Output:
        {
            'cik': str,
            'company_name': str,
            'ticker': str,
            'sic': str,
            'sic_description': str,
            'state_of_incorporation': str,
            'fiscal_year_end': str,
            'filings': [
                {
                    'form': '10-K',
                    'filing_date': '2024-01-15',
                    'accession_number': '...',
                    'primary_document': '...',
                    'description': '...',
                },
                ...
            ],
            'filing_counts': {
                '10-K': 5,
                '10-Q': 20,
                '8-K': 45,
                ...
            },
            'latest_10k': {...},
            'latest_10q': {...},
            'has_recent_8k': bool,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "sec_edgar_filings"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 8.0  # Stay under SEC's 10/sec limit
    COST_TIER = "free"

    # SEC EDGAR API endpoints
    BASE_URL = "https://data.sec.gov"
    SUBMISSIONS_URL = f"{BASE_URL}/submissions/CIK{{cik}}.json"
    COMPANY_TICKERS_URL = f"{BASE_URL}/files/company_tickers.json"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SECFilingsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 15) if config else 15

        # SEC requires identifying User-Agent
        self._user_agent = config.get(
            'sec_user_agent',
            'DSI-Framework/1.0 (contact@example.com)'
        ) if config else 'DSI-Framework/1.0 (contact@example.com)'

        # Cache for ticker -> CIK mapping
        self._ticker_cache: Dict[str, str] = {}
        self._ticker_cache_time: Optional[float] = None

    def get_required_config(self) -> List[str]:
        return []  # Free API, but user_agent is recommended

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract SEC filing data for a company."""
        # Resolve entity_id to CIK
        cik = self._resolve_to_cik(entity_id)

        if not cik:
            return self._create_error_result(
                f"Could not find SEC CIK for: {entity_id}"
            )

        # Fetch submissions data
        try:
            submissions = self._fetch_submissions(cik)
        except Exception as e:
            return self._create_error_result(f"Error fetching SEC data: {e}")

        if not submissions:
            return self._create_error_result(f"No SEC data found for CIK: {cik}")

        # Parse the response
        data = self._parse_submissions(submissions, cik)

        return self._create_success_result(data, confidence=0.95)

    def _resolve_to_cik(self, entity_id: str) -> Optional[str]:
        """Resolve a ticker, CIK, or company name to a CIK."""
        entity_id = entity_id.strip()

        # Check if already a CIK (all digits)
        if entity_id.isdigit():
            return entity_id.zfill(10)

        # Check if looks like a CIK with leading zeros
        if re.match(r'^0+\d+$', entity_id):
            return entity_id.zfill(10)

        # Try as ticker symbol
        cik = self._ticker_to_cik(entity_id.upper())
        if cik:
            return cik

        # Could implement company name search here
        return None

    def _ticker_to_cik(self, ticker: str) -> Optional[str]:
        """Convert a ticker symbol to CIK."""
        # Refresh cache if needed (every 24 hours)
        cache_age = time.time() - (self._ticker_cache_time or 0)
        if not self._ticker_cache or cache_age > 86400:
            self._refresh_ticker_cache()

        return self._ticker_cache.get(ticker)

    def _refresh_ticker_cache(self):
        """Refresh the ticker -> CIK cache from SEC."""
        try:
            response = requests.get(
                self.COMPANY_TICKERS_URL,
                headers={'User-Agent': self._user_agent},
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()

            # Data format: {"0": {"cik_str": "320193", "ticker": "AAPL", "title": "Apple Inc."}, ...}
            self._ticker_cache = {}
            for entry in data.values():
                ticker = entry.get('ticker', '').upper()
                cik = str(entry.get('cik_str', '')).zfill(10)
                if ticker and cik:
                    self._ticker_cache[ticker] = cik

            self._ticker_cache_time = time.time()
            logger.info(f"Refreshed SEC ticker cache: {len(self._ticker_cache)} tickers")

        except Exception as e:
            logger.warning(f"Failed to refresh ticker cache: {e}")

    def _fetch_submissions(self, cik: str) -> Optional[Dict]:
        """Fetch submissions data from SEC EDGAR."""
        url = self.SUBMISSIONS_URL.format(cik=cik)

        response = requests.get(
            url,
            headers={'User-Agent': self._user_agent},
            timeout=self._timeout,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    def _parse_submissions(self, data: Dict, cik: str) -> Dict[str, Any]:
        """Parse SEC submissions response."""
        result = {
            'cik': cik,
            'company_name': data.get('name', ''),
            'ticker': '',
            'sic': data.get('sic', ''),
            'sic_description': data.get('sicDescription', ''),
            'state_of_incorporation': data.get('stateOfIncorporation', ''),
            'fiscal_year_end': data.get('fiscalYearEnd', ''),
            'filings': [],
            'filing_counts': {},
            'latest_10k': None,
            'latest_10q': None,
            'latest_8k': None,
            'has_recent_8k': False,
        }

        # Get tickers
        tickers = data.get('tickers', [])
        if tickers:
            result['ticker'] = tickers[0]

        # Parse recent filings
        recent = data.get('filings', {}).get('recent', {})
        if recent:
            forms = recent.get('form', [])
            filing_dates = recent.get('filingDate', [])
            accession_numbers = recent.get('accessionNumber', [])
            primary_docs = recent.get('primaryDocument', [])
            descriptions = recent.get('primaryDocDescription', [])

            # Count filings and collect details
            filing_counts: Dict[str, int] = {}

            for i in range(min(len(forms), 100)):  # Limit to recent 100
                form = forms[i] if i < len(forms) else ''
                filing_date = filing_dates[i] if i < len(filing_dates) else ''
                accession = accession_numbers[i] if i < len(accession_numbers) else ''
                primary_doc = primary_docs[i] if i < len(primary_docs) else ''
                description = descriptions[i] if i < len(descriptions) else ''

                # Count by form type
                filing_counts[form] = filing_counts.get(form, 0) + 1

                filing = {
                    'form': form,
                    'filing_date': filing_date,
                    'accession_number': accession,
                    'primary_document': primary_doc,
                    'description': description,
                    'url': self._build_filing_url(cik, accession, primary_doc),
                }
                result['filings'].append(filing)

                # Track latest of key types
                if form == '10-K' and not result['latest_10k']:
                    result['latest_10k'] = filing
                elif form == '10-Q' and not result['latest_10q']:
                    result['latest_10q'] = filing
                elif form == '8-K' and not result['latest_8k']:
                    result['latest_8k'] = filing

            result['filing_counts'] = filing_counts

            # Check for recent 8-K (within last 30 days)
            if result['latest_8k']:
                try:
                    latest_8k_date = datetime.strptime(
                        result['latest_8k']['filing_date'], '%Y-%m-%d'
                    )
                    if datetime.now() - latest_8k_date < timedelta(days=30):
                        result['has_recent_8k'] = True
                except ValueError:
                    pass

        return result

    def _build_filing_url(self, cik: str, accession: str, primary_doc: str) -> str:
        """Build URL to a specific filing document."""
        # Remove dashes from accession number for URL
        accession_clean = accession.replace('-', '')
        return (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik.lstrip('0')}/{accession_clean}/{primary_doc}"
        )

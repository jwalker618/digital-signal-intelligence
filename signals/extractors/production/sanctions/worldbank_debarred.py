"""
DSI Production Extractor - World Bank Debarred Firms

Queries the World Bank Listing of Ineligible Firms and Individuals.
FREE - Public World Bank procurement sanctions data.

World Bank Debarment:
    - Firms/individuals debarred from World Bank contracts
    - Cross-debarment from other MDBs (ADB, AfDB, EBRD, IDB)
    - Fraud, corruption, collusion, coercion cases
    - Temporary and permanent exclusions

Data Source:
    https://www.worldbank.org/en/projects-operations/procurement/debarred-firms

Cross-Debarment Coverage:
    - African Development Bank (AfDB)
    - Asian Development Bank (ADB)
    - European Bank for Reconstruction and Development (EBRD)
    - Inter-American Development Bank (IDB)

Scoring Implications:
    - Debarred = Critical (80+ risk)
    - Cross-debarred = Critical (75+ risk)
    - Conditionally released = Moderate (40-60 risk)
    - No match = Positive signal
"""

import logging
import csv
import io
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


class WorldBankDebarredExtractor(ProductionExtractor):
    """
    Queries World Bank debarred firms/individuals list.

    Downloads and searches the official World Bank exclusion list.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'matches': [
                {
                    'firm_name': str,
                    'address': str,
                    'country': str,
                    'from_date': str,
                    'to_date': str,
                    'grounds': str,
                    'sanction_type': str,
                    'is_permanent': bool,
                    'is_cross_debarment': bool,
                }
            ],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "worldbank_debarred"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # World Bank debarred list URLs
    DEBARRED_CSV_URL = "https://thedocs.worldbank.org/en/doc/World_Bank_Debarred_Cross-Debarred_Firms_and_Individuals_as_of_.csv"
    DEBARRED_PAGE_URL = "https://www.worldbank.org/en/projects-operations/procurement/debarred-firms"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for WorldBankDebarredExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 60) if config else 60
        self._debarred_cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search World Bank debarred list for an entity."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Get debarred data
            debarred_data = self._get_debarred_list()

            if debarred_data is None:
                return self._create_error_result("Could not retrieve World Bank debarred list")

            # Search for matches
            matches = self._search_debarred(search_term, debarred_data)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"World Bank debarred search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'debarred_hit': False,
                'risk_score': 0.0,
                'note': 'No matches found in World Bank debarred list',
            })

        # Calculate risk score
        risk_score = self._calculate_risk_score(matches)

        data = {
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],
            'debarred_hit': True,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _get_debarred_list(self) -> Optional[List[Dict]]:
        """Download and parse World Bank debarred list."""
        # Check cache
        if self._debarred_cache and self._cache_time:
            cache_age = (datetime.utcnow() - self._cache_time).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                return self._debarred_cache

        # Try to get the CSV file
        try:
            response = requests.get(
                self.DEBARRED_CSV_URL,
                headers={'User-Agent': 'DSI-Framework/1.0 (procurement-screening)'},
                timeout=self._timeout,
                allow_redirects=True,
            )

            if response.status_code == 200 and 'csv' in response.headers.get('content-type', '').lower():
                debarred = self._parse_csv(response.text)
                if debarred:
                    self._debarred_cache = debarred
                    self._cache_time = datetime.utcnow()
                    return debarred

        except Exception as e:
            logger.debug(f"Failed to fetch World Bank CSV: {e}")

        # Fall back to scraping the page
        try:
            debarred = self._scrape_debarred_page()
            if debarred:
                self._debarred_cache = debarred
                self._cache_time = datetime.utcnow()
                return debarred

        except Exception as e:
            logger.debug(f"Failed to scrape World Bank page: {e}")

        return None

    def _parse_csv(self, csv_content: str) -> List[Dict]:
        """Parse World Bank debarred CSV."""
        debarred = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content))

            for row in reader:
                entry = {
                    'firm_name': row.get('Firm Name', row.get('Name', '')).strip(),
                    'address': row.get('Address', '').strip(),
                    'country': row.get('Country', row.get('Nationality', '')).strip(),
                    'from_date': row.get('From Date', row.get('Ineligibility Period From', '')).strip(),
                    'to_date': row.get('To Date', row.get('Ineligibility Period To', '')).strip(),
                    'grounds': row.get('Grounds', row.get('Ground(s)', '')).strip(),
                }

                # Determine sanction type
                to_date = entry['to_date'].lower()
                if 'permanent' in to_date or '2999' in to_date or '9999' in to_date:
                    entry['is_permanent'] = True
                    entry['sanction_type'] = 'Permanent Debarment'
                else:
                    entry['is_permanent'] = False
                    entry['sanction_type'] = 'Temporary Debarment'

                # Check for cross-debarment
                grounds = entry['grounds'].lower()
                entry['is_cross_debarment'] = 'cross' in grounds or 'mdb' in grounds

                if entry['firm_name']:
                    debarred.append(entry)

        except Exception as e:
            logger.debug(f"CSV parse error: {e}")

        return debarred

    def _scrape_debarred_page(self) -> List[Dict]:
        """Scrape World Bank debarred firms page."""
        import re
        debarred = []

        try:
            response = requests.get(
                self.DEBARRED_PAGE_URL,
                headers={'User-Agent': 'DSI-Framework/1.0 (procurement-screening)'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                # Look for table rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', response.text, re.DOTALL | re.IGNORECASE)

                for row in rows:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

                    if len(cells) >= 4 and cells[0]:
                        entry = {
                            'firm_name': cells[0],
                            'address': cells[1] if len(cells) > 1 else '',
                            'country': cells[2] if len(cells) > 2 else '',
                            'from_date': cells[3] if len(cells) > 3 else '',
                            'to_date': cells[4] if len(cells) > 4 else '',
                            'grounds': cells[5] if len(cells) > 5 else '',
                            'is_permanent': False,
                            'is_cross_debarment': False,
                            'sanction_type': 'Debarment',
                        }
                        debarred.append(entry)

        except Exception as e:
            logger.debug(f"Page scrape error: {e}")

        return debarred

    def _search_debarred(self, query: str, debarred: List[Dict]) -> List[Dict]:
        """Search debarred list for matching entries."""
        query_lower = query.lower()
        query_parts = set(query_lower.split())
        matches = []

        for entry in debarred:
            firm_name = entry.get('firm_name', '').lower()

            # Exact or partial match
            if query_lower in firm_name or firm_name in query_lower:
                matches.append(entry)
                continue

            # Word overlap match
            firm_parts = set(firm_name.split())
            if query_parts and firm_parts:
                overlap = len(query_parts & firm_parts)
                if overlap >= min(2, len(query_parts)):
                    matches.append(entry)

        return matches

    def _calculate_risk_score(self, matches: List[Dict]) -> float:
        """Calculate risk score from matches."""
        if not matches:
            return 0.0

        score = 75.0  # Base score for any debarment match

        # Permanent debarment is most serious
        has_permanent = any(m.get('is_permanent') for m in matches)
        if has_permanent:
            score = 90.0

        # Multiple entries increase concern
        if len(matches) > 3:
            score += 8
        elif len(matches) > 1:
            score += 4

        # Check grounds for severity
        for match in matches:
            grounds = match.get('grounds', '').lower()
            if 'fraud' in grounds:
                score += 5
            if 'corruption' in grounds:
                score += 5
            if 'collusion' in grounds:
                score += 3

        return min(100.0, score)

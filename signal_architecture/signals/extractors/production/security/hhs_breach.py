"""
DSI Production Extractor - HHS Healthcare Breach Portal

Searches the HHS (Department of Health and Human Services) Breach Portal
for healthcare data breaches reported under HIPAA.

This is a FREE extractor - HHS breach data is public.

HHS Breach Portal:
    - HIPAA-covered entity breaches affecting 500+ individuals
    - Reported breaches from 2009 to present
    - Includes breach type, affected individuals, and resolution

Data Source:
    https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf

Scoring Implications:
    - Large breach (10,000+) = Critical negative
    - Multiple breaches = Major concern
    - Recent breach = Higher concern
    - No breaches = Positive (for healthcare entities)
"""

import logging
import re
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


class HHSBreachExtractor(ProductionExtractor):
    """
    Searches HHS HIPAA breach portal for healthcare data breaches.

    Searches by covered entity name and returns breach history.

    Output:
        {
            'searched_name': str,
            'breaches_found': int,
            'breaches': [
                {
                    'name': str,
                    'state': str,
                    'breach_date': str,
                    'reported_date': str,
                    'individuals_affected': int,
                    'breach_type': str,
                    'location': str,
                    'status': str,
                }
            ],
            'summary': {
                'total_affected': int,
                'largest_breach': int,
                'most_recent': str,
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "hhs_breach"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 1.0  # Be conservative with government sites
    COST_TIER = "free"

    # HHS Breach Portal URLs
    BREACH_PORTAL_URL = "https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf"
    BREACH_API_URL = "https://ocrportal.hhs.gov/ocr/breach/data"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for HHSBreachExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search HHS breach portal for a covered entity."""
        entity_name = entity_id.strip()

        if not entity_name:
            return self._create_error_result("Empty entity name provided")

        try:
            breaches = self._search_breaches(entity_name)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"HHS portal error: {e}")

        if not breaches:
            return self._create_success_result({
                'searched_name': entity_name,
                'breaches_found': 0,
                'breaches': [],
                'summary': {
                    'total_affected': 0,
                    'largest_breach': 0,
                    'most_recent': None,
                },
                'risk_score': 0.0,
                'note': 'No HIPAA breaches found (entity may not be HIPAA-covered)',
            })

        # Calculate summary
        summary = self._calculate_summary(breaches)

        # Calculate risk score
        risk_score = self._calculate_risk_score(breaches, summary)

        data = {
            'searched_name': entity_name,
            'breaches_found': len(breaches),
            'breaches': breaches[:20],  # Limit response
            'summary': summary,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _search_breaches(self, entity_name: str) -> List[Dict[str, Any]]:
        """Search for breaches in HHS portal."""
        # Try the data API first
        try:
            breaches = self._search_api(entity_name)
            if breaches is not None:  # May return empty list
                return breaches
        except Exception as e:
            logger.debug(f"HHS API search failed: {e}")

        # Fallback to scraping
        return self._search_scrape(entity_name)

    def _search_api(self, entity_name: str) -> Optional[List[Dict]]:
        """Search using any available API."""
        # HHS has a data download option - try to get the data
        # Note: The actual API structure may vary

        headers = {
            'User-Agent': 'DSI-Framework/1.0 (healthcare-research)',
            'Accept': 'application/json',
        }

        # Try to get breach data
        response = requests.get(
            self.BREACH_PORTAL_URL,
            params={'searchText': entity_name},
            headers=headers,
            timeout=self._timeout,
        )

        if response.status_code == 200:
            # The portal returns HTML, need to parse
            return self._parse_portal_html(response.text, entity_name)

        return None

    def _search_scrape(self, entity_name: str) -> List[Dict[str, Any]]:
        """Scrape the breach portal for results."""
        breaches = []

        try:
            # Initial page load to get session
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'DSI-Framework/1.0 (healthcare-research)',
            })

            response = session.get(
                self.BREACH_PORTAL_URL,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                breaches = self._parse_portal_html(response.text, entity_name)

        except Exception as e:
            logger.debug(f"Breach portal scraping failed: {e}")

        return breaches

    def _parse_portal_html(self, html: str, search_name: str) -> List[Dict[str, Any]]:
        """Parse breach data from portal HTML."""
        breaches = []
        search_lower = search_name.lower()

        # Look for table rows with breach data
        # The HHS portal uses a DataTable structure

        # Pattern to find entity names and their breach data
        # This is a simplified parser - would need enhancement for production

        # Look for entity name matches
        entity_pattern = rf'<td[^>]*>([^<]*{re.escape(search_name[:15])}[^<]*)</td>'
        matches = re.finditer(entity_pattern, html, re.IGNORECASE)

        for match in matches:
            entity = match.group(1).strip()

            # Try to extract surrounding row data
            row_start = html.rfind('<tr', 0, match.start())
            row_end = html.find('</tr>', match.end())

            if row_start != -1 and row_end != -1:
                row_html = html[row_start:row_end]
                breach = self._parse_breach_row(row_html, entity)
                if breach:
                    breaches.append(breach)

        # Also try to find any breach data in JSON format
        json_pattern = r'\{[^}]*"name"[^}]*\}'
        json_matches = re.findall(json_pattern, html)

        for json_str in json_matches:
            try:
                import json
                data = json.loads(json_str)
                if search_lower in data.get('name', '').lower():
                    breaches.append(self._parse_json_breach(data))
            except:
                pass

        return breaches

    def _parse_breach_row(self, row_html: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """Parse a single breach row from HTML."""
        cells = re.findall(r'<td[^>]*>([^<]*)</td>', row_html)

        if len(cells) >= 6:
            try:
                return {
                    'name': entity_name,
                    'state': cells[1].strip() if len(cells) > 1 else '',
                    'individuals_affected': self._parse_number(cells[2]) if len(cells) > 2 else 0,
                    'breach_date': cells[3].strip() if len(cells) > 3 else '',
                    'breach_type': cells[4].strip() if len(cells) > 4 else '',
                    'location': cells[5].strip() if len(cells) > 5 else '',
                    'status': 'Reported',
                }
            except Exception:
                pass

        return None

    def _parse_json_breach(self, data: Dict) -> Dict[str, Any]:
        """Parse breach data from JSON."""
        return {
            'name': data.get('name', data.get('coveredEntityName', '')),
            'state': data.get('state', ''),
            'individuals_affected': int(data.get('individualsAffected', 0)),
            'breach_date': data.get('breachSubmissionDate', data.get('breachDate', '')),
            'breach_type': data.get('typeOfBreach', ''),
            'location': data.get('locationOfBreachedInformation', ''),
            'status': data.get('status', 'Reported'),
            'reported_date': data.get('webPostingDate', ''),
        }

    def _parse_number(self, text: str) -> int:
        """Parse a number from text, handling commas."""
        try:
            return int(re.sub(r'[^\d]', '', text))
        except ValueError:
            return 0

    def _calculate_summary(self, breaches: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from breaches."""
        total_affected = sum(b.get('individuals_affected', 0) for b in breaches)
        largest = max((b.get('individuals_affected', 0) for b in breaches), default=0)

        dates = []
        for b in breaches:
            date_str = b.get('breach_date', '') or b.get('reported_date', '')
            if date_str:
                dates.append(date_str)

        most_recent = max(dates) if dates else None

        return {
            'total_affected': total_affected,
            'largest_breach': largest,
            'breach_count': len(breaches),
            'most_recent': most_recent,
        }

    def _calculate_risk_score(self, breaches: List[Dict], summary: Dict) -> float:
        """Calculate risk score from breach data."""
        score = 0.0

        # Number of breaches
        count = len(breaches)
        if count >= 5:
            score += 25
        elif count >= 3:
            score += 15
        elif count >= 1:
            score += 10

        # Size of largest breach
        largest = summary.get('largest_breach', 0)
        if largest >= 1000000:
            score += 30
        elif largest >= 100000:
            score += 25
        elif largest >= 10000:
            score += 15
        elif largest >= 1000:
            score += 10

        # Total affected
        total = summary.get('total_affected', 0)
        if total >= 5000000:
            score += 20
        elif total >= 500000:
            score += 15
        elif total >= 50000:
            score += 10

        # Recency
        most_recent = summary.get('most_recent')
        if most_recent:
            try:
                # Try to parse date
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y']:
                    try:
                        breach_date = datetime.strptime(most_recent[:10], fmt)
                        days_ago = (datetime.utcnow() - breach_date).days
                        if days_ago < 365:
                            score += 15
                        elif days_ago < 730:
                            score += 10
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        return min(100.0, score)

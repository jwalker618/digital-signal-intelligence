"""
DSI Production Extractor - SEC 8-K Litigation/Legal Disclosures

Extracts legal and litigation disclosures from SEC 8-K filings.
This is a FREE extractor - SEC EDGAR is a public database.

8-K Filing Items Related to Legal Matters:
    - Item 1.01: Entry into Material Definitive Agreement
    - Item 2.01: Completion of Acquisition/Disposition
    - Item 3.01: Notice of Delisting or Failure to Meet Listing Standards
    - Item 4.01: Changes in Registrant's Certifying Accountant
    - Item 4.02: Non-Reliance on Previously Issued Financial Statements
    - Item 5.02: Departure of Directors or Principal Officers
    - Item 8.01: Other Events (often includes litigation)

API Documentation:
    https://www.sec.gov/edgar/sec-api-documentation

Scoring Implications:
    - Recent material litigation = Negative signal
    - SEC enforcement = Critical negative
    - Accountant changes = Concerning
    - Officer departures = May be concerning
"""

import logging
import re
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


# Keywords indicating litigation/legal issues
LITIGATION_KEYWORDS = [
    'litigation', 'lawsuit', 'legal action', 'legal proceeding',
    'class action', 'derivative action', 'arbitration', 'settlement',
    'judgment', 'verdict', 'injunction', 'subpoena', 'investigation',
    'enforcement action', 'regulatory action', 'consent decree',
    'cease and desist', 'violation', 'fine', 'penalty', 'sanction',
    'indictment', 'criminal', 'fraud', 'breach of fiduciary',
    'securities violation', 'sec investigation', 'doj investigation',
    'ftc investigation', 'antitrust', 'patent infringement',
    'intellectual property', 'trade secret', 'whistleblower',
]

# 8-K items of interest for risk assessment
RISK_ITEMS = {
    '1.01': 'Material Definitive Agreement',
    '1.02': 'Termination of Material Agreement',
    '1.03': 'Bankruptcy or Receivership',
    '2.04': 'Triggering Events (Acceleration)',
    '2.06': 'Material Impairments',
    '3.01': 'Delisting Notice',
    '4.01': 'Accountant Change',
    '4.02': 'Non-Reliance on Financials',
    '5.02': 'Director/Officer Departure',
    '8.01': 'Other Events',
}


class SECLitigationExtractor(ProductionExtractor):
    """
    Extracts litigation and legal disclosures from SEC 8-K filings.

    Searches recent 8-K filings for legal matters and risk events.

    Output:
        {
            'entity': str,
            'cik': str,
            'total_8k_filings': int,
            'risk_filings': [
                {
                    'date': str,
                    'form': str,
                    'items': [...],
                    'description': str,
                    'litigation_keywords': [...],
                    'url': str,
                }
            ],
            'litigation_mentions': int,
            'risk_score': float,
        }
    """

    SOURCE_NAME = "sec_litigation"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 8.0  # SEC limit is 10/sec
    COST_TIER = "free"

    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    FILING_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SECLitigationExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._lookback_days = config.get('lookback_days', 365) if config else 365

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract litigation disclosures for a company."""
        entity = entity_id.strip().upper()

        if not entity:
            return self._create_error_result("Empty entity provided")

        # Resolve to CIK
        cik = self._resolve_to_cik(entity)
        if not cik:
            return self._create_success_result({
                'entity': entity,
                'cik': None,
                'error': 'Could not resolve entity to CIK',
                'total_8k_filings': 0,
                'risk_filings': [],
            }, confidence=0.5)

        try:
            # Get submissions
            submissions = self._get_submissions(cik)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"SEC API error: {e}")

        if not submissions:
            return self._create_success_result({
                'entity': entity,
                'cik': cik,
                'total_8k_filings': 0,
                'risk_filings': [],
                'litigation_mentions': 0,
                'risk_score': 0.0,
            })

        # Filter for 8-K filings in lookback period
        cutoff_date = datetime.utcnow() - timedelta(days=self._lookback_days)
        eight_k_filings = self._filter_8k_filings(submissions, cutoff_date)

        # Analyze filings for risk content
        risk_filings = []
        total_litigation_mentions = 0

        for filing in eight_k_filings[:50]:  # Limit analysis
            analysis = self._analyze_filing(cik, filing)
            if analysis.get('is_risk_filing') or analysis.get('litigation_keywords'):
                risk_filings.append(analysis)
                total_litigation_mentions += len(analysis.get('litigation_keywords', []))

        # Calculate risk score
        risk_score = self._calculate_risk_score(risk_filings, total_litigation_mentions)

        data = {
            'entity': entity,
            'cik': cik,
            'company_name': submissions.get('name', ''),
            'total_8k_filings': len(eight_k_filings),
            'risk_filings': risk_filings[:20],  # Limit response
            'risk_filing_count': len(risk_filings),
            'litigation_mentions': total_litigation_mentions,
            'risk_score': round(risk_score, 1),
            'lookback_days': self._lookback_days,
        }

        return self._create_success_result(data, confidence=0.90)

    def _resolve_to_cik(self, entity: str) -> Optional[str]:
        """Resolve ticker symbol or CIK to padded CIK."""
        # If already looks like CIK
        if entity.isdigit():
            return entity.zfill(10)

        # Try ticker lookup
        try:
            response = requests.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    'action': 'getcompany',
                    'CIK': entity,
                    'type': '8-K',
                    'dateb': '',
                    'owner': 'include',
                    'count': '1',
                    'output': 'atom',
                },
                headers={'User-Agent': 'DSI-Framework/1.0 (research@example.com)'},
                timeout=self._timeout,
            )

            # Parse CIK from response
            match = re.search(r'CIK=(\d+)', response.text)
            if match:
                return match.group(1).zfill(10)

        except Exception as e:
            logger.debug(f"CIK lookup failed for {entity}: {e}")

        return None

    def _get_submissions(self, cik: str) -> Optional[Dict]:
        """Get company submissions from SEC."""
        url = self.SUBMISSIONS_URL.format(cik=cik)

        response = requests.get(
            url,
            headers={'User-Agent': 'DSI-Framework/1.0 (research@example.com)'},
            timeout=self._timeout,
        )
        response.raise_for_status()

        return response.json()

    def _filter_8k_filings(self, submissions: Dict, cutoff_date: datetime) -> List[Dict]:
        """Filter submissions for 8-K filings after cutoff date."""
        filings = []

        recent = submissions.get('filings', {}).get('recent', {})
        forms = recent.get('form', [])
        dates = recent.get('filingDate', [])
        accessions = recent.get('accessionNumber', [])
        primary_docs = recent.get('primaryDocument', [])
        descriptions = recent.get('primaryDocDescription', [])

        for i, form in enumerate(forms):
            if form in ('8-K', '8-K/A'):
                try:
                    filing_date = datetime.strptime(dates[i], '%Y-%m-%d')
                    if filing_date >= cutoff_date:
                        filings.append({
                            'form': form,
                            'date': dates[i],
                            'accession': accessions[i].replace('-', ''),
                            'accession_formatted': accessions[i],
                            'primary_doc': primary_docs[i] if i < len(primary_docs) else None,
                            'description': descriptions[i] if i < len(descriptions) else '',
                        })
                except (ValueError, IndexError):
                    continue

        return filings

    def _analyze_filing(self, cik: str, filing: Dict) -> Dict[str, Any]:
        """Analyze an 8-K filing for risk content."""
        result = {
            'date': filing['date'],
            'form': filing['form'],
            'accession': filing['accession_formatted'],
            'items': [],
            'description': filing.get('description', ''),
            'litigation_keywords': [],
            'is_risk_filing': False,
            'url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K&dateb=&owner=include&count=40",
        }

        # Try to fetch and analyze the filing content
        if filing.get('primary_doc'):
            try:
                content = self._fetch_filing_content(cik, filing)
                if content:
                    # Extract 8-K items
                    result['items'] = self._extract_items(content)

                    # Check for risk items
                    for item in result['items']:
                        if item in RISK_ITEMS:
                            result['is_risk_filing'] = True

                    # Search for litigation keywords
                    content_lower = content.lower()
                    for keyword in LITIGATION_KEYWORDS:
                        if keyword in content_lower:
                            if keyword not in result['litigation_keywords']:
                                result['litigation_keywords'].append(keyword)

            except Exception as e:
                logger.debug(f"Could not analyze filing content: {e}")

        return result

    def _fetch_filing_content(self, cik: str, filing: Dict) -> Optional[str]:
        """Fetch the content of an 8-K filing."""
        url = self.FILING_URL.format(
            cik=cik.lstrip('0'),
            accession=filing['accession'],
            filename=filing['primary_doc'],
        )

        response = requests.get(
            url,
            headers={'User-Agent': 'DSI-Framework/1.0 (research@example.com)'},
            timeout=self._timeout,
        )

        if response.status_code == 200:
            return response.text[:100000]  # Limit size

        return None

    def _extract_items(self, content: str) -> List[str]:
        """Extract 8-K item numbers from filing content."""
        items = []

        # Pattern to match Item X.XX
        pattern = r'Item\s+(\d+\.\d+)'
        matches = re.findall(pattern, content, re.IGNORECASE)

        for match in matches:
            if match not in items:
                items.append(match)

        return items

    def _calculate_risk_score(self, risk_filings: List[Dict], litigation_mentions: int) -> float:
        """Calculate aggregate risk score from filings."""
        score = 0.0

        # Score based on number of risk filings
        score += len(risk_filings) * 5

        # Score based on litigation mentions
        score += litigation_mentions * 2

        # Extra weight for critical items
        for filing in risk_filings:
            items = filing.get('items', [])
            if '1.03' in items:  # Bankruptcy
                score += 30
            if '4.02' in items:  # Non-reliance on financials
                score += 25
            if '3.01' in items:  # Delisting
                score += 20
            if '4.01' in items:  # Accountant change
                score += 10

            # Extra for certain keywords
            keywords = filing.get('litigation_keywords', [])
            if 'fraud' in keywords:
                score += 15
            if 'sec investigation' in keywords or 'doj investigation' in keywords:
                score += 20
            if 'class action' in keywords:
                score += 10

        return min(100.0, score)

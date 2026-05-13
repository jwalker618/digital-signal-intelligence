"""
DSI Production Extractor - SEC DEF 14A Governance Analysis

Extracts corporate governance data from SEC proxy statements (DEF 14A).
This is a FREE extractor - SEC EDGAR is a public database.

DEF 14A Contains:
    - Board composition (independence, diversity, tenure)
    - Executive compensation
    - Related party transactions
    - Shareholder proposals
    - Audit committee information
    - Risk oversight disclosures

API Documentation:
    https://www.sec.gov/edgar/sec-api-documentation

Scoring Implications:
    - Independent board majority = Positive
    - Diverse board = Positive
    - Excessive executive pay = May be concerning
    - Related party transactions = Requires scrutiny
    - Failed say-on-pay vote = Negative
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


class SECGovernanceExtractor(ProductionExtractor):
    """
    Extracts governance data from SEC DEF 14A proxy statements.

    Analyzes board composition, executive compensation, and governance practices.

    Output:
        {
            'entity': str,
            'cik': str,
            'latest_proxy_date': str,
            'board': {
                'size': int,
                'independent_count': int,
                'independence_ratio': float,
                'female_count': int,
                'diversity_disclosed': bool,
            },
            'compensation': {
                'ceo_total': float,
                'ceo_name': str,
                'say_on_pay_support': float,
            },
            'governance_practices': {
                'separate_chair_ceo': bool,
                'lead_independent_director': bool,
                'majority_voting': bool,
                'proxy_access': bool,
            },
            'risk_factors': [...],
            'governance_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "sec_governance"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week (proxies are annual)
    RATE_LIMIT = 8.0
    COST_TIER = "free"

    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SECGovernanceExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract governance data for a company."""
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
            }, confidence=0.5)

        try:
            # Get submissions
            submissions = self._get_submissions(cik)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"SEC API error: {e}")

        # Find latest DEF 14A
        proxy = self._find_latest_proxy(submissions)

        if not proxy:
            return self._create_success_result({
                'entity': entity,
                'cik': cik,
                'company_name': submissions.get('name', ''),
                'latest_proxy_date': None,
                'note': 'No DEF 14A filings found (may not be required to file)',
            }, confidence=0.70)

        # Analyze proxy content
        governance_data = self._analyze_proxy(cik, proxy)

        data = {
            'entity': entity,
            'cik': cik,
            'company_name': submissions.get('name', ''),
            'latest_proxy_date': proxy.get('date'),
            'fiscal_year': proxy.get('fiscal_year'),
            **governance_data,
        }

        return self._create_success_result(data, confidence=0.85)

    def _resolve_to_cik(self, entity: str) -> Optional[str]:
        """Resolve ticker or CIK to padded CIK."""
        if entity.isdigit():
            return entity.zfill(10)

        try:
            response = requests.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    'action': 'getcompany',
                    'CIK': entity,
                    'type': 'DEF 14A',
                    'dateb': '',
                    'owner': 'include',
                    'count': '1',
                    'output': 'atom',
                },
                headers={'User-Agent': 'DSI-Framework/1.0 (research@example.com)'},
                timeout=self._timeout,
            )

            match = re.search(r'CIK=(\d+)', response.text)
            if match:
                return match.group(1).zfill(10)

        except Exception as e:
            logger.debug(f"CIK lookup failed for {entity}: {e}")

        return None

    def _get_submissions(self, cik: str) -> Dict:
        """Get company submissions from SEC."""
        url = self.SUBMISSIONS_URL.format(cik=cik)

        response = requests.get(
            url,
            headers={'User-Agent': 'DSI-Framework/1.0 (research@example.com)'},
            timeout=self._timeout,
        )
        response.raise_for_status()

        return response.json()

    def _find_latest_proxy(self, submissions: Dict) -> Optional[Dict]:
        """Find the most recent DEF 14A filing."""
        recent = submissions.get('filings', {}).get('recent', {})
        forms = recent.get('form', [])
        dates = recent.get('filingDate', [])
        accessions = recent.get('accessionNumber', [])
        primary_docs = recent.get('primaryDocument', [])

        for i, form in enumerate(forms):
            if form == 'DEF 14A':
                return {
                    'form': form,
                    'date': dates[i],
                    'accession': accessions[i].replace('-', ''),
                    'accession_formatted': accessions[i],
                    'primary_doc': primary_docs[i] if i < len(primary_docs) else None,
                    'fiscal_year': self._extract_fiscal_year(dates[i]),
                }

        return None

    def _extract_fiscal_year(self, filing_date: str) -> Optional[int]:
        """Extract fiscal year from filing date (proxy typically filed 3-4 months after FY end)."""
        try:
            date = datetime.strptime(filing_date, '%Y-%m-%d')
            # If filed in Q1, likely for prior year
            if date.month <= 4:
                return date.year - 1
            return date.year
        except ValueError:
            return None

    def _analyze_proxy(self, cik: str, proxy: Dict) -> Dict[str, Any]:
        """Analyze proxy statement content."""
        result = {
            'board': {
                'size': None,
                'independent_count': None,
                'independence_ratio': None,
                'female_count': None,
                'diversity_disclosed': False,
            },
            'compensation': {
                'ceo_total': None,
                'ceo_name': None,
                'say_on_pay_support': None,
            },
            'governance_practices': {
                'separate_chair_ceo': None,
                'lead_independent_director': None,
                'majority_voting': None,
                'proxy_access': None,
                'annual_elections': None,
            },
            'committees': {
                'audit': False,
                'compensation': False,
                'nominating': False,
                'risk': False,
            },
            'risk_factors': [],
            'governance_score': 50.0,  # Default middle score
        }

        # Try to fetch and analyze the proxy
        if proxy.get('primary_doc'):
            try:
                content = self._fetch_proxy_content(cik, proxy)
                if content:
                    result = self._parse_proxy_content(content, result)
            except Exception as e:
                logger.debug(f"Could not analyze proxy content: {e}")

        return result

    def _fetch_proxy_content(self, cik: str, proxy: Dict) -> Optional[str]:
        """Fetch proxy statement content."""
        url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{proxy['accession']}/{proxy['primary_doc']}"

        response = requests.get(
            url,
            headers={'User-Agent': 'DSI-Framework/1.0 (research@example.com)'},
            timeout=self._timeout,
        )

        if response.status_code == 200:
            return response.text[:500000]  # Limit size

        return None

    def _parse_proxy_content(self, content: str, result: Dict) -> Dict:
        """Parse governance information from proxy content."""
        content_lower = content.lower()

        # Board size and independence
        board_patterns = [
            r'board\s+(?:of\s+)?directors?\s+(?:consists?\s+of\s+|has\s+|includes?\s+)?(\d+)\s+(?:members?|directors?)',
            r'(\d+)\s+(?:members?|directors?)\s+(?:on\s+)?(?:our\s+)?board',
        ]

        for pattern in board_patterns:
            match = re.search(pattern, content_lower)
            if match:
                result['board']['size'] = int(match.group(1))
                break

        # Independence
        indep_patterns = [
            r'(\d+)\s+(?:of\s+)?(?:our\s+)?(?:\d+\s+)?directors?\s+(?:are|is)\s+independent',
            r'independent\s+directors?[:\s]+(\d+)',
        ]

        for pattern in indep_patterns:
            match = re.search(pattern, content_lower)
            if match:
                result['board']['independent_count'] = int(match.group(1))
                break

        if result['board']['size'] and result['board']['independent_count']:
            result['board']['independence_ratio'] = round(
                result['board']['independent_count'] / result['board']['size'], 2
            )

        # Diversity
        if 'diversity' in content_lower or 'diverse' in content_lower:
            result['board']['diversity_disclosed'] = True

        female_patterns = [
            r'(\d+)\s+(?:female|women)\s+directors?',
            r'(\d+)\s+directors?\s+(?:are|who\s+are)\s+(?:female|women)',
        ]

        for pattern in female_patterns:
            match = re.search(pattern, content_lower)
            if match:
                result['board']['female_count'] = int(match.group(1))
                break

        # Governance practices
        if 'separate' in content_lower and 'chair' in content_lower and 'ceo' in content_lower:
            if 'not' not in content_lower[max(0, content_lower.find('separate chair') - 20):content_lower.find('separate chair') + 50]:
                result['governance_practices']['separate_chair_ceo'] = True

        if 'lead independent director' in content_lower or 'lead director' in content_lower:
            result['governance_practices']['lead_independent_director'] = True

        if 'majority voting' in content_lower:
            result['governance_practices']['majority_voting'] = True

        if 'proxy access' in content_lower:
            result['governance_practices']['proxy_access'] = True

        if 'annual election' in content_lower or 'elected annually' in content_lower:
            result['governance_practices']['annual_elections'] = True

        # Committees
        if 'audit committee' in content_lower:
            result['committees']['audit'] = True
        if 'compensation committee' in content_lower:
            result['committees']['compensation'] = True
        if 'nominating' in content_lower or 'governance committee' in content_lower:
            result['committees']['nominating'] = True
        if 'risk committee' in content_lower or 'risk oversight' in content_lower:
            result['committees']['risk'] = True

        # Say on pay
        sop_patterns = [
            r'say.on.pay.*?(\d{1,3}(?:\.\d+)?)\s*(?:percent|%)',
            r'advisory.*?compensation.*?(\d{1,3}(?:\.\d+)?)\s*(?:percent|%)\s*(?:approval|support|favor)',
        ]

        for pattern in sop_patterns:
            match = re.search(pattern, content_lower)
            if match:
                result['compensation']['say_on_pay_support'] = float(match.group(1))
                break

        # Risk factors
        if 'related party transaction' in content_lower or 'related person transaction' in content_lower:
            result['risk_factors'].append('related_party_transactions')

        if 'material weakness' in content_lower:
            result['risk_factors'].append('material_weakness_disclosed')

        # Calculate governance score
        result['governance_score'] = self._calculate_governance_score(result)

        return result

    def _calculate_governance_score(self, data: Dict) -> float:
        """Calculate governance score based on extracted data."""
        score = 50.0  # Start at middle

        board = data.get('board', {})
        practices = data.get('governance_practices', {})
        committees = data.get('committees', {})
        compensation = data.get('compensation', {})

        # Independence (up to +20)
        ratio = board.get('independence_ratio')
        if ratio:
            if ratio >= 0.75:
                score += 20
            elif ratio >= 0.5:
                score += 10
            elif ratio < 0.33:
                score -= 10

        # Diversity (+5)
        if board.get('diversity_disclosed'):
            score += 3
        if board.get('female_count') and board.get('female_count') >= 2:
            score += 5

        # Governance practices (up to +15)
        if practices.get('separate_chair_ceo'):
            score += 5
        if practices.get('lead_independent_director'):
            score += 3
        if practices.get('majority_voting'):
            score += 3
        if practices.get('proxy_access'):
            score += 2
        if practices.get('annual_elections'):
            score += 2

        # Committees (+10)
        if committees.get('audit'):
            score += 3
        if committees.get('compensation'):
            score += 2
        if committees.get('nominating'):
            score += 2
        if committees.get('risk'):
            score += 3

        # Say on pay (-10 to +5)
        sop = compensation.get('say_on_pay_support')
        if sop:
            if sop >= 90:
                score += 5
            elif sop < 70:
                score -= 10

        # Risk factors (-5 each)
        score -= len(data.get('risk_factors', [])) * 5

        return max(0, min(100, score))

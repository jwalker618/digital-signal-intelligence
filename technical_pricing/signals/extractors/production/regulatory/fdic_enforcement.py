"""
DSI Production Extractor - FDIC/OCC Bank Enforcement Actions

Queries federal bank regulatory enforcement databases.
This is a FREE extractor - regulatory data is public.

Data Sources:
    - FDIC Enforcement Decisions and Orders
    - OCC Enforcement Actions
    - Federal Reserve Enforcement Actions
    - NCUA Enforcement (credit unions)

Database URLs:
    - FDIC: https://www.fdic.gov/resources/regulations/enforcement/
    - OCC: https://www.occ.gov/topics/laws-and-regulations/enforcement-actions/
    - Fed: https://www.federalreserve.gov/supervisionreg/enforcement-actions.htm

Scoring Implications:
    - Cease and desist order = Critical negative
    - Civil money penalty = Significant negative
    - Consent order = Concerning
    - Formal agreement = Moderate concern
    - No actions = Positive (for banks)
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


# Enforcement action severity levels
ACTION_SEVERITY = {
    'cease_and_desist': 5,
    'civil_money_penalty': 4,
    'removal_prohibition': 4,
    'consent_order': 3,
    'formal_agreement': 2,
    'memorandum_of_understanding': 1,
    'supervisory_letter': 1,
}


class FDICEnforcementExtractor(ProductionExtractor):
    """
    Searches federal bank enforcement action databases.

    Queries FDIC, OCC, and Federal Reserve enforcement records.

    Output:
        {
            'searched_name': str,
            'actions_found': int,
            'actions': [
                {
                    'agency': str,  # 'FDIC', 'OCC', 'FRB', 'NCUA'
                    'date': str,
                    'action_type': str,
                    'description': str,
                    'docket_number': str,
                    'penalty_amount': float,
                }
            ],
            'summary': {
                'total_actions': int,
                'total_penalties': float,
                'most_severe': str,
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "fdic_enforcement"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # Enforcement database URLs
    FDIC_URL = "https://www.fdic.gov/resources/regulations/enforcement/decisions-and-orders.html"
    OCC_URL = "https://apps.occ.gov/EASearch/"
    FRB_URL = "https://www.federalreserve.gov/supervisionreg/enforcement-actions.htm"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for FDICEnforcementExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._lookback_years = config.get('lookback_years', 10) if config else 10

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search enforcement databases for a bank."""
        bank_name = entity_id.strip()

        if not bank_name:
            return self._create_error_result("Empty bank name provided")

        all_actions = []

        # Search each regulatory database
        try:
            fdic_actions = self._search_fdic(bank_name)
            all_actions.extend(fdic_actions)
        except Exception as e:
            logger.debug(f"FDIC search failed: {e}")

        try:
            occ_actions = self._search_occ(bank_name)
            all_actions.extend(occ_actions)
        except Exception as e:
            logger.debug(f"OCC search failed: {e}")

        try:
            frb_actions = self._search_frb(bank_name)
            all_actions.extend(frb_actions)
        except Exception as e:
            logger.debug(f"FRB search failed: {e}")

        if not all_actions:
            return self._create_success_result({
                'searched_name': bank_name,
                'actions_found': 0,
                'actions': [],
                'summary': {
                    'total_actions': 0,
                    'total_penalties': 0.0,
                    'most_severe': None,
                },
                'risk_score': 0.0,
                'note': 'No enforcement actions found (may not be a regulated bank)',
            })

        # Sort by date (most recent first)
        all_actions.sort(key=lambda x: x.get('date', ''), reverse=True)

        # Calculate summary
        summary = self._calculate_summary(all_actions)

        # Calculate risk score
        risk_score = self._calculate_risk_score(all_actions, summary)

        data = {
            'searched_name': bank_name,
            'actions_found': len(all_actions),
            'actions': all_actions[:20],  # Limit response
            'summary': summary,
            'risk_score': round(risk_score, 1),
            'lookback_years': self._lookback_years,
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_fdic(self, bank_name: str) -> List[Dict[str, Any]]:
        """Search FDIC enforcement database."""
        actions = []

        try:
            response = requests.get(
                self.FDIC_URL,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (banking-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                actions = self._parse_fdic_html(response.text, bank_name)

        except Exception as e:
            logger.debug(f"FDIC search error: {e}")

        return actions

    def _parse_fdic_html(self, html: str, bank_name: str) -> List[Dict[str, Any]]:
        """Parse FDIC enforcement actions from HTML."""
        actions = []
        bank_lower = bank_name.lower()

        # Look for bank name in the HTML
        # FDIC typically lists actions in tables or lists
        if bank_lower not in html.lower():
            return actions

        # Try to extract action details around bank name mentions
        pattern = rf'<tr[^>]*>.*?{re.escape(bank_name[:15])}.*?</tr>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            action = self._parse_action_row(match, 'FDIC')
            if action:
                actions.append(action)

        return actions

    def _search_occ(self, bank_name: str) -> List[Dict[str, Any]]:
        """Search OCC enforcement database."""
        actions = []

        try:
            # OCC has a searchable database
            params = {
                'SearchText': bank_name,
                'SortColumn': 'EffectiveDate',
                'SortDirection': 'desc',
            }

            response = requests.get(
                self.OCC_URL,
                params=params,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (banking-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                actions = self._parse_occ_html(response.text, bank_name)

        except Exception as e:
            logger.debug(f"OCC search error: {e}")

        return actions

    def _parse_occ_html(self, html: str, bank_name: str) -> List[Dict[str, Any]]:
        """Parse OCC enforcement actions from HTML."""
        actions = []
        bank_lower = bank_name.lower()

        if bank_lower not in html.lower():
            return actions

        # Look for action entries
        # OCC typically uses structured tables
        row_pattern = r'<tr[^>]*class="[^"]*result[^"]*"[^>]*>.*?</tr>'
        rows = re.findall(row_pattern, html, re.IGNORECASE | re.DOTALL)

        for row in rows:
            if bank_lower in row.lower():
                action = self._parse_action_row(row, 'OCC')
                if action:
                    actions.append(action)

        return actions

    def _search_frb(self, bank_name: str) -> List[Dict[str, Any]]:
        """Search Federal Reserve enforcement database."""
        actions = []

        try:
            response = requests.get(
                self.FRB_URL,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (banking-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                actions = self._parse_frb_html(response.text, bank_name)

        except Exception as e:
            logger.debug(f"FRB search error: {e}")

        return actions

    def _parse_frb_html(self, html: str, bank_name: str) -> List[Dict[str, Any]]:
        """Parse Federal Reserve enforcement actions from HTML."""
        actions = []
        bank_lower = bank_name.lower()

        if bank_lower not in html.lower():
            return actions

        # Look for enforcement action entries
        pattern = rf'<tr[^>]*>.*?{re.escape(bank_name[:15])}.*?</tr>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            action = self._parse_action_row(match, 'FRB')
            if action:
                actions.append(action)

        return actions

    def _parse_action_row(self, row_html: str, agency: str) -> Optional[Dict[str, Any]]:
        """Parse a single enforcement action row."""
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)

        if len(cells) >= 3:
            # Clean cell contents
            cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

            # Try to identify action type
            action_type = 'Unknown'
            action_text = ' '.join(cells).lower()

            if 'cease' in action_text and 'desist' in action_text:
                action_type = 'Cease and Desist Order'
            elif 'civil money penalty' in action_text or 'cmp' in action_text:
                action_type = 'Civil Money Penalty'
            elif 'consent order' in action_text:
                action_type = 'Consent Order'
            elif 'formal agreement' in action_text:
                action_type = 'Formal Agreement'
            elif 'removal' in action_text or 'prohibition' in action_text:
                action_type = 'Removal/Prohibition Order'

            # Try to extract date
            date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})'
            date_match = re.search(date_pattern, row_html)
            date = date_match.group(1) if date_match else ''

            # Try to extract penalty amount
            penalty_pattern = r'\$[\d,]+(?:\.\d{2})?'
            penalty_match = re.search(penalty_pattern, row_html)
            penalty = 0.0
            if penalty_match:
                try:
                    penalty = float(penalty_match.group().replace('$', '').replace(',', ''))
                except ValueError:
                    pass

            return {
                'agency': agency,
                'date': date,
                'action_type': action_type,
                'description': cells[0][:200] if cells else '',
                'docket_number': '',
                'penalty_amount': penalty,
            }

        return None

    def _calculate_summary(self, actions: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from actions."""
        total_penalties = sum(a.get('penalty_amount', 0) for a in actions)

        # Find most severe action type
        most_severe = None
        max_severity = 0

        for action in actions:
            action_type = action.get('action_type', '').lower().replace(' ', '_')
            for key, severity in ACTION_SEVERITY.items():
                if key in action_type:
                    if severity > max_severity:
                        max_severity = severity
                        most_severe = action.get('action_type')
                    break

        return {
            'total_actions': len(actions),
            'total_penalties': round(total_penalties, 2),
            'most_severe': most_severe,
            'agencies': list(set(a.get('agency') for a in actions if a.get('agency'))),
        }

    def _calculate_risk_score(self, actions: List[Dict], summary: Dict) -> float:
        """Calculate risk score from enforcement actions."""
        score = 0.0

        # Score based on number of actions
        count = len(actions)
        if count >= 5:
            score += 25
        elif count >= 3:
            score += 15
        elif count >= 1:
            score += 10

        # Score based on action severity
        for action in actions:
            action_type = action.get('action_type', '').lower().replace(' ', '_')
            for key, severity in ACTION_SEVERITY.items():
                if key in action_type:
                    score += severity * 5
                    break

        # Score based on penalties
        penalties = summary.get('total_penalties', 0)
        if penalties >= 10000000:  # $10M+
            score += 25
        elif penalties >= 1000000:  # $1M+
            score += 20
        elif penalties >= 100000:  # $100K+
            score += 10

        # Recency factor
        for action in actions[:3]:  # Check most recent
            date_str = action.get('date', '')
            if date_str:
                try:
                    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y']:
                        try:
                            action_date = datetime.strptime(date_str, fmt)
                            if (datetime.utcnow() - action_date).days < 365:
                                score += 10  # Recent action
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

        return min(100.0, score)

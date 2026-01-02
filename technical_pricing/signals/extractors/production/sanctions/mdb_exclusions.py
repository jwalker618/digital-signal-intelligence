"""
DSI Production Extractor - Multilateral Development Bank (MDB) Exclusion Lists

Queries the exclusion/debarment lists from major MDBs.
FREE - Public MDB transparency databases.

MDBs Covered:
    - Asian Development Bank (ADB)
    - Inter-American Development Bank (IDB)
    - European Bank for Reconstruction and Development (EBRD)
    - African Development Bank (AfDB)

Cross-Debarment:
    Under the 2010 Agreement for Mutual Enforcement of Debarment Decisions,
    debarment by one MDB typically results in cross-debarment by others.

Data Sources:
    - ADB: https://sanctions.adb.org/
    - IDB: https://www.iadb.org/en/who-we-are/transparency/sanctions-system/sanctioned-firms-and-individuals
    - EBRD: https://www.ebrd.com/ineligible-entities.html
    - AfDB: https://www.afdb.org/en/projects-operations/debarment-and-sanctions-procedures

Scoring Implications:
    - Debarred by any MDB = Critical (80+ risk)
    - Cross-debarred = Critical (75+ risk)
    - No match = Positive signal
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


class ADBSanctionsExtractor(ProductionExtractor):
    """
    Queries Asian Development Bank sanctions/debarment list.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'matches': [...],
            'debarred_hit': bool,
            'risk_score': float,
        }
    """

    SOURCE_NAME = "adb_sanctions"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # ADB sanctions URL
    ADB_SANCTIONS_URL = "https://lnadbg4.adb.org/oga0009p.nsf/sancalilookupadjalialialialialialialialialialialialialialialialialialialialialia"
    ADB_PUBLIC_LIST = "https://www.adb.org/who-we-are/integrity/sanctions"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for ADBSanctionsExtractor.")
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search ADB sanctions list."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            sanctions = self._get_sanctions_list()
            matches = self._search_sanctions(search_term, sanctions)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"ADB sanctions search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'debarred_hit': False,
                'risk_score': 0.0,
                'note': 'No matches in ADB sanctions list',
            })

        return self._create_success_result({
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],
            'debarred_hit': True,
            'risk_score': 85.0,
        }, confidence=0.90)

    def _get_sanctions_list(self) -> List[Dict]:
        """Get ADB sanctions list (with caching)."""
        if self._cache and self._cache_time:
            if (datetime.utcnow() - self._cache_time).total_seconds() < 3600:
                return self._cache

        sanctions = []

        try:
            response = requests.get(
                self.ADB_PUBLIC_LIST,
                headers={'User-Agent': 'DSI-Framework/1.0'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                sanctions = self._parse_html_list(response.text)
                self._cache = sanctions
                self._cache_time = datetime.utcnow()

        except Exception as e:
            logger.debug(f"ADB list fetch error: {e}")

        return sanctions

    def _parse_html_list(self, html: str) -> List[Dict]:
        """Parse sanctions from ADB HTML page."""
        sanctions = []

        # Look for table rows with entity names
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

            if cells and len(cells) >= 2:
                name = cells[0]
                if name and not any(x in name.lower() for x in ['name', 'entity', 'firm']):
                    sanctions.append({
                        'name': name,
                        'country': cells[1] if len(cells) > 1 else '',
                        'from_date': cells[2] if len(cells) > 2 else '',
                        'to_date': cells[3] if len(cells) > 3 else '',
                        'grounds': cells[4] if len(cells) > 4 else '',
                        'source': 'ADB',
                    })

        return sanctions

    def _search_sanctions(self, query: str, sanctions: List[Dict]) -> List[Dict]:
        """Search sanctions for matching names."""
        query_lower = query.lower()
        query_parts = set(query_lower.split())
        matches = []

        for s in sanctions:
            name = s.get('name', '').lower()
            if query_lower in name or name in query_lower:
                matches.append(s)
            elif query_parts:
                name_parts = set(name.split())
                if len(query_parts & name_parts) >= min(2, len(query_parts)):
                    matches.append(s)

        return matches


class IDBSanctionsExtractor(ProductionExtractor):
    """
    Queries Inter-American Development Bank sanctions list.
    """

    SOURCE_NAME = "idb_sanctions"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    IDB_DATA_URL = "https://data.iadb.org/dataset/dataset-of-sanctioned-firms-and-individuals"
    IDB_LIST_URL = "https://www.iadb.org/en/who-we-are/transparency/sanctions-system/sanctioned-firms-and-individuals"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for IDBSanctionsExtractor.")
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search IDB sanctions list."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            sanctions = self._get_sanctions_list()
            matches = self._search_sanctions(search_term, sanctions)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"IDB sanctions search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'debarred_hit': False,
                'risk_score': 0.0,
                'note': 'No matches in IDB sanctions list',
            })

        return self._create_success_result({
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],
            'debarred_hit': True,
            'risk_score': 85.0,
        }, confidence=0.90)

    def _get_sanctions_list(self) -> List[Dict]:
        """Get IDB sanctions list."""
        if self._cache and self._cache_time:
            if (datetime.utcnow() - self._cache_time).total_seconds() < 3600:
                return self._cache

        sanctions = []

        try:
            response = requests.get(
                self.IDB_LIST_URL,
                headers={'User-Agent': 'DSI-Framework/1.0'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                sanctions = self._parse_html_list(response.text)
                self._cache = sanctions
                self._cache_time = datetime.utcnow()

        except Exception as e:
            logger.debug(f"IDB list fetch error: {e}")

        return sanctions

    def _parse_html_list(self, html: str) -> List[Dict]:
        """Parse IDB sanctions from HTML."""
        sanctions = []

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

            if cells and len(cells) >= 2:
                name = cells[0]
                if name and len(name) > 3 and not any(x in name.lower() for x in ['name', 'entity', 'firm', 'sanctioned']):
                    sanctions.append({
                        'name': name,
                        'country': cells[1] if len(cells) > 1 else '',
                        'sanction_type': cells[2] if len(cells) > 2 else '',
                        'from_date': cells[3] if len(cells) > 3 else '',
                        'to_date': cells[4] if len(cells) > 4 else '',
                        'source': 'IDB',
                    })

        return sanctions

    def _search_sanctions(self, query: str, sanctions: List[Dict]) -> List[Dict]:
        """Search sanctions for matching names."""
        query_lower = query.lower()
        query_parts = set(query_lower.split())
        matches = []

        for s in sanctions:
            name = s.get('name', '').lower()
            if query_lower in name or name in query_lower:
                matches.append(s)
            elif query_parts:
                name_parts = set(name.split())
                if len(query_parts & name_parts) >= min(2, len(query_parts)):
                    matches.append(s)

        return matches


class EBRDIneligibleExtractor(ProductionExtractor):
    """
    Queries European Bank for Reconstruction and Development ineligible entities.
    """

    SOURCE_NAME = "ebrd_ineligible"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    EBRD_LIST_URL = "https://www.ebrd.com/ineligible-entities.html"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for EBRDIneligibleExtractor.")
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search EBRD ineligible entities."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            entities = self._get_ineligible_list()
            matches = self._search_entities(search_term, entities)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"EBRD search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'ineligible_hit': False,
                'risk_score': 0.0,
                'note': 'No matches in EBRD ineligible entities list',
            })

        return self._create_success_result({
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],
            'ineligible_hit': True,
            'risk_score': 85.0,
        }, confidence=0.90)

    def _get_ineligible_list(self) -> List[Dict]:
        """Get EBRD ineligible entities list."""
        if self._cache and self._cache_time:
            if (datetime.utcnow() - self._cache_time).total_seconds() < 3600:
                return self._cache

        entities = []

        try:
            response = requests.get(
                self.EBRD_LIST_URL,
                headers={'User-Agent': 'DSI-Framework/1.0'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                entities = self._parse_html_list(response.text)
                self._cache = entities
                self._cache_time = datetime.utcnow()

        except Exception as e:
            logger.debug(f"EBRD list fetch error: {e}")

        return entities

    def _parse_html_list(self, html: str) -> List[Dict]:
        """Parse EBRD ineligible entities from HTML."""
        entities = []

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

            if cells and len(cells) >= 2:
                name = cells[0]
                if name and len(name) > 3 and not any(x in name.lower() for x in ['name', 'entity', 'firm']):
                    entities.append({
                        'name': name,
                        'address': cells[1] if len(cells) > 1 else '',
                        'ineligible_from': cells[2] if len(cells) > 2 else '',
                        'ineligible_until': cells[3] if len(cells) > 3 else '',
                        'prohibited_practice': cells[4] if len(cells) > 4 else '',
                        'source': 'EBRD',
                    })

        return entities

    def _search_entities(self, query: str, entities: List[Dict]) -> List[Dict]:
        """Search entities for matching names."""
        query_lower = query.lower()
        query_parts = set(query_lower.split())
        matches = []

        for e in entities:
            name = e.get('name', '').lower()
            if query_lower in name or name in query_lower:
                matches.append(e)
            elif query_parts:
                name_parts = set(name.split())
                if len(query_parts & name_parts) >= min(2, len(query_parts)):
                    matches.append(e)

        return matches


class AfDBSanctionsExtractor(ProductionExtractor):
    """
    Queries African Development Bank sanctions list.
    """

    SOURCE_NAME = "afdb_sanctions"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    AFDB_LIST_URL = "https://www.afdb.org/en/projects-operations/debarment-and-sanctions-procedures"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for AfDBSanctionsExtractor.")
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search AfDB sanctions list."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            sanctions = self._get_sanctions_list()
            matches = self._search_sanctions(search_term, sanctions)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"AfDB sanctions search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'debarred_hit': False,
                'risk_score': 0.0,
                'note': 'No matches in AfDB sanctions list',
            })

        return self._create_success_result({
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],
            'debarred_hit': True,
            'risk_score': 85.0,
        }, confidence=0.90)

    def _get_sanctions_list(self) -> List[Dict]:
        """Get AfDB sanctions list."""
        if self._cache and self._cache_time:
            if (datetime.utcnow() - self._cache_time).total_seconds() < 3600:
                return self._cache

        sanctions = []

        try:
            response = requests.get(
                self.AFDB_LIST_URL,
                headers={'User-Agent': 'DSI-Framework/1.0'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                sanctions = self._parse_html_list(response.text)
                self._cache = sanctions
                self._cache_time = datetime.utcnow()

        except Exception as e:
            logger.debug(f"AfDB list fetch error: {e}")

        return sanctions

    def _parse_html_list(self, html: str) -> List[Dict]:
        """Parse AfDB sanctions from HTML."""
        sanctions = []

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

            if cells and len(cells) >= 2:
                name = cells[0]
                if name and len(name) > 3 and not any(x in name.lower() for x in ['name', 'entity', 'firm']):
                    sanctions.append({
                        'name': name,
                        'nationality': cells[1] if len(cells) > 1 else '',
                        'from_date': cells[2] if len(cells) > 2 else '',
                        'to_date': cells[3] if len(cells) > 3 else '',
                        'ground': cells[4] if len(cells) > 4 else '',
                        'source': 'AfDB',
                    })

        return sanctions

    def _search_sanctions(self, query: str, sanctions: List[Dict]) -> List[Dict]:
        """Search sanctions for matching names."""
        query_lower = query.lower()
        query_parts = set(query_lower.split())
        matches = []

        for s in sanctions:
            name = s.get('name', '').lower()
            if query_lower in name or name in query_lower:
                matches.append(s)
            elif query_parts:
                name_parts = set(name.split())
                if len(query_parts & name_parts) >= min(2, len(query_parts)):
                    matches.append(s)

        return matches

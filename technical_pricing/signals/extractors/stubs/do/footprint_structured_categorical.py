"""
D&O Stub Extractors - Corporate Footprint, Structured Data, Categorical

CORPORATE FOOTPRINT signals:
- investor_relations: IR quality
- governance_page: Governance information
- esg_reporting: ESG reporting quality
- press_release: Corporate communications
- leadership_visibility: Executive accessibility
- hiring_signals: Risk/compliance hiring

STRUCTURED DATA signals:
- esg_rating: ESG rating
- governance_rating: Governance quality rating
- iss_governance: ISS QualityScore

Note: credit_rating uses common CreditRatingExtractor

CATEGORICAL signals:
- company_type: Public/private classification
- industry: Industry classification
- stock_exchange: Primary exchange listing
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import random

from ...base import StubExtractor, utcnow


# =============================================================================
# CORPORATE FOOTPRINT EXTRACTORS
# =============================================================================

class InvestorRelationsExtractor(StubExtractor):
    """
    STUB: Simulates investor relations quality analysis.
    
    Source: Company IR website, earnings calls
    """
    SOURCE_NAME = "investor_relations"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_ir = self._random_bool(0.7)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_ir_website": has_ir,
                "ir_site_quality": self._random_choice(["COMPREHENSIVE", "GOOD", "BASIC", "MINIMAL"]) if has_ir else None,
                "earnings_call_regular": self._random_bool(0.85) if has_ir else False,
                "investor_day_annual": self._random_bool(0.4) if has_ir else False,
                "guidance_provided": self._random_bool(0.6) if has_ir else False,
                "ir_contact_accessible": self._random_bool(0.8) if has_ir else False,
                "ir_quality_score": self._random_float(40, 95) if has_ir else 20,
            }
        }
        return self._create_success_result(data)


class GovernancePageExtractor(StubExtractor):
    """
    STUB: Simulates governance page quality analysis.
    
    Source: Company website
    """
    SOURCE_NAME = "governance_page"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_page = self._random_bool(0.65)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_governance_page": has_page,
                "board_bios_complete": self._random_bool(0.85) if has_page else False,
                "committee_charters_posted": self._random_bool(0.8) if has_page else False,
                "governance_guidelines_posted": self._random_bool(0.7) if has_page else False,
                "code_of_conduct_posted": self._random_bool(0.9) if has_page else False,
                "whistleblower_policy_posted": self._random_bool(0.6) if has_page else False,
                "governance_page_score": self._random_float(50, 95) if has_page else 15,
            }
        }
        return self._create_success_result(data)


class ESGReportingExtractor(StubExtractor):
    """
    STUB: Simulates ESG reporting quality analysis.
    
    Source: Company sustainability reports, website
    """
    SOURCE_NAME = "esg_reporting"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_reporting = self._random_bool(0.5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_esg_report": has_reporting,
                "report_framework": self._random_choice(["GRI", "SASB", "TCFD", "MULTIPLE", "CUSTOM"]) if has_reporting else None,
                "climate_disclosure": self._random_bool(0.6) if has_reporting else False,
                "diversity_disclosure": self._random_bool(0.7) if has_reporting else False,
                "human_capital_disclosure": self._random_bool(0.65) if has_reporting else False,
                "assurance_obtained": self._random_bool(0.3) if has_reporting else False,
                "esg_reporting_score": self._random_float(40, 90) if has_reporting else 20,
            }
        }
        return self._create_success_result(data)


class PressReleaseExtractor(StubExtractor):
    """
    STUB: Simulates press release quality analysis.
    
    Source: Company newsroom, PR Newswire
    """
    SOURCE_NAME = "press_release"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        pr_count = self._random_int(0, 50)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "press_releases_12m": pr_count,
                "has_newsroom": pr_count > 0,
                "communication_frequency": "HIGH" if pr_count > 30 else "MODERATE" if pr_count > 10 else "LOW",
                "earnings_pr_quality": self._random_choice(["COMPREHENSIVE", "STANDARD", "MINIMAL"]) if pr_count > 0 else None,
                "forward_looking_balanced": self._random_bool(0.75) if pr_count > 0 else None,
                "press_release_score": min(100, pr_count * 3 + self._random_int(20, 50)),
            }
        }
        return self._create_success_result(data)


class LeadershipVisibilityExtractor(StubExtractor):
    """
    STUB: Simulates leadership visibility analysis.
    
    Source: Conference appearances, media, LinkedIn
    """
    SOURCE_NAME = "leadership_visibility"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "ceo_conference_appearances": self._random_int(0, 15),
                "ceo_media_mentions": self._random_int(0, 50),
                "leadership_linkedin_active": self._random_bool(0.6),
                "accessible_to_investors": self._random_bool(0.7),
                "thought_leadership_content": self._random_bool(0.4),
                "visibility_score": self._random_float(30, 90),
            }
        }
        return self._create_success_result(data)


class HiringSignalsExtractor(StubExtractor):
    """
    STUB: Simulates risk/compliance hiring analysis.
    
    Source: Job postings, LinkedIn
    """
    SOURCE_NAME = "hiring_signals"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_postings = self._random_bool(0.4)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_compliance_postings": has_postings,
                "legal_hiring": self._random_bool(0.3),
                "internal_audit_hiring": self._random_bool(0.25),
                "risk_management_hiring": self._random_bool(0.2),
                "governance_role_hiring": self._random_bool(0.15),
                "total_risk_compliance_postings": self._random_int(0, 10) if has_postings else 0,
                "hiring_signals_score": self._random_float(30, 80),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# STRUCTURED DATA EXTRACTORS
# =============================================================================

class ESGRatingExtractor(StubExtractor):
    """
    STUB: Simulates ESG rating lookup.
    
    Source: MSCI, Sustainalytics, ISS
    """
    SOURCE_NAME = "esg_rating"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rating = self._random_bool(0.5)
        
        if has_rating:
            msci_grade = self._random_choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"])
            score = {"AAA": 95, "AA": 85, "A": 75, "BBB": 65, "BB": 50, "B": 35, "CCC": 20}.get(msci_grade, 50)
        else:
            msci_grade = None
            score = 50
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_esg_rating": has_rating,
                "msci_esg_rating": msci_grade,
                "sustainalytics_risk": self._random_choice(["NEGLIGIBLE", "LOW", "MEDIUM", "HIGH", "SEVERE"]) if has_rating else None,
                "esg_percentile": self._random_int(10, 95) if has_rating else None,
                "controversy_flag": self._random_bool(0.1) if has_rating else False,
                "esg_rating_score": score,
            }
        }
        return self._create_success_result(data)


class GovernanceRatingExtractor(StubExtractor):
    """
    STUB: Simulates governance rating lookup.
    
    Source: Governance rating providers
    """
    SOURCE_NAME = "governance_rating"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rating = self._random_bool(0.45)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_governance_rating": has_rating,
                "governance_score": self._random_float(30, 95) if has_rating else 50,
                "board_score": self._random_float(30, 95) if has_rating else None,
                "shareholder_rights_score": self._random_float(30, 95) if has_rating else None,
                "compensation_score": self._random_float(30, 95) if has_rating else None,
                "audit_score": self._random_float(30, 95) if has_rating else None,
            }
        }
        return self._create_success_result(data)


class ISSGovernanceExtractor(StubExtractor):
    """
    STUB: Simulates ISS Governance QualityScore lookup.
    
    Source: ISS
    """
    SOURCE_NAME = "iss_governance"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_score = self._random_bool(0.4)
        
        if has_score:
            # ISS uses decile scores 1-10 (1 = lowest risk)
            overall_decile = self._random_int(1, 10)
            board_decile = self._random_int(1, 10)
            compensation_decile = self._random_int(1, 10)
            audit_decile = self._random_int(1, 10)
            rights_decile = self._random_int(1, 10)
        else:
            overall_decile = None
            board_decile = None
            compensation_decile = None
            audit_decile = None
            rights_decile = None
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_iss_score": has_score,
                "overall_decile": overall_decile,
                "board_structure_decile": board_decile,
                "compensation_decile": compensation_decile,
                "audit_risk_decile": audit_decile,
                "shareholder_rights_decile": rights_decile,
                "iss_governance_score": (11 - overall_decile) * 10 if overall_decile else 50,  # Convert to 0-100
            }
        }
        return self._create_success_result(data)


# =============================================================================
# CATEGORICAL EXTRACTORS
# =============================================================================

class CompanyTypeExtractor(StubExtractor):
    """
    STUB: Simulates company type classification.
    
    Source: SEC filings, market data
    """
    SOURCE_NAME = "company_type"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        is_public = self._random_bool(0.6)
        
        if is_public:
            market_cap = self._random_int(50_000_000, 500_000_000_000)
            if market_cap > 10_000_000_000:
                company_type = "PUBLIC_LARGE_CAP"
            elif market_cap > 2_000_000_000:
                company_type = "PUBLIC_MID_CAP"
            elif market_cap > 300_000_000:
                company_type = "PUBLIC_SMALL_CAP"
            else:
                company_type = "PUBLIC_MICRO_CAP"
            
            # Override for special cases
            if self._random_bool(0.05):
                company_type = "SPAC"
            elif self._random_bool(0.08):
                company_type = "PRE_IPO"
        else:
            market_cap = None
            if self._random_bool(0.6):
                company_type = "PRIVATE_BACKED"
            elif self._random_bool(0.2):
                company_type = "NONPROFIT"
            else:
                company_type = "PRIVATE_OTHER"
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "company_type": company_type,
                "is_public": is_public,
                "market_cap": market_cap,
                "sec_reporting": is_public,
                "is_spac": company_type == "SPAC",
                "is_pre_ipo": company_type == "PRE_IPO",
            }
        }
        return self._create_success_result(data)


class DOIndustryExtractor(StubExtractor):
    """
    STUB: Simulates D&O-specific industry classification.
    
    Source: SEC filings, business databases
    """
    SOURCE_NAME = "do_industry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    INDUSTRIES = [
        "CRYPTO_DIGITAL", "CANNABIS", "HEALTHCARE_PHARMA", "FINANCIAL_SERVICES",
        "TECHNOLOGY", "ENERGY", "REAL_ESTATE", "RETAIL_CONSUMER", "MANUFACTURING", "OTHER"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        industry = self._random_choice(
            self.INDUSTRIES,
            weights=[0.03, 0.02, 0.15, 0.18, 0.20, 0.08, 0.08, 0.10, 0.10, 0.06]
        )
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_industry": industry,
                "sic_code": self._random_int(1000, 9999),
                "naics_code": self._random_int(100000, 999999),
                "is_high_risk_industry": industry in ["CRYPTO_DIGITAL", "CANNABIS", "HEALTHCARE_PHARMA"],
                "is_regulated_industry": industry in ["FINANCIAL_SERVICES", "HEALTHCARE_PHARMA", "ENERGY"],
            }
        }
        return self._create_success_result(data)


class StockExchangeExtractor(StubExtractor):
    """
    STUB: Simulates stock exchange listing lookup.
    
    Source: Exchange data, SEC filings
    """
    SOURCE_NAME = "stock_exchange"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        is_listed = self._random_bool(0.6)
        
        if is_listed:
            exchange = self._random_choice(
                ["NYSE", "NASDAQ", "NYSE_AMERICAN", "OTC", "FOREIGN"],
                weights=[0.35, 0.40, 0.05, 0.10, 0.10]
            )
        else:
            exchange = "NONE"
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_exchange": exchange,
                "is_listed": is_listed,
                "is_major_exchange": exchange in ["NYSE", "NASDAQ"],
                "foreign_private_issuer": exchange == "FOREIGN" and self._random_bool(0.5),
                "adr": exchange == "FOREIGN" and self._random_bool(0.3),
            }
        }
        return self._create_success_result(data)

"""
Cyber Stub Extractors - Public Record & Structured Data Signal Groups

PUBLIC RECORD signals:
- breach_history: Historical data breaches
- litigation_history: Privacy/data breach lawsuits
- credential_exposure: Corporate domain credential exposure
- dark_web: Dark web data exposure

Note: regulatory_action uses common RegulatoryEnforcementExtractor

STRUCTURED DATA signals:
- security_rating: Third-party security ratings (BitSight, etc.)
- esg_cyber: ESG cyber component

Note: credit_rating uses common CreditRatingExtractor
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import random

from ...base import StubExtractor, utcnow


# =============================================================================
# PUBLIC RECORD EXTRACTORS
# =============================================================================

class BreachHistoryExtractor(StubExtractor):
    """
    STUB: Simulates data breach history lookup.
    
    Real implementation would check:
    - HHS breach portal (healthcare)
    - State AG breach notifications
    - Have I Been Pwned corporate breaches
    - News/press mentions
    - SEC filings (material breaches)
    
    Source: HHS, State AGs, HIBP, news APIs
    """
    SOURCE_NAME = "breach_history_lookup"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_breach = self._random_bool(0.25)
        
        if has_breach:
            breach_count = self._random_int(1, 4)
            most_recent_years_ago = self._random_float(0.1, 8)
            total_records = self._random_int(1000, 50_000_000)
            breach_types = self._random_sample(
                ["PII", "PHI", "FINANCIAL", "CREDENTIALS", "SSN", "PAYMENT_CARD"],
                self._random_int(1, 3)
            )
        else:
            breach_count = 0
            most_recent_years_ago = None
            total_records = 0
            breach_types = []
        
        # Calculate score (higher = better/cleaner record)
        if not has_breach:
            score = 100
        else:
            score = 100
            score -= breach_count * 15
            score -= min(40, total_records / 500000)  # Scale penalty by records
            if most_recent_years_ago and most_recent_years_ago < 1:
                score -= 30  # Recent breach penalty
            elif most_recent_years_ago and most_recent_years_ago < 3:
                score -= 15
            score = max(0, score)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_breach_history": has_breach,
                "breach_count": breach_count,
                "total_records_exposed": total_records,
                "most_recent_breach_years_ago": round(most_recent_years_ago, 1) if most_recent_years_ago else None,
                "breach_types": breach_types,
                "has_recent_breach": most_recent_years_ago is not None and most_recent_years_ago < 2,
                "has_major_breach": total_records > 1_000_000 if has_breach else False,
                "regulatory_notification_required": self._random_bool(0.8) if has_breach else False,
                "class_action_filed": self._random_bool(0.3) if has_breach else False,
                "breach_history_score": round(score, 1),
            }
        }
        return self._create_success_result(data)


class LitigationHistoryExtractor(StubExtractor):
    """
    STUB: Simulates data breach/privacy litigation lookup.
    
    Real implementation would check:
    - PACER/federal court records
    - State court records
    - Class action databases
    - Settlement tracking
    
    Source: Court records, legal databases
    """
    SOURCE_NAME = "litigation_lookup"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_litigation = self._random_bool(0.15)
        
        if has_litigation:
            case_count = self._random_int(1, 5)
            has_class_action = self._random_bool(0.4)
            largest_settlement = self._random_int(50000, 50_000_000) if self._random_bool(0.5) else None
        else:
            case_count = 0
            has_class_action = False
            largest_settlement = None
        
        # Score calculation
        score = 100
        if has_litigation:
            score -= case_count * 10
            if has_class_action:
                score -= 20
            if largest_settlement and largest_settlement > 1_000_000:
                score -= 15
        score = max(0, score)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_privacy_litigation": has_litigation,
                "case_count": case_count,
                "has_class_action": has_class_action,
                "pending_cases": self._random_int(0, 2) if has_litigation else 0,
                "resolved_cases": case_count - self._random_int(0, min(2, case_count)) if has_litigation else 0,
                "largest_settlement_usd": largest_settlement,
                "total_settlements_usd": largest_settlement * self._random_float(1, 2.5) if largest_settlement else None,
                "case_types": self._random_sample(
                    ["DATA_BREACH", "PRIVACY_VIOLATION", "GDPR", "CCPA", "WIRETAPPING"],
                    self._random_int(1, 2)
                ) if has_litigation else [],
                "litigation_score": round(score, 1),
            }
        }
        return self._create_success_result(data)


class CredentialExposureExtractor(StubExtractor):
    """
    STUB: Simulates corporate credential exposure check.
    
    Real implementation would check:
    - Have I Been Pwned API for domain
    - Credential dump databases
    - Paste sites
    - Dark web monitoring services
    
    Source: HIBP API, breach databases
    """
    SOURCE_NAME = "credential_exposure_check"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_exposure = self._random_bool(0.55)  # Most companies have some exposure
        
        if has_exposure:
            breach_count = self._random_int(1, 15)  # Breaches containing domain emails
            email_count = self._random_int(10, 10000)
            password_count = self._random_int(0, email_count)
            recent_exposure = self._random_bool(0.3)
        else:
            breach_count = 0
            email_count = 0
            password_count = 0
            recent_exposure = False
        
        # Score (higher = safer)
        score = 100
        if has_exposure:
            score -= min(30, breach_count * 3)
            score -= min(30, email_count / 500)
            if password_count > 100:
                score -= 15
            if recent_exposure:
                score -= 15
        score = max(0, score)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_credential_exposure": has_exposure,
                "breach_count": breach_count,
                "total_emails_exposed": email_count,
                "emails_with_passwords": password_count,
                "password_exposure_percentage": round(password_count / email_count * 100, 1) if email_count > 0 else 0,
                "most_recent_exposure_date": self._random_date_or_none(years_back=3) if has_exposure else None,
                "has_recent_exposure": recent_exposure,
                "executive_emails_exposed": self._random_int(0, 10) if has_exposure else 0,
                "plaintext_passwords_found": self._random_bool(0.2) if password_count > 0 else False,
                "credential_exposure_score": round(score, 1),
            }
        }
        return self._create_success_result(data)


class DarkWebExtractor(StubExtractor):
    """
    STUB: Simulates dark web monitoring.
    
    Real implementation would check:
    - Dark web forums for company mentions
    - Leaked data for sale
    - Access credentials being sold
    - Threat actor discussions
    
    Source: Dark web monitoring services
    """
    SOURCE_NAME = "dark_web_monitoring"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_exposure = self._random_bool(0.20)
        has_active_threat = self._random_bool(0.05)
        
        if has_exposure:
            mention_count = self._random_int(1, 20)
            data_for_sale = self._random_bool(0.3)
            access_for_sale = self._random_bool(0.1)
        else:
            mention_count = 0
            data_for_sale = False
            access_for_sale = False
        
        # Score (higher = safer)
        score = 100
        if has_exposure:
            score -= min(30, mention_count * 3)
            if data_for_sale:
                score -= 25
            if access_for_sale:
                score -= 30
            if has_active_threat:
                score -= 20
        score = max(0, score)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_dark_web_presence": has_exposure,
                "mention_count": mention_count,
                "data_for_sale": data_for_sale,
                "access_for_sale": access_for_sale,
                "has_active_threat": has_active_threat,
                "threat_types": self._random_sample(
                    ["DATA_DUMP", "CREDENTIALS", "NETWORK_ACCESS", "RANSOMWARE_LISTING", "THREAT_DISCUSSION"],
                    self._random_int(1, 3)
                ) if has_exposure else [],
                "most_recent_detection_date": self._random_date_or_none(years_back=1) if has_exposure else None,
                "threat_severity": "CRITICAL" if access_for_sale else "HIGH" if data_for_sale else "MODERATE" if has_exposure else "LOW",
                "dark_web_score": round(score, 1),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# STRUCTURED DATA EXTRACTORS
# =============================================================================

class SecurityRatingExtractor(StubExtractor):
    """
    STUB: Simulates third-party security rating lookup.
    
    Real implementation would check:
    - BitSight rating
    - SecurityScorecard rating
    - RiskRecon
    - UpGuard
    
    Source: Security rating vendor APIs
    """
    SOURCE_NAME = "security_rating_lookup"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rating = self._random_bool(0.6)
        
        if has_rating:
            bitsight_score = self._random_int(300, 900)
            securityscorecard = self._random_choice(["A", "B", "C", "D", "F"])
            grade_scores = {"A": 90, "B": 75, "C": 60, "D": 45, "F": 25}
            normalized_score = (bitsight_score - 300) / 6  # Normalize to 0-100
        else:
            bitsight_score = None
            securityscorecard = None
            normalized_score = 50  # Default neutral
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_security_rating": has_rating,
                "bitsight_score": bitsight_score,
                "bitsight_grade": self._bitsight_grade(bitsight_score) if bitsight_score else None,
                "securityscorecard_grade": securityscorecard,
                "normalized_score": round(normalized_score, 1),
                "rating_trend": self._random_choice(["IMPROVING", "STABLE", "DECLINING"]) if has_rating else None,
                "peer_comparison": self._random_choice(["ABOVE_AVERAGE", "AVERAGE", "BELOW_AVERAGE"]) if has_rating else None,
                "risk_factors_count": self._random_int(0, 15) if has_rating else None,
                "critical_findings": self._random_int(0, 5) if has_rating else None,
                "security_rating_score": round(normalized_score, 1),
            }
        }
        return self._create_success_result(data)
    
    def _bitsight_grade(self, score: int) -> str:
        if score >= 740:
            return "ADVANCED"
        elif score >= 640:
            return "GOOD"
        elif score >= 540:
            return "INTERMEDIATE"
        elif score >= 440:
            return "BASIC"
        else:
            return "MINIMAL"


class ESGCyberExtractor(StubExtractor):
    """
    STUB: Simulates ESG cyber component extraction.
    
    Real implementation would check:
    - ESG rating providers' cyber component
    - Data privacy/security governance scores
    - Cyber risk management indicators
    
    Source: ESG rating providers (MSCI, Sustainalytics, etc.)
    """
    SOURCE_NAME = "esg_cyber_lookup"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_esg_rating = self._random_bool(0.4)
        
        if has_esg_rating:
            cyber_score = self._random_int(30, 95)
            governance_score = self._random_int(35, 90)
            data_privacy_score = self._random_int(30, 90)
        else:
            cyber_score = 50  # Default neutral
            governance_score = 50
            data_privacy_score = 50
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_esg_rating": has_esg_rating,
                "cyber_risk_score": cyber_score,
                "data_governance_score": governance_score,
                "data_privacy_score": data_privacy_score,
                "overall_esg_cyber_score": round((cyber_score + governance_score + data_privacy_score) / 3, 1),
                "rating_provider": self._random_choice(["MSCI", "SUSTAINALYTICS", "ISS", "REFINITIV"]) if has_esg_rating else None,
                "peer_percentile": self._random_int(10, 95) if has_esg_rating else None,
                "has_cyber_governance_policy": self._random_bool(0.6) if has_esg_rating else None,
                "board_cyber_oversight": self._random_bool(0.5) if has_esg_rating else None,
                "esg_cyber_score": cyber_score,
            }
        }
        return self._create_success_result(data)


# =============================================================================
# CATEGORICAL EXTRACTORS
# =============================================================================

class IndustryClassificationExtractor(StubExtractor):
    """
    STUB: Simulates industry classification inference.
    
    Real implementation would use:
    - Company website analysis
    - LinkedIn company page
    - Crunchbase industry
    - Business registries
    - SIC/NAICS codes
    
    Source: Web scraping, business databases
    """
    SOURCE_NAME = "industry_classification"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    INDUSTRIES = [
        "TECHNOLOGY", "FINANCIAL_SERVICES", "HEALTHCARE", "RETAIL",
        "MANUFACTURING", "PROFESSIONAL_SERVICES", "EDUCATION",
        "GOVERNMENT", "ENERGY", "OTHER"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        primary_industry = self._random_choice(self.INDUSTRIES)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_industry": primary_industry,
                "confidence": self._random_float(0.7, 0.99),
                "secondary_industries": self._random_sample(
                    [i for i in self.INDUSTRIES if i != primary_industry], 
                    self._random_int(0, 2)
                ),
                "sic_code": self._random_int(1000, 9999),
                "naics_code": self._random_int(100000, 999999),
                "is_regulated_industry": primary_industry in ["FINANCIAL_SERVICES", "HEALTHCARE", "ENERGY", "GOVERNMENT"],
                "is_high_data_volume": primary_industry in ["TECHNOLOGY", "FINANCIAL_SERVICES", "HEALTHCARE", "RETAIL"],
            }
        }
        return self._create_success_result(data)


class CompanySizeExtractor(StubExtractor):
    """
    STUB: Simulates company size inference.
    
    Real implementation would use:
    - LinkedIn employee count
    - Revenue estimates (ZoomInfo, etc.)
    - Office locations
    - Job posting volume
    
    Source: LinkedIn, business databases
    """
    SOURCE_NAME = "company_size_inference"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    SIZE_BANDS = ["MICRO", "SMALL", "MEDIUM", "LARGE", "ENTERPRISE"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        employee_count = self._random_choice([
            self._random_int(1, 10),      # MICRO
            self._random_int(11, 50),     # SMALL
            self._random_int(51, 250),    # MEDIUM
            self._random_int(251, 1000),  # LARGE
            self._random_int(1001, 50000) # ENTERPRISE
        ])
        
        if employee_count <= 10:
            size_band = "MICRO"
        elif employee_count <= 50:
            size_band = "SMALL"
        elif employee_count <= 250:
            size_band = "MEDIUM"
        elif employee_count <= 1000:
            size_band = "LARGE"
        else:
            size_band = "ENTERPRISE"
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "size_band": size_band,
                "employee_count_estimate": employee_count,
                "employee_count_confidence": self._random_float(0.6, 0.95),
                "revenue_estimate_usd": employee_count * self._random_int(50000, 200000),
                "office_count": self._random_int(1, max(1, employee_count // 100)),
                "is_public": self._random_bool(0.15) if size_band in ["LARGE", "ENTERPRISE"] else False,
            }
        }
        return self._create_success_result(data)


class OperationalBaseExtractor(StubExtractor):
    """
    STUB: Simulates primary geography inference.
    
    Real implementation would use:
    - Headquarters location
    - Domain TLD
    - Employee distribution
    - Customer base indicators
    
    Source: Company website, business registries
    """
    SOURCE_NAME = "geography_inference"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    GEOGRAPHIES = ["US", "UK", "EU", "APAC", "OTHER"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        primary_geography = self._random_choice(self.GEOGRAPHIES, weights=[0.5, 0.15, 0.2, 0.1, 0.05])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_geography": primary_geography,
                "headquarters_country": self._random_choice(["US", "UK", "DE", "FR", "SG", "AU", "CA", "JP"]),
                "operational_countries_count": self._random_int(1, 20),
                "has_eu_presence": primary_geography in ["UK", "EU"] or self._random_bool(0.3),
                "has_us_presence": primary_geography == "US" or self._random_bool(0.4),
                "has_apac_presence": primary_geography == "APAC" or self._random_bool(0.2),
                "gdpr_applicable": primary_geography in ["UK", "EU"] or self._random_bool(0.3),
                "ccpa_applicable": primary_geography == "US" or self._random_bool(0.2),
            }
        }
        return self._create_success_result(data)

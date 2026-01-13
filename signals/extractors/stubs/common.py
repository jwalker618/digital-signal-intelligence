"""
Common Stub Extractors - Reusable Across Coverage Domains

These extractors provide data that is common across multiple coverage types
as identified in the coverage_crosswalk.json:

- Credit Rating: All 7 coverages
- Leadership Stability: All 7 coverages  
- Public Reporting/Disclosure: All 7 coverages
- Regulatory Actions/Enforcement: All 7 coverages
- Incident/Breach History: All 7 coverages
- Industry Engagement: All 7 coverages
- Certification/License Status: 6 coverages
- Banking Relationship: 5 coverages

Each extractor simulates realistic API responses from common data providers.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from ..base import StubExtractor, utcnow
from ...types import ExtractorResult


# =============================================================================
# CREDIT RATING EXTRACTOR
# Used by: aerospace, cyber, do, energy, fi, pi, marine
# =============================================================================

class CreditRatingExtractor(StubExtractor):
    """
    STUB: Simulates credit rating data from major rating agencies.
    
    Real implementation would query:
    - S&P Global Ratings API
    - Moody's Analytics API
    - Fitch Ratings API
    - Commercial credit bureaus (D&B, Experian Business)
    
    Crosswalk mapping:
    - aerospace: signal_features/financial_stability/credit_rating
    - cyber: signal_features/structured_data/credit_rating
    - do: signal_features/structured_data/credit_rating
    - energy: signal_features/financial_stability/credit_rating
    - fi: signal_features/network_authority/credit_rating
    - pi: signal_features/firm_stability/financial_stability
    - marine: signal_features/structured_data/credit_rating
    """
    SOURCE_NAME = "credit_rating_aggregator"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY  # Ratings change infrequently
    
    # Rating scales
    SP_RATINGS = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", 
                  "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
                  "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]
    
    MOODY_RATINGS = ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3",
                     "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3",
                     "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C"]
    
    OUTLOOKS = ["POSITIVE", "STABLE", "NEGATIVE", "WATCH_POSITIVE", 
                "WATCH_NEGATIVE", "DEVELOPING"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Simulate whether entity has ratings (large entities more likely)
        has_sp = self._random_bool(0.6)
        has_moody = self._random_bool(0.5)
        has_fitch = self._random_bool(0.4)
        
        # Higher probability of no ratings for smaller entities
        if not has_sp and not has_moody and not has_fitch:
            has_sp = self._random_bool(0.3)  # Give another chance
        
        ratings = []
        
        if has_sp:
            # Weight towards investment grade
            sp_idx = self._random_int(0, len(self.SP_RATINGS) - 1)
            if self._random_bool(0.6):  # Bias towards investment grade
                sp_idx = min(sp_idx, 9)  # BBB- or better
            ratings.append({
                "agency": "S&P",
                "rating": self.SP_RATINGS[sp_idx],
                "outlook": self._random_choice(self.OUTLOOKS, weights=[0.2, 0.5, 0.2, 0.03, 0.05, 0.02]),
                "rating_date": self._random_date_iso(years_back=2),
                "is_investment_grade": sp_idx <= 9,
            })
        
        if has_moody:
            moody_idx = self._random_int(0, len(self.MOODY_RATINGS) - 1)
            if self._random_bool(0.6):
                moody_idx = min(moody_idx, 9)
            ratings.append({
                "agency": "Moodys",
                "rating": self.MOODY_RATINGS[moody_idx],
                "outlook": self._random_choice(self.OUTLOOKS, weights=[0.2, 0.5, 0.2, 0.03, 0.05, 0.02]),
                "rating_date": self._random_date_iso(years_back=2),
                "is_investment_grade": moody_idx <= 9,
            })
        
        if has_fitch:
            fitch_idx = self._random_int(0, len(self.SP_RATINGS) - 1)
            if self._random_bool(0.6):
                fitch_idx = min(fitch_idx, 9)
            ratings.append({
                "agency": "Fitch",
                "rating": self.SP_RATINGS[fitch_idx],  # Fitch uses S&P scale
                "outlook": self._random_choice(self.OUTLOOKS, weights=[0.2, 0.5, 0.2, 0.03, 0.05, 0.02]),
                "rating_date": self._random_date_iso(years_back=2),
                "is_investment_grade": fitch_idx <= 9,
            })
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_rating": len(ratings) > 0,
                "ratings": ratings,
                "rating_count": len(ratings),
                "any_investment_grade": any(r.get("is_investment_grade") for r in ratings),
                "any_negative_outlook": any(r.get("outlook") in ["NEGATIVE", "WATCH_NEGATIVE"] for r in ratings),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# CORPORATE REGISTRY EXTRACTOR
# Provides: Leadership stability, corporate structure, incorporation data
# Used by: All coverages for management_stability, corporate_structure
# =============================================================================

class CorporateRegistryExtractor(StubExtractor):
    """
    STUB: Simulates corporate registry and business intelligence data.
    
    Real implementation would query:
    - Companies House (UK)
    - SEC EDGAR (US)
    - OpenCorporates
    - D&B / Experian Business
    - Bloomberg Company Data
    
    Crosswalk mapping (Leadership Stability):
    - aerospace: signal_features/corporate_governance/management_stability
    - cyber: signal_features/corporate_footprint/security_leadership
    - do: signal_features/executive/executive_stability
    - energy: signal_features/corporate_footprint/hse_leadership
    - fi: signal_features/governance/executive_stability
    - pi: signal_features/firm_stability/partner_stability
    - marine: signal_features/fleet_profile/management_consistency
    """
    SOURCE_NAME = "corporate_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    COMPANY_TYPES = ["PUBLIC", "PRIVATE", "SUBSIDIARY", "PARTNERSHIP", "STATE_OWNED"]
    INCORPORATION_JURISDICTIONS = ["US_DE", "US_NY", "UK", "IE", "LU", "NL", "SG", "HK", "AE", "CH"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        company_type = self._random_choice(self.COMPANY_TYPES, weights=[0.3, 0.4, 0.15, 0.05, 0.1])
        years_operating = self._random_int(1, 80)
        
        # Generate executive team
        executives = []
        roles = ["CEO", "CFO", "COO", "General Counsel", "Chief Safety Officer", "VP Operations"]
        for role in roles:
            if role in ["CEO", "CFO"] or self._random_bool(0.7):
                tenure_years = self._random_int(0, min(15, years_operating))
                executives.append({
                    "role": role,
                    "tenure_years": tenure_years,
                    "appointment_date": self._random_date_iso(years_back=tenure_years) if tenure_years > 0 else utcnow().date().isoformat(),
                    "previous_company_count": self._random_int(0, 5),
                    "industry_experience_years": tenure_years + self._random_int(0, 20),
                })
        
        # Calculate turnover metrics
        recent_departures = self._random_int(0, 3) if self._random_bool(0.3) else 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "legal_name": f"Entity {entity_id}",
                "company_type": company_type,
                "incorporation_jurisdiction": self._random_choice(self.INCORPORATION_JURISDICTIONS),
                "incorporation_date": self._random_date_iso(years_back=years_operating),
                "years_operating": years_operating,
                "is_public": company_type == "PUBLIC",
                "is_state_owned": company_type == "STATE_OWNED",
                "parent_company": f"Parent_{self._random_id()}" if company_type == "SUBSIDIARY" else None,
                "executives": executives,
                "ceo_tenure_years": next((e["tenure_years"] for e in executives if e["role"] == "CEO"), 0),
                "executive_count": len(executives),
                "recent_executive_departures": recent_departures,
                "has_dedicated_safety_officer": any(e["role"] == "Chief Safety Officer" for e in executives),
                "board_size": self._random_int(5, 15) if company_type == "PUBLIC" else self._random_int(3, 9),
                "independent_directors_pct": self._random_float(0.3, 0.8, 2) if company_type == "PUBLIC" else None,
                "last_agm_date": self._random_date_iso(years_back=1) if company_type == "PUBLIC" else None,
                "subsidiaries_count": self._random_int(0, 50),
                "operating_countries": self._random_int(1, 30),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# REGULATORY ENFORCEMENT EXTRACTOR
# Used by: All coverages for enforcement_actions, regulatory_action
# =============================================================================

class RegulatoryEnforcementExtractor(StubExtractor):
    """
    STUB: Simulates regulatory enforcement data across multiple regulators.
    
    Real implementation would query:
    - FAA Enforcement Database (aviation)
    - SEC EDGAR (financial)
    - EPA ECHO (environmental)
    - OSHA violations (safety)
    - FCA/PRA Register (UK financial)
    - State regulator databases
    
    Crosswalk mapping:
    - aerospace: signal_features/regulatory_compliance/enforcement_actions
    - cyber: signal_features/public_record/regulatory_action
    - do: signal_features/litigation/regulatory_action
    - energy: signal_features/environmental_compliance/epa_violation
    - fi: signal_features/regulatory_compliance/enforcement_action
    - pi: signal_features/litigation_history/regulatory_enforcement
    - marine: signal_features/sanctions_compliance/sanctions_status
    """
    SOURCE_NAME = "regulatory_enforcement_aggregator"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    ENFORCEMENT_TYPES = ["FINE", "WARNING", "CONSENT_ORDER", "CEASE_DESIST", 
                         "LICENSE_SUSPENSION", "LICENSE_REVOCATION", "CIVIL_PENALTY"]
    
    SEVERITY_LEVELS = ["MINOR", "MODERATE", "SIGNIFICANT", "SEVERE"]
    
    def _do_extract(self, entity_id: str, regulator_type: str = None, **kwargs) -> ExtractorResult:
        """
        Extract enforcement data.
        
        Args:
            entity_id: Entity identifier
            regulator_type: Optional filter (e.g., "AVIATION", "FINANCIAL", "ENVIRONMENTAL")
        """
        # Most entities have clean records
        has_enforcement = self._random_bool(0.25)
        
        actions = []
        if has_enforcement:
            num_actions = self._random_int(1, 5)
            for _ in range(num_actions):
                action_type = self._random_choice(self.ENFORCEMENT_TYPES, 
                    weights=[0.35, 0.25, 0.15, 0.10, 0.08, 0.02, 0.05])
                severity = self._random_choice(self.SEVERITY_LEVELS,
                    weights=[0.4, 0.35, 0.20, 0.05])
                
                fine_amount = None
                if action_type in ["FINE", "CIVIL_PENALTY"]:
                    if severity == "MINOR":
                        fine_amount = self._random_int(1000, 50000)
                    elif severity == "MODERATE":
                        fine_amount = self._random_int(50000, 500000)
                    elif severity == "SIGNIFICANT":
                        fine_amount = self._random_int(500000, 5000000)
                    else:
                        fine_amount = self._random_int(5000000, 50000000)
                
                actions.append({
                    "action_id": self._random_id("ENF"),
                    "action_type": action_type,
                    "severity": severity,
                    "action_date": self._random_date_iso(years_back=5),
                    "regulator": self._random_choice(["FAA", "EASA", "CAA", "DGCA", "CAAC"]) if regulator_type == "AVIATION" else self._random_choice(["FTC", "SEC", "FCA", "FINMA", "EPA"]),
                    "fine_amount": fine_amount,
                    "fine_currency": "USD" if fine_amount else None,
                    "is_resolved": self._random_bool(0.8),
                    "resolution_date": self._random_date_iso(years_back=3) if self._random_bool(0.8) else None,
                    "description": f"Enforcement action {action_type}",
                })
        
        # Calculate summary metrics
        total_fines = sum(a.get("fine_amount", 0) or 0 for a in actions)
        severe_actions = sum(1 for a in actions if a.get("severity") in ["SIGNIFICANT", "SEVERE"])
        pending_actions = sum(1 for a in actions if not a.get("is_resolved"))
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "regulator_type_filter": regulator_type,
            "data": {
                "has_enforcement_history": has_enforcement,
                "total_actions": len(actions),
                "actions": actions,
                "total_fines_usd": total_fines,
                "severe_action_count": severe_actions,
                "pending_action_count": pending_actions,
                "most_recent_action_date": max((a["action_date"] for a in actions), default=None),
                "has_license_action": any(a["action_type"] in ["LICENSE_SUSPENSION", "LICENSE_REVOCATION"] for a in actions),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# INDUSTRY ASSOCIATION EXTRACTOR
# Used by: All coverages for industry_engagement, association_leadership
# =============================================================================

class IndustryAssociationExtractor(StubExtractor):
    """
    STUB: Simulates industry association membership data.
    
    Real implementation would query:
    - Association membership directories
    - Conference attendance records
    - Committee participation lists
    - LinkedIn/professional network data
    
    Crosswalk mapping:
    - aerospace: signal_features/corporate_governance/industry_engagement
    - cyber: signal_features/network_authority/industry_body
    - do: signal_features/network_authority/industry_association
    - energy: signal_features/network_authority/industry_association
    - fi: signal_features/network_authority/industry_association
    - pi: signal_features/network_authority/association_leadership
    - marine: signal_features/network_authority/industry_association
    """
    SOURCE_NAME = "industry_association_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    # Generic associations - specific coverages add their own
    MEMBERSHIP_TIERS = ["FOUNDING", "PLATINUM", "GOLD", "STANDARD", "ASSOCIATE"]
    
    def _do_extract(self, entity_id: str, industry: str = None, **kwargs) -> ExtractorResult:
        """
        Extract industry association data.
        
        Args:
            entity_id: Entity identifier
            industry: Industry filter (AVIATION, CYBER, FINANCIAL, etc.)
        """
        # Define associations by industry
        if industry == "AVIATION":
            associations = [
                {"name": "IATA", "type": "TRADE", "prestige": "HIGH"},
                {"name": "Flight Safety Foundation", "type": "SAFETY", "prestige": "HIGH"},
                {"name": "ACI", "type": "TRADE", "prestige": "MEDIUM"},
                {"name": "NBAA", "type": "TRADE", "prestige": "MEDIUM"},
                {"name": "Regional Airline Association", "type": "TRADE", "prestige": "MEDIUM"},
            ]
        elif industry == "CYBER":
            associations = [
                {"name": "ISACA", "type": "PROFESSIONAL", "prestige": "HIGH"},
                {"name": "ISC2", "type": "PROFESSIONAL", "prestige": "HIGH"},
                {"name": "FS-ISAC", "type": "SHARING", "prestige": "HIGH"},
            ]
        elif industry == "MARINE":
            associations = [
                {"name": "BIMCO", "type": "TRADE", "prestige": "HIGH"},
                {"name": "ICS", "type": "TRADE", "prestige": "HIGH"},
                {"name": "INTERTANKO", "type": "TRADE", "prestige": "MEDIUM"},
            ]
        else:
            associations = [
                {"name": "Industry Trade Association", "type": "TRADE", "prestige": "MEDIUM"},
                {"name": "Professional Standards Body", "type": "PROFESSIONAL", "prestige": "MEDIUM"},
            ]
        
        memberships = []
        for assoc in associations:
            if self._random_bool(0.5):  # 50% chance of each membership
                memberships.append({
                    "association_name": assoc["name"],
                    "association_type": assoc["type"],
                    "prestige_level": assoc["prestige"],
                    "membership_tier": self._random_choice(self.MEMBERSHIP_TIERS, 
                        weights=[0.05, 0.10, 0.20, 0.50, 0.15]),
                    "member_since": self._random_date_iso(years_back=15),
                    "years_member": self._random_int(1, 15),
                    "committee_participation": self._random_bool(0.3),
                    "leadership_role": self._random_bool(0.1),
                    "conference_speaker": self._random_bool(0.2),
                    "is_active": self._random_bool(0.9),
                })
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "industry_filter": industry,
            "data": {
                "membership_count": len(memberships),
                "memberships": memberships,
                "has_high_prestige_membership": any(m.get("prestige_level") == "HIGH" for m in memberships),
                "has_leadership_role": any(m.get("leadership_role") for m in memberships),
                "has_committee_participation": any(m.get("committee_participation") for m in memberships),
                "total_years_membership": sum(m.get("years_member", 0) for m in memberships),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# PUBLIC FINANCIALS EXTRACTOR
# Used by: All coverages for public_financials, financial_stability
# =============================================================================

class PublicFinancialsExtractor(StubExtractor):
    """
    STUB: Simulates public financial data from regulatory filings.
    
    Real implementation would query:
    - SEC EDGAR
    - Companies House
    - Bloomberg
    - S&P Capital IQ
    - Reuters/Refinitiv
    
    Crosswalk mapping:
    - aerospace: signal_features/financial_stability/public_financials
    - energy: signal_features/financial_stability
    - fi: signal_features/structured_data
    - marine: signal_features/structured_data
    """
    SOURCE_NAME = "public_financials"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY  # Financials change with market
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        is_public = self._random_bool(0.4)  # 40% are public companies
        
        if is_public:
            revenue = self._random_float(1e8, 5e10, 0)
            net_income_margin = self._random_float(-0.1, 0.2, 3)
            
            financials = {
                "is_public": True,
                "ticker_symbol": self._random_string(4),
                "exchange": self._random_choice(["NYSE", "NASDAQ", "LSE", "FRA", "HKG"]),
                "market_cap_usd": revenue * self._random_float(0.5, 3, 1),
                "fiscal_year_end": self._random_choice(["12-31", "03-31", "06-30", "09-30"]),
                "last_filing_date": self._random_date_iso(years_back=1),
                "revenue_usd": revenue,
                "revenue_growth_yoy": self._random_float(-0.2, 0.3, 3),
                "net_income_usd": revenue * net_income_margin,
                "net_income_margin": net_income_margin,
                "total_assets_usd": revenue * self._random_float(1, 3, 1),
                "total_liabilities_usd": revenue * self._random_float(0.5, 2, 1),
                "debt_to_equity": self._random_float(0.2, 3, 2),
                "current_ratio": self._random_float(0.5, 2.5, 2),
                "cash_position_usd": revenue * self._random_float(0.05, 0.3, 2),
                "operating_cash_flow_usd": revenue * self._random_float(-0.05, 0.2, 2),
                "is_profitable": net_income_margin > 0,
                "consecutive_profitable_years": self._random_int(0, 10) if net_income_margin > 0 else 0,
                "dividend_yield": self._random_float(0, 0.05, 3) if net_income_margin > 0.05 else None,
                "auditor": self._random_choice(["Deloitte", "PwC", "EY", "KPMG", "BDO", "Grant Thornton"]),
                "audit_opinion": self._random_choice(["UNQUALIFIED", "QUALIFIED", "ADVERSE"], weights=[0.9, 0.08, 0.02]),
            }
        else:
            # Limited data for private companies
            financials = {
                "is_public": False,
                "ticker_symbol": None,
                "exchange": None,
                "estimated_revenue_range": self._random_choice([
                    "UNDER_10M", "10M_50M", "50M_100M", "100M_500M", "500M_1B", "OVER_1B"
                ]),
                "employee_count_estimate": self._random_int(10, 10000),
                "last_known_funding_date": self._random_date_or_none(years_back=5),
                "last_known_funding_amount": self._random_float(1e6, 5e8, 0) if self._random_bool(0.3) else None,
                "has_pe_backing": self._random_bool(0.2),
                "has_vc_backing": self._random_bool(0.15),
            }
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": financials
        }
        
        return self._create_success_result(data)


# =============================================================================
# INCIDENT HISTORY EXTRACTOR (Generic)
# Used by: All coverages for incident_history, breach_history, etc.
# =============================================================================

class IncidentHistoryExtractor(StubExtractor):
    """
    STUB: Simulates generic incident/event history data.
    
    This is a parameterizable extractor that can be configured for different
    incident types across coverages:
    - Aerospace: accidents, incidents
    - Cyber: breaches, security incidents
    - Marine: casualties, environmental incidents
    - Energy: spills, safety incidents
    
    Real implementation would query domain-specific databases.
    """
    SOURCE_NAME = "incident_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, incident_type: str = "GENERAL", 
                   lookback_years: int = 10, **kwargs) -> ExtractorResult:
        """
        Extract incident history.
        
        Args:
            entity_id: Entity identifier
            incident_type: Type of incidents (AVIATION, CYBER, MARINE, ENERGY, GENERAL)
            lookback_years: Years of history to retrieve
        """
        # Define incident characteristics by type
        if incident_type == "AVIATION":
            severity_levels = ["ACCIDENT_FATAL", "ACCIDENT_NONFATAL", "SERIOUS_INCIDENT", 
                             "INCIDENT", "GROUND_INCIDENT"]
            base_probability = 0.15
        elif incident_type == "CYBER":
            severity_levels = ["MAJOR_BREACH", "MINOR_BREACH", "ATTEMPTED_BREACH",
                             "SYSTEM_OUTAGE", "DATA_EXPOSURE"]
            base_probability = 0.25
        elif incident_type == "MARINE":
            severity_levels = ["TOTAL_LOSS", "MAJOR_CASUALTY", "SERIOUS_CASUALTY",
                             "LESS_SERIOUS", "MARINE_INCIDENT"]
            base_probability = 0.20
        else:
            severity_levels = ["CRITICAL", "MAJOR", "MODERATE", "MINOR"]
            base_probability = 0.20
        
        has_incidents = self._random_bool(base_probability)
        
        incidents = []
        if has_incidents:
            num_incidents = self._random_int(1, 8)
            for _ in range(num_incidents):
                severity_weights = [0.02, 0.08, 0.20, 0.40, 0.30][:len(severity_levels)]
                # Normalize weights
                total = sum(severity_weights)
                severity_weights = [w/total for w in severity_weights]
                
                incidents.append({
                    "incident_id": self._random_id("INC"),
                    "incident_date": self._random_date_iso(years_back=lookback_years),
                    "severity": self._random_choice(severity_levels, weights=severity_weights),
                    "description": f"Incident of type {incident_type}",
                    "location": self._random_country_code(),
                    "investigation_complete": self._random_bool(0.85),
                    "operator_cited": self._random_bool(0.3),
                    "injuries": self._random_int(0, 10) if incident_type in ["AVIATION", "MARINE"] else None,
                    "fatalities": self._random_int(0, 2) if incident_type in ["AVIATION", "MARINE"] and self._random_bool(0.1) else 0,
                    "financial_impact_usd": self._random_float(10000, 10000000, 0) if self._random_bool(0.5) else None,
                })
        
        # Sort by date descending
        incidents.sort(key=lambda x: x["incident_date"], reverse=True)
        
        # Calculate summary metrics
        fatal_incidents = sum(1 for i in incidents if i.get("fatalities", 0) > 0)
        severe_incidents = sum(1 for i in incidents if severity_levels.index(i["severity"]) <= 1) if incidents else 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "incident_type": incident_type,
            "lookback_years": lookback_years,
            "data": {
                "has_incidents": has_incidents,
                "total_incidents": len(incidents),
                "incidents": incidents,
                "fatal_incident_count": fatal_incidents,
                "severe_incident_count": severe_incidents,
                "operator_cited_count": sum(1 for i in incidents if i.get("operator_cited")),
                "total_fatalities": sum(i.get("fatalities", 0) for i in incidents),
                "total_injuries": sum(i.get("injuries", 0) or 0 for i in incidents),
                "most_recent_incident_date": incidents[0]["incident_date"] if incidents else None,
                "years_since_last_incident": None,  # Would be calculated from most_recent
            }
        }
        
        return self._create_success_result(data)

"""
Aerospace Stub Extractors - Part 2

Signal Groups Covered:
- regulatory_compliance: Certificate status, IOSA, enforcement, ramp inspections
- fleet_quality: Age, composition, order backlog
- operational_quality: OTP, dispatch reliability
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from signal_architecture.signals.extractors.base import StubExtractor, utcnow
from signal_architecture.signals.types import ExtractorResult


# =============================================================================
# OPERATING CERTIFICATE EXTRACTOR
# Signals: certificate_status, regulatory_framework (categorical)
# =============================================================================

class OperatingCertificateExtractor(StubExtractor):
    """
    STUB: Simulates operating certificate data from aviation regulators.
    
    Real implementation would query:
    - FAA Certificate Management Database
    - EASA European Central Repository
    - National CAA databases
    
    Used for: certificate_status, regulatory_framework signals
    """
    SOURCE_NAME = "operating_certificate_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    CERTIFICATE_TYPES = ["PART_121", "PART_135", "PART_125", "EASA_AOC", "CAA_AOC"]
    CERTIFICATE_STATUSES = ["ACTIVE", "ACTIVE_WITH_CONDITIONS", "SUSPENDED", "REVOKED"]
    
    REGULATORS = [
        {"code": "FAA", "region": "US", "tier": 1},
        {"code": "EASA", "region": "EU", "tier": 1},
        {"code": "CAA_UK", "region": "UK", "tier": 1},
        {"code": "TCCA", "region": "CA", "tier": 1},
        {"code": "CASA", "region": "AU", "tier": 1},
        {"code": "CAAC", "region": "CN", "tier": 2},
        {"code": "DGCA_IN", "region": "IN", "tier": 2},
        {"code": "ANAC", "region": "BR", "tier": 2},
        {"code": "OTHER_ICAO", "region": "OTHER", "tier": 3},
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Select primary regulator
        regulator = self._random_choice(self.REGULATORS, 
            weights=[0.25, 0.25, 0.10, 0.08, 0.07, 0.08, 0.07, 0.05, 0.05])
        
        # Certificate status - mostly active
        status = self._random_choice(self.CERTIFICATE_STATUSES,
            weights=[0.85, 0.10, 0.04, 0.01])
        
        # Generate certificate details
        cert_type = self._random_choice(self.CERTIFICATE_TYPES)
        issue_date = self._random_date_iso(years_back=20)
        
        conditions = []
        if status == "ACTIVE_WITH_CONDITIONS":
            conditions = [
                self._random_choice([
                    "LIMITED_INTERNATIONAL_OPS",
                    "ENHANCED_OVERSIGHT",
                    "RESTRICTED_FLEET_EXPANSION",
                    "MANDATORY_SAFETY_PROGRAM",
                ])
            ]
        
        # Recent inspections
        inspections = []
        num_inspections = self._random_int(2, 8)
        for _ in range(num_inspections):
            inspections.append({
                "inspection_date": self._random_date_iso(years_back=2),
                "inspection_type": self._random_choice(["BASE", "EN_ROUTE", "RAMP", "SPECIAL"]),
                "findings_count": self._random_int(0, 5),
                "critical_findings": self._random_int(0, 1) if self._random_bool(0.1) else 0,
                "satisfactory": self._random_bool(0.85),
            })
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_regulator": regulator["code"],
                "regulator_tier": regulator["tier"],
                "regulator_region": regulator["region"],
                "certificate_type": cert_type,
                "certificate_number": self._random_id("AOC"),
                "certificate_status": status,
                "issue_date": issue_date,
                "last_renewal_date": self._random_date_iso(years_back=2),
                "expiry_date": self._random_date_iso(years_forward=2) if self._random_bool(0.3) else None,
                "conditions": conditions,
                "has_conditions": len(conditions) > 0,
                "operations_specs": {
                    "passenger": self._random_bool(0.8),
                    "cargo": self._random_bool(0.5),
                    "international": self._random_bool(0.7),
                    "charter": self._random_bool(0.4),
                    "dangerous_goods": self._random_bool(0.3),
                },
                "inspections": inspections,
                "total_findings_2yr": sum(i["findings_count"] for i in inspections),
                "critical_findings_2yr": sum(i["critical_findings"] for i in inspections),
                "is_suspended": status == "SUSPENDED",
                "is_revoked": status == "REVOKED",
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# IOSA REGISTRY EXTRACTOR  
# Signals: iosa_audit_status, iosa_status (categorical)
# =============================================================================

class IOSARegistryExtractor(StubExtractor):
    """
    STUB: Simulates IATA IOSA (Operational Safety Audit) registry data.
    
    Real implementation would query:
    - IATA IOSA Registry public API
    
    Used for: iosa_audit_status, iosa_status categorical group
    """
    SOURCE_NAME = "iosa_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # IOSA registration status
        is_registered = self._random_bool(0.6)
        was_registered = self._random_bool(0.15) if not is_registered else False
        
        if is_registered:
            registration_date = self._random_date_iso(years_back=10)
            last_audit_date = self._random_date_iso(years_back=2)
            expiry_date = self._random_date_iso(years_forward=1)
            
            # Audit findings
            findings_count = self._random_int(0, 15)
            critical_findings = self._random_int(0, 2) if findings_count > 5 else 0
            
            iosa_data = {
                "registration_status": "REGISTERED",
                "registration_date": registration_date,
                "last_audit_date": last_audit_date,
                "audit_expiry_date": expiry_date,
                "years_registered": self._random_int(1, 15),
                "consecutive_renewals": self._random_int(1, 10),
                "audit_findings_count": findings_count,
                "critical_findings": critical_findings,
                "findings_resolved": findings_count - self._random_int(0, findings_count),
                "enhanced_audit": self._random_bool(0.2),
                "audit_sections": {
                    "ORG": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                    "FLT": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                    "DSP": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                    "MNT": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION", "FINDING"]),
                    "CAB": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                    "GRH": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                    "CGO": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                    "SEC": self._random_choice(["CONFORMANCE", "CONFORMANCE", "OBSERVATION"]),
                },
            }
        elif was_registered:
            iosa_data = {
                "registration_status": "EXPIRED",
                "registration_date": self._random_date_iso(years_back=8),
                "last_audit_date": self._random_date_iso(years_back=3),
                "audit_expiry_date": self._random_date_iso(years_back=1),
                "years_since_expiry": self._random_int(1, 3),
                "reason_for_lapse": self._random_choice(["COST", "RENEWAL_DELAY", "FINDINGS_UNRESOLVED"]),
            }
        else:
            iosa_data = {
                "registration_status": "NEVER_REGISTERED",
                "applicable": self._random_bool(0.7),  # Some operators don't need IOSA
                "reason_not_registered": self._random_choice([
                    "NOT_REQUIRED", "IN_PROCESS", "COST_PROHIBITIVE", "NEW_OPERATOR"
                ]) if self._random_bool(0.7) else None,
            }
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": iosa_data
        }
        
        return self._create_success_result(data)


# =============================================================================
# RAMP INSPECTION EXTRACTOR
# Signal: ramp_inspection (SAFA/SACA results)
# =============================================================================

class RampInspectionExtractor(StubExtractor):
    """
    STUB: Simulates ramp inspection data (SAFA, SACA, FAA ramp checks).
    
    Real implementation would query:
    - EASA SAFA results database
    - FAA ramp inspection records
    - Transport Canada SACA database
    
    Used for: ramp_inspection signal
    """
    SOURCE_NAME = "ramp_inspection_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    FINDING_CATEGORIES = [
        "DOCUMENTS", "FLIGHT_CREW", "CABIN", "CARGO", "AIRCRAFT",
        "DANGEROUS_GOODS", "FLIGHT_OPERATIONS"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Generate inspections over 3 years
        num_inspections = self._random_int(5, 50)
        
        inspections = []
        total_findings = 0
        cat2_findings = 0
        cat3_findings = 0
        
        for _ in range(num_inspections):
            findings = []
            num_findings = self._random_int(0, 5) if self._random_bool(0.4) else 0
            
            for _ in range(num_findings):
                category = self._random_choice([1, 2, 3], weights=[0.6, 0.3, 0.1])
                findings.append({
                    "finding_category": self._random_choice(self.FINDING_CATEGORIES),
                    "severity_category": category,
                    "corrected_on_spot": self._random_bool(0.5) if category < 3 else False,
                })
                total_findings += 1
                if category == 2:
                    cat2_findings += 1
                elif category == 3:
                    cat3_findings += 1
            
            inspections.append({
                "inspection_id": self._random_id("RAMP"),
                "inspection_date": self._random_date_iso(years_back=3),
                "location": self._random_choice(["LHR", "CDG", "FRA", "AMS", "MAD", "FCO"]),
                "inspector_authority": self._random_choice(["EASA_SAFA", "FAA", "TCCA_SACA"]),
                "aircraft_type": self._random_choice(["B737", "A320", "E190", "B777"]),
                "findings_count": num_findings,
                "findings": findings,
                "satisfactory": num_findings == 0 or all(f["severity_category"] == 1 for f in findings),
            })
        
        # Calculate metrics
        findings_rate = total_findings / num_inspections if num_inspections > 0 else 0
        industry_avg_rate = 0.8  # Industry average findings per inspection
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_inspections_3yr": num_inspections,
                "inspections": inspections[:10],  # Return last 10 for detail
                "total_findings": total_findings,
                "category_2_findings": cat2_findings,
                "category_3_findings": cat3_findings,
                "findings_per_inspection": round(findings_rate, 2),
                "industry_average_rate": industry_avg_rate,
                "rate_vs_industry": round(findings_rate / industry_avg_rate, 2) if industry_avg_rate > 0 else None,
                "has_category_3_findings": cat3_findings > 0,
                "ground_stop_events": self._random_int(0, 1) if cat3_findings > 0 else 0,
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# EU SAFETY LIST EXTRACTOR
# Signal: eu_safety_list
# =============================================================================

class EUSafetyListExtractor(StubExtractor):
    """
    STUB: Simulates EU Air Safety List status check.
    
    Real implementation would query:
    - European Commission Air Safety List
    
    Used for: eu_safety_list signal
    """
    SOURCE_NAME = "eu_safety_list"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Very few operators on the list
        on_annex_a = self._random_bool(0.02)  # Full ban
        on_annex_b = self._random_bool(0.03) if not on_annex_a else False  # Restrictions
        
        status_data = {
            "is_on_safety_list": on_annex_a or on_annex_b,
            "annex_a_banned": on_annex_a,
            "annex_b_restricted": on_annex_b,
            "list_check_date": utcnow().isoformat(),
            "state_of_operator": self._random_country_code(),
        }
        
        if on_annex_a:
            status_data["ban_effective_date"] = self._random_date_iso(years_back=5)
            status_data["ban_reason"] = "SAFETY_OVERSIGHT_DEFICIENCIES"
        elif on_annex_b:
            status_data["restriction_effective_date"] = self._random_date_iso(years_back=3)
            status_data["restricted_aircraft_types"] = [self._random_string(4) for _ in range(self._random_int(1, 3))]
            status_data["restriction_reason"] = "SPECIFIC_AIRCRAFT_CONCERNS"
        
        # Check if country has any operators on list
        status_data["country_operators_banned"] = self._random_int(0, 5) if self._random_bool(0.1) else 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": status_data
        }
        
        return self._create_success_result(data)


# =============================================================================
# STATE SAFETY OVERSIGHT EXTRACTOR
# Signal: state_safety_rating (ICAO USOAP results)
# =============================================================================

class StateSafetyExtractor(StubExtractor):
    """
    STUB: Simulates ICAO USOAP (Universal Safety Oversight Audit Programme) data.
    
    Real implementation would query:
    - ICAO USOAP results database
    
    Used for: state_safety_rating signal
    """
    SOURCE_NAME = "icao_usoap_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, state_code: str = None, **kwargs) -> ExtractorResult:
        state = state_code or self._random_country_code()
        
        # USOAP effective implementation scores by area
        # Scale 0-100, global average around 65
        ei_scores = {
            "LEG": self._random_float(50, 95, 1),  # Legislation
            "ORG": self._random_float(50, 95, 1),  # Organization
            "PEL": self._random_float(50, 95, 1),  # Personnel Licensing
            "OPS": self._random_float(50, 95, 1),  # Operations
            "AIR": self._random_float(50, 95, 1),  # Airworthiness
            "AIG": self._random_float(50, 95, 1),  # Accident Investigation
            "ANS": self._random_float(50, 95, 1),  # Air Navigation Services
            "AGA": self._random_float(50, 95, 1),  # Aerodromes
        }
        
        overall_ei = sum(ei_scores.values()) / len(ei_scores)
        
        # Significant Safety Concerns
        has_ssc = overall_ei < 50 or self._random_bool(0.05)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "state_code": state,
            "data": {
                "state_code": state,
                "last_audit_date": self._random_date_iso(years_back=5),
                "overall_effective_implementation": round(overall_ei, 1),
                "global_average_ei": 65.0,
                "ei_vs_global_average": round(overall_ei - 65.0, 1),
                "area_scores": ei_scores,
                "has_significant_safety_concern": has_ssc,
                "ssc_areas": ["OPS", "AIR"] if has_ssc else [],
                "is_above_global_average": overall_ei > 65,
                "icao_tier": 1 if overall_ei >= 80 else (2 if overall_ei >= 60 else 3),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# FLIGHT OPERATIONS EXTRACTOR
# Signals: otp_score, dispatch_reliability
# =============================================================================

class FlightOperationsExtractor(StubExtractor):
    """
    STUB: Simulates flight operations performance data.
    
    Real implementation would query:
    - OAG Schedules and Punctuality
    - FlightStats/Cirium
    - DOT Air Travel Consumer Report (US)
    
    Used for: otp_score, dispatch_reliability signals
    """
    SOURCE_NAME = "flight_operations_data"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_HOURLY  # Operations data changes frequently
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # On-time performance metrics
        otp_15min = self._random_float(0.65, 0.92, 3)  # Industry range
        otp_0min = self._random_float(0.30, 0.70, 3)
        
        # Dispatch reliability
        dispatch_reliability = self._random_float(0.95, 0.999, 4)
        completion_factor = self._random_float(0.97, 0.999, 4)
        
        # Calculate by cause
        delay_causes = {
            "CARRIER": self._random_float(0.02, 0.15, 3),
            "WEATHER": self._random_float(0.01, 0.10, 3),
            "NAS": self._random_float(0.01, 0.08, 3),
            "SECURITY": self._random_float(0.001, 0.02, 4),
            "LATE_AIRCRAFT": self._random_float(0.02, 0.12, 3),
        }
        
        # Industry benchmarks
        industry_otp_15min = 0.78
        industry_dispatch = 0.985
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                # On-time performance
                "otp_15min_pct": otp_15min,
                "otp_0min_pct": otp_0min,
                "average_delay_minutes": self._random_float(5, 25, 1),
                "industry_otp_15min_avg": industry_otp_15min,
                "otp_vs_industry": round((otp_15min - industry_otp_15min) * 100, 1),
                
                # Delay causes
                "delay_causes": delay_causes,
                "carrier_controllable_delay_pct": delay_causes["CARRIER"],
                
                # Dispatch reliability
                "dispatch_reliability_pct": dispatch_reliability,
                "completion_factor_pct": completion_factor,
                "industry_dispatch_avg": industry_dispatch,
                "dispatch_vs_industry": round((dispatch_reliability - industry_dispatch) * 100, 2),
                
                # Cancellation metrics
                "cancellation_rate_pct": self._random_float(0.005, 0.04, 4),
                "mechanical_cancellation_rate": self._random_float(0.001, 0.01, 4),
                
                # Period
                "measurement_period": "LAST_12_MONTHS",
                "flights_measured": self._random_int(10000, 500000),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# FLEET REGISTRY EXTRACTOR
# Signals: fleet_age, fleet_homogeneity, aircraft_generation, 
#          fleet_category (categorical), fleet_size (categorical)
# =============================================================================

class FleetRegistryExtractor(StubExtractor):
    """
    STUB: Simulates aircraft fleet registry data.
    
    Real implementation would query:
    - FAA Aircraft Registry
    - EASA Aircraft Registry
    - Cirium Fleets Analyzer
    - ch-aviation
    
    Used for: fleet_age, fleet_homogeneity, aircraft_generation,
              fleet_category, fleet_size categorical groups
    """
    SOURCE_NAME = "fleet_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    AIRCRAFT_TYPES = [
        {"type": "B737-800", "category": "NARROWBODY", "generation": "CURRENT", "typical_age": 10},
        {"type": "B737-MAX8", "category": "NARROWBODY", "generation": "NEW", "typical_age": 3},
        {"type": "A320neo", "category": "NARROWBODY", "generation": "NEW", "typical_age": 4},
        {"type": "A320ceo", "category": "NARROWBODY", "generation": "CURRENT", "typical_age": 12},
        {"type": "B777-300ER", "category": "WIDEBODY", "generation": "CURRENT", "typical_age": 10},
        {"type": "A350-900", "category": "WIDEBODY", "generation": "NEW", "typical_age": 4},
        {"type": "E190", "category": "REGIONAL_JET", "generation": "CURRENT", "typical_age": 10},
        {"type": "ATR72-600", "category": "TURBOPROP", "generation": "CURRENT", "typical_age": 8},
        {"type": "G650", "category": "BUSINESS_JET", "generation": "NEW", "typical_age": 5},
        {"type": "EC135", "category": "HELICOPTER", "generation": "CURRENT", "typical_age": 12},
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Determine fleet size
        fleet_size = self._random_int(1, 200)
        
        # Select aircraft types (1-4 types for homogeneity)
        num_types = min(self._random_int(1, 4), fleet_size)
        selected_types = []
        remaining = fleet_size
        
        for i in range(num_types):
            ac_type = self._random_choice(self.AIRCRAFT_TYPES)
            if i == num_types - 1:
                count = remaining
            else:
                count = self._random_int(1, remaining - (num_types - i - 1))
                remaining -= count
            
            # Generate individual aircraft
            aircraft = []
            for _ in range(count):
                base_age = ac_type["typical_age"]
                age = max(0, self._random_int(base_age - 5, base_age + 10))
                aircraft.append({
                    "registration": self._random_id("N" if self._random_bool(0.5) else "G"),
                    "type": ac_type["type"],
                    "age_years": age,
                    "owned": self._random_bool(0.4),
                    "lessor": self._random_choice(["AerCap", "GECAS", "SMBC", "Owned"]),
                })
            
            selected_types.append({
                "aircraft_type": ac_type["type"],
                "category": ac_type["category"],
                "generation": ac_type["generation"],
                "count": count,
                "aircraft": aircraft,
                "average_age": round(sum(a["age_years"] for a in aircraft) / len(aircraft), 1),
            })
        
        # Calculate fleet metrics
        all_aircraft = [a for t in selected_types for a in t["aircraft"]]
        avg_fleet_age = sum(a["age_years"] for a in all_aircraft) / len(all_aircraft) if all_aircraft else 0
        
        # Determine primary category
        category_counts = {}
        for t in selected_types:
            cat = t["category"]
            category_counts[cat] = category_counts.get(cat, 0) + t["count"]
        primary_category = max(category_counts, key=category_counts.get)
        
        # Fleet homogeneity (1 type = 100%, more types = lower)
        homogeneity = 100 if num_types == 1 else round(100 / num_types, 1)
        
        # Generation breakdown
        new_gen_count = sum(t["count"] for t in selected_types if t["generation"] == "NEW")
        new_gen_pct = round(new_gen_count / fleet_size * 100, 1) if fleet_size > 0 else 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "fleet_size": fleet_size,
                "fleet_types": selected_types,
                "type_count": num_types,
                "primary_category": primary_category,
                "average_fleet_age": round(avg_fleet_age, 1),
                "youngest_aircraft_age": min(a["age_years"] for a in all_aircraft) if all_aircraft else 0,
                "oldest_aircraft_age": max(a["age_years"] for a in all_aircraft) if all_aircraft else 0,
                "homogeneity_score": homogeneity,
                "new_generation_percentage": new_gen_pct,
                "owned_percentage": round(sum(1 for a in all_aircraft if a["owned"]) / len(all_aircraft) * 100, 1) if all_aircraft else 0,
                "industry_average_age": 11.5,
                "age_vs_industry": round(avg_fleet_age - 11.5, 1),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# ORDER BACKLOG EXTRACTOR
# Signal: order_backlog
# =============================================================================

class OrderBacklogExtractor(StubExtractor):
    """
    STUB: Simulates aircraft order backlog data.
    
    Real implementation would query:
    - Boeing Orders and Deliveries
    - Airbus Orders and Deliveries
    - Embraer Backlog Reports
    
    Used for: order_backlog signal
    """
    SOURCE_NAME = "order_backlog_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        has_orders = self._random_bool(0.4)
        
        orders = []
        if has_orders:
            num_orders = self._random_int(1, 5)
            for _ in range(num_orders):
                orders.append({
                    "order_id": self._random_id("ORD"),
                    "aircraft_type": self._random_choice(["B737MAX", "A320neo", "A350", "B787", "E2"]),
                    "quantity": self._random_int(1, 50),
                    "order_date": self._random_date_iso(years_back=5),
                    "delivery_start": self._random_date_iso(years_forward=1),
                    "delivery_end": self._random_date_iso(years_forward=5),
                    "oem": self._random_choice(["Boeing", "Airbus", "Embraer"]),
                    "is_firm_order": self._random_bool(0.8),
                    "is_option": self._random_bool(0.3),
                })
        
        total_firm_orders = sum(o["quantity"] for o in orders if o["is_firm_order"])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_order_backlog": has_orders,
                "orders": orders,
                "total_firm_orders": total_firm_orders,
                "total_options": sum(o["quantity"] for o in orders if o["is_option"]),
                "years_of_backlog": round(total_firm_orders / 10, 1) if total_firm_orders > 0 else 0,
                "investment_signal": "STRONG" if total_firm_orders > 20 else ("MODERATE" if total_firm_orders > 5 else "LOW"),
            }
        }
        
        return self._create_success_result(data)

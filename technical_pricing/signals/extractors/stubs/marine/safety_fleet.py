"""
Marine Extractors - Safety Compliance & Fleet Profile

Stub extractors for marine insurance signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from ...base import StubExtractor


# =============================================================================
# SAFETY COMPLIANCE EXTRACTORS
# =============================================================================

class PSCDetentionExtractor(StubExtractor):
    """Extract port state control detention history."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_detentions = random.random() < 0.12
        
        detentions = []
        if has_detentions:
            for _ in range(random.randint(1, 4)):
                detentions.append({
                    "date": (datetime.utcnow() - timedelta(days=random.randint(30, 1095))).strftime("%Y-%m-%d"),
                    "port": random.choice(["Rotterdam", "Singapore", "Shanghai", "Tokyo", "Houston"]),
                    "authority": random.choice(["Paris MoU", "Tokyo MoU", "USCG", "Indian Ocean MoU"]),
                    "detention_days": random.randint(1, 14),
                    "primary_deficiency": random.choice(["ISM", "Fire Safety", "Life Saving", "Navigation", "Propulsion"])
                })
        
        return {
            "entity_id": entity_id,
            "total_detentions_36mo": len(detentions),
            "detentions": detentions,
            "detention_rate_vs_fleet_avg": round(random.uniform(0.5, 2.0), 2) if has_detentions else round(random.uniform(0, 0.5), 2),
            "most_recent_detention_days_ago": min([(datetime.utcnow() - datetime.strptime(d["date"], "%Y-%m-%d")).days for d in detentions]) if detentions else None,
            "psc_detention_score": random.randint(30, 60) if has_detentions else random.randint(75, 100),
            "data_source": "equasis_psc_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PSCDeficiencyExtractor(StubExtractor):
    """Extract PSC deficiency rates."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        inspections = random.randint(5, 50)
        deficiency_rate = random.uniform(0.5, 4.0)
        
        return {
            "entity_id": entity_id,
            "inspections_36mo": inspections,
            "total_deficiencies": int(inspections * deficiency_rate),
            "average_deficiencies_per_inspection": round(deficiency_rate, 2),
            "deficiency_rate_vs_benchmark": round(deficiency_rate / 2.5, 2),  # 2.5 is typical benchmark
            "zero_deficiency_rate": round(random.uniform(0.1, 0.5), 2),
            "common_deficiency_categories": random.sample(
                ["Fire Safety", "Life Saving", "Navigation", "ISM", "Structural", "Pollution Prevention"],
                k=random.randint(2, 4)
            ),
            "psc_deficiency_score": max(20, 100 - int(deficiency_rate * 15)),
            "data_source": "equasis_psc_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ClassStatusExtractor(StubExtractor):
    """Extract classification status and conditions."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        status = random.choices(
            ["in_class", "conditions", "recommendations", "suspended", "withdrawn"],
            weights=[0.75, 0.12, 0.08, 0.03, 0.02]
        )[0]
        
        return {
            "entity_id": entity_id,
            "class_status": status,
            "conditions_outstanding": random.randint(0, 5) if status in ["conditions", "recommendations"] else 0,
            "recommendations_outstanding": random.randint(0, 8) if status == "recommendations" else 0,
            "overdue_surveys": random.randint(0, 2),
            "class_changes_5yr": random.randint(0, 2),
            "notation_changes": random.random() < 0.1,
            "class_status_score": 100 if status == "in_class" else 70 if status == "recommendations" else 50 if status == "conditions" else 15,
            "data_source": "class_society_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ISMComplianceExtractor(StubExtractor):
    """Extract ISM/ISPS compliance status."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        doc_status = random.choices(
            ["valid", "interim", "expired", "suspended"],
            weights=[0.88, 0.05, 0.04, 0.03]
        )[0]
        
        return {
            "entity_id": entity_id,
            "doc_status": doc_status,
            "smc_status": random.choice(["valid", "valid", "interim", "expired"]),
            "issc_status": random.choice(["valid", "valid", "interim", "expired"]),
            "mlc_compliance": random.choice(["certified", "certified", "pending", "issues"]),
            "ism_observations": random.randint(0, 5),
            "major_nonconformities": random.randint(0, 2) if doc_status != "valid" else 0,
            "ism_compliance_score": 95 if doc_status == "valid" else 70 if doc_status == "interim" else 30,
            "data_source": "flag_state_ism_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CasualtyHistoryExtractor(StubExtractor):
    """Extract casualty and incident history."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_casualties = random.random() < 0.15
        
        casualties = []
        if has_casualties:
            types = ["collision", "grounding", "fire", "machinery_failure", "structural", "cargo"]
            severities = ["minor", "moderate", "serious", "very_serious"]
            
            for _ in range(random.randint(1, 4)):
                casualties.append({
                    "date": (datetime.utcnow() - timedelta(days=random.randint(90, 1825))).strftime("%Y-%m-%d"),
                    "type": random.choice(types),
                    "severity": random.choices(severities, weights=[0.4, 0.35, 0.2, 0.05])[0],
                    "location": random.choice(["At sea", "In port", "Anchorage", "Restricted waters"]),
                    "injuries": random.randint(0, 3),
                    "reported_to": random.choice(["Flag state", "IMO", "Class society"])
                })
        
        return {
            "entity_id": entity_id,
            "total_casualties_5yr": len(casualties),
            "casualties": casualties,
            "serious_casualties": len([c for c in casualties if c.get("severity") in ["serious", "very_serious"]]),
            "casualty_free_years": random.randint(0, 10) if not has_casualties else 0,
            "casualty_history_score": random.randint(40, 65) if has_casualties else random.randint(80, 100),
            "data_source": "imo_gisis_casualty_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class TotalLossHistoryExtractor(StubExtractor):
    """Extract total loss history."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_total_loss = random.random() < 0.03
        
        return {
            "entity_id": entity_id,
            "total_losses_10yr": random.randint(1, 2) if has_total_loss else 0,
            "constructive_total_losses": random.randint(0, 1) if has_total_loss else 0,
            "actual_total_losses": random.randint(0, 1) if has_total_loss else 0,
            "most_recent_loss_years_ago": random.randint(1, 8) if has_total_loss else None,
            "loss_causes": ["Fire", "Grounding", "Collision", "Structural failure"][:random.randint(1, 2)] if has_total_loss else [],
            "total_loss_score": 40 if has_total_loss else 100,
            "data_source": "iumi_loss_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# FLEET PROFILE EXTRACTORS
# =============================================================================

class FleetAgeExtractor(StubExtractor):
    """Extract fleet age profile."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        avg_age = random.uniform(5, 22)
        
        return {
            "entity_id": entity_id,
            "weighted_average_age": round(avg_age, 1),
            "oldest_vessel_age": round(avg_age + random.uniform(3, 12), 1),
            "newest_vessel_age": max(0, round(avg_age - random.uniform(3, 10), 1)),
            "vessels_over_20yr_pct": round(random.uniform(0, 0.4), 2) if avg_age > 12 else 0,
            "vessels_under_5yr_pct": round(random.uniform(0, 0.4), 2) if avg_age < 12 else round(random.uniform(0, 0.15), 2),
            "age_band": "AGE_0_5" if avg_age <= 5 else "AGE_5_10" if avg_age <= 10 else "AGE_10_15" if avg_age <= 15 else "AGE_15_20" if avg_age <= 20 else "AGE_20_25" if avg_age <= 25 else "AGE_25_PLUS",
            "fleet_age_score": max(20, 100 - int(avg_age * 3.5)),
            "data_source": "equasis_fleet_data",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FleetStabilityExtractor(StubExtractor):
    """Extract fleet size and stability indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        fleet_size = random.randint(1, 200)
        
        return {
            "entity_id": entity_id,
            "current_fleet_size": fleet_size,
            "fleet_size_change_12mo": random.randint(-10, 15),
            "fleet_size_change_pct": round(random.uniform(-0.2, 0.3), 2),
            "vessels_acquired_12mo": random.randint(0, 10),
            "vessels_sold_12mo": random.randint(0, 8),
            "newbuilding_orderbook": random.randint(0, 5),
            "fleet_stability_score": random.randint(60, 95),
            "data_source": "clarkson_fleet_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class VesselQualityExtractor(StubExtractor):
    """Extract vessel quality indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "enhanced_class_notation_pct": round(random.uniform(0.2, 0.8), 2),
            "eco_notation_pct": round(random.uniform(0.1, 0.6), 2),
            "ice_class_pct": round(random.uniform(0, 0.3), 2),
            "dp_notation_pct": round(random.uniform(0, 0.4), 2),
            "tier_iii_engine_pct": round(random.uniform(0.1, 0.5), 2),
            "scrubber_fitted_pct": round(random.uniform(0.1, 0.4), 2),
            "vessel_quality_score": random.randint(55, 95),
            "data_source": "class_society_notations",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CrewCertificationExtractor(StubExtractor):
    """Extract crew certification quality patterns."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        white_list_countries = ["Philippines", "India", "Ukraine", "Russia", "Poland", "Croatia"]
        
        return {
            "entity_id": entity_id,
            "primary_crew_nationalities": random.sample(white_list_countries, k=random.randint(1, 3)),
            "stcw_compliance_rate": round(random.uniform(0.95, 1.0), 3),
            "certification_issues_12mo": random.randint(0, 3),
            "manning_agency_quality": random.choice(["top_tier", "established", "standard", "unknown"]),
            "officer_experience_avg_years": random.randint(5, 20),
            "crew_retention_rate": round(random.uniform(0.6, 0.95), 2),
            "crew_certification_score": random.randint(65, 95),
            "data_source": "manning_agency_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ManagementConsistencyExtractor(StubExtractor):
    """Extract management consistency indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "technical_manager_tenure_years": random.randint(1, 15),
            "manager_changes_5yr": random.randint(0, 3),
            "dpa_tenure_years": random.randint(1, 10),
            "consistent_sms": random.random() > 0.2,
            "management_stability_score": random.randint(55, 95),
            "data_source": "imo_company_records",
            "extracted_at": datetime.utcnow().isoformat()
        }

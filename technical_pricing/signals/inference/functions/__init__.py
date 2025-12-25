"""
DSI Inference Functions by Coverage Domain

Aerospace modules:
    - aerospace_categorical.py: Categorical group functions (operator_type, fleet_size, etc.)
    - aerospace_network_authority.py: Network authority signal functions
    - aerospace_safety_record.py: Safety record signal functions
    - aerospace_regulatory.py: Regulatory compliance signal functions
    - aerospace_others.py: Operational, fleet, route, corporate, financial functions

Cyber modules:
    - cyber_categorical.py: Categorical group functions (industry, size, geography)
    - cyber_network_authority.py: Network authority signal functions
    - cyber_technical_infrastructure.py: Technical infrastructure signal functions
    - cyber_footprint_and_record.py: Corporate footprint and public record functions
    - cyber_structured_data.py: Structured data signal functions

Each function:
    - Maps to an `inference_utility_function` in the YAML config
    - Orchestrates: Extractor(s) → Aggregator(s) → Categorizer
    - Returns a SignalResult with score/category and audit trail

Registration:
    Functions are registered via @register_inference_function decorator.
    Import the modules to trigger registration.
"""

# Import all aerospace modules to register functions
from . import aerospace_categorical
from . import aerospace_network_authority
from . import aerospace_safety_record
from . import aerospace_regulatory
from . import aerospace_others

# Import all cyber modules to register functions
from . import cyber_categorical
from . import cyber_network_authority
from . import cyber_technical_infrastructure
from . import cyber_footprint_and_record
from . import cyber_structured_data

# Re-export commonly used functions for convenience
from .aerospace_categorical import (
    operatortype_basefunction,
    fleetcategory_basefunction,
    fleetsize_basefunction,
    regulatoryframework_basefunction,
    iosastatus_basefunction,
)

from .aerospace_network_authority import (
    alliance_membership_basefunction,
    codeshare_partner_basefunction,
    aircraft_lessor_basefunction,
    oem_relationship_basefunction,
    mro_quality_basefunction,
)

from .aerospace_safety_record import (
    accident_history_basefunction,
    incident_history_basefunction,
    accident_rate_basefunction,
    fatality_history_basefunction,
    investigation_finding_basefunction,
)

from .aerospace_regulatory import (
    certificate_status_basefunction,
    enforcement_action_basefunction,
    iosa_audit_basefunction,
    ramp_inspection_basefunction,
    eu_safetylist_basefunction,
    state_safety_basefunction,
)

from .aerospace_others import (
    # Operational Quality
    otp_score_basefunction,
    dispatch_reliability_basefunction,
    crew_experience_basefunction,
    training_indicators_basefunction,
    operational_complexity_basefunction,
    growth_rate_basefunction,
    # Fleet Quality
    fleet_age_basefunction,
    fleet_homogeneity_basefunction,
    aircraft_generation_basefunction,
    order_backlog_basefunction,
    maintenance_indicators_basefunction,
    # Route Risk
    conflict_zone_basefunction,
    challenging_airports_basefunction,
    highrisk_exposure_basefunction,
    weather_exposure_basefunction,
    terrain_exposure_basefunction,
    # Corporate Governance
    management_stability_basefunction,
    safety_leadership_basefunction,
    safety_reporting_basefunction,
    corporate_structure_basefunction,
    industry_engagement_basefunction,
    # Financial
    credit_rating_basefunction,
    public_financials_basefunction,
    market_position_basefunction,
    government_support_basefunction,
)

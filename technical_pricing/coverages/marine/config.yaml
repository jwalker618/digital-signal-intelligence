# =============================================================================
# DSI Model Configuration - Marine Insurance
# =============================================================================
#
# This file defines the complete configuration for Marine insurance coverage.
# It is the single source of truth for:
#   - Model structure and parameters
#   - Signal definitions and weights
#   - Pricing factors and thresholds
#   - Operator type, vessel category, and trading pattern modifiers
#   - Test profiles for actuarial validation
#
# Premium calculation follows DSI Foundational Principle 9: Signal -> Score -> Tier -> Price
#
# DSI PRINCIPLES APPLIED:
#   1. All signals must be externally observable (AIS, PSC, classification societies)
#   2. Direct queries are OPTIONAL - model works without them
#   3. Categorical features are inferred from fleet registries and tracking data
#   4. Tier determines base rate; modifiers adjust for exposure characteristics
#   5. Marine is uniquely suited to DSI due to comprehensive vessel tracking
#
# KEY DSI PRINCIPLE: We assess OPERATOR behavior patterns, not individual vessel
# pricing. A well-managed operator's fleet behavior indicates individual vessel quality.
#
# KEY DATA SOURCES:
#   - AIS tracking (vessel positions, behavior patterns, dark activity)
#   - Port State Control databases (Paris MoU, Tokyo MoU, USCG)
#   - Classification society registries (Lloyd's, DNV, BV, etc.)
#   - Equasis (EU maritime safety database)
#   - IMO GISIS (ship particulars, company data)
#   - OFAC, EU sanctions lists
#   - P&I Club records
#
# Version: 2.0.0
# Last Updated: 2025-12
# =============================================================================

marine:
  marine_general:
    metadata:
      name: "DSI Marine Insurance Model"
      description: "Marine hull and liability coverage based on observable operator behavior, safety records, and fleet patterns"
      version: "2.0.0"
      coverage_types:
        - "hull_machinery"
        - "total_loss"
        - "increased_value"
        - "loss_of_hire"
        - "war_risks"
        - "pi_liability"
        - "cargo"
      applicable_vessel_categories:
        - "container"
        - "tanker"
        - "dry_bulk"
        - "lng_lpg"
        - "offshore"
        - "passenger"
        - "general_cargo"
      applicable_markets: ["global"]
      min_premium: 50000
      default_currency: "USD"

    # -------------------------------------------------------------------------
    # DIRECT OPTIONAL QUERIES
    # -------------------------------------------------------------------------
    direct_optional_queries:
      - id: "fleet_size"
        question: "Total number of vessels in owned/operated fleet?"
        direct_condition: fleet_size_info
        
      - id: "psc_detentions"
        question: "Any vessels detained by port state control in past 36 months?"
        direct_condition: psc_detentions_true
        
      - id: "total_losses"
        question: "Any total losses or major casualties in past 5 years?"
        direct_condition: total_losses_true
        
      - id: "third_party_manager"
        question: "Is the fleet managed by a third-party technical manager?"
        direct_condition: third_party_manager_info
        
      - id: "sanctioned_trade"
        question: "Any vessels currently trading to sanctioned regions?"
        direct_condition: sanctioned_trade_true

    # -------------------------------------------------------------------------
    # CATEGORICAL FEATURES
    # -------------------------------------------------------------------------
    categorical_features:
      operator_type:
        description: "Operator classification based on fleet size and segment"
        inference_method:
          primary: "equasis_fleet_analysis"
          fallback: "ais_pattern_analysis"
          sources:
            - {type: "api", provider: "equasis", endpoint: "companies/fleet"}
            - {type: "api", provider: "ihs_markit", endpoint: "ownership/search"}
            - {type: "api", provider: "clarksons", endpoint: "owners/profile"}
            - {type: "api", provider: "lloyd_list", endpoint: "companies/search"}
          confidence_threshold: 0.90
          default_on_failure: "INDEPENDENT"
        values:
          - id: "MAJOR_LINER"
            label: "Major Liner Operator"
            modifier: 0.80
            description: "Top 20 container lines (Maersk, MSC, CMA CGM, etc.)"
            inference_criteria: {vessel_category: "container", fleet_min: 50, liner_service: true}
            
          - id: "MAJOR_TANKER"
            label: "Major Tanker Operator"
            modifier: 0.90
            description: "Major tanker fleet operators"
            inference_criteria: {vessel_category: "tanker", fleet_min: 30}
            
          - id: "MAJOR_BULK"
            label: "Major Bulk Operator"
            modifier: 0.95
            description: "Major dry bulk fleet operators"
            inference_criteria: {vessel_category: "dry_bulk", fleet_min: 30}
            
          - id: "REGIONAL_OPERATOR"
            label: "Regional Fleet Operator"
            modifier: 1.00
            description: "Regional fleet operators (10-30 vessels)"
            inference_criteria: {fleet_range: [10, 30]}
            
          - id: "INDEPENDENT"
            label: "Independent Operator"
            modifier: 1.25
            description: "Single or few vessel operators (<10 vessels)"
            inference_criteria: {fleet_max: 10}
            
          - id: "STATE_OWNED"
            label: "State-Owned Operator"
            modifier: 1.10
            description: "Government-owned shipping lines"
            inference_criteria: {state_ownership: true}
            
          - id: "UNKNOWN"
            label: "Unknown Operator"
            modifier: 1.50
            description: "New or unverified operator"
            inference_criteria: {}

      vessel_category:
        description: "Primary vessel category for fleet"
        inference_method:
          primary: "fleet_registry_analysis"
          sources:
            - {type: "api", provider: "equasis", endpoint: "companies/fleet"}
            - {type: "api", provider: "ihs_markit", endpoint: "vessels/search"}
          confidence_threshold: 0.95
          default_on_failure: "MIXED"
        values:
          - id: "CONTAINER"
            label: "Container"
            modifier: 0.90
            description: "Container vessels"
            
          - id: "TANKER"
            label: "Tanker"
            modifier: 1.10
            description: "Crude, product, chemical tankers"
            
          - id: "DRY_BULK"
            label: "Dry Bulk"
            modifier: 1.00
            description: "Dry bulk carriers"
            
          - id: "LNG_LPG"
            label: "LNG/LPG Carrier"
            modifier: 0.85
            description: "Gas carriers (typically highest standards)"
            
          - id: "OFFSHORE"
            label: "Offshore"
            modifier: 1.30
            description: "Offshore supply, construction vessels"
            
          - id: "PASSENGER"
            label: "Passenger"
            modifier: 1.25
            description: "Cruise, ferry, passenger vessels"
            
          - id: "GENERAL_CARGO"
            label: "General Cargo"
            modifier: 1.10
            description: "General cargo, MPP vessels"
            
          - id: "MIXED"
            label: "Mixed Fleet"
            modifier: 1.05
            description: "Diversified vessel types"

      trading_pattern:
        description: "Trading pattern from AIS analysis"
        inference_method:
          primary: "ais_route_analysis"
          sources:
            - {type: "api", provider: "marinetraffic", endpoint: "routes/analysis"}
            - {type: "api", provider: "spire", endpoint: "vessels/routes"}
            - {type: "api", provider: "exactearth", endpoint: "patterns/analysis"}
          confidence_threshold: 0.85
          default_on_failure: "MIXED"
        values:
          - id: "LINER_REGULAR"
            label: "Liner/Regular Service"
            modifier: 0.85
            description: "Fixed routes, scheduled services"
            inference_criteria: {route_regularity: "high", schedule: true}
            
          - id: "SPOT_TRAMP"
            label: "Spot/Tramp Trading"
            modifier: 1.15
            description: "Voyage charter, variable routes"
            inference_criteria: {route_regularity: "low"}
            
          - id: "INDUSTRIAL"
            label: "Industrial Shipping"
            modifier: 0.90
            description: "Dedicated cargo flows (e.g., iron ore majors)"
            inference_criteria: {dedicated_cargo: true}
            
          - id: "MIXED"
            label: "Mixed Trading"
            modifier: 1.00
            description: "Combination of trading patterns"
            inference_criteria: {}

      flag_state_quality:
        description: "Flag state quality based on Paris MoU performance"
        inference_method:
          primary: "paris_mou_lookup"
          sources:
            - {type: "api", provider: "paris_mou", endpoint: "performance/flags"}
            - {type: "api", provider: "tokyo_mou", endpoint: "performance/flags"}
          confidence_threshold: 0.99
          default_on_failure: "GREY_LIST"
        values:
          - id: "WHITE_LIST"
            label: "Paris MoU White List"
            modifier: 0.95
            description: "High-performing flag states"
            
          - id: "GREY_LIST"
            label: "Paris MoU Grey List"
            modifier: 1.10
            description: "Average-performing flag states"
            
          - id: "BLACK_LIST"
            label: "Paris MoU Black List"
            modifier: 1.40
            description: "Poor-performing flag states"

      fleet_age_band:
        description: "Average fleet age classification"
        inference_method:
          primary: "registry_age_calculation"
          sources:
            - {type: "api", provider: "equasis", endpoint: "vessels/age"}
            - {type: "api", provider: "ihs_markit", endpoint: "vessels/particulars"}
          confidence_threshold: 0.99
          default_on_failure: "AGE_10_15"
        values:
          - {id: "AGE_0_5", label: "0-5 Years", modifier: 0.85}
          - {id: "AGE_5_10", label: "5-10 Years", modifier: 0.95}
          - {id: "AGE_10_15", label: "10-15 Years", modifier: 1.05}
          - {id: "AGE_15_20", label: "15-20 Years", modifier: 1.20}
          - {id: "AGE_20_25", label: "20-25 Years", modifier: 1.40}
          - {id: "AGE_25_PLUS", label: "25+ Years", modifier: 1.60}

    # -------------------------------------------------------------------------
    # SIGNAL GROUPS
    # -------------------------------------------------------------------------
    signal_groups:
      - id: "network_authority"
        name: "Network Authority"
        description: "Classification society, P&I Club, charterer relationships"
        weight: 0.15
        test_scores: {excellent: 92, average: 70, poor: 40}
        critical: false
        score_condition: null
        
      - id: "operational_telemetry"
        name: "Operational Telemetry"
        description: "AIS behavior patterns, dark activity, route risk"
        weight: 0.20
        test_scores: {excellent: 95, average: 72, poor: 38}
        critical: true
        score_condition: operational_telemetry_critical
        
      - id: "safety_compliance"
        name: "Safety Compliance"
        description: "PSC performance, class status, incident history"
        weight: 0.25
        test_scores: {excellent: 95, average: 75, poor: 35}
        critical: true
        score_condition: safety_compliance_critical
        
      - id: "fleet_profile"
        name: "Fleet Profile"
        description: "Fleet age, stability, vessel quality, crew certification"
        weight: 0.10
        test_scores: {excellent: 88, average: 68, poor: 42}
        critical: false
        score_condition: null
        
      - id: "sanctions_compliance"
        name: "Sanctions Compliance"
        description: "Sanctions status, ownership transparency, STS patterns"
        weight: 0.15
        test_scores: {excellent: 100, average: 85, poor: 30}
        critical: true
        score_condition: sanctions_compliance_critical
        
      - id: "environmental"
        name: "Environmental Compliance"
        description: "IMO 2020, ballast water, CII rating, incidents"
        weight: 0.05
        test_scores: {excellent: 92, average: 70, poor: 45}
        critical: false
        score_condition: null
        
      - id: "corporate_footprint"
        name: "Corporate Footprint"
        description: "Transparency, sustainability reporting, safety culture"
        weight: 0.05
        test_scores: {excellent: 88, average: 62, poor: 38}
        critical: false
        score_condition: null
        
      - id: "structured_data"
        name: "Structured Data"
        description: "RightShip vetting, ESG ratings, credit ratings"
        weight: 0.05
        test_scores: {excellent: 90, average: 68, poor: 40}
        critical: false
        score_condition: null

    # -------------------------------------------------------------------------
    # SIGNAL FEATURES
    # -------------------------------------------------------------------------
    signal_features:
      network_authority:
        - id: "classification_society"
          name: "Classification Society Quality"
          description: "IACS member vs non-IACS classification"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "equasis", endpoint: "vessels/class"}
            - {type: "api", provider: "iacs", endpoint: "members/search"}
            - {type: "api", provider: "lloyd_register", endpoint: "vessels/search"}
            - {type: "api", provider: "dnv", endpoint: "vessels/search"}
          score_range: [0, 100]
          scoring_logic:
            top_iacs_member: 100
            iacs_member: 90
            recognized_non_iacs: 70
            other_class: 50
            no_class: 20
          critical: false
          score_condition: null
          
        - id: "pi_club"
          name: "P&I Club Membership"
          description: "International Group club vs fixed premium"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "ig_clubs", endpoint: "members/search"}
            - {type: "scrape", target: "pi_club_websites"}
          score_range: [0, 100]
          scoring_logic:
            ig_club_top_tier: 100
            ig_club: 90
            quality_fixed_premium: 70
            standard_fixed_premium: 55
            unknown_insurer: 35
          critical: false
          score_condition: null
          
        - id: "charterer_quality"
          name: "Charterer Relationships"
          description: "Quality of major charterers (oil majors, commodity traders)"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "clarksons", endpoint: "fixtures/search"}
            - {type: "api", provider: "ais_data", endpoint: "port_calls/charterer"}
          score_range: [0, 100]
          scoring_logic:
            major_oil_company_approved: 100
            major_commodity_traders: 90
            quality_charterers: 75
            mixed_charterers: 60
            unknown_charterers: 40
          critical: false
          score_condition: null
          
        - id: "banking_relationship"
          name: "Ship Finance Relationships"
          description: "Quality of ship finance banks"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "marine_money", endpoint: "transactions"}
            - {type: "filing", provider: "company_registries", document_types: ["mortgages"]}
          score_range: [0, 100]
          scoring_logic:
            major_ship_banks: 100
            established_lenders: 80
            regional_banks: 65
            alternative_finance: 45
            unknown: 35
          critical: false
          score_condition: null
          
        - id: "flag_state"
          name: "Flag State Quality"
          description: "Paris MoU white/grey/black list status"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "paris_mou", endpoint: "performance/flags"}
            - {type: "api", provider: "tokyo_mou", endpoint: "performance/flags"}
            - {type: "api", provider: "uscg", endpoint: "qualship21"}
          score_range: [0, 100]
          scoring_logic:
            white_list_top: 100
            white_list: 90
            grey_list_top: 70
            grey_list: 55
            black_list: 25
          critical: false
          score_condition: null
          
        - id: "industry_association"
          name: "Industry Association Membership"
          description: "BIMCO, Intertanko, Intercargo membership"
          weight: 0.10
          ttl: "static"
          ttl_seconds: 7776000
          sources:
            - {type: "api", provider: "bimco", endpoint: "members"}
            - {type: "api", provider: "intertanko", endpoint: "members"}
            - {type: "api", provider: "intercargo", endpoint: "members"}
          score_range: [0, 100]
          scoring_logic:
            multiple_memberships: 100
            major_association: 85
            regional_association: 65
            no_membership: 40
          critical: false
          score_condition: null
          
        - id: "technical_manager"
          name: "Technical Manager Quality"
          description: "Quality of third-party technical manager if applicable"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "equasis", endpoint: "companies/managers"}
            - {type: "api", provider: "ihs_markit", endpoint: "managers/search"}
          score_range: [0, 100]
          scoring_logic:
            top_tier_manager: 100
            quality_manager: 85
            average_manager: 65
            unknown_manager: 45
            in_house_quality: 90
            in_house_unknown: 55
          critical: false
          score_condition: null
          
        - id: "port_relationship"
          name: "Port Relationships"
          description: "Relationships with major ports and terminals"
          weight: 0.05
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "ais_data", endpoint: "port_calls/history"}
          score_range: [0, 100]
          scoring_logic:
            major_port_regular: 100
            quality_ports: 80
            mixed_ports: 60
            minor_ports_only: 45
          critical: false
          score_condition: null

      operational_telemetry:
        - id: "ais_compliance"
          name: "AIS Transmission Compliance"
          description: "Consistency of AIS transmission across fleet"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "marinetraffic", endpoint: "vessels/ais_quality"}
            - {type: "api", provider: "spire", endpoint: "vessels/transmission"}
            - {type: "api", provider: "exactearth", endpoint: "coverage/analysis"}
          score_range: [0, 100]
          scoring_logic:
            excellent_99plus: 100
            good_95_99: 85
            acceptable_90_95: 70
            concerning_80_90: 50
            poor_below_80: 30
          critical: true
          score_condition: ais_compliance_critical
          
        - id: "dark_activity"
          name: "Dark Activity Patterns"
          description: "AIS gaps in suspicious locations or patterns"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "marinetraffic", endpoint: "vessels/dark_events"}
            - {type: "api", provider: "windward", endpoint: "risk/dark_activity"}
            - {type: "api", provider: "pole_star", endpoint: "ais_gaps/analysis"}
          score_range: [0, 100]
          scoring_logic:
            no_unexplained_gaps: 100
            minor_technical_gaps: 85
            some_unexplained: 60
            concerning_patterns: 35
            high_risk_dark_activity: 15
          critical: true
          score_condition: dark_activity_critical
          
        - id: "route_risk"
          name: "Trading Route Risk Profile"
          description: "Exposure to high-risk areas (piracy, war zones)"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "marinetraffic", endpoint: "routes/risk"}
            - {type: "api", provider: "dryad_global", endpoint: "risk/areas"}
            - {type: "api", provider: "jwc", endpoint: "war_risk/areas"}
          score_range: [0, 100]
          scoring_logic:
            low_risk_routes: 100
            standard_risk: 80
            some_high_risk: 60
            frequent_high_risk: 40
            persistent_war_zone: 20
          critical: false
          score_condition: null
          
        - id: "psc_region_exposure"
          name: "PSC Region Exposure"
          description: "Trading pattern by PSC regime quality"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "ais_data", endpoint: "port_calls/regions"}
            - {type: "correlation", analyzer: "psc_regime_mapper"}
          score_range: [0, 100]
          scoring_logic:
            primarily_paris_tokyo_uscg: 100
            mixed_quality_regimes: 75
            primarily_weaker_regimes: 50
          critical: false
          score_condition: null
          
        - id: "operational_efficiency"
          name: "Operational Efficiency"
          description: "Speed/fuel efficiency patterns indicating discipline"
          weight: 0.10
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "marinetraffic", endpoint: "vessels/performance"}
            - {type: "api", provider: "siglar", endpoint: "efficiency/analysis"}
          score_range: [0, 100]
          scoring_logic:
            optimal_slow_steaming: 100
            efficient_operations: 85
            standard_operations: 70
            inefficient_patterns: 50
            erratic_operations: 35
          critical: false
          score_condition: null
          
        - id: "weather_routing"
          name: "Weather Routing Behavior"
          description: "Evidence of weather routing and risk management"
          weight: 0.10
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "ais_data", endpoint: "routes/weather_analysis"}
            - {type: "correlation", analyzer: "weather_routing_detector"}
          score_range: [0, 100]
          scoring_logic:
            consistent_routing_service: 100
            evidence_of_routing: 80
            standard_practices: 65
            poor_routing_decisions: 40
          critical: false
          score_condition: null

      safety_compliance:
        - id: "psc_detention"
          name: "PSC Detention Rate"
          description: "Port state control detention history"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "equasis", endpoint: "inspections/detentions"}
            - {type: "api", provider: "paris_mou", endpoint: "inspections/search"}
            - {type: "api", provider: "tokyo_mou", endpoint: "inspections/search"}
            - {type: "api", provider: "uscg", endpoint: "psc/search"}
          score_range: [0, 100]
          scoring_logic:
            no_detentions_3yr: 100
            no_detentions_2yr: 90
            single_detention_3yr: 70
            multiple_detentions: 45
            frequent_detentions: 20
            banned_vessels: 5
          critical: true
          score_condition: psc_detention_critical
          
        - id: "psc_deficiency"
          name: "PSC Deficiency Rate"
          description: "Average deficiencies per inspection vs benchmark"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "equasis", endpoint: "inspections/deficiencies"}
            - {type: "api", provider: "paris_mou", endpoint: "inspections/search"}
          score_range: [0, 100]
          scoring_logic:
            below_50pct_benchmark: 100
            50_75pct_benchmark: 85
            75_100pct_benchmark: 70
            100_150pct_benchmark: 50
            above_150pct: 30
          critical: false
          score_condition: null
          
        - id: "class_status"
          name: "Classification Status"
          description: "Class status, conditions, recommendations outstanding"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "class_societies", endpoint: "vessels/status"}
            - {type: "api", provider: "equasis", endpoint: "vessels/class_status"}
          score_range: [0, 100]
          scoring_logic:
            full_class_no_conditions: 100
            minor_recommendations: 85
            conditions_of_class: 60
            multiple_conditions: 40
            suspended_class: 15
            withdrawn_class: 0
          critical: true
          score_condition: class_status_critical
          
        - id: "ism_compliance"
          name: "ISM/ISPS Compliance"
          description: "Document of Compliance and safety management status"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "equasis", endpoint: "companies/ism"}
            - {type: "api", provider: "imo_gisis", endpoint: "ism/search"}
          score_range: [0, 100]
          scoring_logic:
            full_compliance_verified: 100
            compliant: 90
            minor_observations: 75
            major_observations: 50
            suspended: 20
            no_doc: 0
          critical: true
          score_condition: ism_compliance_critical
          
        - id: "casualty_history"
          name: "Casualty/Incident History"
          description: "Fleet casualty and incident history"
          weight: 0.10
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "ihs_markit", endpoint: "casualties/search"}
            - {type: "api", provider: "lloyd_list", endpoint: "casualties/search"}
            - {type: "api", provider: "imo_gisis", endpoint: "casualties/search"}
          score_range: [0, 100]
          scoring_logic:
            no_casualties_5yr: 100
            minor_incidents_only: 85
            moderate_casualty: 60
            serious_casualty: 40
            very_serious_casualty: 20
          critical: true
          score_condition: casualty_history_critical
          
        - id: "total_loss"
          name: "Total Loss History"
          description: "Total loss history (CTL or ATL)"
          weight: 0.10
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "ihs_markit", endpoint: "total_losses/search"}
            - {type: "api", provider: "iumi", endpoint: "statistics/losses"}
          score_range: [0, 100]
          scoring_logic:
            no_total_losses_10yr: 100
            no_total_losses_5yr: 85
            total_loss_over_5yr: 55
            total_loss_recent: 30
            multiple_total_losses: 10
          critical: true
          score_condition: total_loss_critical

      fleet_profile:
        - id: "fleet_age"
          name: "Fleet Age Profile"
          description: "Weighted average fleet age"
          weight: 0.30
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "equasis", endpoint: "vessels/particulars"}
            - {type: "api", provider: "ihs_markit", endpoint: "vessels/age"}
          score_range: [0, 100]
          scoring_logic:
            avg_under_5yr: 100
            avg_5_10yr: 85
            avg_10_15yr: 70
            avg_15_20yr: 50
            avg_20_25yr: 35
            avg_over_25yr: 20
          critical: false
          score_condition: null
          
        - id: "fleet_stability"
          name: "Fleet Size and Stability"
          description: "Fleet size changes and stability indicators"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "equasis", endpoint: "companies/fleet_history"}
            - {type: "api", provider: "clarksons", endpoint: "fleet/changes"}
          score_range: [0, 100]
          scoring_logic:
            stable_large_fleet: 100
            stable_medium_fleet: 85
            growing_fleet: 80
            stable_small_fleet: 70
            contracting_fleet: 50
            high_turnover: 35
          critical: false
          score_condition: null
          
        - id: "vessel_quality"
          name: "Vessel Quality Indicators"
          description: "Class notations, equipment quality"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "class_societies", endpoint: "vessels/notations"}
            - {type: "api", provider: "equasis", endpoint: "vessels/equipment"}
          score_range: [0, 100]
          scoring_logic:
            top_notations_equipment: 100
            quality_vessels: 85
            standard_vessels: 70
            basic_vessels: 50
            substandard_vessels: 30
          critical: false
          score_condition: null
          
        - id: "crew_certification"
          name: "Crew Certification Quality"
          description: "Crew nationality and certification patterns"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "paris_mou", endpoint: "inspections/crew"}
            - {type: "api", provider: "imo_gisis", endpoint: "stcw/performance"}
          score_range: [0, 100]
          scoring_logic:
            top_stcw_compliance: 100
            good_compliance: 85
            adequate: 70
            some_concerns: 50
            significant_concerns: 30
          critical: false
          score_condition: null
          
        - id: "management_consistency"
          name: "Management Consistency"
          description: "Stability of technical management"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "equasis", endpoint: "vessels/management_history"}
          score_range: [0, 100]
          scoring_logic:
            stable_long_term: 100
            stable: 85
            recent_change_quality: 70
            frequent_changes: 45
            recent_change_unknown: 40
          critical: false
          score_condition: null

      sanctions_compliance:
        - id: "sanctions_status"
          name: "Direct Sanctions Status"
          description: "OFAC, EU, UN sanctions list status"
          weight: 0.30
          ttl: "real_time"
          ttl_seconds: 3600
          sources:
            - {type: "api", provider: "ofac", endpoint: "sdn/search"}
            - {type: "api", provider: "eu_sanctions", endpoint: "search"}
            - {type: "api", provider: "un_sanctions", endpoint: "search"}
            - {type: "api", provider: "windward", endpoint: "sanctions/check"}
          score_range: [0, 100]
          scoring_logic:
            clean_all_lists: 100
            previously_listed_cleared: 70
            associated_entity_listed: 40
            directly_listed: 0
          critical: true
          score_condition: sanctions_status_critical
          
        - id: "ownership_transparency"
          name: "Beneficial Ownership Transparency"
          description: "Clarity of beneficial ownership structure"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "equasis", endpoint: "companies/ownership"}
            - {type: "api", provider: "ihs_markit", endpoint: "ownership/beneficial"}
            - {type: "api", provider: "lloyd_list", endpoint: "ownership/search"}
          score_range: [0, 100]
          scoring_logic:
            fully_transparent: 100
            reasonably_clear: 80
            some_opacity: 55
            significant_opacity: 35
            opaque_structure: 15
          critical: true
          score_condition: ownership_transparency_critical
          
        - id: "jurisdiction_risk"
          name: "High-Risk Jurisdiction Exposure"
          description: "Exposure to sanctioned or high-risk jurisdictions"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "ais_data", endpoint: "port_calls/jurisdiction"}
            - {type: "api", provider: "windward", endpoint: "risk/jurisdiction"}
          score_range: [0, 100]
          scoring_logic:
            no_high_risk_exposure: 100
            minimal_exposure: 80
            some_exposure_legitimate: 60
            concerning_exposure: 35
            sanctioned_jurisdiction: 10
          critical: true
          score_condition: jurisdiction_risk_critical
          
        - id: "sts_pattern"
          name: "STS Transfer Patterns"
          description: "Ship-to-ship transfer activity analysis"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "marinetraffic", endpoint: "vessels/sts_events"}
            - {type: "api", provider: "windward", endpoint: "risk/sts"}
            - {type: "satellite", provider: "planet", analyzer: "sts_detector"}
          score_range: [0, 100]
          scoring_logic:
            no_sts_or_legitimate: 100
            legitimate_sts_documented: 90
            some_unexplained_sts: 55
            suspicious_sts_patterns: 30
            high_risk_sts_activity: 10
          critical: true
          score_condition: sts_pattern_critical
          
        - id: "historical_sanctions"
          name: "Historical Sanctions Connections"
          description: "Historical connections to sanctioned entities"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "windward", endpoint: "risk/historical"}
            - {type: "api", provider: "refinitiv", endpoint: "world_check"}
          score_range: [0, 100]
          scoring_logic:
            no_historical_connection: 100
            distant_connection_cleared: 75
            previous_ownership_cleared: 55
            recent_connection: 30
            ongoing_concerns: 15
          critical: false
          score_condition: null

      environmental:
        - id: "imo2020_compliance"
          name: "IMO 2020 Sulphur Compliance"
          description: "Compliance with 0.5% sulphur cap"
          weight: 0.30
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "psc_databases", endpoint: "deficiencies/marpol"}
            - {type: "api", provider: "bunker_suppliers", endpoint: "fuel_records"}
          score_range: [0, 100]
          scoring_logic:
            full_compliance_verified: 100
            compliant_scrubbers: 90
            compliant_lsfo: 85
            minor_issues_resolved: 65
            violations_detected: 35
          critical: false
          score_condition: null
          
        - id: "bwm_compliance"
          name: "Ballast Water Management Compliance"
          description: "BWM convention compliance status"
          weight: 0.25
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "psc_databases", endpoint: "deficiencies/bwm"}
            - {type: "api", provider: "class_societies", endpoint: "vessels/bwm"}
          score_range: [0, 100]
          scoring_logic:
            type_d_compliant: 100
            compliant_schedule: 85
            pending_compliance: 65
            non_compliant: 30
          critical: false
          score_condition: null
          
        - id: "cii_rating"
          name: "CII Rating"
          description: "Carbon Intensity Indicator rating"
          weight: 0.25
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "class_societies", endpoint: "vessels/cii"}
            - {type: "api", provider: "imo_dcs", endpoint: "emissions/cii"}
          score_range: [0, 100]
          scoring_logic:
            rating_a: 100
            rating_b: 85
            rating_c: 70
            rating_d: 45
            rating_e: 20
          critical: false
          score_condition: null
          
        - id: "environmental_incident"
          name: "Environmental Incidents"
          description: "Pollution incidents and environmental fines"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "psc_databases", endpoint: "incidents/pollution"}
            - {type: "api", provider: "imo_gisis", endpoint: "incidents/pollution"}
            - {type: "news", provider: "gdelt", query: "{operator} pollution OR spill"}
          score_range: [0, 100]
          scoring_logic:
            no_incidents: 100
            minor_incident_resolved: 80
            moderate_incident: 55
            serious_incident: 30
            major_pollution: 10
          critical: false
          score_condition: null

      corporate_footprint:
        - id: "website_quality"
          name: "Website Quality and Transparency"
          description: "Quality of corporate website and disclosures"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", analyzer: "transparency_scorer"}
          score_range: [0, 100]
          scoring_logic:
            comprehensive_professional: 100
            good_quality: 80
            basic: 60
            minimal: 40
            no_website: 20
          critical: false
          score_condition: null
          
        - id: "fleet_disclosure"
          name: "Fleet List Disclosure"
          description: "Public fleet list availability"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/fleet", "/vessels"]}
          score_range: [0, 100]
          scoring_logic:
            full_fleet_list_published: 100
            partial_list: 75
            general_description: 50
            no_disclosure: 30
          critical: false
          score_condition: null
          
        - id: "sustainability_reporting"
          name: "Sustainability/ESG Reporting"
          description: "Quality of sustainability reporting"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/sustainability", "/esg"]}
            - {type: "api", provider: "cdp", endpoint: "responses/search"}
          score_range: [0, 100]
          scoring_logic:
            comprehensive_third_party_verified: 100
            good_reporting: 80
            basic_report: 60
            website_only: 40
            none: 20
          critical: false
          score_condition: null
          
        - id: "safety_communication"
          name: "Safety Culture Communication"
          description: "Evidence of safety culture in communications"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/safety", "/hseq", "/quality"]}
          score_range: [0, 100]
          scoring_logic:
            strong_safety_focus: 100
            good_communication: 80
            basic: 60
            minimal: 40
            none: 25
          critical: false
          score_condition: null
          
        - id: "crew_welfare"
          name: "Crew Welfare Visibility"
          description: "Visible commitment to crew welfare"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/careers", "/seafarers"]}
            - {type: "api", provider: "itf", endpoint: "welfare/search"}
          score_range: [0, 100]
          scoring_logic:
            strong_welfare_programs: 100
            good_welfare: 80
            standard: 60
            minimal: 40
            concerns: 25
          critical: false
          score_condition: null
          
        - id: "industry_presence"
          name: "Industry Presence"
          description: "Conference attendance, publications, industry engagement"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "conference_websites"}
            - {type: "news", provider: "tradewinds", query: "{operator}"}
          score_range: [0, 100]
          scoring_logic:
            active_industry_leader: 100
            regular_presence: 80
            occasional: 60
            minimal: 40
            none: 25
          critical: false
          score_condition: null

      structured_data:
        - id: "vetting"
          name: "RightShip/Vetting Score"
          description: "Third-party vetting scores"
          weight: 0.50
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "rightship", endpoint: "vessels/score"}
            - {type: "api", provider: "ocimf_sire", endpoint: "reports/search"}
            - {type: "api", provider: "cdp", endpoint: "vessel_inspection/search"}
          score_range: [0, 100]
          scoring_logic:
            5_star: 100
            4_star: 85
            3_star: 70
            2_star: 50
            1_star: 30
            not_rated: 55
          critical: false
          score_condition: null
          
        - id: "esg_rating"
          name: "ESG Maritime Rating"
          description: "Maritime-specific ESG ratings"
          weight: 0.30
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "sustainalytics", endpoint: "ratings/shipping"}
            - {type: "api", provider: "msci", endpoint: "esg/ratings"}
          score_range: [0, 100]
          scoring_logic:
            leader: 100
            above_avg: 80
            average: 60
            below_avg: 40
            laggard: 20
          critical: false
          score_condition: null
          
        - id: "credit_rating"
          name: "Credit Rating"
          description: "Corporate credit rating if available"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "sp_global", endpoint: "ratings"}
            - {type: "api", provider: "moodys", endpoint: "ratings"}
          score_range: [0, 100]
          scoring_logic:
            investment_grade: 100
            bb_range: 70
            b_range: 50
            ccc_below: 30
            not_rated: 55
          critical: false
          score_condition: null

    # -------------------------------------------------------------------------
    # TIER THRESHOLDS
    # -------------------------------------------------------------------------
    tier_thresholds:
      tier_1:
        id: 1
        label: "PREFERRED"
        min_score: 800
        max_score: 1000
        description: "Excellent operator - auto-approve at preferred pricing"
        auto_approve: true
        auto_decline: false
        base_rate: 0.0015  # 0.15% of insured value
        
      tier_2:
        id: 2
        label: "STANDARD"
        min_score: 650
        max_score: 799
        description: "Good operator - auto-approve at standard pricing"
        auto_approve: true
        auto_decline: false
        base_rate: 0.0022  # 0.22% of insured value
        
      tier_3:
        id: 3
        label: "ELEVATED"
        min_score: 500
        max_score: 649
        description: "Moderate risk - auto-approve with conditions"
        auto_approve: false
        auto_decline: false
        base_rate: 0.0032  # 0.32% of insured value
        
      tier_4:
        id: 4
        label: "HIGH_RISK"
        min_score: 350
        max_score: 499
        description: "High risk - manual review required"
        auto_approve: false
        auto_decline: false
        base_rate: 0.0050  # 0.50% of insured value
        
      tier_5:
        id: 5
        label: "CRITICAL"
        min_score: 0
        max_score: 349
        description: "Critical risk - decline or senior review"
        auto_approve: false
        auto_decline: true
        base_rate: 0.0080  # 0.80% of insured value

    # -------------------------------------------------------------------------
    # CONDITION DEFINITIONS
    # -------------------------------------------------------------------------
    direct_conditions:
      - id: fleet_size_info
        bands:
          - {return: true, tier_override: null, action: "INFO", note: "Fleet size recorded"}
      
      - id: psc_detentions_true
        bands:
          - {return: true, tier_override: null, action: "REFER", note: "PSC detentions in past 36 months"}
      
      - id: total_losses_true
        bands:
          - {return: true, tier_override: 4, action: "REFER", note: "Total losses in past 5 years"}
      
      - id: third_party_manager_info
        bands:
          - {return: true, tier_override: null, action: "INFO", note: "Third-party technical management"}
      
      - id: sanctioned_trade_true
        bands:
          - {return: true, tier_override: 5, action: "DECLINE", note: "Trading to sanctioned regions - coverage not available"}
  
    score_conditions:
      - id: operational_telemetry_critical
        bands:
          - {max: 30, tier_override: 5, action: "DECLINE", note: "Critical AIS/operational concerns"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant operational concerns"}
        inclusive_max: false
      
      - id: safety_compliance_critical
        bands:
          - {max: 30, tier_override: 5, action: "DECLINE", note: "Critical safety compliance issues"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant safety concerns"}
        inclusive_max: false
      
      - id: sanctions_compliance_critical
        bands:
          - {max: 20, tier_override: 5, action: "DECLINE", note: "Sanctions exposure - coverage not available"}
          - {max: 40, tier_override: 4, action: "REFER", note: "Sanctions concerns require review"}
        inclusive_max: false
      
      - id: ais_compliance_critical
        bands:
          - {max: 40, tier_override: 4, action: "REFER", note: "AIS compliance concerns"}
        inclusive_max: false
      
      - id: dark_activity_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "High-risk dark activity"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Concerning dark activity patterns"}
        inclusive_max: false
      
      - id: psc_detention_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Elevated PSC detention rate"}
        inclusive_max: false
      
      - id: class_status_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Class suspended/withdrawn"}
          - {max: 50, tier_override: 4, action: "REFER", note: "Class status concerns"}
        inclusive_max: false
      
      - id: ism_compliance_critical
        bands:
          - {max: 30, tier_override: 5, action: "DECLINE", note: "ISM compliance failure"}
          - {max: 50, tier_override: 4, action: "REFER", note: "ISM concerns"}
        inclusive_max: false
      
      - id: casualty_history_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Serious casualty history"}
        inclusive_max: false
      
      - id: total_loss_critical
        bands:
          - {max: 40, tier_override: 4, action: "REFER", note: "Total loss history"}
        inclusive_max: false
      
      - id: sanctions_status_critical
        bands:
          - {max: 20, tier_override: 5, action: "DECLINE", note: "Sanctions listed - coverage not available"}
        inclusive_max: false
      
      - id: ownership_transparency_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Ownership transparency concerns"}
        inclusive_max: false
      
      - id: jurisdiction_risk_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Sanctioned jurisdiction exposure"}
          - {max: 45, tier_override: 4, action: "REFER", note: "High-risk jurisdiction exposure"}
        inclusive_max: false
      
      - id: sts_pattern_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "High-risk STS activity"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Suspicious STS patterns"}
        inclusive_max: false

    # -------------------------------------------------------------------------
    # PRICING PARAMETERS
    # -------------------------------------------------------------------------
    pricing:
      deductible_guidelines:
        tier_1_pct: 0.005
        tier_2_pct: 0.0075
        tier_3_pct: 0.01
        tier_4_pct: 0.015
        tier_5_pct: 0.02
        standard_amounts: [50000, 100000, 150000, 250000, 500000, 1000000]
      
      experience_modifiers:
        excellent_5yr: 0.85
        good_5yr: 0.90
        clean_3yr: 0.95
        minor_claims: 1.00
        moderate_claims: 1.20
        significant_claims: 1.40
        total_loss: 1.75
        
      war_risk_additional:
        standard_areas: 0.00
        listed_areas: 0.0025
        high_risk_areas: 0.0075
        breach_areas: "quoted_separately"
        
      taxes_fees_rate: 0.03

    # -------------------------------------------------------------------------
    # TEST PROFILES
    # -------------------------------------------------------------------------
    test_profiles:
      excellent_liner:
        description: "Major container liner with excellent record"
        expected_tier: [1, 2]
        expected_score_range: [800, 950]
        operator_type: "MAJOR_LINER"
        vessel_category: "CONTAINER"
        trading_pattern: "LINER_REGULAR"
        flag_state_quality: "WHITE_LIST"
        fleet_age_band: "AGE_5_10"
        signals:
          network_authority:
            classification_society: 95
            pi_club: 92
            charterer_quality: 88
            banking_relationship: 90
            flag_state: 95
            industry_association: 85
            technical_manager: 90
            port_relationship: 85
          operational_telemetry:
            ais_compliance: 98
            dark_activity: 95
            route_risk: 85
            psc_region_exposure: 80
            operational_efficiency: 88
            weather_routing: 85
          safety_compliance:
            psc_detention: 95
            psc_deficiency: 88
            class_status: 98
            ism_compliance: 95
            casualty_history: 90
            total_loss: 100
          fleet_profile:
            fleet_age: 85
            fleet_stability: 90
            vessel_quality: 92
            crew_certification: 88
            management_consistency: 95
          sanctions_compliance:
            sanctions_status: 100
            ownership_transparency: 95
            jurisdiction_risk: 90
            sts_pattern: 100
            historical_sanctions: 100
          environmental:
            imo2020_compliance: 95
            bwm_compliance: 92
            cii_rating: 85
            environmental_incident: 95
          corporate_footprint:
            website_quality: 90
            fleet_disclosure: 95
            sustainability_reporting: 88
            safety_communication: 85
            crew_welfare: 82
            industry_presence: 90
          structured_data:
            vetting: 92
            esg_rating: 85
            credit_rating: 88

      average_tanker:
        description: "Mid-size tanker operator with typical profile"
        expected_tier: [2, 3]
        expected_score_range: [580, 720]
        operator_type: "REGIONAL_OPERATOR"
        vessel_category: "TANKER"
        trading_pattern: "SPOT_TRAMP"
        flag_state_quality: "WHITE_LIST"
        fleet_age_band: "AGE_10_15"
        signals:
          network_authority:
            classification_society: 85
            pi_club: 78
            charterer_quality: 72
            banking_relationship: 70
            flag_state: 80
            industry_association: 65
            technical_manager: 75
            port_relationship: 70
          operational_telemetry:
            ais_compliance: 88
            dark_activity: 82
            route_risk: 70
            psc_region_exposure: 72
            operational_efficiency: 75
            weather_routing: 70
          safety_compliance:
            psc_detention: 78
            psc_deficiency: 72
            class_status: 85
            ism_compliance: 85
            casualty_history: 80
            total_loss: 95
          fleet_profile:
            fleet_age: 65
            fleet_stability: 75
            vessel_quality: 72
            crew_certification: 75
            management_consistency: 80
          sanctions_compliance:
            sanctions_status: 100
            ownership_transparency: 80
            jurisdiction_risk: 78
            sts_pattern: 85
            historical_sanctions: 95
          environmental:
            imo2020_compliance: 85
            bwm_compliance: 78
            cii_rating: 70
            environmental_incident: 88
          corporate_footprint:
            website_quality: 65
            fleet_disclosure: 70
            sustainability_reporting: 55
            safety_communication: 60
            crew_welfare: 60
            industry_presence: 55
          structured_data:
            vetting: 75
            esg_rating: 60
            credit_rating: 65

      high_risk_independent:
        description: "Small independent with safety concerns"
        expected_tier: [4, 5]
        expected_score_range: [280, 450]
        operator_type: "INDEPENDENT"
        vessel_category: "GENERAL_CARGO"
        trading_pattern: "SPOT_TRAMP"
        flag_state_quality: "GREY_LIST"
        fleet_age_band: "AGE_20_25"
        signals:
          network_authority:
            classification_society: 55
            pi_club: 45
            charterer_quality: 40
            banking_relationship: 35
            flag_state: 50
            industry_association: 30
            technical_manager: 45
            port_relationship: 40
          operational_telemetry:
            ais_compliance: 65
            dark_activity: 50
            route_risk: 45
            psc_region_exposure: 50
            operational_efficiency: 50
            weather_routing: 45
          safety_compliance:
            psc_detention: 45
            psc_deficiency: 48
            class_status: 55
            ism_compliance: 60
            casualty_history: 55
            total_loss: 75
          fleet_profile:
            fleet_age: 35
            fleet_stability: 50
            vessel_quality: 45
            crew_certification: 52
            management_consistency: 55
          sanctions_compliance:
            sanctions_status: 90
            ownership_transparency: 50
            jurisdiction_risk: 55
            sts_pattern: 70
            historical_sanctions: 85
          environmental:
            imo2020_compliance: 60
            bwm_compliance: 55
            cii_rating: 45
            environmental_incident: 70
          corporate_footprint:
            website_quality: 35
            fleet_disclosure: 30
            sustainability_reporting: 20
            safety_communication: 30
            crew_welfare: 35
            industry_presence: 25
          structured_data:
            vetting: 50
            esg_rating: 35
            credit_rating: 40

      lng_carrier:
        description: "LNG carrier operator with high standards"
        expected_tier: [1, 2]
        expected_score_range: [750, 920]
        operator_type: "MAJOR_TANKER"
        vessel_category: "LNG_LPG"
        trading_pattern: "INDUSTRIAL"
        flag_state_quality: "WHITE_LIST"
        fleet_age_band: "AGE_5_10"
        signals:
          network_authority:
            classification_society: 100
            pi_club: 95
            charterer_quality: 95
            banking_relationship: 92
            flag_state: 95
            industry_association: 88
            technical_manager: 95
            port_relationship: 90
          operational_telemetry:
            ais_compliance: 99
            dark_activity: 98
            route_risk: 85
            psc_region_exposure: 88
            operational_efficiency: 92
            weather_routing: 90
          safety_compliance:
            psc_detention: 98
            psc_deficiency: 95
            class_status: 100
            ism_compliance: 98
            casualty_history: 95
            total_loss: 100
          fleet_profile:
            fleet_age: 88
            fleet_stability: 92
            vessel_quality: 95
            crew_certification: 95
            management_consistency: 95
          sanctions_compliance:
            sanctions_status: 100
            ownership_transparency: 98
            jurisdiction_risk: 92
            sts_pattern: 100
            historical_sanctions: 100
          environmental:
            imo2020_compliance: 98
            bwm_compliance: 95
            cii_rating: 88
            environmental_incident: 98
          corporate_footprint:
            website_quality: 92
            fleet_disclosure: 95
            sustainability_reporting: 90
            safety_communication: 92
            crew_welfare: 88
            industry_presence: 85
          structured_data:
            vetting: 95
            esg_rating: 88
            credit_rating: 90

      sanctions_concern:
        description: "Operator with sanctions exposure concerns"
        expected_tier: [5]
        expected_score_range: [0, 350]
        operator_type: "UNKNOWN"
        vessel_category: "TANKER"
        trading_pattern: "SPOT_TRAMP"
        flag_state_quality: "BLACK_LIST"
        fleet_age_band: "AGE_15_20"
        direct_queries:
          sanctioned_trade: true
        signals:
          network_authority:
            classification_society: 50
            pi_club: 35
            flag_state: 25
            industry_association: 20
          operational_telemetry:
            ais_compliance: 40
            dark_activity: 25
            route_risk: 30
          safety_compliance:
            psc_detention: 45
            psc_deficiency: 50
            class_status: 55
            ism_compliance: 55
          sanctions_compliance:
            sanctions_status: 15
            ownership_transparency: 25
            jurisdiction_risk: 20
            sts_pattern: 20
            historical_sanctions: 30

      offshore_operator:
        description: "Offshore supply vessel operator"
        expected_tier: [2, 3]
        expected_score_range: [580, 720]
        operator_type: "REGIONAL_OPERATOR"
        vessel_category: "OFFSHORE"
        trading_pattern: "INDUSTRIAL"
        flag_state_quality: "WHITE_LIST"
        fleet_age_band: "AGE_10_15"
        signals:
          network_authority:
            classification_society: 90
            pi_club: 82
            charterer_quality: 85
            banking_relationship: 75
            flag_state: 85
            industry_association: 75
            technical_manager: 80
            port_relationship: 78
          operational_telemetry:
            ais_compliance: 92
            dark_activity: 88
            route_risk: 70
            psc_region_exposure: 75
            operational_efficiency: 80
            weather_routing: 78
          safety_compliance:
            psc_detention: 85
            psc_deficiency: 80
            class_status: 90
            ism_compliance: 88
            casualty_history: 82
            total_loss: 95
          fleet_profile:
            fleet_age: 70
            fleet_stability: 78
            vessel_quality: 82
            crew_certification: 85
            management_consistency: 80
          sanctions_compliance:
            sanctions_status: 100
            ownership_transparency: 88
            jurisdiction_risk: 82
            sts_pattern: 100
            historical_sanctions: 100
          environmental:
            imo2020_compliance: 88
            bwm_compliance: 82
            cii_rating: 72
            environmental_incident: 90
          corporate_footprint:
            website_quality: 75
            fleet_disclosure: 80
            sustainability_reporting: 65
            safety_communication: 78
            crew_welfare: 75
            industry_presence: 68
          structured_data:
            vetting: 82
            esg_rating: 68
            credit_rating: 70

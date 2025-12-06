# =============================================================================
# DSI Model Configuration - Energy Insurance
# =============================================================================
#
# This file defines the complete configuration for Energy insurance coverage.
# It is the single source of truth for:
#   - Model structure and parameters
#   - Signal definitions and weights
#   - Pricing factors and thresholds
#   - Operator type, segment, and geography modifiers
#   - Test profiles for actuarial validation
#
# Premium calculation follows DSI Foundational Principle 9: Signal -> Score -> Tier -> Price
#
# DSI PRINCIPLES APPLIED:
#   1. All signals must be externally observable (OSHA, EPA, BSEE, satellite data)
#   2. Direct queries are OPTIONAL - model works without them
#   3. Categorical features are inferred from regulatory filings and public data
#   4. Tier determines base rate; modifiers adjust for exposure characteristics
#   5. Energy is suited to DSI due to extensive regulatory disclosure requirements
#
# KEY DSI PRINCIPLE: We assess OPERATOR safety culture and operational patterns,
# not individual asset characteristics. Good operators maintain all assets well;
# poor operators have systemic issues across their portfolio.
#
# KEY DATA SOURCES:
#   - OSHA (injury/illness records, violations)
#   - BSEE (offshore incidents, inspections)
#   - EPA (violations, spills, emissions)
#   - State oil/gas commissions
#   - Satellite imagery (flaring, facility activity)
#   - SEC filings (public companies)
#   - Industry databases (IOGP, API)
#
# Version: 2.0.0
# Last Updated: 2025-12
# =============================================================================

energy:
  energy_general:
    metadata:
      name: "DSI Energy Insurance Model"
      description: "Energy property and liability coverage based on observable safety, environmental, and operational signals"
      version: "2.0.0"
      coverage_types:
        - "property_damage"
        - "business_interruption"
        - "control_of_well"
        - "operators_extra_expense"
        - "third_party_liability"
        - "pollution_liability"
        - "removal_of_wreck"
      applicable_segments:
        - "upstream_conventional"
        - "upstream_unconventional"
        - "upstream_offshore"
        - "upstream_deepwater"
        - "midstream_pipeline"
        - "midstream_processing"
        - "midstream_storage"
        - "downstream_refining"
        - "downstream_petrochemical"
        - "power_generation"
        - "renewable"
      applicable_markets: ["us", "uk", "eu", "apac", "latam", "mena"]
      min_premium: 100000
      default_currency: "USD"

    # -------------------------------------------------------------------------
    # DIRECT OPTIONAL QUERIES
    # -------------------------------------------------------------------------
    direct_optional_queries:
      - id: "major_incidents"
        question: "Any major incidents (explosion, blowout, major spill) in past 5 years?"
        direct_condition: major_incidents_true
        
      - id: "fatalities"
        question: "Any work-related fatalities in past 3 years?"
        direct_condition: fatalities_true
        
      - id: "regulatory_enforcement"
        question: "Any significant regulatory enforcement actions pending?"
        direct_condition: regulatory_enforcement_true
        
      - id: "decommissioning_obligations"
        question: "Any significant unfunded decommissioning obligations?"
        direct_condition: decommissioning_obligations_true
        
      - id: "joint_venture_operator"
        question: "Are you the designated operator for JV assets?"
        direct_condition: jv_operator_info
        
      - id: "third_party_contractor"
        question: "Do you use third-party contractors for drilling/completions?"
        direct_condition: contractor_info

    # -------------------------------------------------------------------------
    # CATEGORICAL FEATURES
    # -------------------------------------------------------------------------
    categorical_features:
      operator_type:
        description: "Operator classification based on size, integration, and ownership"
        inference_method:
          primary: "sec_filing_analysis"
          fallback: "production_database_lookup"
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K", "20-F"]}
            - {type: "api", provider: "enverus", endpoint: "operators/profile"}
            - {type: "api", provider: "rystad", endpoint: "companies/profile"}
            - {type: "api", provider: "ihs_markit", endpoint: "operators/search"}
          confidence_threshold: 0.90
          default_on_failure: "MID_INDEPENDENT"
        values:
          - id: "SUPERMAJOR"
            label: "Supermajor"
            modifier: 0.75
            description: "ExxonMobil, Shell, BP, Chevron, TotalEnergies, etc."
            inference_criteria: {production_min_boed: 2000000, integrated: true, market_cap_min: 100000000000}
            
          - id: "MAJOR_INTEGRATED"
            label: "Major Integrated"
            modifier: 0.85
            description: "Large integrated oil companies"
            inference_criteria: {production_min_boed: 500000, integrated: true}
            
          - id: "LARGE_INDEPENDENT"
            label: "Large Independent"
            modifier: 0.95
            description: "Large E&P independents (ConocoPhillips, EOG, etc.)"
            inference_criteria: {production_min_boed: 200000, integrated: false}
            
          - id: "MID_INDEPENDENT"
            label: "Mid-Size Independent"
            modifier: 1.00
            description: "Mid-size E&P companies"
            inference_criteria: {production_range_boed: [50000, 200000]}
            
          - id: "SMALL_INDEPENDENT"
            label: "Small Independent"
            modifier: 1.20
            description: "Small E&P operators"
            inference_criteria: {production_max_boed: 50000}
            
          - id: "NATIONAL_OIL"
            label: "National Oil Company"
            modifier: 0.90
            description: "State-owned national oil companies"
            inference_criteria: {state_owned: true}
            
          - id: "MIDSTREAM_MAJOR"
            label: "Major Midstream"
            modifier: 0.85
            description: "Major pipeline/processing operators"
            inference_criteria: {midstream_focus: true, market_cap_min: 10000000000}
            
          - id: "DOWNSTREAM_MAJOR"
            label: "Major Downstream"
            modifier: 0.90
            description: "Major refining operators"
            inference_criteria: {refining_focus: true, capacity_min_bpd: 200000}
            
          - id: "PRIVATE_EQUITY"
            label: "Private Equity Backed"
            modifier: 1.15
            description: "PE-backed operators"
            inference_criteria: {pe_ownership: true}
            
          - id: "UNKNOWN"
            label: "Unknown/New Operator"
            modifier: 1.40
            description: "New or unclassified operator"
            inference_criteria: {}

      operation_segment:
        description: "Primary operational segment"
        inference_method:
          primary: "production_data_analysis"
          fallback: "asset_registry_lookup"
          sources:
            - {type: "api", provider: "enverus", endpoint: "production/summary"}
            - {type: "api", provider: "bsee", endpoint: "operators/assets"}
            - {type: "api", provider: "state_commissions", endpoint: "permits/operator"}
          confidence_threshold: 0.85
          default_on_failure: "MIXED"
        values:
          - id: "UPSTREAM_CONVENTIONAL"
            label: "Upstream Conventional"
            modifier: 1.00
            description: "Conventional onshore oil & gas production"
            
          - id: "UPSTREAM_UNCONVENTIONAL"
            label: "Upstream Unconventional"
            modifier: 0.95
            description: "Shale, tight oil, CBM operations"
            
          - id: "UPSTREAM_OFFSHORE"
            label: "Upstream Offshore (Shelf)"
            modifier: 1.20
            description: "Shallow water offshore operations"
            
          - id: "UPSTREAM_DEEPWATER"
            label: "Upstream Deepwater"
            modifier: 1.50
            description: "Deepwater offshore operations (>500m)"
            
          - id: "MIDSTREAM_PIPELINE"
            label: "Midstream Pipeline"
            modifier: 0.80
            description: "Oil & gas pipeline operations"
            
          - id: "MIDSTREAM_PROCESSING"
            label: "Midstream Processing"
            modifier: 1.00
            description: "Gas processing, NGL fractionation"
            
          - id: "MIDSTREAM_STORAGE"
            label: "Midstream Storage"
            modifier: 0.85
            description: "Crude/product storage terminals"
            
          - id: "DOWNSTREAM_REFINING"
            label: "Downstream Refining"
            modifier: 1.30
            description: "Petroleum refining operations"
            
          - id: "DOWNSTREAM_PETROCHEMICAL"
            label: "Downstream Petrochemical"
            modifier: 1.25
            description: "Petrochemical manufacturing"
            
          - id: "POWER_GENERATION"
            label: "Power Generation"
            modifier: 0.90
            description: "Gas-fired power generation"
            
          - id: "RENEWABLE"
            label: "Renewable Energy"
            modifier: 0.70
            description: "Wind, solar, other renewables"
            
          - id: "MIXED"
            label: "Mixed Operations"
            modifier: 1.05
            description: "Diversified operations across segments"

      geographic_focus:
        description: "Primary geographic focus of operations"
        inference_method:
          primary: "asset_location_analysis"
          sources:
            - {type: "api", provider: "enverus", endpoint: "assets/geography"}
            - {type: "api", provider: "rystad", endpoint: "production/geography"}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          confidence_threshold: 0.85
          default_on_failure: "OTHER"
        values:
          - {id: "US_ONSHORE", label: "US Onshore", modifier: 1.00}
          - {id: "US_GULF_SHELF", label: "US Gulf Shelf", modifier: 1.10}
          - {id: "US_GULF_DEEPWATER", label: "US Gulf Deepwater", modifier: 1.40}
          - {id: "NORTH_SEA", label: "North Sea", modifier: 1.15}
          - {id: "WEST_AFRICA", label: "West Africa", modifier: 1.25}
          - {id: "MIDDLE_EAST", label: "Middle East", modifier: 1.20}
          - {id: "ASIA_PACIFIC", label: "Asia Pacific", modifier: 1.10}
          - {id: "LATIN_AMERICA", label: "Latin America", modifier: 1.20}
          - {id: "GLOBAL_DIVERSIFIED", label: "Global Diversified", modifier: 1.05}
          - {id: "OTHER", label: "Other", modifier: 1.15}

    # -------------------------------------------------------------------------
    # SIGNAL GROUPS
    # -------------------------------------------------------------------------
    signal_groups:
      - id: "network_authority"
        name: "Network Authority"
        description: "Quality of partnerships, contractors, and industry relationships"
        weight: 0.10
        test_scores: {excellent: 88, average: 68, poor: 40}
        critical: false
        score_condition: null
        
      - id: "safety_performance"
        name: "Safety Performance"
        description: "OSHA metrics, incidents, process safety events"
        weight: 0.30
        test_scores: {excellent: 92, average: 72, poor: 35}
        critical: true
        score_condition: safety_performance_critical
        
      - id: "environmental_compliance"
        name: "Environmental Compliance"
        description: "EPA violations, spills, emissions, flaring"
        weight: 0.20
        test_scores: {excellent: 90, average: 70, poor: 38}
        critical: true
        score_condition: environmental_compliance_critical
        
      - id: "operational_telemetry"
        name: "Operational Telemetry"
        description: "Production patterns, facility activity, maintenance signals"
        weight: 0.10
        test_scores: {excellent: 85, average: 68, poor: 45}
        critical: false
        score_condition: null
        
      - id: "financial_stability"
        name: "Financial Stability"
        description: "Credit rating, leverage, ARO coverage, capex trends"
        weight: 0.10
        test_scores: {excellent: 88, average: 70, poor: 40}
        critical: false
        score_condition: financial_stability_critical
        
      - id: "asset_portfolio"
        name: "Asset Portfolio"
        description: "Asset age, concentration, complexity, permit status"
        weight: 0.10
        test_scores: {excellent: 82, average: 65, poor: 42}
        critical: false
        score_condition: null
        
      - id: "corporate_footprint"
        name: "Corporate Footprint"
        description: "Safety culture communication, ESG reporting, HSE leadership"
        weight: 0.05
        test_scores: {excellent: 85, average: 62, poor: 38}
        critical: false
        score_condition: null
        
      - id: "structured_data"
        name: "Structured Data"
        description: "Third-party ESG ratings and industry benchmarks"
        weight: 0.05
        test_scores: {excellent: 85, average: 65, poor: 40}
        critical: false
        score_condition: null

    # -------------------------------------------------------------------------
    # SIGNAL FEATURES
    # -------------------------------------------------------------------------
    signal_features:
      network_authority:
        - id: "partner_quality"
          name: "JV Partner Quality"
          description: "Quality of joint venture partners"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
            - {type: "api", provider: "enverus", endpoint: "joint_ventures"}
            - {type: "scrape", target: "company_website", pages: ["/operations", "/partners"]}
          score_range: [0, 100]
          scoring_logic:
            supermajor_partners: 100
            major_quality_partners: 85
            reputable_independents: 70
            mixed_quality: 55
            unknown_partners: 40
          critical: false
          score_condition: null
          
        - id: "contractor_quality"
          name: "Contractor Relationships"
          description: "Quality of drilling/service contractors"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "rigzone", endpoint: "contractors/search"}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            tier_1_contractors: 100
            major_contractors: 85
            regional_reputable: 70
            small_contractors: 55
            unknown: 40
          critical: false
          score_condition: null
          
        - id: "banking_relationship"
          name: "Banking/Financing Relationships"
          description: "Quality of banking relationships"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K", "8-K"]}
          score_range: [0, 100]
          scoring_logic:
            major_banks_syndicate: 100
            quality_regional_banks: 80
            specialty_lenders: 65
            limited_access: 45
            distressed_financing: 25
          critical: false
          score_condition: null
          
        - id: "insurance_history"
          name: "Insurance Market Reputation"
          description: "Historical insurance placement and claims record"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "internal", provider: "placement_history"}
            - {type: "api", provider: "insurance_market_data"}
          score_range: [0, 100]
          scoring_logic:
            excellent_history: 100
            good_history: 85
            average: 70
            some_concerns: 50
            poor_history: 30
          critical: false
          score_condition: null
          
        - id: "industry_association"
          name: "Industry Association Membership"
          description: "API, IOGP, and other association involvement"
          weight: 0.10
          ttl: "static"
          ttl_seconds: 7776000
          sources:
            - {type: "api", provider: "api", endpoint: "members"}
            - {type: "api", provider: "iogp", endpoint: "members"}
            - {type: "scrape", target: "association_websites"}
          score_range: [0, 100]
          scoring_logic:
            leadership_roles: 100
            active_committee_member: 85
            regular_member: 70
            limited_participation: 50
            non_member: 35
          critical: false
          score_condition: null
          
        - id: "regulator_relationship"
          name: "Regulator Relationship Quality"
          description: "Quality of regulatory relationships"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "bsee", endpoint: "operators/compliance"}
            - {type: "api", provider: "state_commissions", endpoint: "compliance/summary"}
          score_range: [0, 100]
          scoring_logic:
            exemplary_compliance: 100
            good_standing: 85
            minor_issues_resolved: 70
            ongoing_issues: 45
            adversarial_relationship: 25
          critical: false
          score_condition: null
          
        - id: "customer_quality"
          name: "Offtake/Customer Quality"
          description: "Quality of product offtake relationships"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            major_creditworthy: 100
            diversified_quality: 85
            concentrated_quality: 70
            mixed: 55
            weak_counterparties: 35
          critical: false
          score_condition: null

      safety_performance:
        - id: "osha_trir"
          name: "OSHA Total Recordable Incident Rate"
          description: "TRIR vs industry benchmark"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "osha", endpoint: "iir/search"}
            - {type: "api", provider: "bls", endpoint: "industry_safety"}
          score_range: [0, 100]
          scoring_logic:
            below_50pct_benchmark: 100
            50_75pct_benchmark: 85
            75_100pct_benchmark: 70
            100_150pct_benchmark: 50
            above_150pct_benchmark: 30
            above_200pct_benchmark: 15
          critical: true
          score_condition: osha_trir_critical
          
        - id: "osha_violations"
          name: "OSHA Serious Violations"
          description: "History of serious/willful OSHA violations"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "osha", endpoint: "violations/search"}
          score_range: [0, 100]
          scoring_logic:
            no_serious_5yr: 100
            minor_violations_only: 85
            serious_over_3yr_ago: 65
            serious_recent: 40
            willful_any: 20
            repeat_violations: 10
          critical: true
          score_condition: osha_violations_critical
          
        - id: "bsee_incident"
          name: "BSEE Incidents"
          description: "Offshore incidents reported to BSEE"
          weight: 0.10
          ttl: "dynamic"
          ttl_seconds: 86400
          applicable_segments: ["upstream_offshore", "upstream_deepwater"]
          sources:
            - {type: "api", provider: "bsee", endpoint: "incidents/search"}
          score_range: [0, 100]
          scoring_logic:
            no_incidents_5yr: 100
            minor_incidents_only: 80
            moderate_incidents: 60
            significant_incidents: 40
            major_incidents: 20
          critical: true
          score_condition: bsee_incident_critical
          
        - id: "process_safety"
          name: "Process Safety Events"
          description: "Tier 1 and Tier 2 process safety events"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "api", endpoint: "pse/reports"}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
            - {type: "api", provider: "csb", endpoint: "investigations"}
          score_range: [0, 100]
          scoring_logic:
            no_tier_1_5yr: 100
            tier_2_only: 85
            tier_1_over_5yr_ago: 70
            tier_1_recent_isolated: 50
            tier_1_pattern: 30
            major_pse: 15
          critical: true
          score_condition: process_safety_critical
          
        - id: "fatality"
          name: "Fatality History"
          description: "Work-related fatality history"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "osha", endpoint: "fatalities/search"}
            - {type: "api", provider: "bsee", endpoint: "fatalities/search"}
            - {type: "news", provider: "gdelt", query: "{operator} fatality OR death"}
          score_range: [0, 100]
          scoring_logic:
            no_fatalities_10yr: 100
            no_fatalities_5yr: 90
            single_over_5yr_ago: 75
            single_recent: 50
            multiple_over_5yr: 40
            multiple_recent: 20
          critical: true
          score_condition: fatality_critical
          
        - id: "major_incident"
          name: "Major Incident History"
          description: "Explosions, blowouts, major spills"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "csb", endpoint: "incidents/search"}
            - {type: "api", provider: "nrc", endpoint: "reports/search"}
            - {type: "api", provider: "bsee", endpoint: "incidents/major"}
            - {type: "news", provider: "gdelt", query: "{operator} explosion OR blowout OR spill"}
          score_range: [0, 100]
          scoring_logic:
            no_major_10yr: 100
            no_major_5yr: 85
            minor_incident_only: 75
            major_over_5yr_ago: 50
            major_recent: 25
            multiple_major: 10
          critical: true
          score_condition: major_incident_critical
          
        - id: "near_miss"
          name: "Near-Miss Reporting"
          description: "Near-miss reporting culture (if disclosed)"
          weight: 0.05
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/safety", "/sustainability"]}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            active_reporting_disclosed: 100
            some_disclosure: 75
            minimal_disclosure: 50
            no_disclosure: 40
          critical: false
          score_condition: null

      environmental_compliance:
        - id: "epa_violation"
          name: "EPA Violations"
          description: "CAA, CWA, RCRA violations"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "epa_echo", endpoint: "violations/search"}
            - {type: "api", provider: "epa", endpoint: "enforcement/search"}
          score_range: [0, 100]
          scoring_logic:
            no_violations_5yr: 100
            minor_violations_resolved: 85
            moderate_violations: 60
            significant_violations: 40
            consent_decree: 25
            ongoing_enforcement: 15
          critical: true
          score_condition: epa_violation_critical
          
        - id: "spill_history"
          name: "Spill History"
          description: "Oil/chemical spill history from NRC and state records"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "nrc", endpoint: "reports/search"}
            - {type: "api", provider: "state_commissions", endpoint: "spills/search"}
            - {type: "api", provider: "epa", endpoint: "spills/search"}
          score_range: [0, 100]
          scoring_logic:
            no_reportable_5yr: 100
            minor_spills_only: 85
            moderate_spills: 65
            significant_spills: 45
            major_spill: 25
            multiple_major: 10
          critical: true
          score_condition: spill_history_critical
          
        - id: "emissions_compliance"
          name: "Air Emissions Compliance"
          description: "Air permit compliance and emissions"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "epa_echo", endpoint: "air/compliance"}
            - {type: "api", provider: "state_env_agencies", endpoint: "air/violations"}
          score_range: [0, 100]
          scoring_logic:
            full_compliance: 100
            minor_exceedances: 80
            moderate_issues: 60
            significant_violations: 40
            ongoing_noncompliance: 20
          critical: false
          score_condition: null
          
        - id: "flaring"
          name: "Flaring Intensity"
          description: "Flaring intensity from satellite data"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "satellite", provider: "viirs", analyzer: "flaring_detector"}
            - {type: "api", provider: "skytruth", endpoint: "flaring/operator"}
            - {type: "api", provider: "world_bank_ggfr", endpoint: "flaring/data"}
          score_range: [0, 100]
          scoring_logic:
            minimal_flaring: 100
            below_avg_basin: 85
            at_avg_basin: 70
            above_avg_basin: 50
            high_flaring: 30
            extreme_flaring: 15
          critical: false
          score_condition: null
          
        - id: "methane"
          name: "Methane Emissions"
          description: "Methane emissions from satellite and ground monitoring"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "satellite", provider: "ghgsat", analyzer: "methane_detector"}
            - {type: "satellite", provider: "sentinel5p", analyzer: "methane"}
            - {type: "api", provider: "epa", endpoint: "ghgrp/methane"}
          score_range: [0, 100]
          scoring_logic:
            best_in_class: 100
            below_peer_avg: 85
            at_peer_avg: 70
            above_peer_avg: 50
            high_emissions: 30
            super_emitter_events: 15
          critical: false
          score_condition: null
          
        - id: "remediation"
          name: "Remediation Obligations"
          description: "Environmental remediation obligations"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "epa", endpoint: "superfund/search"}
            - {type: "api", provider: "state_env_agencies", endpoint: "brownfields/search"}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            no_obligations: 100
            minor_funded: 85
            moderate_funded: 70
            significant_funded: 55
            significant_unfunded: 35
            superfund_liability: 20
          critical: false
          score_condition: null

      operational_telemetry:
        - id: "production_consistency"
          name: "Production Consistency"
          description: "Volatility in reported production"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "enverus", endpoint: "production/history"}
            - {type: "api", provider: "state_commissions", endpoint: "production/operator"}
          score_range: [0, 100]
          scoring_logic:
            highly_consistent: 100
            normal_variation: 80
            elevated_volatility: 60
            high_volatility: 40
            erratic: 25
          critical: false
          score_condition: null
          
        - id: "facility_activity"
          name: "Facility Activity Patterns"
          description: "Satellite-derived facility activity indicators"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "satellite", provider: "planet", analyzer: "activity_detector"}
            - {type: "satellite", provider: "sentinel2", analyzer: "change_detection"}
          score_range: [0, 100]
          scoring_logic:
            consistent_normal_activity: 100
            normal_variation: 80
            unusual_patterns: 55
            concerning_patterns: 35
          critical: false
          score_condition: null
          
        - id: "well_integrity"
          name: "Well Integrity Indicators"
          description: "Shut-in patterns, workovers, P&A activity"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "state_commissions", endpoint: "wells/status"}
            - {type: "api", provider: "enverus", endpoint: "wells/integrity"}
          score_range: [0, 100]
          scoring_logic:
            excellent_integrity: 100
            normal_operations: 80
            elevated_workovers: 60
            integrity_concerns: 40
            significant_issues: 25
          critical: false
          score_condition: null
          
        - id: "maintenance_pattern"
          name: "Maintenance Patterns"
          description: "Observable turnarounds and maintenance activity"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "news", provider: "gdelt", query: "{operator} turnaround OR maintenance"}
            - {type: "api", provider: "industry_intel", endpoint: "turnarounds"}
          score_range: [0, 100]
          scoring_logic:
            regular_scheduled: 100
            adequate_maintenance: 80
            deferred_maintenance: 55
            concerning_patterns: 35
          critical: false
          score_condition: null
          
        - id: "operational_efficiency"
          name: "Operational Efficiency"
          description: "Production per well, utilization metrics"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "enverus", endpoint: "production/efficiency"}
            - {type: "correlation", analyzer: "peer_efficiency_benchmark"}
          score_range: [0, 100]
          scoring_logic:
            top_quartile: 100
            above_median: 80
            at_median: 65
            below_median: 50
            bottom_quartile: 35
          critical: false
          score_condition: null

      financial_stability:
        - id: "credit_rating"
          name: "Credit Rating"
          description: "Corporate credit rating"
          weight: 0.25
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "sp_global", endpoint: "ratings"}
            - {type: "api", provider: "moodys", endpoint: "ratings"}
            - {type: "api", provider: "fitch", endpoint: "ratings"}
          score_range: [0, 100]
          scoring_logic:
            investment_grade: 100
            bb_range: 70
            b_range: 50
            ccc_below: 30
            not_rated_strong: 65
            not_rated_unknown: 45
          critical: false
          score_condition: null
          
        - id: "leverage"
          name: "Debt/Equity Leverage"
          description: "Leverage ratio vs peer benchmark"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K", "10-Q"]}
            - {type: "api", provider: "bloomberg", endpoint: "fundamentals"}
          score_range: [0, 100]
          scoring_logic:
            conservative_leverage: 100
            moderate_leverage: 80
            at_peer_avg: 65
            elevated_leverage: 45
            high_leverage: 25
          critical: false
          score_condition: null
          
        - id: "aro_coverage"
          name: "ARO Coverage"
          description: "Asset retirement obligation funding status"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
            - {type: "api", provider: "bsee", endpoint: "bonds/search"}
          score_range: [0, 100]
          scoring_logic:
            fully_bonded_funded: 100
            adequate_coverage: 80
            partial_coverage: 55
            underfunded: 35
            significantly_underfunded: 15
          critical: true
          score_condition: aro_coverage_critical
          
        - id: "capex_trend"
          name: "Capex Trends"
          description: "Maintenance vs growth capital trends"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K", "10-Q"]}
          score_range: [0, 100]
          scoring_logic:
            balanced_investment: 100
            growth_focused: 80
            maintenance_focused: 75
            declining_investment: 50
            severe_cuts: 30
          critical: false
          score_condition: null
          
        - id: "restructuring"
          name: "Bankruptcy/Restructuring History"
          description: "Bankruptcy or debt restructuring history"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "pacer", endpoint: "bankruptcy/search"}
            - {type: "filing", provider: "sec_edgar", document_types: ["8-K"]}
          score_range: [0, 100]
          scoring_logic:
            no_history: 100
            restructuring_over_10yr: 75
            restructuring_over_5yr: 55
            restructuring_recent: 30
            bankruptcy_recent: 15
          critical: true
          score_condition: restructuring_critical

      asset_portfolio:
        - id: "asset_age"
          name: "Asset Age Profile"
          description: "Weighted average asset age vs peers"
          weight: 0.25
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "enverus", endpoint: "assets/age"}
            - {type: "api", provider: "bsee", endpoint: "platforms/age"}
            - {type: "api", provider: "eia", endpoint: "refineries/age"}
          score_range: [0, 100]
          scoring_logic:
            modern_assets: 100
            below_peer_avg_age: 85
            at_peer_avg: 70
            above_peer_avg: 50
            aging_assets: 35
          critical: false
          score_condition: null
          
        - id: "concentration"
          name: "Geographic Concentration"
          description: "Geographic and asset concentration risk"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
            - {type: "api", provider: "enverus", endpoint: "assets/geography"}
          score_range: [0, 100]
          scoring_logic:
            well_diversified: 100
            moderately_diversified: 80
            some_concentration: 60
            high_concentration: 40
            single_asset_dependency: 20
          critical: false
          score_condition: null
          
        - id: "complexity"
          name: "Technology/Complexity Profile"
          description: "Operational complexity and technology risk"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "enverus", endpoint: "assets/profile"}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            conventional_low_complexity: 100
            moderate_complexity: 80
            high_complexity_managed: 60
            high_complexity_concerns: 40
            frontier_technology: 30
          critical: false
          score_condition: null
          
        - id: "decommissioning"
          name: "Decommissioning Obligations"
          description: "Decommissioning liability status"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "bsee", endpoint: "decommissioning/obligations"}
            - {type: "api", provider: "state_commissions", endpoint: "plugging/obligations"}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            minimal_obligations: 100
            moderate_well_funded: 80
            significant_funded: 65
            significant_partial: 45
            large_unfunded: 25
          critical: false
          score_condition: null
          
        - id: "permit_status"
          name: "Permit Status"
          description: "Operating permit status and compliance"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_commissions", endpoint: "permits/status"}
            - {type: "api", provider: "bsee", endpoint: "permits/status"}
            - {type: "api", provider: "epa", endpoint: "permits/status"}
          score_range: [0, 100]
          scoring_logic:
            all_active_current: 100
            minor_admin_issues: 85
            pending_renewals: 70
            expired_permits: 45
            permit_violations: 25
          critical: false
          score_condition: null

      corporate_footprint:
        - id: "safety_communication"
          name: "Safety Culture Communication"
          description: "Observable safety culture and communication"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/safety", "/hse", "/sustainability"]}
            - {type: "filing", provider: "sec_edgar", document_types: ["10-K"]}
          score_range: [0, 100]
          scoring_logic:
            comprehensive_disclosure: 100
            good_disclosure: 80
            basic_disclosure: 60
            minimal_disclosure: 40
            no_disclosure: 25
          critical: false
          score_condition: null
          
        - id: "esg_reporting"
          name: "ESG/Sustainability Reporting"
          description: "Quality of ESG and sustainability reporting"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/sustainability", "/esg"]}
            - {type: "api", provider: "cdp", endpoint: "responses/search"}
            - {type: "api", provider: "sasb", endpoint: "disclosures"}
          score_range: [0, 100]
          scoring_logic:
            comprehensive_sasb_tcfd: 100
            good_reporting: 80
            basic_report: 60
            website_only: 40
            none: 20
          critical: false
          score_condition: null
          
        - id: "technical_hiring"
          name: "Technical/HSE Hiring"
          description: "HSE and engineering hiring signals"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "linkedin", endpoint: "jobs/search"}
            - {type: "scrape", target: "job_boards"}
          score_range: [0, 100]
          scoring_logic:
            active_hse_hiring: 100
            steady_technical: 80
            minimal: 55
            cutbacks: 35
          critical: false
          score_condition: null
          
        - id: "industry_presence"
          name: "Industry Conference Presence"
          description: "Presence at industry conferences"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "conference_websites"}
            - {type: "news", provider: "gdelt", query: "{operator} conference OR presentation"}
          score_range: [0, 100]
          scoring_logic:
            active_presenter: 100
            regular_attendee: 75
            occasional: 55
            minimal: 35
          critical: false
          score_condition: null
          
        - id: "disclosure_quality"
          name: "Transparency/Disclosure Quality"
          description: "Overall transparency and disclosure quality"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "filing", provider: "sec_edgar", analyzer: "disclosure_quality_scorer"}
            - {type: "scrape", target: "company_website"}
          score_range: [0, 100]
          scoring_logic:
            exemplary: 100
            good: 80
            adequate: 60
            minimal: 40
            opaque: 20
          critical: false
          score_condition: null
          
        - id: "hse_leadership"
          name: "HSE Leadership Visibility"
          description: "HSE leadership profiles and visibility"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/leadership", "/about"]}
            - {type: "api", provider: "linkedin", endpoint: "people/search"}
          score_range: [0, 100]
          scoring_logic:
            c_suite_hse: 100
            dedicated_vp_hse: 85
            senior_hse_role: 70
            hse_function_exists: 50
            unclear: 30
          critical: false
          score_condition: null

      structured_data:
        - id: "esg_rating"
          name: "ESG Rating"
          description: "Third-party ESG ratings"
          weight: 0.40
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "msci", endpoint: "esg/ratings"}
            - {type: "api", provider: "sustainalytics", endpoint: "ratings"}
            - {type: "api", provider: "sp_global", endpoint: "esg/scores"}
          score_range: [0, 100]
          scoring_logic:
            leader: 100
            above_avg: 80
            average: 60
            below_avg: 40
            laggard: 20
          critical: false
          score_condition: null
          
        - id: "benchmark"
          name: "Industry Benchmark Data"
          description: "Performance vs industry benchmarks"
          weight: 0.35
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "iogp", endpoint: "safety/benchmarks"}
            - {type: "api", provider: "api", endpoint: "industry/benchmarks"}
          score_range: [0, 100]
          scoring_logic:
            top_quartile: 100
            above_median: 80
            at_median: 60
            below_median: 40
            bottom_quartile: 20
          critical: false
          score_condition: null
          
        - id: "credit"
          name: "Credit Rating (Structured)"
          description: "Credit rating from structured feed"
          weight: 0.25
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
            not_rated: 50
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
        base_rate: 0.0008  # 0.08% of TIV
        
      tier_2:
        id: 2
        label: "STANDARD"
        min_score: 650
        max_score: 799
        description: "Good operator - auto-approve at standard pricing"
        auto_approve: true
        auto_decline: false
        base_rate: 0.0012  # 0.12% of TIV
        
      tier_3:
        id: 3
        label: "ELEVATED"
        min_score: 500
        max_score: 649
        description: "Moderate risk - auto-approve with conditions"
        auto_approve: false
        auto_decline: false
        base_rate: 0.0018  # 0.18% of TIV
        
      tier_4:
        id: 4
        label: "HIGH_RISK"
        min_score: 350
        max_score: 499
        description: "High risk - manual review with loading"
        auto_approve: false
        auto_decline: false
        base_rate: 0.0028  # 0.28% of TIV
        
      tier_5:
        id: 5
        label: "CRITICAL"
        min_score: 0
        max_score: 349
        description: "Critical risk - decline or senior review"
        auto_approve: false
        auto_decline: true
        base_rate: 0.0045  # 0.45% of TIV

    # -------------------------------------------------------------------------
    # CONDITION DEFINITIONS
    # -------------------------------------------------------------------------
    direct_conditions:
      - id: major_incidents_true
        bands:
          - {return: true, tier_override: 4, action: "REFER", note: "Major incidents disclosed"}
      
      - id: fatalities_true
        bands:
          - {return: true, tier_override: 3, action: "REFER", note: "Fatalities disclosed"}
      
      - id: regulatory_enforcement_true
        bands:
          - {return: true, tier_override: null, action: "REFER", note: "Pending regulatory enforcement"}
      
      - id: decommissioning_obligations_true
        bands:
          - {return: true, tier_override: null, action: "FLAG", note: "Unfunded decommissioning obligations"}
      
      - id: jv_operator_info
        bands:
          - {return: true, tier_override: null, action: "INFO", note: "JV operator status"}
      
      - id: contractor_info
        bands:
          - {return: true, tier_override: null, action: "INFO", note: "Third-party contractor usage"}
  
    score_conditions:
      - id: safety_performance_critical
        bands:
          - {max: 30, tier_override: 5, action: "DECLINE", note: "Critical safety performance"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant safety concerns"}
        inclusive_max: false
      
      - id: environmental_compliance_critical
        bands:
          - {max: 30, tier_override: 5, action: "DECLINE", note: "Critical environmental violations"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant environmental concerns"}
        inclusive_max: false
      
      - id: osha_trir_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "TRIR significantly above benchmark"}
        inclusive_max: false
      
      - id: osha_violations_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Willful/repeat OSHA violations"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Serious OSHA violation history"}
        inclusive_max: false
      
      - id: bsee_incident_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Significant BSEE incident history"}
        inclusive_max: false
      
      - id: process_safety_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Major process safety events"}
          - {max: 40, tier_override: 4, action: "REFER", note: "Process safety concerns"}
        inclusive_max: false
      
      - id: fatality_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Fatality history concerns"}
        inclusive_max: false
      
      - id: major_incident_critical
        bands:
          - {max: 20, tier_override: 5, action: "DECLINE", note: "Major incident history"}
          - {max: 40, tier_override: 4, action: "REFER", note: "Incident history concerns"}
        inclusive_max: false
      
      - id: epa_violation_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Ongoing EPA enforcement"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant EPA violations"}
        inclusive_max: false
      
      - id: spill_history_critical
        bands:
          - {max: 20, tier_override: 5, action: "DECLINE", note: "Major spill history"}
          - {max: 40, tier_override: 4, action: "REFER", note: "Spill history concerns"}
        inclusive_max: false
      
      - id: financial_stability_critical
        bands:
          - {max: 35, tier_override: 4, action: "REFER", note: "Financial stability concerns"}
        inclusive_max: false
      
      - id: aro_coverage_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "ARO underfunding concerns"}
        inclusive_max: false
      
      - id: restructuring_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Recent bankruptcy"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Restructuring history"}
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
        minimum: 250000
        maximum: 10000000
      
      experience_modifiers:
        excellent_5yr: 0.85
        good_5yr: 0.90
        clean_3yr: 0.95
        minor_losses: 1.00
        moderate_losses: 1.20
        significant_losses: 1.40
        major_losses: 1.75
        
      nat_cat_loadings:
        gulf_hurricane: 1.15
        earthquake_zone: 1.10
        flood_zone: 1.05
        
      taxes_fees_rate: 0.05

    # -------------------------------------------------------------------------
    # TEST PROFILES
    # -------------------------------------------------------------------------
    test_profiles:
      excellent_major:
        description: "Major integrated operator with excellent safety record"
        expected_tier: [1, 2]
        expected_score_range: [780, 950]
        operator_type: "MAJOR_INTEGRATED"
        operation_segment: "MIXED"
        geographic_focus: "GLOBAL_DIVERSIFIED"
        signals:
          network_authority:
            partner_quality: 90
            contractor_quality: 88
            banking_relationship: 92
            insurance_history: 85
            industry_association: 90
            regulator_relationship: 85
            customer_quality: 88
          safety_performance:
            osha_trir: 88
            osha_violations: 92
            bsee_incident: 85
            process_safety: 90
            fatality: 95
            major_incident: 92
            near_miss: 80
          environmental_compliance:
            epa_violation: 88
            spill_history: 85
            emissions_compliance: 82
            flaring: 78
            methane: 80
            remediation: 85
          operational_telemetry:
            production_consistency: 88
            facility_activity: 85
            well_integrity: 90
            maintenance_pattern: 85
            operational_efficiency: 82
          financial_stability:
            credit_rating: 88
            leverage: 82
            aro_coverage: 90
            capex_trend: 85
            restructuring: 100
          asset_portfolio:
            asset_age: 80
            concentration: 85
            complexity: 75
            decommissioning: 82
            permit_status: 95
          corporate_footprint:
            safety_communication: 88
            esg_reporting: 85
            technical_hiring: 82
            industry_presence: 90
            disclosure_quality: 85
            hse_leadership: 88
          structured_data:
            esg_rating: 82
            benchmark: 85
            credit: 88

      average_independent:
        description: "Mid-size independent with typical profile"
        expected_tier: [2, 3]
        expected_score_range: [550, 720]
        operator_type: "MID_INDEPENDENT"
        operation_segment: "UPSTREAM_UNCONVENTIONAL"
        geographic_focus: "US_ONSHORE"
        signals:
          network_authority:
            partner_quality: 70
            contractor_quality: 72
            banking_relationship: 68
            insurance_history: 70
            industry_association: 65
            regulator_relationship: 72
            customer_quality: 70
          safety_performance:
            osha_trir: 70
            osha_violations: 78
            process_safety: 72
            fatality: 90
            major_incident: 88
            near_miss: 60
          environmental_compliance:
            epa_violation: 75
            spill_history: 72
            emissions_compliance: 68
            flaring: 65
            methane: 62
            remediation: 70
          operational_telemetry:
            production_consistency: 75
            facility_activity: 70
            well_integrity: 72
            maintenance_pattern: 68
            operational_efficiency: 70
          financial_stability:
            credit_rating: 65
            leverage: 60
            aro_coverage: 70
            capex_trend: 68
            restructuring: 100
          asset_portfolio:
            asset_age: 65
            concentration: 55
            complexity: 80
            decommissioning: 70
            permit_status: 85
          corporate_footprint:
            safety_communication: 65
            esg_reporting: 55
            technical_hiring: 60
            industry_presence: 55
            disclosure_quality: 60
            hse_leadership: 58
          structured_data:
            esg_rating: 55
            benchmark: 65
            credit: 65

      high_risk_small:
        description: "Small independent with safety concerns"
        expected_tier: [4, 5]
        expected_score_range: [250, 450]
        operator_type: "SMALL_INDEPENDENT"
        operation_segment: "UPSTREAM_CONVENTIONAL"
        geographic_focus: "US_ONSHORE"
        signals:
          network_authority:
            partner_quality: 40
            contractor_quality: 45
            banking_relationship: 35
            insurance_history: 40
            industry_association: 30
            regulator_relationship: 38
            customer_quality: 45
          safety_performance:
            osha_trir: 35
            osha_violations: 40
            process_safety: 42
            fatality: 55
            major_incident: 50
            near_miss: 35
          environmental_compliance:
            epa_violation: 45
            spill_history: 40
            emissions_compliance: 42
            flaring: 35
            methane: 38
            remediation: 45
          operational_telemetry:
            production_consistency: 50
            facility_activity: 45
            well_integrity: 42
            maintenance_pattern: 40
            operational_efficiency: 45
          financial_stability:
            credit_rating: 35
            leverage: 30
            aro_coverage: 40
            capex_trend: 35
            restructuring: 60
          asset_portfolio:
            asset_age: 40
            concentration: 35
            complexity: 70
            decommissioning: 35
            permit_status: 55
          corporate_footprint:
            safety_communication: 35
            esg_reporting: 25
            technical_hiring: 30
            industry_presence: 25
            disclosure_quality: 35
            hse_leadership: 30
          structured_data:
            esg_rating: 30
            benchmark: 35
            credit: 35

      offshore_operator:
        description: "Offshore operator in Gulf of Mexico"
        expected_tier: [2, 3]
        expected_score_range: [580, 750]
        operator_type: "LARGE_INDEPENDENT"
        operation_segment: "UPSTREAM_OFFSHORE"
        geographic_focus: "US_GULF_SHELF"
        signals:
          network_authority:
            partner_quality: 80
            contractor_quality: 82
            banking_relationship: 78
            insurance_history: 75
            industry_association: 78
            regulator_relationship: 80
            customer_quality: 78
          safety_performance:
            osha_trir: 78
            osha_violations: 85
            bsee_incident: 75
            process_safety: 80
            fatality: 92
            major_incident: 85
            near_miss: 70
          environmental_compliance:
            epa_violation: 82
            spill_history: 75
            emissions_compliance: 78
            flaring: 72
            methane: 70
            remediation: 78
          operational_telemetry:
            production_consistency: 80
            facility_activity: 75
            well_integrity: 82
            maintenance_pattern: 78
            operational_efficiency: 75
          financial_stability:
            credit_rating: 75
            leverage: 70
            aro_coverage: 78
            capex_trend: 75
            restructuring: 100
          asset_portfolio:
            asset_age: 65
            concentration: 60
            complexity: 55
            decommissioning: 70
            permit_status: 90
          corporate_footprint:
            safety_communication: 78
            esg_reporting: 72
            technical_hiring: 75
            industry_presence: 72
            disclosure_quality: 75
            hse_leadership: 78
          structured_data:
            esg_rating: 70
            benchmark: 75
            credit: 75

      pe_backed:
        description: "Private equity backed operator"
        expected_tier: [3, 4]
        expected_score_range: [450, 620]
        operator_type: "PRIVATE_EQUITY"
        operation_segment: "UPSTREAM_UNCONVENTIONAL"
        geographic_focus: "US_ONSHORE"
        signal_coverage: 0.65
        signals:
          network_authority:
            partner_quality: 60
            contractor_quality: 65
            banking_relationship: 55
            insurance_history: 58
            industry_association: 45
          safety_performance:
            osha_trir: 62
            osha_violations: 70
            process_safety: 65
            fatality: 85
            major_incident: 80
          environmental_compliance:
            epa_violation: 65
            spill_history: 60
            emissions_compliance: 58
            flaring: 52
            methane: 50
          financial_stability:
            credit_rating: 50
            leverage: 40
            aro_coverage: 55
            capex_trend: 60
            restructuring: 75
          asset_portfolio:
            asset_age: 55
            concentration: 50
            complexity: 75
            decommissioning: 50
            permit_status: 80
          corporate_footprint:
            safety_communication: 50
            esg_reporting: 40
            technical_hiring: 55
            hse_leadership: 45

      refinery_operator:
        description: "Major refinery operator"
        expected_tier: [2, 3]
        expected_score_range: [580, 750]
        operator_type: "DOWNSTREAM_MAJOR"
        operation_segment: "DOWNSTREAM_REFINING"
        geographic_focus: "US_ONSHORE"
        signals:
          network_authority:
            partner_quality: 75
            contractor_quality: 80
            banking_relationship: 82
            insurance_history: 78
            industry_association: 82
            regulator_relationship: 75
            customer_quality: 85
          safety_performance:
            osha_trir: 75
            osha_violations: 82
            process_safety: 78
            fatality: 90
            major_incident: 82
            near_miss: 75
          environmental_compliance:
            epa_violation: 72
            spill_history: 78
            emissions_compliance: 70
            flaring: 80
            methane: 75
            remediation: 72
          operational_telemetry:
            production_consistency: 82
            facility_activity: 80
            maintenance_pattern: 78
            operational_efficiency: 75
          financial_stability:
            credit_rating: 80
            leverage: 75
            aro_coverage: 85
            capex_trend: 78
            restructuring: 100
          asset_portfolio:
            asset_age: 55
            concentration: 65
            complexity: 50
            decommissioning: 75
            permit_status: 88
          corporate_footprint:
            safety_communication: 75
            esg_reporting: 70
            technical_hiring: 72
            industry_presence: 78
            disclosure_quality: 75
            hse_leadership: 75
          structured_data:
            esg_rating: 68
            benchmark: 72
            credit: 80

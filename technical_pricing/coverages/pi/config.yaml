# =============================================================================
# DSI Model Configuration - Professional Indemnity Insurance
# =============================================================================
#
# This file defines the complete configuration for Professional Indemnity coverage.
# It is the single source of truth for:
#   - Model structure and parameters
#   - Signal definitions and weights (profession-specific)
#   - Pricing factors and thresholds
#   - Practice area risk modifiers
#   - Test profiles for actuarial validation
#
# Premium calculation follows DSI Foundational Principle 9: Signal -> Score -> Tier -> Price
#
# DSI PRINCIPLES APPLIED:
#   1. All signals must be externally observable (licensing boards, court records, ratings)
#   2. Direct queries are OPTIONAL - model works without them
#   3. Categorical features are inferred from regulatory registrations
#   4. Tier determines base premium; modifiers adjust for exposure characteristics
#   5. PI is suited to DSI due to extensive regulatory/licensing disclosure
#
# KEY DATA SOURCES:
#   - State bar associations (law firms)
#   - AICPA peer review database (accounting)
#   - State licensing boards (all professions)
#   - PACER and state court records
#   - Chambers, Legal 500, Best Lawyers rankings
#   - PCAOB registration (accounting)
#   - Professional association directories
#
# Version: 2.0.0
# Last Updated: 2025-12
# =============================================================================

professional_indemnity:
  pi_general:
    metadata:
      name: "DSI Professional Indemnity Insurance Model"
      description: "PI/E&O coverage based on observable regulatory, practice quality, and stability signals"
      version: "2.0.0"
      coverage_types:
        - "professional_liability"
        - "errors_omissions"
        - "malpractice"
      applicable_professions:
        - "law_firm"
        - "accounting_firm"
        - "architecture"
        - "engineering"
        - "management_consulting"
        - "it_consulting"
        - "real_estate"
        - "insurance_broker"
        - "financial_planning"
        - "healthcare_admin"
        - "appraisal_valuation"
        - "environmental_consulting"
      applicable_markets: ["us", "uk", "eu", "apac"]
      min_premium: 2500
      default_currency: "USD"

    # -------------------------------------------------------------------------
    # DIRECT OPTIONAL QUERIES
    # -------------------------------------------------------------------------
    direct_optional_queries:
      - id: "pending_claims"
        question: "Any pending or threatened malpractice claims?"
        direct_condition: pending_claims_true
        
      - id: "disciplinary_pending"
        question: "Any pending disciplinary proceedings against any professional?"
        direct_condition: disciplinary_pending_true
        
      - id: "coverage_declined"
        question: "Has any PI coverage been declined or non-renewed in past 3 years?"
        direct_condition: coverage_declined_true
        
      - id: "practice_area_change"
        question: "Any significant change in practice areas in past 2 years?"
        direct_condition: practice_area_change_true
        
      - id: "merger_activity"
        question: "Any merger, acquisition, or spin-off in past 2 years?"
        direct_condition: merger_activity_true
        
      - id: "major_client_loss"
        question: "Loss of client representing >25% of revenue in past year?"
        direct_condition: major_client_loss_true

    # -------------------------------------------------------------------------
    # CATEGORICAL FEATURES
    # -------------------------------------------------------------------------
    categorical_features:
      profession_type:
        description: "Primary professional classification"
        inference_method:
          primary: "license_type_lookup"
          fallback: "website_nlp_classification"
          sources:
            - {type: "api", provider: "state_licensing_boards", endpoint: "license/search"}
            - {type: "api", provider: "bar_associations", endpoint: "attorney/search"}
            - {type: "api", provider: "aicpa", endpoint: "member/search"}
            - {type: "api", provider: "ncarb", endpoint: "certificate/search"}
            - {type: "api", provider: "ncees", endpoint: "pe/search"}
            - {type: "scrape", target: "company_website", analyzer: "profession_classifier"}
          confidence_threshold: 0.90
          default_on_failure: "OTHER"
        values:
          - id: "LAW_FIRM"
            label: "Law Firm"
            base_rate: 8500
            description: "Law firms of all sizes and practice areas"
            inference_criteria: {bar_license: true}
            
          - id: "ACCOUNTING_FIRM"
            label: "Accounting Firm"
            base_rate: 9000
            description: "CPA firms - audit, tax, advisory"
            inference_criteria: {cpa_license: true}
            
          - id: "ARCHITECTURE"
            label: "Architecture"
            base_rate: 7500
            description: "Licensed architects"
            inference_criteria: {architecture_license: true}
            
          - id: "ENGINEERING"
            label: "Engineering"
            base_rate: 8000
            description: "Licensed professional engineers"
            inference_criteria: {pe_license: true}
            
          - id: "MANAGEMENT_CONSULTING"
            label: "Management Consulting"
            base_rate: 6000
            description: "Strategy, operations, organizational consulting"
            inference_criteria: {consulting_practice: true, management_focus: true}
            
          - id: "IT_CONSULTING"
            label: "IT Consulting"
            base_rate: 7000
            description: "Technology consulting and implementation"
            inference_criteria: {consulting_practice: true, it_focus: true}
            
          - id: "HR_CONSULTING"
            label: "HR Consulting"
            base_rate: 5500
            description: "Human resources and benefits consulting"
            inference_criteria: {consulting_practice: true, hr_focus: true}
            
          - id: "REAL_ESTATE"
            label: "Real Estate"
            base_rate: 5500
            description: "Real estate agents, brokers, property managers"
            inference_criteria: {real_estate_license: true}
            
          - id: "INSURANCE_BROKER"
            label: "Insurance Broker"
            base_rate: 6500
            description: "Insurance agents and brokers"
            inference_criteria: {insurance_license: true}
            
          - id: "FINANCIAL_PLANNING"
            label: "Financial Planning"
            base_rate: 7500
            description: "Financial planners and advisers (non-SEC)"
            inference_criteria: {cfp_designation: true}
            
          - id: "HEALTHCARE_ADMIN"
            label: "Healthcare Administration"
            base_rate: 6000
            description: "Healthcare management and administration"
            inference_criteria: {healthcare_admin: true}
            
          - id: "APPRAISAL_VALUATION"
            label: "Appraisal/Valuation"
            base_rate: 6500
            description: "Real estate appraisers, business valuators"
            inference_criteria: {appraisal_license: true}
            
          - id: "ENVIRONMENTAL_CONSULTING"
            label: "Environmental Consulting"
            base_rate: 7000
            description: "Environmental assessment and remediation"
            inference_criteria: {environmental_practice: true}
            
          - id: "OTHER"
            label: "Other Professional"
            base_rate: 6000
            description: "Other professional services"
            inference_criteria: {}

      firm_size:
        description: "Firm size by professional headcount"
        inference_method:
          primary: "linkedin_employee_count"
          fallback: "website_team_analysis"
          sources:
            - {type: "api", provider: "linkedin", endpoint: "company/employees"}
            - {type: "api", provider: "dnb", endpoint: "company/employees"}
            - {type: "scrape", target: "company_website", pages: ["/team", "/attorneys", "/people", "/about"]}
          confidence_threshold: 0.80
          default_on_failure: "SMALL"
        values:
          - id: "SOLO"
            label: "Solo Practitioner"
            modifier: 1.20
            headcount_range: [1, 1]
            description: "Single professional practice"
            
          - id: "MICRO"
            label: "Micro Firm"
            modifier: 1.10
            headcount_range: [2, 5]
            description: "2-5 professionals"
            
          - id: "SMALL"
            label: "Small Firm"
            modifier: 1.00
            headcount_range: [6, 20]
            description: "6-20 professionals"
            
          - id: "MEDIUM"
            label: "Medium Firm"
            modifier: 0.95
            headcount_range: [21, 100]
            description: "21-100 professionals"
            
          - id: "LARGE"
            label: "Large Firm"
            modifier: 0.90
            headcount_range: [101, 500]
            description: "101-500 professionals"
            
          - id: "MAJOR"
            label: "Major Firm"
            modifier: 0.85
            headcount_range: [501, 999999]
            description: "500+ professionals"

      revenue_size:
        description: "Annual revenue classification"
        inference_method:
          primary: "financial_database_lookup"
          fallback: "headcount_revenue_estimate"
          sources:
            - {type: "api", provider: "dnb", endpoint: "company/financials"}
            - {type: "api", provider: "pitchbook", endpoint: "company/financials"}
            - {type: "correlation", analyzer: "headcount_to_revenue", inputs: ["headcount", "profession"]}
          confidence_threshold: 0.70
          default_on_failure: "R_1M_5M"
        values:
          - id: "UNDER_500K"
            label: "Under $500K"
            modifier: 0.85
            revenue_range: [0, 500000]
            
          - id: "R_500K_1M"
            label: "$500K - $1M"
            modifier: 0.90
            revenue_range: [500000, 1000000]
            
          - id: "R_1M_5M"
            label: "$1M - $5M"
            modifier: 1.00
            revenue_range: [1000000, 5000000]
            
          - id: "R_5M_25M"
            label: "$5M - $25M"
            modifier: 1.10
            revenue_range: [5000000, 25000000]
            
          - id: "R_25M_100M"
            label: "$25M - $100M"
            modifier: 1.25
            revenue_range: [25000000, 100000000]
            
          - id: "R_100M_500M"
            label: "$100M - $500M"
            modifier: 1.40
            revenue_range: [100000000, 500000000]
            
          - id: "OVER_500M"
            label: "Over $500M"
            modifier: 1.60
            revenue_range: [500000000, 999999999999]

    # -------------------------------------------------------------------------
    # PRACTICE AREA MODIFIERS (PROFESSION-SPECIFIC)
    # -------------------------------------------------------------------------
    practice_area_modifiers:
      law_firm:
        - {id: "SECURITIES", label: "Securities Law", modifier: 1.40}
        - {id: "CORPORATE_MA", label: "Corporate M&A", modifier: 1.25}
        - {id: "TRUSTS_ESTATES", label: "Trusts & Estates", modifier: 1.20}
        - {id: "ENVIRONMENTAL", label: "Environmental Law", modifier: 1.20}
        - {id: "TAX", label: "Tax Law", modifier: 1.15}
        - {id: "BANKRUPTCY", label: "Bankruptcy", modifier: 1.15}
        - {id: "HEALTHCARE", label: "Healthcare Law", modifier: 1.15}
        - {id: "INTELLECTUAL_PROPERTY", label: "Intellectual Property", modifier: 1.15}
        - {id: "LITIGATION_PLAINTIFF", label: "Plaintiff Litigation", modifier: 1.15}
        - {id: "PERSONAL_INJURY_PLAINTIFF", label: "PI Plaintiff", modifier: 1.30}
        - {id: "REAL_ESTATE", label: "Real Estate Law", modifier: 1.10}
        - {id: "EMPLOYMENT", label: "Employment Law", modifier: 1.10}
        - {id: "INSURANCE_COVERAGE", label: "Insurance Coverage", modifier: 1.05}
        - {id: "GENERAL_PRACTICE", label: "General Practice", modifier: 1.05}
        - {id: "LITIGATION_GENERAL", label: "General Litigation", modifier: 1.00}
        - {id: "PERSONAL_INJURY_DEFENSE", label: "PI Defense", modifier: 0.95}
        - {id: "FAMILY", label: "Family Law", modifier: 0.90}
        - {id: "CRIMINAL", label: "Criminal Defense", modifier: 0.85}
        
      accounting_firm:
        - {id: "AUDIT_PUBLIC", label: "Public Company Audit", modifier: 1.50}
        - {id: "ADVISORY_VALUATION", label: "Valuation Advisory", modifier: 1.35}
        - {id: "ADVISORY_MA", label: "M&A Advisory", modifier: 1.30}
        - {id: "FORENSIC", label: "Forensic Accounting", modifier: 1.25}
        - {id: "AUDIT_PRIVATE", label: "Private Company Audit", modifier: 1.25}
        - {id: "TAX_ESTATE", label: "Estate Tax", modifier: 1.20}
        - {id: "TAX_CORPORATE", label: "Corporate Tax", modifier: 1.10}
        - {id: "GENERAL_PRACTICE", label: "General Practice", modifier: 1.00}
        - {id: "TAX_INDIVIDUAL", label: "Individual Tax", modifier: 0.90}
        - {id: "BOOKKEEPING", label: "Bookkeeping", modifier: 0.80}
        
      architecture:
        - {id: "STRUCTURAL", label: "Structural Design", modifier: 1.35}
        - {id: "HEALTHCARE_FACILITIES", label: "Healthcare Facilities", modifier: 1.25}
        - {id: "HIGH_RISE", label: "High-Rise Construction", modifier: 1.20}
        - {id: "COMMERCIAL", label: "Commercial", modifier: 1.10}
        - {id: "INSTITUTIONAL", label: "Institutional", modifier: 1.05}
        - {id: "RESIDENTIAL_MULTI", label: "Multi-Family Residential", modifier: 1.00}
        - {id: "RESIDENTIAL_SINGLE", label: "Single-Family Residential", modifier: 0.90}
        - {id: "INTERIOR_DESIGN", label: "Interior Design", modifier: 0.85}
        
      engineering:
        - {id: "STRUCTURAL", label: "Structural Engineering", modifier: 1.40}
        - {id: "GEOTECHNICAL", label: "Geotechnical Engineering", modifier: 1.35}
        - {id: "ENVIRONMENTAL", label: "Environmental Engineering", modifier: 1.25}
        - {id: "CIVIL", label: "Civil Engineering", modifier: 1.15}
        - {id: "MECHANICAL", label: "Mechanical Engineering", modifier: 1.10}
        - {id: "ELECTRICAL", label: "Electrical Engineering", modifier: 1.05}
        - {id: "SURVEYING", label: "Surveying", modifier: 1.00}
        - {id: "CONSULTING", label: "Consulting Only", modifier: 0.90}

    # -------------------------------------------------------------------------
    # PROFESSION-SPECIFIC SIGNAL WEIGHTS
    # -------------------------------------------------------------------------
    profession_weights:
      law_firm:
        network_authority: 0.20
        regulatory_standing: 0.25
        firm_stability: 0.15
        practice_quality: 0.15
        technical_infrastructure: 0.05
        corporate_footprint: 0.10
        litigation_history: 0.10
        
      accounting_firm:
        network_authority: 0.15
        regulatory_standing: 0.30  # Peer review critical
        firm_stability: 0.15
        practice_quality: 0.15
        technical_infrastructure: 0.05
        corporate_footprint: 0.10
        litigation_history: 0.10
        
      architecture:
        network_authority: 0.15
        regulatory_standing: 0.20
        firm_stability: 0.15
        practice_quality: 0.20  # Project outcomes critical
        technical_infrastructure: 0.05
        corporate_footprint: 0.10
        litigation_history: 0.15  # Construction defects common
        
      engineering:
        network_authority: 0.15
        regulatory_standing: 0.25  # PE license critical
        firm_stability: 0.15
        practice_quality: 0.20
        technical_infrastructure: 0.05
        corporate_footprint: 0.05
        litigation_history: 0.15
        
      management_consulting:
        network_authority: 0.25  # Reputation-driven
        regulatory_standing: 0.10  # Less regulated
        firm_stability: 0.15
        practice_quality: 0.20
        technical_infrastructure: 0.10
        corporate_footprint: 0.15
        litigation_history: 0.05
        
      it_consulting:
        network_authority: 0.15
        regulatory_standing: 0.10
        firm_stability: 0.15
        practice_quality: 0.20
        technical_infrastructure: 0.20  # Core competency
        corporate_footprint: 0.10
        litigation_history: 0.10
        
      real_estate:
        network_authority: 0.15
        regulatory_standing: 0.25  # License critical
        firm_stability: 0.15
        practice_quality: 0.15
        technical_infrastructure: 0.05
        corporate_footprint: 0.10
        litigation_history: 0.15
        
      insurance_broker:
        network_authority: 0.20
        regulatory_standing: 0.25
        firm_stability: 0.15
        practice_quality: 0.15
        technical_infrastructure: 0.10
        corporate_footprint: 0.05
        litigation_history: 0.10
        
      financial_planning:
        network_authority: 0.15
        regulatory_standing: 0.30  # Regulatory critical
        firm_stability: 0.15
        practice_quality: 0.15
        technical_infrastructure: 0.10
        corporate_footprint: 0.05
        litigation_history: 0.10
        
      default:
        network_authority: 0.15
        regulatory_standing: 0.25
        firm_stability: 0.15
        practice_quality: 0.15
        technical_infrastructure: 0.10
        corporate_footprint: 0.10
        litigation_history: 0.10

    # -------------------------------------------------------------------------
    # SIGNAL GROUPS
    # -------------------------------------------------------------------------
    signal_groups:
      - id: "network_authority"
        name: "Network Authority"
        description: "Peer recognition, client quality, professional relationships"
        weight: 0.15  # Default, overridden by profession_weights
        test_scores: {excellent: 85, average: 65, poor: 35}
        critical: false
        score_condition: null
        
      - id: "regulatory_standing"
        name: "Regulatory Standing"
        description: "License status, disciplinary history, certifications"
        weight: 0.25
        test_scores: {excellent: 95, average: 75, poor: 35}
        critical: true
        score_condition: regulatory_standing_critical
        
      - id: "firm_stability"
        name: "Firm Stability"
        description: "Tenure, partner retention, financial health"
        weight: 0.15
        test_scores: {excellent: 88, average: 68, poor: 38}
        critical: false
        score_condition: firm_stability_critical
        
      - id: "practice_quality"
        name: "Practice Quality"
        description: "Client reviews, outcomes, complaint history"
        weight: 0.15
        test_scores: {excellent: 90, average: 70, poor: 35}
        critical: false
        score_condition: null
        
      - id: "technical_infrastructure"
        name: "Technical Infrastructure"
        description: "Digital security posture for client confidentiality"
        weight: 0.10
        test_scores: {excellent: 88, average: 65, poor: 40}
        critical: false
        score_condition: null
        
      - id: "corporate_footprint"
        name: "Corporate Footprint"
        description: "Website quality, thought leadership, transparency"
        weight: 0.10
        test_scores: {excellent: 82, average: 60, poor: 35}
        critical: false
        score_condition: null
        
      - id: "litigation_history"
        name: "Litigation History"
        description: "Malpractice suits, fee disputes, regulatory enforcement"
        weight: 0.10
        test_scores: {excellent: 95, average: 78, poor: 35}
        critical: true
        score_condition: litigation_history_critical

    # -------------------------------------------------------------------------
    # SIGNAL FEATURES
    # -------------------------------------------------------------------------
    signal_features:
      network_authority:
        - id: "peer_ranking"
          name: "Peer Rankings"
          description: "Recognition in Chambers, Legal 500, Best Lawyers, etc."
          weight: 0.25
          ttl: "static"
          ttl_seconds: 7776000
          sources:
            - {type: "api", provider: "chambers", endpoint: "rankings/search"}
            - {type: "api", provider: "legal500", endpoint: "rankings/search"}
            - {type: "api", provider: "bestlawyers", endpoint: "search"}
            - {type: "api", provider: "martindale", endpoint: "ratings/search"}
            - {type: "api", provider: "superlawyers", endpoint: "search"}
          score_range: [0, 100]
          scoring_logic:
            band_1_chambers: 100
            band_2_chambers: 90
            band_3_chambers: 80
            ranked_any_tier: 70
            recognized_not_ranked: 55
            not_ranked: 40
          critical: false
          score_condition: null
          
        - id: "client_quality"
          name: "Client Quality"
          description: "Quality of client base (public companies, Fortune 500)"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/clients", "/experience", "/representative-matters"]}
            - {type: "api", provider: "pacer", endpoint: "cases/search"}
            - {type: "api", provider: "sec_edgar", endpoint: "filings/counsel"}
          score_range: [0, 100]
          scoring_logic:
            fortune_500_clients: 100
            public_company_clients: 85
            institutional_clients: 75
            mid_market_clients: 65
            small_business_clients: 50
            individual_clients: 40
          critical: false
          score_condition: null
          
        - id: "referral_network"
          name: "Referral Network Quality"
          description: "Quality of referring relationships"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "linkedin", endpoint: "connections"}
            - {type: "scrape", target: "company_website", pages: ["/about", "/affiliations"]}
          score_range: [0, 100]
          scoring_logic:
            major_firm_referrals: 100
            quality_referral_network: 80
            adequate_network: 65
            limited_network: 45
            no_apparent_network: 30
          critical: false
          score_condition: null
          
        - id: "association_leadership"
          name: "Association Leadership"
          description: "Leadership roles in professional associations"
          weight: 0.15
          ttl: "static"
          ttl_seconds: 7776000
          sources:
            - {type: "api", provider: "aba", endpoint: "leadership/search"}
            - {type: "api", provider: "aicpa", endpoint: "leadership/search"}
            - {type: "api", provider: "aia", endpoint: "leadership/search"}
            - {type: "scrape", target: "association_websites"}
          score_range: [0, 100]
          scoring_logic:
            national_leadership: 100
            state_leadership: 85
            committee_chair: 75
            active_member: 60
            member: 45
            non_member: 30
          critical: false
          score_condition: null
          
        - id: "thought_leadership"
          name: "Thought Leadership"
          description: "Publications, speaking, CLE presentations"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/publications", "/news", "/insights"]}
            - {type: "api", provider: "google_scholar", endpoint: "author/search"}
            - {type: "api", provider: "ssrn", endpoint: "author/search"}
          score_range: [0, 100]
          scoring_logic:
            extensive_publishing: 100
            regular_publishing: 80
            occasional_publishing: 60
            minimal: 40
            none: 25
          critical: false
          score_condition: null
          
        - id: "panel_membership"
          name: "Panel Membership"
          description: "Insurance defense panels, bank approved lists"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "insurance_panels", endpoint: "search"}
            - {type: "scrape", target: "company_website", pages: ["/about", "/clients"]}
          score_range: [0, 100]
          scoring_logic:
            major_panels: 100
            regional_panels: 80
            some_panel_work: 60
            no_panel_work: 40
          critical: false
          score_condition: null

      regulatory_standing:
        - id: "license_status"
          name: "License Status"
          description: "Current status of all professional licenses"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_bar", endpoint: "attorney/status"}
            - {type: "api", provider: "state_cpa_board", endpoint: "license/status"}
            - {type: "api", provider: "state_architect_board", endpoint: "license/status"}
            - {type: "api", provider: "state_pe_board", endpoint: "license/status"}
            - {type: "api", provider: "state_real_estate", endpoint: "license/status"}
          score_range: [0, 100]
          scoring_logic:
            all_active_good_standing: 100
            active_minor_admin_issue: 80
            probationary_status: 45
            suspended: 20
            revoked: 0
            inactive: 30
          critical: true
          score_condition: license_status_critical
          
        - id: "disciplinary_history"
          name: "Disciplinary History"
          description: "Sanctions, censures, suspensions, reprimands"
          weight: 0.30
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_bar", endpoint: "discipline/search"}
            - {type: "api", provider: "state_cpa_board", endpoint: "discipline/search"}
            - {type: "api", provider: "state_pe_board", endpoint: "discipline/search"}
            - {type: "api", provider: "finra", endpoint: "brokercheck"}
          score_range: [0, 100]
          scoring_logic:
            no_history: 100
            private_admonition_over_10yr: 90
            private_admonition_recent: 75
            public_censure_over_10yr: 60
            public_censure_recent: 40
            suspension_any: 20
            multiple_actions: 10
          critical: true
          score_condition: disciplinary_history_critical
          
        - id: "malpractice_record"
          name: "Public Malpractice Record"
          description: "Public judgments and disclosed settlements"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "pacer", endpoint: "cases/search"}
            - {type: "api", provider: "state_courts", endpoint: "judgments/search"}
            - {type: "api", provider: "westlaw", endpoint: "verdicts/search"}
          score_range: [0, 100]
          scoring_logic:
            no_record: 100
            dismissed_only: 90
            minor_settlement_over_5yr: 75
            significant_settlement: 50
            judgment_against: 30
            multiple_matters: 15
          critical: true
          score_condition: malpractice_record_critical
          
        - id: "ce_compliance"
          name: "Continuing Education Compliance"
          description: "CLE/CPE/CE requirements current"
          weight: 0.05
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "state_bar", endpoint: "cle/status"}
            - {type: "api", provider: "nasba", endpoint: "cpe/status"}
          score_range: [0, 100]
          scoring_logic:
            fully_compliant: 100
            minor_deficiency: 75
            moderate_deficiency: 50
            significant_deficiency: 25
            non_compliant: 10
          critical: false
          score_condition: null
          
        - id: "specialty_certification"
          name: "Specialty Certifications"
          description: "Board certifications, specialty designations"
          weight: 0.10
          ttl: "static"
          ttl_seconds: 7776000
          sources:
            - {type: "api", provider: "abota", endpoint: "members"}
            - {type: "api", provider: "state_bar", endpoint: "certifications"}
            - {type: "api", provider: "aicpa", endpoint: "credentials"}
          score_range: [0, 100]
          scoring_logic:
            multiple_certifications: 100
            single_certification: 85
            certification_eligible: 65
            no_certification: 50
          critical: false
          score_condition: null
          
        - id: "peer_review"
          name: "Peer Review Rating"
          description: "AICPA peer review rating (accounting firms)"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          applicable_professions: ["accounting_firm"]
          sources:
            - {type: "api", provider: "aicpa", endpoint: "peerreview/search"}
          score_range: [0, 100]
          scoring_logic:
            pass_no_deficiencies: 100
            pass_with_deficiencies: 60
            pass_with_significant: 35
            fail: 10
            not_enrolled: 40
          critical: true
          score_condition: peer_review_critical
          
        - id: "pcaob_standing"
          name: "PCAOB/SEC Standing"
          description: "PCAOB registration and inspection results"
          weight: 0.05
          ttl: "dynamic"
          ttl_seconds: 86400
          applicable_professions: ["accounting_firm"]
          sources:
            - {type: "api", provider: "pcaob", endpoint: "firms/search"}
            - {type: "api", provider: "sec", endpoint: "enforcement/search"}
          score_range: [0, 100]
          scoring_logic:
            registered_clean: 100
            registered_minor_findings: 75
            registered_significant_findings: 45
            enforcement_action: 20
            not_registered: 60
          critical: false
          score_condition: null

      firm_stability:
        - id: "tenure"
          name: "Years in Practice"
          description: "Firm establishment and longevity"
          weight: 0.20
          ttl: "static"
          ttl_seconds: 7776000
          sources:
            - {type: "api", provider: "dnb", endpoint: "company/profile"}
            - {type: "api", provider: "secretary_of_state", endpoint: "entity/search"}
            - {type: "scrape", target: "company_website", pages: ["/about", "/history"]}
          score_range: [0, 100]
          scoring_logic:
            over_25_years: 100
            15_25_years: 90
            10_15_years: 80
            5_10_years: 65
            3_5_years: 50
            under_3_years: 35
          critical: false
          score_condition: null
          
        - id: "partner_stability"
          name: "Partner/Principal Stability"
          description: "Partner retention and turnover patterns"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "linkedin", endpoint: "company/employees"}
            - {type: "scrape", target: "company_website", pages: ["/attorneys", "/team", "/partners"]}
            - {type: "news", provider: "gdelt", query: "{firm} partner departure OR lateral"}
          score_range: [0, 100]
          scoring_logic:
            stable_long_tenure: 100
            mostly_stable: 80
            normal_turnover: 65
            elevated_turnover: 45
            high_turnover: 25
            mass_departure: 10
          critical: true
          score_condition: partner_stability_critical
          
        - id: "staff_retention"
          name: "Staff Retention"
          description: "Associate/staff retention signals"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "glassdoor", endpoint: "reviews/company"}
            - {type: "api", provider: "indeed", endpoint: "reviews/company"}
            - {type: "api", provider: "linkedin", endpoint: "company/insights"}
          score_range: [0, 100]
          scoring_logic:
            excellent_retention: 100
            good_retention: 80
            average_retention: 65
            below_average: 45
            poor_retention: 25
          critical: false
          score_condition: null
          
        - id: "office_stability"
          name: "Office Stability"
          description: "Office locations and changes"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/contact", "/locations"]}
            - {type: "api", provider: "google_places", endpoint: "search"}
          score_range: [0, 100]
          scoring_logic:
            long_term_stable: 100
            stable_with_growth: 90
            recent_relocation: 70
            multiple_moves: 50
            contraction: 40
          critical: false
          score_condition: null
          
        - id: "financial_stability"
          name: "Financial Stability"
          description: "Financial health indicators"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "dnb", endpoint: "company/financials"}
            - {type: "api", provider: "experian", endpoint: "business/credit"}
            - {type: "news", provider: "gdelt", query: "{firm} bankruptcy OR layoffs OR financial"}
          score_range: [0, 100]
          scoring_logic:
            strong_financials: 100
            stable: 80
            adequate: 65
            concerns_present: 45
            distress_signals: 25
            bankruptcy_risk: 10
          critical: true
          score_condition: financial_stability_critical
          
        - id: "succession_planning"
          name: "Succession Planning"
          description: "Observable succession planning indicators"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/about", "/leadership"]}
            - {type: "api", provider: "linkedin", endpoint: "company/employees"}
          score_range: [0, 100]
          scoring_logic:
            clear_succession: 100
            emerging_leaders: 80
            adequate_depth: 65
            key_person_risk: 45
            significant_risk: 25
          critical: false
          score_condition: null

      practice_quality:
        - id: "outcome_patterns"
          name: "Matter Outcome Patterns"
          description: "Case outcomes, transaction completion rates"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "api", provider: "pacer", endpoint: "cases/outcomes"}
            - {type: "api", provider: "westlaw", endpoint: "verdicts/search"}
            - {type: "scrape", target: "company_website", pages: ["/results", "/victories", "/transactions"]}
          score_range: [0, 100]
          scoring_logic:
            excellent_outcomes: 100
            above_average: 80
            average: 65
            below_average: 45
            poor_outcomes: 25
          critical: false
          score_condition: null
          
        - id: "client_reviews"
          name: "Client Reviews"
          description: "Client ratings on professional platforms"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "google_reviews", endpoint: "place/reviews"}
            - {type: "api", provider: "avvo", endpoint: "reviews"}
            - {type: "api", provider: "martindale", endpoint: "reviews"}
            - {type: "api", provider: "yelp", endpoint: "reviews"}
          score_range: [0, 100]
          scoring_logic:
            4.5_plus_significant_volume: 100
            4.0_4.5_good_volume: 85
            3.5_4.0: 70
            3.0_3.5: 50
            below_3.0: 30
            no_reviews: 55
          critical: false
          score_condition: null
          
        - id: "work_quality"
          name: "Work Product Quality"
          description: "Observable work quality indicators"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "api", provider: "pacer", endpoint: "documents/quality"}
            - {type: "api", provider: "westlaw", endpoint: "briefs/citations"}
          score_range: [0, 100]
          scoring_logic:
            exemplary: 100
            high_quality: 80
            competent: 65
            adequate: 50
            concerns: 30
          critical: false
          score_condition: null
          
        - id: "fee_dispute"
          name: "Fee Dispute History"
          description: "Fee arbitrations and disputes"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_bar", endpoint: "fee_arbitration/search"}
            - {type: "api", provider: "bbb", endpoint: "complaints"}
          score_range: [0, 100]
          scoring_logic:
            no_disputes: 100
            resolved_favorably: 85
            rare_disputes: 70
            occasional_disputes: 50
            frequent_disputes: 30
            pattern_of_disputes: 15
          critical: false
          score_condition: null
          
        - id: "complaint_history"
          name: "Professional Complaints"
          description: "Complaints to professional bodies"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_bar", endpoint: "complaints/search"}
            - {type: "api", provider: "state_boards", endpoint: "complaints/search"}
          score_range: [0, 100]
          scoring_logic:
            no_complaints: 100
            dismissed_complaints: 90
            minor_resolved: 70
            moderate_resolved: 50
            serious_resolved: 30
            pattern: 15
          critical: false
          score_condition: null

      technical_infrastructure:
        - id: "tls_score"
          name: "TLS/SSL Configuration"
          description: "Website encryption quality"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "scan", provider: "ssllabs", endpoint: "analyze"}
          score_range: [0, 100]
          scoring_logic: {grade_a_plus: 100, grade_a: 90, grade_b: 70, grade_c: 45, below_c: 20}
          critical: false
          score_condition: null
          
        - id: "email_auth"
          name: "Email Authentication"
          description: "SPF, DMARC, DKIM configuration"
          weight: 0.25
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "dns", records: ["TXT", "MX"], analyzer: "email_auth_scorer"}
          score_range: [0, 100]
          scoring_logic: {dmarc_reject: 100, dmarc_quarantine: 80, dmarc_none: 60, spf_only: 45, nothing: 20}
          critical: false
          score_condition: null
          
        - id: "security_headers"
          name: "Security Headers"
          description: "HTTP security headers"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "scan", provider: "securityheaders.com", endpoint: "scan"}
          score_range: [0, 100]
          scoring_logic: {grade_a: 100, grade_b: 75, grade_c: 55, grade_d: 35, grade_f: 15}
          critical: false
          score_condition: null
          
        - id: "portal_security"
          name: "Client Portal Security"
          description: "Client portal security if applicable"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "scan", provider: "internal", analyzer: "portal_scanner"}
          score_range: [0, 100]
          scoring_logic: {secure_mfa: 100, secure_password: 80, basic_security: 60, weak: 35, no_portal: 50}
          critical: false
          score_condition: null
          
        - id: "breach_history"
          name: "Data Breach History"
          description: "Historical data breaches"
          weight: 0.20
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "haveibeenpwned", endpoint: "breaches/domain"}
            - {type: "api", provider: "privacyrights", endpoint: "breaches/search"}
            - {type: "news", provider: "gdelt", query: "{firm} data breach"}
          score_range: [0, 100]
          scoring_logic:
            no_breaches: 100
            minor_resolved: 75
            significant_resolved: 50
            recent_breach: 25
            multiple: 10
          critical: true
          score_condition: breach_history_critical

      corporate_footprint:
        - id: "website_quality"
          name: "Website Professionalism"
          description: "Website quality and completeness"
          weight: 0.25
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", analyzer: "website_quality_scorer"}
          score_range: [0, 100]
          scoring_logic:
            professional_comprehensive: 100
            professional_adequate: 80
            basic_functional: 60
            outdated: 40
            poor: 20
            no_website: 15
          critical: false
          score_condition: null
          
        - id: "bio_completeness"
          name: "Professional Bio Quality"
          description: "Attorney/professional bio completeness"
          weight: 0.20
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/attorneys", "/team", "/people"]}
          score_range: [0, 100]
          scoring_logic:
            comprehensive_all: 100
            detailed_most: 80
            basic_all: 65
            incomplete: 45
            minimal: 25
          critical: false
          score_condition: null
          
        - id: "practice_clarity"
          name: "Practice Area Clarity"
          description: "Clear description of services"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/services", "/practice-areas"]}
          score_range: [0, 100]
          scoring_logic:
            clear_detailed: 100
            adequate: 75
            basic: 55
            vague: 35
            missing: 20
          critical: false
          score_condition: null
          
        - id: "publications"
          name: "Publications/Insights"
          description: "Thought leadership content"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 604800
          sources:
            - {type: "scrape", target: "company_website", pages: ["/news", "/insights", "/publications", "/blog"]}
          score_range: [0, 100]
          scoring_logic:
            extensive_current: 100
            regular: 80
            occasional: 60
            minimal: 40
            none: 25
          critical: false
          score_condition: null
          
        - id: "community_involvement"
          name: "Community Involvement"
          description: "Pro bono, community service"
          weight: 0.15
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/community", "/pro-bono", "/giving-back"]}
          score_range: [0, 100]
          scoring_logic:
            significant_commitment: 100
            regular_involvement: 75
            some_involvement: 55
            minimal: 35
            none_apparent: 25
          critical: false
          score_condition: null
          
        - id: "diversity"
          name: "Diversity & Inclusion"
          description: "Diversity signals and commitment"
          weight: 0.10
          ttl: "semi_static"
          ttl_seconds: 2592000
          sources:
            - {type: "scrape", target: "company_website", pages: ["/diversity", "/dei", "/about"]}
            - {type: "api", provider: "mansfield_certification", endpoint: "search"}
          score_range: [0, 100]
          scoring_logic:
            certified_leader: 100
            demonstrated_commitment: 80
            stated_commitment: 60
            minimal: 40
            none: 30
          critical: false
          score_condition: null

      litigation_history:
        - id: "malpractice_suits"
          name: "Malpractice Suits"
          description: "Professional negligence suits filed"
          weight: 0.35
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "pacer", endpoint: "cases/search"}
            - {type: "api", provider: "state_courts", endpoint: "cases/search"}
          score_range: [0, 100]
          scoring_logic:
            no_suits: 100
            dismissed_over_5yr: 90
            settled_over_5yr: 75
            settled_recent: 55
            active_suit: 30
            multiple_active: 10
          critical: true
          score_condition: malpractice_suits_critical
          
        - id: "fee_disputes_litigation"
          name: "Fee Disputes/Arbitration"
          description: "Fee-related litigation and arbitration"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_bar", endpoint: "fee_arbitration/search"}
            - {type: "api", provider: "aaa", endpoint: "arbitrations/search"}
          score_range: [0, 100]
          scoring_logic:
            no_disputes: 100
            rare_resolved: 85
            occasional: 65
            frequent: 40
            pattern: 20
          critical: false
          score_condition: null
          
        - id: "regulatory_enforcement"
          name: "Regulatory Enforcement"
          description: "Regulatory enforcement actions"
          weight: 0.25
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "state_bar", endpoint: "enforcement/search"}
            - {type: "api", provider: "state_boards", endpoint: "enforcement/search"}
            - {type: "api", provider: "sec", endpoint: "enforcement/search"}
          score_range: [0, 100]
          scoring_logic:
            no_actions: 100
            minor_resolved_over_5yr: 85
            significant_resolved: 55
            recent_action: 30
            active_action: 10
          critical: true
          score_condition: regulatory_enforcement_critical
          
        - id: "civil_litigation"
          name: "Civil Litigation as Defendant"
          description: "Other civil suits as defendant"
          weight: 0.15
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "pacer", endpoint: "cases/search"}
            - {type: "api", provider: "state_courts", endpoint: "cases/search"}
          score_range: [0, 100]
          scoring_logic:
            no_suits: 100
            routine_resolved: 85
            significant_resolved: 65
            active: 45
            multiple_active: 25
          critical: false
          score_condition: null
          
        - id: "bankruptcy"
          name: "Bankruptcy History"
          description: "Firm or principal bankruptcy"
          weight: 0.10
          ttl: "dynamic"
          ttl_seconds: 86400
          sources:
            - {type: "api", provider: "pacer", endpoint: "bankruptcy/search"}
          score_range: [0, 100]
          scoring_logic:
            no_history: 100
            principal_over_10yr: 70
            principal_recent: 40
            firm_history: 25
          critical: true
          score_condition: bankruptcy_critical

    # -------------------------------------------------------------------------
    # TIER THRESHOLDS
    # -------------------------------------------------------------------------
    tier_thresholds:
      tier_1:
        id: 1
        label: "PREFERRED"
        min_score: 800
        max_score: 1000
        description: "Excellent firm - auto-approve at preferred pricing"
        auto_approve: true
        auto_decline: false
        tier_modifier: 0.75
        
      tier_2:
        id: 2
        label: "STANDARD"
        min_score: 650
        max_score: 799
        description: "Good firm - auto-approve at standard pricing"
        auto_approve: true
        auto_decline: false
        tier_modifier: 1.00
        
      tier_3:
        id: 3
        label: "ELEVATED"
        min_score: 500
        max_score: 649
        description: "Moderate risk - manual review recommended"
        auto_approve: false
        auto_decline: false
        tier_modifier: 1.30
        
      tier_4:
        id: 4
        label: "HIGH_RISK"
        min_score: 350
        max_score: 499
        description: "High risk - senior underwriter review with loading"
        auto_approve: false
        auto_decline: false
        tier_modifier: 1.75
        
      tier_5:
        id: 5
        label: "CRITICAL"
        min_score: 0
        max_score: 349
        description: "Critical risk - decline recommended"
        auto_approve: false
        auto_decline: true
        tier_modifier: 2.50

    # -------------------------------------------------------------------------
    # CONDITION DEFINITIONS
    # -------------------------------------------------------------------------
    direct_conditions:
      - id: pending_claims_true
        bands:
          - {return: true, tier_override: 4, action: "REFER", note: "Pending malpractice claims disclosed"}
      
      - id: disciplinary_pending_true
        bands:
          - {return: true, tier_override: 4, action: "REFER", note: "Pending disciplinary proceedings"}
      
      - id: coverage_declined_true
        bands:
          - {return: true, tier_override: 5, action: "DECLINE", note: "Prior PI coverage declined/non-renewed"}
      
      - id: practice_area_change_true
        bands:
          - {return: true, tier_override: null, action: "FLAG", note: "Significant practice area change"}
      
      - id: merger_activity_true
        bands:
          - {return: true, tier_override: null, action: "FLAG", note: "Recent merger/acquisition activity"}
      
      - id: major_client_loss_true
        bands:
          - {return: true, tier_override: null, action: "FLAG", note: "Major client loss (>25% revenue)"}
  
    score_conditions:
      - id: regulatory_standing_critical
        bands:
          - {max: 30, tier_override: 5, action: "DECLINE", note: "Critical regulatory issues"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant regulatory concerns"}
        inclusive_max: false
      
      - id: litigation_history_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Severe litigation history"}
          - {max: 40, tier_override: 4, action: "REFER", note: "Significant litigation concerns"}
        inclusive_max: false
      
      - id: license_status_critical
        bands:
          - {max: 35, tier_override: 5, action: "DECLINE", note: "License status critical"}
          - {max: 50, tier_override: 4, action: "REFER", note: "License status concerns"}
        inclusive_max: false
      
      - id: disciplinary_history_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Severe disciplinary history"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Significant disciplinary history"}
        inclusive_max: false
      
      - id: malpractice_record_critical
        bands:
          - {max: 35, tier_override: 4, action: "REFER", note: "Malpractice record concerns"}
        inclusive_max: false
      
      - id: peer_review_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Failed peer review"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Peer review deficiencies"}
        inclusive_max: false
      
      - id: partner_stability_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Partner stability concerns"}
        inclusive_max: false
      
      - id: financial_stability_critical
        bands:
          - {max: 30, tier_override: 4, action: "REFER", note: "Financial stability concerns"}
        inclusive_max: false
      
      - id: firm_stability_critical
        bands:
          - {max: 35, tier_override: 4, action: "REFER", note: "Firm stability concerns"}
        inclusive_max: false
      
      - id: breach_history_critical
        bands:
          - {max: 35, tier_override: 4, action: "REFER", note: "Data breach history concerns"}
        inclusive_max: false
      
      - id: malpractice_suits_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Multiple active malpractice suits"}
          - {max: 40, tier_override: 4, action: "REFER", note: "Active malpractice litigation"}
        inclusive_max: false
      
      - id: regulatory_enforcement_critical
        bands:
          - {max: 25, tier_override: 5, action: "DECLINE", note: "Active regulatory enforcement"}
          - {max: 45, tier_override: 4, action: "REFER", note: "Regulatory enforcement history"}
        inclusive_max: false
      
      - id: bankruptcy_critical
        bands:
          - {max: 40, tier_override: 4, action: "REFER", note: "Bankruptcy history concerns"}
        inclusive_max: false

    # -------------------------------------------------------------------------
    # PRICING PARAMETERS
    # -------------------------------------------------------------------------
    pricing:
      limit_ilf:
        base_limit: 1000000
        factors:
          - {limit: 250000, factor: 0.50}
          - {limit: 500000, factor: 0.75}
          - {limit: 1000000, factor: 1.00}
          - {limit: 2000000, factor: 1.60}
          - {limit: 3000000, factor: 2.10}
          - {limit: 5000000, factor: 2.80}
          - {limit: 10000000, factor: 4.20}
      
      retention_credits:
        - {min_retention: 5000, max_retention: 10000, credit: 0.00}
        - {min_retention: 10000, max_retention: 25000, credit: 0.05}
        - {min_retention: 25000, max_retention: 50000, credit: 0.10}
        - {min_retention: 50000, max_retention: 100000, credit: 0.15}
        - {min_retention: 100000, max_retention: null, credit: 0.20}
      
      experience_modifiers:
        clean_10yr: 0.85
        clean_5yr: 0.90
        clean_3yr: 0.95
        minor_losses: 1.00
        moderate_losses: 1.20
        significant_losses: 1.40
        
      taxes_fees_rate: 0.05

    # -------------------------------------------------------------------------
    # TEST PROFILES
    # -------------------------------------------------------------------------
    test_profiles:
      excellent_law_firm:
        description: "Well-established mid-size law firm with excellent standing"
        expected_tier: [1, 2]
        expected_score_range: [780, 950]
        profession_type: "LAW_FIRM"
        firm_size: "MEDIUM"
        revenue_size: "R_5M_25M"
        practice_area: "CORPORATE_MA"
        signals:
          network_authority:
            peer_ranking: 80
            client_quality: 85
            referral_network: 75
            association_leadership: 70
            thought_leadership: 75
            panel_membership: 65
          regulatory_standing:
            license_status: 100
            disciplinary_history: 95
            malpractice_record: 90
            ce_compliance: 100
            specialty_certification: 75
          firm_stability:
            tenure: 90
            partner_stability: 85
            staff_retention: 78
            office_stability: 95
            financial_stability: 85
            succession_planning: 70
          practice_quality:
            outcome_patterns: 80
            client_reviews: 85
            work_quality: 80
            fee_dispute: 95
            complaint_history: 98
          technical_infrastructure:
            tls_score: 90
            email_auth: 85
            security_headers: 75
            portal_security: 80
            breach_history: 100
          corporate_footprint:
            website_quality: 85
            bio_completeness: 90
            practice_clarity: 85
            publications: 75
            community_involvement: 70
            diversity: 65
          litigation_history:
            malpractice_suits: 90
            fee_disputes_litigation: 95
            regulatory_enforcement: 100
            civil_litigation: 95
            bankruptcy: 100

      average_accounting_firm:
        description: "Typical small CPA firm with standard profile"
        expected_tier: [2, 3]
        expected_score_range: [550, 720]
        profession_type: "ACCOUNTING_FIRM"
        firm_size: "SMALL"
        revenue_size: "R_1M_5M"
        practice_area: "GENERAL_PRACTICE"
        signals:
          network_authority:
            peer_ranking: 55
            client_quality: 65
            referral_network: 60
            association_leadership: 50
            thought_leadership: 45
          regulatory_standing:
            license_status: 100
            disciplinary_history: 95
            malpractice_record: 90
            ce_compliance: 95
            specialty_certification: 50
            peer_review: 85
            pcaob_standing: 60
          firm_stability:
            tenure: 75
            partner_stability: 70
            staff_retention: 65
            office_stability: 80
            financial_stability: 72
            succession_planning: 55
          practice_quality:
            outcome_patterns: 70
            client_reviews: 72
            work_quality: 70
            fee_dispute: 90
            complaint_history: 95
          technical_infrastructure:
            tls_score: 75
            email_auth: 70
            security_headers: 60
            breach_history: 100
          corporate_footprint:
            website_quality: 65
            bio_completeness: 70
            practice_clarity: 70
            publications: 40
            community_involvement: 55
          litigation_history:
            malpractice_suits: 95
            fee_disputes_litigation: 90
            regulatory_enforcement: 100
            civil_litigation: 95
            bankruptcy: 100

      high_risk_solo:
        description: "Solo practitioner with disciplinary history"
        expected_tier: [4, 5]
        expected_score_range: [250, 450]
        profession_type: "LAW_FIRM"
        firm_size: "SOLO"
        revenue_size: "UNDER_500K"
        practice_area: "PERSONAL_INJURY_PLAINTIFF"
        signals:
          network_authority:
            peer_ranking: 30
            client_quality: 40
            referral_network: 35
            association_leadership: 25
            thought_leadership: 20
          regulatory_standing:
            license_status: 80
            disciplinary_history: 45
            malpractice_record: 50
            ce_compliance: 70
            specialty_certification: 30
          firm_stability:
            tenure: 60
            partner_stability: 50
            staff_retention: 45
            office_stability: 55
            financial_stability: 45
            succession_planning: 20
          practice_quality:
            outcome_patterns: 50
            client_reviews: 55
            work_quality: 50
            fee_dispute: 60
            complaint_history: 55
          technical_infrastructure:
            tls_score: 50
            email_auth: 40
            security_headers: 35
            breach_history: 85
          corporate_footprint:
            website_quality: 45
            bio_completeness: 50
            practice_clarity: 45
            publications: 20
            community_involvement: 30
          litigation_history:
            malpractice_suits: 50
            fee_disputes_litigation: 60
            regulatory_enforcement: 55
            civil_litigation: 70
            bankruptcy: 90

      engineering_firm:
        description: "Mid-size structural engineering firm"
        expected_tier: [2, 3]
        expected_score_range: [580, 750]
        profession_type: "ENGINEERING"
        firm_size: "MEDIUM"
        revenue_size: "R_5M_25M"
        practice_area: "STRUCTURAL"
        signals:
          network_authority:
            peer_ranking: 70
            client_quality: 75
            referral_network: 70
            association_leadership: 60
            thought_leadership: 55
          regulatory_standing:
            license_status: 100
            disciplinary_history: 95
            malpractice_record: 80
            ce_compliance: 100
            specialty_certification: 70
          firm_stability:
            tenure: 80
            partner_stability: 75
            staff_retention: 70
            office_stability: 85
            financial_stability: 78
            succession_planning: 65
          practice_quality:
            outcome_patterns: 75
            client_reviews: 78
            work_quality: 80
            fee_dispute: 88
            complaint_history: 92
          technical_infrastructure:
            tls_score: 80
            email_auth: 75
            security_headers: 65
            breach_history: 100
          corporate_footprint:
            website_quality: 75
            bio_completeness: 80
            practice_clarity: 80
            publications: 50
            community_involvement: 55
          litigation_history:
            malpractice_suits: 75
            fee_disputes_litigation: 90
            regulatory_enforcement: 100
            civil_litigation: 85
            bankruptcy: 100

      it_consulting:
        description: "Growing IT consulting firm"
        expected_tier: [2, 3]
        expected_score_range: [550, 720]
        profession_type: "IT_CONSULTING"
        firm_size: "SMALL"
        revenue_size: "R_1M_5M"
        signals:
          network_authority:
            peer_ranking: 50
            client_quality: 70
            referral_network: 65
            association_leadership: 45
            thought_leadership: 60
          regulatory_standing:
            license_status: 100
            disciplinary_history: 100
            malpractice_record: 95
            ce_compliance: 90
          firm_stability:
            tenure: 55
            partner_stability: 70
            staff_retention: 68
            office_stability: 75
            financial_stability: 72
            succession_planning: 50
          practice_quality:
            client_reviews: 80
            work_quality: 75
            fee_dispute: 92
            complaint_history: 95
          technical_infrastructure:
            tls_score: 95
            email_auth: 92
            security_headers: 88
            portal_security: 85
            breach_history: 100
          corporate_footprint:
            website_quality: 80
            bio_completeness: 75
            practice_clarity: 82
            publications: 65
            community_involvement: 45
          litigation_history:
            malpractice_suits: 100
            fee_disputes_litigation: 95
            regulatory_enforcement: 100
            civil_litigation: 95
            bankruptcy: 100

      real_estate_brokerage:
        description: "Real estate brokerage with recent claims"
        expected_tier: [3, 4]
        expected_score_range: [420, 600]
        profession_type: "REAL_ESTATE"
        firm_size: "MICRO"
        revenue_size: "R_500K_1M"
        direct_queries:
          pending_claims: true
        signals:
          network_authority:
            peer_ranking: 45
            client_quality: 55
            referral_network: 60
            association_leadership: 40
          regulatory_standing:
            license_status: 95
            disciplinary_history: 80
            malpractice_record: 65
            ce_compliance: 90
          firm_stability:
            tenure: 70
            partner_stability: 65
            staff_retention: 60
            office_stability: 75
            financial_stability: 65
          practice_quality:
            client_reviews: 68
            fee_dispute: 75
            complaint_history: 70
          technical_infrastructure:
            tls_score: 70
            email_auth: 60
            security_headers: 50
            breach_history: 95
          corporate_footprint:
            website_quality: 65
            bio_completeness: 60
            practice_clarity: 70
          litigation_history:
            malpractice_suits: 55
            fee_disputes_litigation: 80
            regulatory_enforcement: 90
            civil_litigation: 85
            bankruptcy: 100

# Phase 6 Instructions — PI Coverage Expansion

## Context

You are working on branch `claude/review-dsi-phase-5-TuTs8` in `jwalker618/digital-signal-intelligence`.

Phase 5 (`development/project/version/4/phase_5.md`) expanded Energy from 1 to 12 configurations. Phase 6 does the same for Professional Indemnity (PI).

## Task

**Create `/home/user/digital-signal-intelligence/development/project/version/4/phase_6.md`** — a comprehensive Phase 6 specification document for PI coverage expansion. Follow Phase 5's structure exactly. The document should be 2000+ lines covering all sections below. Do NOT ask questions. Do NOT plan. Just write the document, commit, and push.

## Reference Files

- **Phase 5 template** (follow this structure exactly): `development/project/version/4/phase_5.md`
- **Existing PI config** (current signal groups, weights, signals, pricing): `coverages/pi/config.yaml`
- **Seed script** (current PI seed entries): `seed_dsi_bench.py`

## Agreed Architecture: 13 Configurations (2 existing + 11 new)

```
pi/
├── pi_general                      (exists)   specificity=1   Universal fallback (revenue > $50M)
├── pi_sme                          (exists)   specificity=2   Small practices (revenue ≤ $50M, BUNDLED)
│
├── LEGAL
│   ├── pi_legal_large              (new)      specificity=4   Top-tier corporate/commercial (AmLaw 200, Magic Circle)
│   └── pi_legal_specialist         (new)      specificity=3   Specialist/plaintiff/niche practices
│
├── ACCOUNTING & AUDIT
│   ├── pi_audit                    (new)      specificity=4   Public company audit (Big 4, mid-tier audit)
│   └── pi_accounting               (new)      specificity=2   Non-audit: tax, advisory, bookkeeping
│
├── DESIGN & CONSTRUCTION
│   ├── pi_architecture             (new)      specificity=3   Architecture & landscape design
│   └── pi_engineering              (new)      specificity=3   Structural, civil, geotechnical engineering
│
├── TECHNOLOGY
│   └── pi_technology               (new)      specificity=3   IT consulting, systems integration, managed services
│
├── FINANCIAL & ADVISORY
│   ├── pi_financial_advisory       (new)      specificity=3   Wealth management, IFAs, investment/pension advisers
│   └── pi_management_consulting    (new)      specificity=2   Strategy & management advisory
│
├── REAL ESTATE & VALUATION
│   └── pi_real_estate              (new)      specificity=3   Surveyors, valuers, estate agents
│
└── ENVIRONMENTAL
    └── pi_environmental            (new)      specificity=3   EIA, contaminated land, remediation advisory
```

## Routing

Routes via `profession_segment` (analogous to energy's `operation_segment`) with `sub_profession_type` as secondary routing dimension for legal and accounting.

| Configuration | Specificity | Routing Constraints | Fallback |
|---|---|---|---|
| `pi_legal_large` | 4 | `profession_segment == LEGAL` AND `revenue > 100000000` | `pi_legal_specialist` |
| `pi_audit` | 4 | `profession_segment == ACCOUNTING` AND `sub_profession_type IN [AUDIT_PUBLIC, AUDIT_PRIVATE]` | `pi_accounting` |
| `pi_legal_specialist` | 3 | `profession_segment == LEGAL` | `pi_general` |
| `pi_architecture` | 3 | `profession_segment == DESIGN_CONSTRUCTION` AND `sub_profession_type IN [ARCHITECTURE, LANDSCAPE, INTERIOR_DESIGN]` | `pi_general` |
| `pi_engineering` | 3 | `profession_segment == DESIGN_CONSTRUCTION` AND `sub_profession_type IN [STRUCTURAL, GEOTECHNICAL, CIVIL, MECHANICAL, ELECTRICAL, ENVIRONMENTAL_ENG]` | `pi_general` |
| `pi_technology` | 3 | `profession_segment == TECHNOLOGY` | `pi_general` |
| `pi_financial_advisory` | 3 | `profession_segment == FINANCIAL_ADVISORY` | `pi_general` |
| `pi_real_estate` | 3 | `profession_segment == REAL_ESTATE_VALUATION` | `pi_general` |
| `pi_environmental` | 3 | `profession_segment == ENVIRONMENTAL` | `pi_general` |
| `pi_accounting` | 2 | `profession_segment == ACCOUNTING` | `pi_general` |
| `pi_management_consulting` | 2 | `profession_segment == MANAGEMENT_CONSULTING` | `pi_general` |
| `pi_sme` | 2 | `revenue <= 50000000` AND `employee_count <= 200` | `pi_general` |
| `pi_general` | 1 | `revenue > 50000000` | — |

## Existing PI Signal Groups (from config.yaml)

7 scored groups + 4 categorical groups:

**Categorical:** profession_type, sub_profession_type, firm_size, revenue_size

**Scored groups with current pi_general weights (R/L/E):**
- network_authority (0.15 / 0.10 / 0.05) — peer_ranking, client_quality, referral_network, association_leadership, thought_leadership, panel_membership
- regulatory_standing (0.25 / 0.25 / 0.10) — license_status, disciplinary_history, malpractice_record, ce_compliance, specialty_certification, peer_review, pcaob_standing
- firm_stability (0.15 / 0.15 / 0.20) — tenure, partner_stability, staff_retention, office_stability, financial_stability, succession_planning
- practice_quality (0.15 / 0.20 / 0.15) — outcome_patterns, client_reviews, work_quality, fee_dispute, complaint_history
- technical_infrastructure (0.10 / 0.10 / 0.10) — tls_score, email_auth, security_headers, portal_security, breach_history
- corporate_footprint (0.10 / 0.05 / 0.25) — website_quality, bio_completeness, practice_clarity, publications, community_involvement, diversity
- litigation_history (0.10 / 0.15 / 0.15) — malpractice_suits, fee_disputes_litigation, regulatory_enforcement, civil_litigation, bankruptcy

**Existing pricing (pi_general):** MULTIPLIER on revenue, DECOUPLED limits $1M-$50M, rates T1=0.0008 to T5=0.0045
**Existing pricing (pi_sme):** Categorical base from profession_type, BUNDLED packages, tier multipliers 0.75-2.50

## New Signal Groups Per Configuration

Each specialist config introduces ONE new profession-specific signal group (except pi_accounting and pi_management_consulting which reuse existing groups with reweighted distributions).

### pi_legal_large — new group: `partner_practice_mix` (R:0.10, L:0.10, E:0.25)
- `lateral_hire_volume` (INFERRED_PROXY) — Rate of lateral partner additions; higher churn = legacy claims risk
- `prior_acts_coverage` (DIRECT_OBSERVABLE) — Prior acts tail coverage status
- `conflict_system_quality` (INFERRED_PROXY) — Conflict-of-interest screening system sophistication
- `trust_account_compliance` (DIRECT_OBSERVABLE) — Client trust/IOLTA account compliance
- `class_action_exposure` (INFERRED_PROXY) — Exposure from class action representation/defense
- `partner_departure_rate` (DIRECT_OBSERVABLE) — Partner departure rate (tail exposure driver)
- `matter_concentration` (INFERRED_PROXY) — Single-matter revenue concentration

### pi_legal_specialist — new group: `case_portfolio` (R:0.10, L:0.10, E:0.35)
- `case_concentration` (INFERRED_PROXY) — Single-case exposure as % of revenue
- `contingency_fee_ratio` (DIRECT_OBSERVABLE) — Contingency vs hourly fee mix
- `trial_success_rate` (INFERRED_PROXY) — Win/loss record as quality proxy
- `statute_tracking_compliance` (INFERRED_PROXY) — SOL/deadline tracking effectiveness
- `case_value_distribution` (INFERRED_PROXY) — Distribution of case values (tail risk indicator)

### pi_audit — new group: `audit_quality` (R:0.20, L:0.20, E:0.40)
- `pcaob_inspection_deficiency_rate` (DIRECT_OBSERVABLE) — PCAOB Part I/II inspection findings rate
- `restatement_rate` (DIRECT_OBSERVABLE) — Audit client financial restatement frequency
- `going_concern_accuracy` (INFERRED_PROXY) — Going-concern opinion accuracy
- `sec_enforcement_exposure` (DIRECT_OBSERVABLE) — SEC enforcement actions against firm/partners
- `audit_client_concentration` (INFERRED_PROXY) — Single-client fee dependency percentage
- `audit_partner_rotation_compliance` (DIRECT_OBSERVABLE) — Partner rotation compliance quality
- `securities_litigation_exposure` (INFERRED_PROXY) — Exposure from audit client securities suits

### pi_accounting — NO new group (reuses existing 7 groups with adjusted weights)
New signals added to existing groups:
- `tax_opinion_quality` (INFERRED_PROXY, practice_quality) — Quality of tax opinions issued
- `irs_examination_track` (DIRECT_OBSERVABLE, regulatory_standing) — Client IRS exam outcomes
- `estate_planning_complexity` (INFERRED_PROXY, practice_quality) — Engagement complexity

### pi_architecture — new group: `design_quality` (R:0.25, L:0.30, E:0.45)
- `design_defect_claims` (DIRECT_OBSERVABLE) — Historical design defect claim frequency
- `building_code_compliance` (DIRECT_OBSERVABLE) — Code compliance track record
- `project_complexity_score` (INFERRED_PROXY) — Average project complexity rating
- `latent_defect_exposure` (INFERRED_PROXY) — Long-tail defect claim exposure
- `sustainability_certification` (DIRECT_OBSERVABLE) — LEED/BREEAM certification track record
- `construction_phase` (categorical: PRE_CONSTRUCTION, CONSTRUCTION, COMMISSIONING, EARLY_OPERATION, MATURE_OPERATION)

### pi_engineering — new group: `engineering_quality` (R:0.35, L:0.35, E:0.50)
- `structural_failure_history` (DIRECT_OBSERVABLE) — Structural failure/deficiency claims
- `pe_license_compliance` (DIRECT_OBSERVABLE) — PE license status across jurisdictions
- `geotechnical_claim_frequency` (DIRECT_OBSERVABLE) — Geotechnical failure claims
- `infrastructure_project_exposure` (INFERRED_PROXY) — Public infrastructure involvement (higher duty of care)
- `project_size_concentration` (INFERRED_PROXY) — Single-project exposure concentration
- `remediation_cost_history` (DIRECT_OBSERVABLE) — Past environmental remediation cost exposure

### pi_technology — new group: `delivery_quality` (R:0.15, L:0.20, E:0.35)
- `project_failure_rate` (INFERRED_PROXY) — IT project abandonment/failure rate
- `sla_compliance` (DIRECT_OBSERVABLE) — Service level agreement adherence
- `data_breach_exposure` (DIRECT_OBSERVABLE) — Client data handling and breach history
- `technology_stack_currency` (INFERRED_PROXY) — Tech stack currency (outdated = risk)
- `implementation_methodology` (INFERRED_PROXY) — Structured methodology adherence (ITIL, Agile maturity)
- `client_data_encryption` (DIRECT_OBSERVABLE) — Client data encryption standards

### pi_financial_advisory — new group: `advisory_quality` (R:0.10, L:0.10, E:0.30)
- `suitability_compliance` (DIRECT_OBSERVABLE) — Investment suitability record
- `complaint_per_aum` (DIRECT_OBSERVABLE) — Complaints per AUM
- `regulatory_exam_results` (DIRECT_OBSERVABLE) — SEC/FCA examination findings
- `churning_indicators` (INFERRED_PROXY) — Excessive trading indicators
- `fee_transparency_score` (INFERRED_PROXY) — Fee disclosure quality

### pi_management_consulting — NO new group (reuses existing 7 groups with adjusted weights)
New signals added to existing groups:
- `engagement_scope_clarity` (INFERRED_PROXY, practice_quality) — Scope definition quality
- `deliverable_acceptance_rate` (DIRECT_OBSERVABLE, practice_quality) — Client deliverable acceptance
- `client_outcome_correlation` (INFERRED_PROXY, practice_quality) — Advice-to-outcome correlation

### pi_real_estate — new group: `valuation_quality` (R:0.20, L:0.25, E:0.40)
- `valuation_accuracy` (DIRECT_OBSERVABLE) — Historical valuation accuracy vs realized prices
- `negligent_misstatement_history` (DIRECT_OBSERVABLE) — Negligent misstatement claims
- `property_type_concentration` (INFERRED_PROXY) — Concentration in specific property types
- `market_knowledge_currency` (INFERRED_PROXY) — Local market expertise currency
- `rics_compliance` (DIRECT_OBSERVABLE) — RICS (UK) / Appraisal Institute (US) compliance

### pi_environmental — new group: `environmental_assessment_quality` (R:0.35, L:0.30, E:0.45)
- `contamination_assessment_accuracy` (DIRECT_OBSERVABLE) — Phase I/II assessment accuracy
- `regulatory_compliance_track` (DIRECT_OBSERVABLE) — Environmental regulation compliance
- `remediation_effectiveness` (INFERRED_PROXY) — Remediation advice effectiveness
- `long_tail_exposure` (INFERRED_PROXY) — Latent contamination discovery risk
- `cercla_superfund_exposure` (DIRECT_OBSERVABLE) — CERCLA/Superfund site involvement

**Total new signals: 58** across 11 new configurations.

## Weight Distributions (R/L/E must each sum to 1.0)

### pi_legal_large
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.20 | 0.20 | 0.10 |
| firm_stability | 0.20 | 0.15 | 0.20 |
| practice_quality | 0.15 | 0.20 | 0.10 |
| technical_infrastructure | 0.10 | 0.10 | 0.10 |
| corporate_footprint | 0.05 | 0.05 | 0.10 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| partner_practice_mix | 0.10 | 0.10 | 0.25 |

### pi_legal_specialist
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.25 | 0.20 | 0.10 |
| firm_stability | 0.15 | 0.10 | 0.15 |
| practice_quality | 0.15 | 0.25 | 0.10 |
| technical_infrastructure | 0.05 | 0.05 | 0.05 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.15 | 0.20 | 0.15 |
| case_portfolio | 0.10 | 0.10 | 0.35 |

### pi_audit
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.05 | 0.05 |
| regulatory_standing | 0.30 | 0.30 | 0.15 |
| firm_stability | 0.10 | 0.10 | 0.10 |
| practice_quality | 0.10 | 0.10 | 0.10 |
| technical_infrastructure | 0.10 | 0.05 | 0.05 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| audit_quality | 0.20 | 0.20 | 0.40 |

### pi_accounting
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.25 | 0.25 | 0.10 |
| firm_stability | 0.15 | 0.15 | 0.20 |
| practice_quality | 0.20 | 0.20 | 0.20 |
| technical_infrastructure | 0.10 | 0.10 | 0.10 |
| corporate_footprint | 0.10 | 0.05 | 0.15 |
| litigation_history | 0.10 | 0.20 | 0.20 |

### pi_architecture
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.15 | 0.15 | 0.05 |
| firm_stability | 0.15 | 0.10 | 0.15 |
| practice_quality | 0.15 | 0.15 | 0.10 |
| technical_infrastructure | 0.05 | 0.05 | 0.05 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| design_quality | 0.25 | 0.30 | 0.45 |

### pi_engineering
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.05 | 0.05 |
| regulatory_standing | 0.20 | 0.15 | 0.05 |
| firm_stability | 0.10 | 0.10 | 0.10 |
| practice_quality | 0.10 | 0.10 | 0.10 |
| technical_infrastructure | 0.05 | 0.05 | 0.05 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| engineering_quality | 0.35 | 0.35 | 0.50 |

### pi_technology
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.15 | 0.10 | 0.05 |
| firm_stability | 0.15 | 0.10 | 0.15 |
| practice_quality | 0.15 | 0.15 | 0.10 |
| technical_infrastructure | 0.15 | 0.20 | 0.15 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| delivery_quality | 0.15 | 0.20 | 0.35 |

### pi_financial_advisory
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.25 | 0.25 | 0.15 |
| firm_stability | 0.15 | 0.10 | 0.15 |
| practice_quality | 0.15 | 0.20 | 0.10 |
| technical_infrastructure | 0.10 | 0.10 | 0.10 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| advisory_quality | 0.10 | 0.10 | 0.30 |

### pi_management_consulting
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.15 | 0.10 | 0.10 |
| regulatory_standing | 0.15 | 0.15 | 0.05 |
| firm_stability | 0.20 | 0.15 | 0.20 |
| practice_quality | 0.20 | 0.25 | 0.15 |
| technical_infrastructure | 0.10 | 0.10 | 0.15 |
| corporate_footprint | 0.10 | 0.10 | 0.20 |
| litigation_history | 0.10 | 0.15 | 0.15 |

### pi_real_estate
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.20 | 0.20 | 0.10 |
| firm_stability | 0.15 | 0.10 | 0.15 |
| practice_quality | 0.15 | 0.15 | 0.10 |
| technical_infrastructure | 0.05 | 0.05 | 0.05 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| valuation_quality | 0.20 | 0.25 | 0.40 |

### pi_environmental
| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.05 | 0.05 |
| regulatory_standing | 0.20 | 0.20 | 0.10 |
| firm_stability | 0.10 | 0.10 | 0.10 |
| practice_quality | 0.10 | 0.10 | 0.10 |
| technical_infrastructure | 0.05 | 0.05 | 0.05 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| litigation_history | 0.10 | 0.15 | 0.10 |
| environmental_assessment_quality | 0.35 | 0.30 | 0.45 |

## Key Design Decisions

1. **Medical malpractice excluded** — Med-mal is a separate coverage line with fundamentally different policy forms, bodily injury component, and consent/standard-of-care dynamics. NOT in PI scope.
2. **Geographic variance via modifiers, not separate configs** — US plaintiff-friendly loading, UK SRA/FCA regulatory overlay, EU mandatory PI requirements handled as jurisdiction modifiers within each config. Otherwise we'd have 40+ configs.
3. **`profession_segment` as pre-routing field** — Mirrors energy's `operation_segment`. Optional input. When absent, routes to `pi_general`.
4. **`sub_profession_type` as secondary routing** — For legal (SECURITIES, CORPORATE_MA, PLAINTIFF, etc.) and accounting (AUDIT_PUBLIC, AUDIT_PRIVATE, TAX, ADVISORY, etc.).
5. **pi_accounting and pi_management_consulting reuse existing 7 groups** — No new group needed; adjusted weights and a few new signals added to existing groups suffice.
6. **All other configs introduce exactly one new profession-specific group** — Keeps the architecture clean and consistent with Phase 5's pattern.
7. **Pricing: all new configs use DECOUPLED** — Only pi_sme uses BUNDLED. New configs use MULTIPLIER on revenue with profession-specific rate tables.

## Document Structure (follow Phase 5 exactly)

1. **Context & Motivation** — Why PI needs expansion (a law firm and an engineering firm share nothing actuarially)
2. **The Thirteen-Configuration Architecture** — Tree diagram + routing table
3. **Configurations 1-11** — Each with: The Underwriting Reality, Signal Architecture Rationale, New Signals table, Pricing Philosophy, Example Company Returns (3 worked examples per config)
4. **Implementation Plan** — What gets built, in what order
5. **Summary of Deliverables** — Numbered list
6. **Signal Registry Confirmation** — All 58 new signals listed by config
7. **Review Resolution Matrix** — How pi_general's known limitations are addressed
8. **Appendix A** — Professional Services Value Chain (13-config diagram)
9. **Appendix B** — Weight Distributions (all 11 new configs, verified R/L/E=1.0)
10. **Appendix C** — Tier Bands (5-tier: PREFERRED/STANDARD_PLUS/STANDARD/SUBSTANDARD/DECLINE with per-config rates)
11. **Appendix D** — Signal Specifications (inference functions, proxy tiers, correlation directions, score conditions)
12. **Appendix E** — Direct Queries (4-7 per config)
13. **Appendix F** — Pricing Anchors & ILF Curves (base limits, deductibles, ILF tables, worked example corrections)
14. **Appendix G** — Routing Resolution (profession_segment pre-routing, gap closure, tie-breaking)
15. **Appendix H** — Minimum Viable Input per Configuration (required/optional fields in YAML)
16. **Appendix I** — Seed Data Plan (3-5 entries per config, signal profiles, seed_dsi_bench.py expansion plan)

## Example Companies for Worked Examples

- **pi_legal_large:** Kirkland & Ellis (T1), White & Case (T2), mid-tier firm with partner exodus (T5)
- **pi_legal_specialist:** Wachtell Lipton (T1, M&A specialist), plaintiff securities boutique (T3), solo practitioner with bar issues (T5)
- **pi_audit:** PricewaterhouseCoopers (T1), BDO USA (T2), mid-tier firm post-restatement scandal (T5)
- **pi_accounting:** RSM US (T1, tax advisory), regional CPA (T3), firm with IRS penalties (T5)
- **pi_architecture:** Gensler (T1), mid-size firm (T3), firm with latent defect history (T5)
- **pi_engineering:** AECOM (T1), mid-tier structural (T3), firm with bridge/infrastructure failure (T5)
- **pi_technology:** Accenture (T1), mid-tier SI (T3), firm with failed ERP implementation litigation (T5)
- **pi_financial_advisory:** Vanguard Personal Advisor (T1), regional RIA (T3), IFA with mis-selling history (T5)
- **pi_management_consulting:** McKinsey & Company (T1), mid-tier strategy firm (T3), firm with advice-failure litigation (T5)
- **pi_real_estate:** CBRE Valuation (T1), regional surveyor (T3), firm with negligent valuation history (T5)
- **pi_environmental:** ERM Group (T1), regional environmental consultant (T3), firm with Superfund liability (T5)

## Pricing Anchor Table

| Configuration | Pricing Type | Base Limit | Base Deductible | Min Premium |
|---|---|---|---|---|
| `pi_general` | DECOUPLED | $1,000,000 | $50,000 | $25,000 |
| `pi_legal_large` | DECOUPLED | $5,000,000 | $250,000 | $100,000 |
| `pi_legal_specialist` | DECOUPLED | $1,000,000 | $50,000 | $25,000 |
| `pi_audit` | DECOUPLED | $10,000,000 | $500,000 | $250,000 |
| `pi_accounting` | DECOUPLED | $1,000,000 | $25,000 | $15,000 |
| `pi_architecture` | DECOUPLED | $1,000,000 | $25,000 | $15,000 |
| `pi_engineering` | DECOUPLED | $2,000,000 | $50,000 | $20,000 |
| `pi_technology` | DECOUPLED | $2,000,000 | $50,000 | $20,000 |
| `pi_financial_advisory` | DECOUPLED | $2,000,000 | $50,000 | $25,000 |
| `pi_management_consulting` | DECOUPLED | $1,000,000 | $50,000 | $25,000 |
| `pi_real_estate` | DECOUPLED | $1,000,000 | $25,000 | $10,000 |
| `pi_environmental` | DECOUPLED | $2,000,000 | $50,000 | $20,000 |
| `pi_sme` | BUNDLED | Per package | Per package | $1,500 |

## Rate Tables (MULTIPLIER on revenue, by tier)

| Configuration | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| `pi_general` | 0.0008 | 0.0012 | 0.0018 | 0.0028 | 0.0045 |
| `pi_legal_large` | 0.0012 | 0.0018 | 0.0028 | 0.0042 | 0.0065 |
| `pi_legal_specialist` | 0.0015 | 0.0022 | 0.0032 | 0.0048 | 0.0075 |
| `pi_audit` | 0.0020 | 0.0030 | 0.0045 | 0.0070 | 0.0110 |
| `pi_accounting` | 0.0010 | 0.0015 | 0.0022 | 0.0035 | 0.0055 |
| `pi_architecture` | 0.0012 | 0.0018 | 0.0026 | 0.0040 | 0.0060 |
| `pi_engineering` | 0.0015 | 0.0022 | 0.0032 | 0.0050 | 0.0080 |
| `pi_technology` | 0.0010 | 0.0015 | 0.0022 | 0.0035 | 0.0055 |
| `pi_financial_advisory` | 0.0012 | 0.0018 | 0.0028 | 0.0042 | 0.0065 |
| `pi_management_consulting` | 0.0006 | 0.0010 | 0.0015 | 0.0024 | 0.0038 |
| `pi_real_estate` | 0.0010 | 0.0015 | 0.0022 | 0.0035 | 0.0055 |
| `pi_environmental` | 0.0014 | 0.0020 | 0.0030 | 0.0046 | 0.0072 |

## Final Instructions

1. Read `phase_5.md` for structure and tone reference
2. Read `coverages/pi/config.yaml` for existing signal architecture
3. Write the complete `phase_6.md` document (2000+ lines) using all specifications above
4. Verify all weight distributions sum to 1.0 for R, L, and E
5. Commit with message: "Add Phase 6 document: PI Coverage Expansion — Full Spectrum Configuration Suite"
6. Push to branch `claude/review-dsi-phase-5-TuTs8`

Do not ask questions. Do not plan. Write the document.

# Phase 7: Cyber Coverage Expansion — Full Spectrum Configuration Suite

## Context & Motivation

Cyber is the fastest-growing and most rapidly evolving coverage class in commercial insurance. Unlike energy (where risk is fundamentally physical) or PI (where risk is fundamentally advisory), cyber risk spans *technical*, *regulatory*, *operational*, *criminal*, and *reputational* dimensions — and the relative importance of each dimension shifts dramatically depending on what the insured organisation *does* and what data it *holds*.

A hospital network running connected medical devices and storing millions of PHI records shares almost nothing — actuarially, operationally, or legally — with a SaaS platform serving enterprise customers, a regional water utility running SCADA systems, or a national retail chain processing millions of card transactions. The threat actors are different. The regulatory regimes are different. The loss mechanics are different. The recovery timelines are different.

Yet today, DSI has only two cyber configurations attempting to price all of it: `cyber_general` for corporate accounts (revenue > $50M) and `cyber_sme` for small businesses (revenue ≤ $50M, ≤ 200 employees). This is the same structural gap that Phase 5 identified in energy and Phase 6 identified in professional indemnity — one general model trying to serve an entire market that is, in actuarial reality, a dozen distinct markets.

### Why This Matters for Production & Demo

1. **Production Pipeline Readiness**: Cyber submissions represent the highest-growth coverage class in the DSI pipeline. Brokers submitting hospitals, banks, technology companies, and manufacturers expect the system to understand their industry's specific cyber risk drivers. A general model that weights `tls_configuration` identically for a cloud-native SaaS company and a manufacturing plant with air-gapped OT networks will produce pricing that no cyber underwriter trusts.

2. **Demo Credibility**: When demonstrating DSI to cyber underwriters at Lloyd's, Beazley, Coalition, or CFC, the system must show it *understands* that a HIPAA breach notification obligation is qualitatively different from a PCI card-replacement liability, which is qualitatively different from a NERC CIP violation. A single configuration cannot make these distinctions. An underwriter who sees the same signal weights applied to Mount Sinai Health System and Shopify will immediately question the model's credibility.

3. **Multiplexer Demonstration**: With twelve cyber configurations at varying `model_specificity` levels (1-4), cyber joins energy and PI as a definitive showcase for the V4 multiplexer's intelligent routing. The `industry_sector` pre-routing field — analogous to energy's `operation_segment` and PI's `profession_segment` — enables precise configuration selection.

4. **Threat Landscape Fidelity**: Cyber insurance pricing is fundamentally driven by threat intelligence. Ransomware groups target healthcare and critical infrastructure disproportionately. Nation-state actors target government and defence supply chains. Financially motivated groups target retail payment systems and financial institutions. Industry-specific configurations allow DSI to encode these threat landscape realities directly into signal architecture, rather than treating all cyber threats as interchangeable.

### Why Industry Sector Is the Right Segmentation Axis

The existing `cyber_general` already acknowledges that industry matters through its `industry_classification` categorical modifier (Healthcare: 1.5x, Financial Services: 1.4x, Energy: 1.2x, etc.). But a flat multiplier cannot capture what actually differs across sectors:

- **Different regulatory regimes**: HIPAA/HITECH for healthcare, PCI-DSS/GLBA/SOX/DORA for financial services, NERC CIP for critical infrastructure, CMMC/FedRAMP for government — each with different fine structures, notification obligations, and compliance evidence requirements.
- **Different threat models**: Ransomware operators specifically target hospitals because they *must* pay to restore patient care. Nation-state actors specifically target utilities because they seek persistent access to critical systems. These are not generic "cyber threats" — they are sector-specific attack campaigns with sector-specific TTPs.
- **Different loss mechanics**: A healthcare breach produces per-record notification costs ($150-$400/record under HIPAA). A manufacturing OT disruption produces per-day production downtime ($500K-$5M/day). A technology company breach produces downstream third-party liability. These loss shapes cannot be captured by a single set of tier bands.
- **Different signal relevance**: `medical_device_connectivity` is critical for healthcare and meaningless for retail. `ot_it_segmentation` is critical for manufacturing and irrelevant to a SaaS company. `pci_compliance_depth` is critical for retail and tangential to a government agency.

Phase 7 replaces flat industry multipliers with purpose-built configurations that encode *why* each sector carries distinct risk — through sector-specific signals, weights, direct queries, and pricing.

---

## The Twelve-Configuration Architecture

```
cyber/
├── cyber_general                      (exists)   specificity=1   Universal fallback (revenue > $50M)
├── cyber_sme                          (exists)   specificity=2   SME automated (revenue ≤ $50M)
│
├── REGULATED DATA-INTENSIVE
│   ├── cyber_healthcare               (new)      specificity=4   Health systems, hospitals, health tech, pharma
│   └── cyber_financial_services       (new)      specificity=4   Banks, insurers, payment processors, fintech
│
├── TECHNOLOGY & DIGITAL
│   ├── cyber_technology               (new)      specificity=3   SaaS, software vendors, MSPs, IT services
│   └── cyber_digital_platform         (new)      specificity=3   Marketplaces, social, media, adtech, platforms
│
├── INDUSTRIAL & INFRASTRUCTURE
│   ├── cyber_critical_infrastructure  (new)      specificity=4   Utilities, telecom, water, transportation
│   └── cyber_manufacturing            (new)      specificity=3   Manufacturing, industrial OT/IT convergence
│
├── COMMERCE
│   └── cyber_retail                   (new)      specificity=3   Retail, e-commerce, hospitality, consumer data
│
├── PUBLIC SECTOR
│   └── cyber_public_sector            (new)      specificity=3   Government, education, nonprofits
│
└── PROFESSIONAL SERVICES
    └── cyber_professional_services    (new)      specificity=2   Law firms, consultancies, accounting practices
```

### Routing Logic

The multiplexer evaluates routing constraints in descending specificity order. The first configuration whose constraints are satisfied wins. `industry_sector` is an optional input field (see Appendix G.1) — when provided, it enables specific routing; when absent, submissions default to `cyber_general`.

| Configuration | Specificity | Routing Constraints | Fallback |
|---|---|---|---|
| `cyber_healthcare` | 4 | `industry_sector == HEALTHCARE` AND `revenue > 50000000` | `cyber_general` |
| `cyber_financial_services` | 4 | `industry_sector == FINANCIAL_SERVICES` AND `revenue > 50000000` | `cyber_general` |
| `cyber_critical_infrastructure` | 4 | `industry_sector IN [UTILITIES, TELECOM, WATER, TRANSPORTATION]` AND `revenue > 50000000` | `cyber_general` |
| `cyber_technology` | 3 | `industry_sector IN [TECHNOLOGY, SOFTWARE, IT_SERVICES, MSP]` | `cyber_general` |
| `cyber_digital_platform` | 3 | `industry_sector IN [DIGITAL_PLATFORM, MEDIA, ADTECH, SOCIAL]` | `cyber_technology` |
| `cyber_manufacturing` | 3 | `industry_sector IN [MANUFACTURING, INDUSTRIAL]` | `cyber_general` |
| `cyber_retail` | 3 | `industry_sector IN [RETAIL, ECOMMERCE, HOSPITALITY]` | `cyber_general` |
| `cyber_public_sector` | 3 | `industry_sector IN [GOVERNMENT, EDUCATION, NONPROFIT]` | `cyber_general` |
| `cyber_professional_services` | 2 | `industry_sector IN [LEGAL, CONSULTING, ACCOUNTING]` AND `revenue > 50000000` | `cyber_general` |
| `cyber_sme` | 2 | `revenue <= 50000000` AND `employee_count <= 200` | `cyber_general` |
| `cyber_general` | 1 | `revenue > 50000000` | — |

### Key Design Decisions

1. **Industry sector as segmentation axis, not product type or threat vector** — Product types (cyber liability, network security, privacy liability, cyber extortion) and threat vectors (ransomware, data breach, business interruption) cut across all industries. What differs fundamentally by industry is the *regulatory regime*, *loss mechanics*, and *signal relevance*. A healthcare ransomware event and a manufacturing ransomware event are both ransomware — but the notification obligations, recovery constraints, and loss quantification are entirely different.

2. **`industry_sector` as pre-routing field** — Mirrors energy's `operation_segment` and PI's `profession_segment`. Optional input. When absent, routes to `cyber_general`. No secondary routing field required — unlike PI where intra-profession variance (e.g., securities law vs. real estate law) warranted `sub_profession_type`, cyber's intra-industry variance is captured adequately through signal weighting and direct queries.

3. **Three configs at specificity 4** — Healthcare, financial services, and critical infrastructure carry the most distinct regulatory, threat, and loss profiles. Each introduces a dedicated signal group with signals that are meaningless outside their sector (e.g., `medical_device_connectivity` for healthcare, `swift_controls` for financial services, `ot_it_segmentation` for critical infrastructure).

4. **`cyber_digital_platform` falls back to `cyber_technology`** — Digital platforms are a subspecialty of technology risk. If the multiplexer cannot route to `cyber_digital_platform` (e.g., missing `industry_sector` detail), `cyber_technology` provides the next-best fit. All other configs fall back to `cyber_general`.

5. **`cyber_professional_services` at specificity 2** — Professional services cyber risk is less technically differentiated than healthcare or financial services. The primary distinction is client data confidentiality and downstream advisory liability, which requires weight adjustment on existing groups rather than entirely new signal architecture. This parallels PI's `pi_management_consulting` at specificity 2.

6. **Geographic variance via modifiers, not separate configs** — US state-by-state breach notification loading, UK ICO fine exposure, EU GDPR/NIS2 overlay, and APAC regulatory variance are handled as jurisdiction modifiers within each config. Otherwise we would need 40+ configurations.

7. **Product type expansion per config** — Several configs introduce sector-specific product types (`regulatory_defense` for healthcare, `business_interruption_ot` for critical infrastructure, `tech_errors_omissions` for technology, `crime_cyber` for financial services) that reflect coverage forms actually sold in those markets. This is not scope creep — these are real products that brokers submit and underwriters price.

### Signal Group Summary

| Group | Status | Used By |
|---|---|---|
| `network_authority` | Existing | All configs (weight adjustment per sector) |
| `technical_infrastructure` | Existing | All configs (weight adjustment per sector) |
| `public_record` | Existing | All configs (weight adjustment per sector) |
| `structured_data` | Existing | All configs (weight adjustment per sector) |
| `corporate_footprint` | Existing | All configs (weight adjustment per sector) |
| `health_data_security` | **New** | `cyber_healthcare` |
| `financial_system_security` | **New** | `cyber_financial_services` |
| `operational_technology` | **New** | `cyber_critical_infrastructure` (primary), `cyber_manufacturing` (reuse, adjusted weights) |
| `software_security_posture` | **New** | `cyber_technology` (primary), `cyber_digital_platform` (reuse, adjusted weights) |
| `payment_data_security` | **New** | `cyber_retail` |
| `public_sector_governance` | **New** | `cyber_public_sector` |

Six new signal groups. Four configs reuse existing or other new groups with adjusted weights (`cyber_digital_platform` reuses `software_security_posture`, `cyber_manufacturing` reuses `operational_technology`, `cyber_professional_services` and `cyber_sme` use only existing groups).

### New Signals Summary

Approximately 65 new signals across the 10 new configurations, distributed as follows:

| Config | New Signals | New Group | Reused Groups |
|---|---|---|---|
| `cyber_healthcare` | ~8 | `health_data_security` | All 5 existing (adjusted weights) |
| `cyber_financial_services` | ~8 | `financial_system_security` | All 5 existing (adjusted weights) |
| `cyber_critical_infrastructure` | ~8 | `operational_technology` | All 5 existing (adjusted weights) |
| `cyber_technology` | ~8 | `software_security_posture` | All 5 existing (adjusted weights) |
| `cyber_digital_platform` | ~6 | — | `software_security_posture` + 5 existing (adjusted weights) |
| `cyber_manufacturing` | ~7 | — | `operational_technology` + 5 existing (adjusted weights) |
| `cyber_retail` | ~7 | `payment_data_security` | All 5 existing (adjusted weights) |
| `cyber_public_sector` | ~6 | `public_sector_governance` | All 5 existing (adjusted weights) |
| `cyber_professional_services` | ~4 | — | All 5 existing (adjusted weights) |
| `cyber_sme` | 0 | — | Unchanged |
| **Total** | **~62-68** | **6 new** | |

---

## Configuration 1: `cyber_healthcare`

### The Underwriting Reality

Healthcare is the most expensive sector to insure for cyber risk — and for good reason. The average cost of a healthcare data breach is $10.9M (IBM 2023), more than double the cross-industry average. Ransomware groups specifically target hospitals because clinical operations *cannot* be deferred: a hospital that loses access to its EHR system faces immediate patient safety consequences, creating maximum payment pressure. The intersection of life-critical operations, vast PHI datasets, connected medical devices, and one of the most punitive regulatory regimes in existence (HIPAA/HITECH) makes healthcare cyber a class unto itself.

The key insight: **in healthcare cyber, the data sensitivity AND the operational criticality create compound exposure**. A retail breach exposes payment card data (replaceable). A healthcare breach exposes protected health information (irreplaceable — you cannot reissue a patient's medical history). Simultaneously, a ransomware event at a hospital doesn't just lock files — it diverts ambulances, delays surgeries, and can directly contribute to patient mortality. No other sector faces this dual exposure.

The existing `cyber_general` handles healthcare through a flat 1.5x `industry_classification` modifier. This captures none of the sector-specific signal architecture:

1. **Medical device connectivity** — Connected infusion pumps, MRI systems, and ventilators running embedded operating systems (often unpatched Windows XP/7) create an attack surface that has no analogue in other industries. The FDA's premarket cybersecurity guidance and postmarket surveillance requirements are sector-specific regulatory obligations.
2. **EHR system architecture** — The concentration of PHI in electronic health record systems (Epic, Cerner, Meditech) creates catastrophic single-point-of-failure exposure. EHR downtime procedures, redundancy architecture, and vendor security posture are directly predictive of recovery time.
3. **HIPAA compliance depth** — HIPAA is not a checkbox. The difference between a health system that has completed a genuine NIST CSF-aligned risk analysis and one that filed a boilerplate compliance document is the difference between Tier 1 and Tier 4. OCR enforcement data, corrective action plans, and breach notification history are publicly observable.
4. **Clinical network segmentation** — The degree to which clinical networks (medical devices, EHR terminals, imaging systems) are segmented from administrative IT and guest networks is the single most predictive architectural signal for ransomware blast radius in healthcare.

### Signal Architecture Rationale

**Primary driver: Health Data Security — NEW GROUP (Risk: 0.25, Loss: 0.30, Exposure: 0.15 = 0.70 combined)**

This is the sector-specific group that justifies `cyber_healthcare` as a distinct configuration. It contains signals that are meaningless outside healthcare but are the dominant risk drivers within it: medical device connectivity posture, EHR system resilience, PHI data governance, HIPAA compliance depth, and clinical network segmentation. The 0.30 Loss weight reflects that PHI breach costs are deterministic — HIPAA mandates $100-$50,000 per record in civil penalties, and OCR enforcement is not discretionary.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

The standard technical infrastructure signals (TLS, headers, email auth, CVE exposure, etc.) remain relevant but are *deprioritised* relative to `cyber_general`. In healthcare, a perfect TLS configuration on the public website matters far less than whether the radiology PACS system is running on an isolated VLAN. The weight reduction from `cyber_general`'s ~0.50 combined to 0.40 reflects this shift in relevance.

**Elevated: Public Record (Risk: 0.20, Loss: 0.15, Exposure: 0.10 = 0.45 combined)**

Healthcare breach history is the richest public record dataset in cyber insurance. The HHS Breach Portal ("Wall of Shame") publishes every HIPAA breach affecting 500+ individuals, including entity name, breach type, records affected, and date. OCR enforcement actions, corrective action plans, and state attorney general settlements are all public. This data density justifies elevated Public Record weight relative to `cyber_general`.

**Deprioritised: Corporate Footprint, Network Authority**

In healthcare cyber, we care less about whether the hospital has a security.txt file or a bug bounty programme (most don't — and that's fine). We care about whether the infusion pump firmware is current and whether the clinical network is segmented.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `medical_device_connectivity` | INFERRED_PROXY | health_data_security | Connected medical device inventory and security posture. FDA Class II/III devices running embedded OS are the primary attack vector for healthcare-specific compromise. Observable through Shodan, device manufacturer disclosures, and FDA recall/advisory databases. |
| `ehr_system_resilience` | INFERRED_PROXY | health_data_security | EHR platform identification (Epic, Cerner, Meditech), hosting model (on-prem vs cloud), backup architecture, and documented downtime procedures. EHR downtime duration is the primary driver of business interruption severity in healthcare. |
| `hipaa_compliance_depth` | DIRECT_OBSERVABLE | health_data_security | OCR audit history, corrective action plans, breach notification filings, NIST CSF alignment attestation. Goes beyond the binary `phi_handler` direct query in `cyber_general` to assess *how well* HIPAA obligations are met. |
| `clinical_network_segmentation` | INFERRED_PROXY | health_data_security | Degree of isolation between clinical device networks, administrative IT, and guest/public networks. Observable through network scan patterns, VLAN evidence in DNS/certificate data, and published network architecture documentation. The single most predictive architectural signal for ransomware blast radius. |
| `phi_data_volume` | INFERRED_PROXY | health_data_security | Estimated volume of PHI records under management. Directly determines notification cost exposure ($150-$400/record). Observable through reported patient volumes, bed counts, annual visit data, and published statistics. |
| `hhs_breach_portal_history` | DIRECT_OBSERVABLE | health_data_security | Historical entries on the HHS Breach Portal. Unlike the generic `breach_history` signal in `cyber_general`, this is healthcare-specific and includes breach type categorisation (hacking/IT incident, unauthorised access, theft, loss) and records affected. |
| `medical_device_patching_cadence` | INFERRED_PROXY | health_data_security | Frequency and currency of medical device firmware/OS updates. FDA postmarket cybersecurity guidance requires ongoing patching, but many devices run on manufacturer-controlled update cycles. Observable through CVE exposure cross-referenced with known healthcare device manufacturers. |
| `telehealth_exposure` | INFERRED_PROXY | health_data_security | Extent of telehealth/remote care platform deployment. Telehealth expanded attack surface dramatically post-COVID. Observable through published telehealth service listings, app store presence, and third-party platform partnerships. |

### Direct Queries (Healthcare-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_healthcare` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `phi_encryption_at_rest` | Is all PHI encrypted at rest across all storage systems? | `false` → | REFER override: 4. Unencrypted PHI at rest is a HIPAA violation and dramatically increases breach severity. |
| `medical_device_inventory` | Do you maintain a complete inventory of all connected medical devices? | `false` → | FLAG. Without device inventory, segmentation and patching claims are unverifiable. |
| `ehr_downtime_procedures` | Are documented EHR downtime procedures tested at least annually? | `false` → | FLAG. Untested downtime procedures extend business interruption duration by 2-5x. |
| `hipaa_risk_analysis` | Has a NIST CSF-aligned HIPAA risk analysis been completed in the past 12 months? | `false` → | MODIFIER applied: 1.20. Absence of current risk analysis is the #1 OCR enforcement trigger. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0030** (0.30%) — a 50% premium over `cyber_general`'s 0.20%. Reflects the sector's 2x average breach cost, HIPAA notification obligations, and ransomware targeting frequency.
- **Product types**: `cyber_liability`, `privacy_liability`, `regulatory_defense`, `network_security`
  - `regulatory_defense` is new: covers OCR investigation costs, HIPAA penalty defense, and state AG enforcement response. This is a real coverage form sold by Beazley, CFC, and Coalition for healthcare accounts.
- **ILF Curves**: Steeper than `cyber_general` above $10M limits. Healthcare severity tail is heavier due to class action exposure following mass PHI breaches (e.g., Anthem $115M settlement, Premera $74M settlement).
- **Deductible**: Higher minimum deductible ($100K vs $50K in `cyber_general`). Healthcare claims almost never fall below $100K due to mandatory notification costs.
- **Geographic modifiers**:
  - US: 1.0 (base — HIPAA is the reference regulatory regime)
  - UK: 0.90 (NHS cyber is centrally managed; private healthcare sector is smaller)
  - EU: 1.10 (GDPR health data provisions are stricter than standard GDPR; cross-border notification complexity)
  - APAC: 1.05 (emerging healthcare data protection regimes; lower litigation frequency)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Mayo Clinic** — Integrated academic health system
> - Revenue: $16.3B | Limit: $100M | Score: 871
> - Why: Industry-leading cybersecurity programme (dedicated CISO, published security practices), Epic EHR fully cloud-hosted, comprehensive medical device management programme, zero HHS breach portal entries in 5 years, HITRUST CSF certified, clinical network segmentation verified, active bug bounty programme (rare in healthcare)
> - Premium: $16.3B × 0.0010 × ILF(100M) = **~$16.3M base** before modifiers
> - Modifiers: Geographic (US: 1.0), Size band (ENTERPRISE: adjusted), HIPAA risk analysis (current: no modifier) → **Net premium: ~$14.5M**

**Tier 3 — STANDARD (Refer):**
> **Regional Health System** (composite — 5-hospital system, mid-Atlantic US)
> - Revenue: $2.8B | Limit: $25M | Score: 548
> - Why: Mixed security posture — Epic EHR (positive) but on-premises hosting with aging backup infrastructure, 12,000+ connected medical devices with incomplete inventory, one HHS breach portal entry (3,200 records, unauthorized access, 2022), HIPAA risk analysis completed but 18 months old, clinical network partially segmented
> - Referral reasons: `medical_device_connectivity <= 35`, `hipaa_compliance_depth <= 45`, `clinical_network_segmentation <= 40`
> - Premium: $2.8B × 0.0020 × ILF(25M) = **~$5.6M base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Rural Hospital Network** (composite — deterioration scenario)
> - Revenue: $340M | Limit: $10M | Score: 268
> - Why: Legacy Meditech EHR on-premises with no tested downtime procedures, 2 HHS breach portal entries in 3 years (8,400 and 22,000 records — ransomware), connected medical devices running Windows 7 with no segmentation, no HIPAA risk analysis on file, MFA not enabled for remote access (direct query REFER), no incident response plan, PHI encryption at rest not implemented (REFER)
> - Decline triggers: `health_data_security` group score <= 20, multiple REFER conditions from direct queries, `breach_history <= 25`

---

## Configuration 2: `cyber_financial_services`

### The Underwriting Reality

Financial services is the second-most targeted sector for cyber attack and the most heavily regulated. Banks, insurers, payment processors, and fintech companies operate under a regulatory patchwork — PCI-DSS for card data, GLBA/SOX for US financial institutions, DORA for EU firms, FCA/PRA for UK-regulated entities — that creates compliance obligations with no parallel in other industries. The consequence of breach is not merely notification cost (as in healthcare) but *systemic financial risk*: a compromised SWIFT interface, a manipulated trading system, or a breached payment processor can produce cascading losses across counterparties.

The key insight: **in financial services cyber, the regulatory exposure AND the systemic interconnectedness create compound risk**. A healthcare breach is contained to one organisation's patients. A financial services breach can propagate through payment networks, correspondent banking relationships, and settlement systems. The 2016 Bangladesh Bank SWIFT heist ($81M stolen, $951M attempted) demonstrated that a single compromised endpoint in a financial institution can generate losses that dwarf the institution's own balance sheet through downstream systemic effects.

The existing `cyber_general` handles financial services through a flat 1.4x `industry_classification` modifier. This captures none of the sector-specific dynamics:

1. **Payment system architecture** — The topology of payment processing (card-present, card-not-present, ACH, wire, SWIFT, real-time payments) directly determines fraud exposure and regulatory scope. A bank running SWIFT with dual-control and out-of-band verification is fundamentally different from one with single-operator SWIFT access. Observable through published payment capabilities, SWIFT CSP attestation, and PCI compliance documentation.
2. **Regulatory compliance depth** — Financial services faces overlapping regulatory regimes. PCI-DSS compliance is not binary — there are four merchant levels with different validation requirements. SOX IT general controls (ITGCs) are audited annually for public companies. DORA's ICT risk management requirements are prescriptive. The *depth* of compliance, not merely its existence, is predictive.
3. **Third-party/vendor concentration** — Financial services outsources extensively: core banking platforms (FIS, Fiserv, Jack Henry), payment processing (Visa, Mastercard networks), cloud infrastructure, and managed security. A single vendor compromise (e.g., the MOVEit breach affecting financial sector file transfer) can impact hundreds of institutions simultaneously. Vendor concentration is a systemic risk signal.
4. **Transaction fraud controls** — The sophistication of real-time transaction monitoring, anomaly detection, and fraud prevention systems is directly predictive of both frequency (fraud events) and severity (fraud losses). These controls are observable through published capabilities, regulatory examination reports, and vendor relationships.

### Signal Architecture Rationale

**Primary driver: Financial System Security — NEW GROUP (Risk: 0.25, Loss: 0.25, Exposure: 0.20 = 0.70 combined)**

This is the sector-specific group containing signals unique to financial services: payment system architecture, SWIFT/messaging security, PCI compliance depth, transaction fraud controls, core banking platform resilience, and regulatory examination history. The 0.20 Exposure weight is elevated because financial services exposure scales with transaction volume and interconnectedness, not merely with revenue or employee count.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Standard technical signals remain relevant — financial institutions' public-facing infrastructure (online banking, mobile apps, API gateways) is a primary attack surface. However, the weight is reduced from `cyber_general` because the *internal* payment and trading infrastructure (captured by `financial_system_security`) is where the catastrophic exposure lives.

**Elevated: Structured Data (Risk: 0.15, Loss: 0.10, Exposure: 0.10 = 0.35 combined)**

Financial institutions are the most rated sector: SecurityScorecard, BitSight, credit ratings, and regulatory examination grades all provide structured third-party assessments. These are more reliable for financial services than for any other sector because the rating agencies have deep financial sector benchmarks. Elevated from `cyber_general`'s ~0.25 combined.

**Elevated: Network Authority (Risk: 0.10, Loss: 0.10, Exposure: 0.10 = 0.30 combined)**

Financial services network relationships (correspondent banking, payment network membership, clearing house participation) directly determine systemic exposure. A bank that is a major CHIPS participant has fundamentally different interconnection risk than a community bank.

**Deprioritised: Corporate Footprint**

Financial institutions publish security pages, privacy policies, and compliance documentation as a matter of regulatory obligation. These signals carry less discriminatory power in financial services than in other sectors because even poorly-secured banks maintain public-facing compliance documentation.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `payment_system_architecture` | INFERRED_PROXY | financial_system_security | Topology and security controls of payment processing systems (card networks, ACH, wire, SWIFT, real-time payments). Observable through published payment capabilities, SWIFT CSP attestation, and PCI compliance level. The primary determinant of fraud and transaction-based loss exposure. |
| `swift_controls` | INFERRED_PROXY | financial_system_security | SWIFT Customer Security Programme (CSP) attestation status and compliance level. SWIFT's mandatory security controls (26 controls, 7 principles) are specifically designed to prevent repeat Bangladesh Bank-style attacks. Observable through SWIFT's KYC-SA (Know Your Customer Security Attestation) registry. |
| `pci_compliance_depth` | DIRECT_OBSERVABLE | financial_system_security | PCI-DSS compliance level (1-4), last assessment date, QSA identity, and scope (which card brands, which channels). Goes far beyond the binary `pci_scope` direct query in `cyber_general`. Level 1 merchants (>6M transactions) require annual on-site QSA audit; Level 4 merchants self-assess. Observable through PCI Council registries and published compliance documentation. |
| `transaction_fraud_controls` | INFERRED_PROXY | financial_system_security | Sophistication of real-time transaction monitoring, anomaly detection, and fraud prevention. Observable through published fraud prevention capabilities, vendor relationships (e.g., Featurespace, Feedzai, FICO), and regulatory examination commentary. |
| `core_banking_resilience` | INFERRED_PROXY | financial_system_security | Core banking platform identification (FIS, Fiserv, Jack Henry, Temenos, in-house), hosting model, disaster recovery architecture, and documented failover capabilities. Core banking downtime is the primary driver of business interruption severity in financial services. |
| `regulatory_examination_history` | DIRECT_OBSERVABLE | financial_system_security | OCC, FDIC, Fed, FCA/PRA examination results related to IT risk management, cybersecurity, and operational resilience. MRA (Matters Requiring Attention) and MRIA (Matters Requiring Immediate Attention) findings are publicly observable for enforcement actions. |
| `vendor_concentration_risk` | INFERRED_PROXY | financial_system_security | Concentration of critical technology services among third-party vendors. Financial services outsourcing is extensive — a single vendor compromise (MOVEit, SolarWinds) can impact hundreds of institutions. Observable through published vendor relationships, SEC filings, and technology stack analysis. |
| `cyber_insurance_tower` | INFERRED_PROXY | financial_system_security | Existence and structure of the insured's own cyber insurance programme. Financial institutions that maintain robust cyber insurance towers demonstrate risk awareness and have undergone prior underwriting scrutiny. Observable through published annual reports and regulatory filings. |

### Direct Queries (Financial Services-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_financial_services` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `swift_csp_compliant` | Are you SWIFT CSP compliant with independent assessment? | `false` → | REFER override: 4. Non-compliance with SWIFT CSP mandatory controls indicates systemic payment security failure. |
| `real_time_fraud_monitoring` | Do you operate real-time transaction fraud monitoring across all payment channels? | `false` → | MODIFIER applied: 1.25. Absence of real-time monitoring dramatically increases fraud loss severity. |
| `third_party_risk_programme` | Do you maintain a formal third-party/vendor cyber risk management programme? | `false` → | FLAG. Vendor concentration without formal risk management is the primary supply chain exposure in financial services. |
| `segregation_of_duties` | Are IT privileged access controls subject to segregation of duties with independent audit? | `false` → | MODIFIER applied: 1.15. Privileged access without segregation is the primary insider threat vector in financial services. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0028** (0.28%) — a 40% premium over `cyber_general`'s 0.20%. Reflects the sector's regulatory fine exposure (GDPR fines for financial institutions average 3x cross-industry), systemic interconnectedness, and elevated threat actor sophistication (nation-state and organised crime targeting).
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `crime_cyber`
  - `crime_cyber` is new: covers losses from fraudulent electronic fund transfers, social engineering fraud (CEO fraud/BEC), and unauthorised transaction losses. This is a real coverage form — distinct from traditional crime/fidelity policies — offered by AIG, Chubb, and Beazley for financial institution accounts.
- **ILF Curves**: Steeper than `cyber_general` above $25M limits. Financial services severity tail is driven by regulatory fines (GDPR: up to 4% of global turnover), class action settlements (Equifax: $575M), and systemic fraud losses.
- **Deductible**: Higher minimum deductible ($250K vs $50K in `cyber_general`). Financial services claims are high-severity by nature; sub-$250K events are typically absorbed within operational risk budgets.
- **Geographic modifiers**:
  - US: 1.0 (base — deepest regulatory and litigation environment)
  - UK: 1.10 (FCA/PRA cyber resilience requirements are among the most prescriptive globally; ICO enforcement active against financial firms)
  - EU: 1.15 (DORA introduces binding ICT risk requirements from January 2025; GDPR financial sector fines are sector-leading)
  - APAC: 0.95 (MAS Technology Risk Management Guidelines are robust but enforcement is less aggressive; lower litigation frequency)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **JPMorgan Chase** — Global systemically important bank (G-SIB)
> - Revenue: $158B | Limit: $500M | Score: 889
> - Why: $15B+ annual technology spend, 62,000+ technologists, industry-leading security operations (one of few banks to operate a dedicated Cyber Fusion Centre), SWIFT CSP fully compliant with independent assessment, PCI Level 1 compliant, zero material breaches in 5 years (post-2014 remediation), OCC examination clean, comprehensive vendor risk programme, published NIST CSF alignment
> - Premium: $158B × 0.0004 × ILF(500M) = **~$63.2M base** before modifiers
> - Modifiers: Geographic (US: 1.0), Size band (ENTERPRISE: adjusted), Strong controls (0.80) → **Net premium: ~$50.6M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Tier Regional Bank** (composite — $15B assets, Southeast US)
> - Revenue: $2.1B | Limit: $50M | Score: 534
> - Why: FIS core banking platform (adequate but aging), PCI Level 2 compliant, SWIFT CSP compliant but self-assessed (not independently validated), one MRA from OCC examination (IT change management deficiencies), moderate vendor concentration (85% of critical IT services from 3 vendors), adequate but not leading fraud monitoring capabilities
> - Referral reasons: `swift_controls <= 40` (self-assessment only), `vendor_concentration_risk <= 35`, `regulatory_examination_history <= 45`
> - Premium: $2.1B × 0.0018 × ILF(50M) = **~$3.8M base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Distressed Fintech Payment Processor** (composite — deterioration scenario)
> - Revenue: $890M | Limit: $25M | Score: 241
> - Why: 2 material breaches in 18 months (card data exposure affecting 2.3M accounts), PCI compliance lapsed (failed last QSA assessment), real-time fraud monitoring absent for CNP channel, 3 regulatory enforcement actions (CFPB, state regulators), core platform running end-of-life software, single cloud provider with no documented DR, MFA not enabled for administrative access (direct query REFER)
> - Decline triggers: `financial_system_security` group score <= 20, `pci_compliance_depth <= 15`, multiple REFER conditions from direct queries, `breach_history <= 20`

---

## Configuration 3: `cyber_critical_infrastructure`

### The Underwriting Reality

Critical infrastructure — electric utilities, water/wastewater systems, oil & gas pipelines, telecommunications carriers, transportation networks — occupies a unique position in cyber insurance: **the primary risk is not data breach but physical consequence**. When Colonial Pipeline was ransomwared in May 2021, the salient loss was not the 100GB of exfiltrated data or even the $4.4M ransom paid — it was the physical shutdown of 5,500 miles of pipeline that supplies 45% of the US East Coast's fuel, producing fuel shortages, flight disruptions, and a national emergency declaration. When the Oldsmar, Florida water treatment plant was compromised in February 2021, the attacker attempted to increase sodium hydroxide (lye) levels to 111x the normal concentration — a change that, if undetected, would have poisoned the water supply serving 15,000 people.

This is the fundamental distinction: **in critical infrastructure, cyber risk IS physical risk**. The convergence of IT (information technology) and OT (operational technology) networks means that a compromise of business systems can propagate to industrial control systems (ICS), SCADA (supervisory control and data acquisition) systems, PLCs (programmable logic controllers), and RTUs (remote terminal units) that directly control physical processes — generating electricity, treating water, pressurising pipelines, routing telecommunications, managing rail signals.

The existing `cyber_general` configuration is structurally incapable of pricing critical infrastructure because:

1. **IT/OT convergence architecture** — The degree to which IT and OT networks are segmented (air-gapped, firewalled, or converged) is the single most important risk factor. A fully air-gapped OT network (increasingly rare but still found in nuclear facilities and defence installations) has fundamentally different exposure than a converged IT/OT network with shared Active Directory credentials. Observable through published operational architecture, regulatory filings (NERC CIP compliance documentation for electric utilities), and technology vendor relationships.
2. **Industrial control system vintage** — ICS/SCADA systems have lifecycles measured in decades, not years. A water utility running Siemens S7-300 PLCs from 2003 (which cannot be patched and run proprietary protocols without authentication) has different exposure than one running modern S7-1500s with TLS encryption and certificate-based authentication. The installed base of legacy ICS is the dominant vulnerability in critical infrastructure. Observable through vendor relationships, capital expenditure disclosures, and regulatory compliance documentation.
3. **Physical consequence severity** — The potential physical consequences of a successful cyber-physical attack vary enormously: a compromised traffic signal system produces different severity than a compromised nuclear reactor cooling system. The physical consequence ceiling determines the severity tail, and it is sector-specific within critical infrastructure. Observable through the nature of the physical process controlled, regulatory classification, and published safety analysis.
4. **Regulatory regime** — Critical infrastructure is regulated by sector-specific agencies with prescriptive cybersecurity requirements: NERC CIP for electric utilities (mandatory, auditable, with $1M/day penalties), TSA Pipeline Security Directives (mandatory since 2021), EPA Water Sector Cybersecurity requirements, NRC 10 CFR 73.54 for nuclear facilities. Compliance with these regimes is directly predictive and publicly observable.
5. **Nation-state threat concentration** — Critical infrastructure is disproportionately targeted by nation-state actors (Volt Typhoon/PRC pre-positioning in US water and energy infrastructure, Sandworm/Russia targeting Ukrainian power grid, TRITON/TRISIS targeting Saudi petrochemical safety systems). The threat actor sophistication ceiling is higher than any other sector.

### Signal Architecture Rationale

**Primary driver: OT/ICS Security — NEW GROUP (Risk: 0.30, Loss: 0.25, Exposure: 0.20 = 0.75 combined)**

This is the dominant group, weighted higher than any primary group in any other configuration. It captures the signals unique to operational technology environments: IT/OT segmentation architecture, ICS/SCADA system vintage and patch status, safety instrumented system (SIS) independence, physical consequence modelling, and OT-specific incident response capability. The 0.30 Risk weight reflects that OT/ICS security posture is the overwhelmingly dominant predictor of both attack likelihood and attack success in critical infrastructure. The 0.20 Exposure weight reflects that physical consequence severity (explosion, contamination, blackout, service disruption) scales with the physical process controlled, not merely with revenue.

**Secondary driver: Technical Infrastructure (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Significantly reduced from `cyber_general`. IT infrastructure remains relevant (email security, endpoint protection, identity management) because IT compromise is the initial access vector in most OT attacks (the "IT-to-OT pivot"). But the *severity* of an attack depends on OT controls, not IT controls. A critical infrastructure entity with excellent IT security and poor OT segmentation is more dangerous to insure than one with mediocre IT security and robust OT air-gapping.

**Elevated: Regulatory & Compliance (Risk: 0.10, Loss: 0.10, Exposure: 0.10 = 0.30 combined)**

New group. Critical infrastructure regulatory compliance (NERC CIP, TSA directives, EPA requirements, NRC regulations) is mandatory, audited, and carries substantial penalties. Compliance status is publicly observable (NERC publishes enforcement actions with penalties) and is a strong predictor of security posture because the regulations are prescriptive about specific technical controls, not merely about governance frameworks.

**Retained: Structured Data (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Third-party ratings (SecurityScorecard, BitSight) remain relevant but are weighted lower because they primarily assess IT-facing infrastructure and have limited visibility into OT environments. Their value is as a sanity check on IT hygiene, not as a primary OT security signal.

**Deprioritised: Corporate Footprint, Network Authority**

Corporate website signals and network authority metrics are the least informative for critical infrastructure. Many utilities and infrastructure operators have minimal public web presence. Network authority (domain authority, backlink profile) is essentially meaningless for a rural electric cooperative or a municipal water utility.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `it_ot_segmentation` | INFERRED_PROXY | ot_ics_security | Architecture of IT/OT network segmentation: air-gapped, unidirectional gateway (data diode), firewalled DMZ, or converged. This is the single most predictive signal in critical infrastructure cyber. Air-gapped OT networks are nearly immune to IT-originated attacks; converged networks are fully exposed. Observable through published architecture diagrams, vendor relationships (Waterfall Security, Claroty, Dragos), regulatory compliance documentation, and NERC CIP audit results. |
| `ics_scada_vintage` | INFERRED_PROXY | ot_ics_security | Age and patchability of industrial control systems. Systems >15 years old typically run proprietary protocols without authentication, cannot be patched, and rely on obscurity for security. Observable through vendor relationships (Siemens, Honeywell, ABB, Emerson, Schneider Electric), capital expenditure disclosures, and published modernisation programmes. |
| `safety_instrumented_system` | INFERRED_PROXY | ot_ics_security | Independence and integrity of safety instrumented systems (SIS) — the last line of defence preventing physical catastrophe. The TRITON/TRISIS attack targeted Schneider Electric Triconex SIS controllers specifically to disable safety shutdowns before causing physical damage. SIS must be independent from the process control system and from the IT network. Observable through safety case documentation, IEC 61511 compliance, and published safety architecture. |
| `physical_consequence_ceiling` | DIRECT_OBSERVABLE | ot_ics_security | Maximum credible physical consequence of a successful cyber-physical attack: service disruption (telecommunications outage), environmental release (chemical/petrochemical), public safety (water contamination, gas explosion), or mass casualty (nuclear, dam). Determines the severity tail cap. Observable from the nature of the physical process, regulatory classification, and published safety analysis. |
| `ot_incident_response` | INFERRED_PROXY | ot_ics_security | OT-specific incident response capability. Standard IT incident response (isolate, contain, eradicate, recover) cannot be applied to OT environments — you cannot "isolate" a running blast furnace or "reboot" a nuclear reactor. OT IR requires specialised knowledge of physical processes, safe shutdown procedures, and manual override capability. Observable through published IR plans, Dragos/Claroty partnerships, OT-specific IR retainer agreements, and CISA coordination. |
| `nerc_cip_compliance` | DIRECT_OBSERVABLE | regulatory_compliance | NERC CIP compliance status for electric utilities (mandatory for Bulk Electric System operators). NERC publishes enforcement actions including violation details and penalties. Low/medium/high impact BES asset categorisation determines which CIP standards apply. Observable through NERC's public enforcement database and published compliance certifications. |
| `tsa_pipeline_compliance` | DIRECT_OBSERVABLE | regulatory_compliance | TSA Pipeline Security Directive compliance (mandatory since May 2021 for critical pipeline operators). Directives require: (1) designation of Cybersecurity Coordinator, (2) reporting of cybersecurity incidents to CISA, (3) cybersecurity assessment, (4) implementation of specific mitigation measures. Observable through TSA publications and operator attestations. |
| `sector_specific_regulation` | INFERRED_PROXY | regulatory_compliance | Compliance with sector-specific cyber regulations beyond NERC CIP and TSA: EPA Water Sector requirements, NRC 10 CFR 73.54 (nuclear), FAA cybersecurity requirements (aviation), FCC CSRIC (telecommunications). Observable through regulatory filings and published compliance documentation. |
| `scada_network_monitoring` | INFERRED_PROXY | ot_ics_security | Deployment of OT-specific network monitoring and anomaly detection (Dragos Platform, Claroty CTD, Nozomi Guardian, Forescout eyeInspect). Traditional IT security tools (EDR, SIEM) cannot parse OT protocols (Modbus, DNP3, IEC 61850, OPC-UA) and are blind to OT-specific attacks. Observable through vendor relationships and published security architecture. |
| `redundancy_manual_override` | INFERRED_PROXY | ot_ics_security | Availability of manual override capability and physical redundancy for critical processes. The ultimate mitigation for cyber-physical risk is the ability to operate critical systems manually when digital controls are compromised. Observable through published operational procedures, regulatory filings, and safety documentation. |

### Direct Queries (Critical Infrastructure-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_critical_infrastructure` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `ot_network_segmented` | Are your OT/ICS networks segmented from corporate IT networks with at minimum a firewalled DMZ or unidirectional gateway? | `false` → | REFER override: 4. Converged IT/OT without segmentation is the single highest-risk condition in critical infrastructure. |
| `sis_independent` | Are your safety instrumented systems (SIS) architecturally independent from process control and IT networks? | `false` → | REFER override: 4. Non-independent SIS means a single compromise can both cause physical damage AND disable safety protections (TRITON scenario). |
| `ot_patching_programme` | Do you maintain a documented OT patching programme with compensating controls for unpatchable systems? | `false` → | MODIFIER applied: 1.30. Unpatchable OT systems without compensating controls (network segmentation, application whitelisting, monitoring) represent persistent exploitable vulnerabilities. |
| `manual_override_capability` | Can critical physical processes be operated manually if digital control systems are compromised? | `false` → | FLAG + MODIFIER applied: 1.20. Absence of manual override means cyber compromise directly produces physical consequence with no human intervention possible. |
| `cisa_coordination` | Do you participate in CISA's sector-specific information sharing (ISAC/ISAO) and have established communication channels for incident coordination? | `false` → | FLAG. Non-participation in sector ISAC indicates isolation from threat intelligence sharing and coordinated response capabilities. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`, but with SIGNIFICANT sector-specific adjustments
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0035** (0.35%) — a 75% premium over `cyber_general`'s 0.20%. Reflects the physical consequence severity tail, nation-state threat concentration, and the structural difficulty of securing legacy OT environments.
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `business_interruption_cyber`, `bodily_injury_cyber`
  - `business_interruption_cyber` is the primary coverage for critical infrastructure — Colonial Pipeline's losses were overwhelmingly BI, not data breach costs. BI sublimits should be at least 50% of the aggregate limit.
  - `bodily_injury_cyber` is a new coverage form reflecting the physical consequence risk: water contamination, gas explosion, chemical release. This coverage is typically excluded from standard cyber policies but is specifically endorsed for critical infrastructure accounts by specialist markets (Beazley, AIG, Swiss Re Corporate Solutions).
- **ILF Curves**: Significantly steeper than `cyber_general` above $50M limits. Critical infrastructure severity distributions have extreme tails driven by physical consequence scenarios — a single event (grid blackout, pipeline explosion, water contamination) can generate losses in the hundreds of millions.
- **Deductible**: Higher minimum deductible ($500K vs $50K in `cyber_general`). Critical infrastructure events are inherently high-severity; sub-$500K events are operational incidents, not insurance events.
- **Sub-sector modifiers** (applied within the configuration):
  - Electric Utility (Transmission): 1.30 — highest interconnectedness, NERC CIP regulated, grid stability implications
  - Electric Utility (Distribution): 1.10 — lower interconnectedness but direct consumer impact
  - Oil & Gas (Pipeline): 1.25 — Colonial Pipeline demonstrated severity; TSA-regulated post-2021
  - Oil & Gas (Upstream/Refining): 1.15 — physical safety risk (explosion, environmental release)
  - Water/Wastewater: 1.05 — high physical consequence potential but typically lower-value targets; many are small municipal systems
  - Telecommunications: 0.90 — critical infrastructure designation but primarily IT-based (less OT/ICS exposure); regulated by FCC
  - Transportation (Rail): 1.10 — PTC (Positive Train Control) systems are cyber-dependent; FRA-regulated
  - Transportation (Aviation): 1.20 — FAA cybersecurity requirements; air traffic control and flight management system exposure
- **Geographic modifiers**:
  - US: 1.0 (base — deepest regulatory framework, CISA engagement, litigation exposure)
  - UK: 1.05 (NIS Regulations, NCSC engagement with CNI operators)
  - EU: 1.10 (NIS2 Directive substantially expands scope and penalties for essential services from October 2024)
  - Middle East: 1.25 (elevated nation-state targeting — Shamoon/Saudi Aramco, TRITON/Saudi petrochemical; limited regulatory maturity)
  - APAC: 0.95 (AESCSF for Australian energy sector is robust; generally lower litigation frequency)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Dominion Energy** — Major US electric utility
> - Revenue: $14.4B | Limit: $250M | Score: 812
> - Why: NERC CIP High Impact BES asset operator with documented full compliance, published IT/OT segmentation architecture with unidirectional gateways (Waterfall Security data diodes), dedicated OT Security Operations Centre, Dragos Platform deployed across all generating stations and transmission substations, comprehensive OT patching programme with compensating controls documentation, independent SIS architecture across all generating facilities, active CISA/E-ISAC participant, OT-specific incident response plan with annual tabletop exercises, manual override capability documented for all critical generation and transmission processes
> - Premium: $14.4B × 0.0006 × ILF(250M) × 1.30 (transmission) = **~$11.2M base** before modifiers
> - Modifiers: Geographic (US: 1.0), Sub-sector (Transmission: 1.30), Strong controls (0.75) → **Net premium: ~$8.4M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Tier Pipeline Operator** (composite — 2,800 miles of natural gas pipeline, Gulf Coast)
> - Revenue: $3.2B | Limit: $100M | Score: 498
> - Why: TSA Pipeline Security Directive compliant (minimum requirements met), IT/OT segmentation via firewalled DMZ (not unidirectional), SCADA systems partially modernised (60% modern, 40% legacy Honeywell TDC 3000 from 1990s), no dedicated OT SOC (IT SOC handles OT alerts), OT network monitoring deployed on critical segments only, manual override capability available at compressor stations but not at all valve stations, basic OT IR plan but no dedicated OT IR retainer
> - Referral reasons: `ics_scada_vintage <= 40` (40% legacy systems), `ot_incident_response <= 35`, `scada_network_monitoring <= 45` (partial deployment)
> - Premium: $3.2B × 0.0022 × ILF(100M) × 1.25 (pipeline) = **~$8.8M base** → Referred for senior review with OT specialist consultation

**Tier 5 — DECLINE:**
> **Distressed Municipal Water Utility** (composite — deterioration scenario)
> - Revenue: $180M | Limit: $10M | Score: 198
> - Why: No IT/OT segmentation (converged network with shared credentials — direct query REFER), SCADA system running Windows XP-based HMIs with no patching capability, no OT network monitoring, no SIS independence (safety interlocks controlled by same SCADA system — direct query REFER), no manual override for chemical dosing systems (direct query FLAG + MODIFIER), no CISA/ISAC participation, no OT incident response plan, single IT administrator responsible for all systems, 2019 ransomware incident with 72-hour service disruption, failed EPA cybersecurity assessment
> - Decline triggers: `ot_ics_security` group score <= 15, `it_ot_segmentation <= 10`, `sis_independent = false` (REFER), `ot_network_segmented = false` (REFER), multiple REFER conditions from direct queries

---

## Configuration 4: `cyber_technology`

### The Underwriting Reality

Technology companies — SaaS platforms, enterprise software vendors, cloud infrastructure providers, managed service providers (MSPs), cybersecurity vendors, semiconductor companies, hardware manufacturers — represent a paradox in cyber underwriting: **they are simultaneously the most security-sophisticated and the most catastrophically exposed risk class**. Technology companies build and operate the systems that everyone else depends on; a single vulnerability in their product becomes a vulnerability in thousands of their customers' environments.

The SolarWinds supply chain attack (December 2020) demonstrated this at scale: a compromised build system at a single IT management software vendor injected malicious code into updates distributed to ~18,000 organisations, including the US Treasury, Commerce Department, DHS, and Fortune 500 companies. The Kaseya VSA attack (July 2021) compromised a single MSP platform to deploy REvil ransomware across ~1,500 downstream businesses simultaneously. The MOVEit Transfer vulnerability (May 2023) in a single file transfer product exposed data from 2,500+ organisations including government agencies, financial institutions, and healthcare providers.

This is the supply chain amplification problem: **technology companies' risk is not their own risk — it is the aggregate risk of their entire customer base**. A breach at a technology company produces third-party liability claims from every affected customer, regulatory enforcement across multiple jurisdictions (because customers span jurisdictions), and reputational damage that directly impacts revenue (because security IS the product for many tech companies).

The existing `cyber_general` configuration cannot price technology companies because:

1. **Supply chain position** — A technology company's position in the supply chain determines the blast radius of a compromise. A SaaS platform serving 50,000 SMBs has different aggregate exposure than an enterprise software vendor serving 500 large enterprises, even at identical revenue levels. The supply chain position determines the *multiplier* on severity. Observable through published customer counts, platform architecture (multi-tenant vs single-tenant), and market position documentation.
2. **Product security maturity** — Technology companies ship code to customers. The maturity of their secure software development lifecycle (SSDLC) — static analysis, dynamic analysis, dependency scanning, code review, penetration testing, bug bounty programmes — directly determines the probability of shipping exploitable vulnerabilities. This is entirely distinct from the company's own *infrastructure* security. Observable through published security practices, SOC 2 Type II reports, bug bounty programme scope and payouts, CVE history, and CISA Known Exploited Vulnerabilities (KEV) listings.
3. **Customer data concentration** — Technology companies are data processors at scale. A CRM platform holds customer data for thousands of businesses; a cloud infrastructure provider holds everything. The volume, sensitivity, and regulatory classification of customer data determines both regulatory exposure (as a data processor under GDPR, as a business associate under HIPAA) and litigation exposure (class actions from affected data subjects). Observable through published data processing documentation, privacy policies, regulatory certifications, and platform capabilities.
4. **Platform architecture resilience** — Multi-tenant SaaS platforms have blast radius characteristics that single-tenant deployments do not: a single vulnerability in a shared authentication system, a misconfigured IAM policy, or a compromised CI/CD pipeline can expose all tenants simultaneously. The architecture determines whether a breach is contained to one customer or affects all customers. Observable through published architecture documentation, SOC 2 reports, and shared responsibility models.

### Signal Architecture Rationale

**Primary driver: Product & Supply Chain Security — NEW GROUP (Risk: 0.25, Loss: 0.25, Exposure: 0.20 = 0.70 combined)**

The dominant group, reflecting the reality that technology companies' primary cyber risk is through their products and their position in the supply chain, not through their own infrastructure (though that matters too). Contains signals for SSDLC maturity, supply chain position/blast radius, vulnerability management (CVE history), CI/CD pipeline security, dependency management, and customer data processing scope.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

The company's own infrastructure security remains highly relevant — technology companies typically have extensive cloud infrastructure, complex CI/CD pipelines, and large engineering workforces with broad access to production systems. Weight is retained from `cyber_general` (not reduced as in critical infrastructure) because IT infrastructure compromise IS the primary initial access vector in technology company breaches.

**Elevated: Structured Data (Risk: 0.15, Loss: 0.10, Exposure: 0.10 = 0.35 combined)**

Technology companies are well-covered by third-party rating platforms, and SOC 2 Type II reports provide standardised assessments of control environments. SecurityScorecard and BitSight ratings are most reliable for technology companies because these companies have the largest observable attack surfaces (public-facing infrastructure, published APIs, open source contributions).

**Retained: Corporate Footprint (Risk: 0.05, Loss: 0.05, Exposure: 0.05 = 0.15 combined)**

Technology companies typically have extensive public-facing security documentation: security pages, trust centres, responsible disclosure policies, transparency reports. These are somewhat informative but are also performative — a well-designed security page does not guarantee good security. Low weight.

**Deprioritised: Network Authority**

Technology companies have high domain authority by nature of their business. Network authority metrics (backlinks, domain age) are meaningless for discriminating between well-secured and poorly-secured technology companies.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `ssdlc_maturity` | INFERRED_PROXY | product_supply_chain_security | Maturity of secure software development lifecycle: static analysis (SAST), dynamic analysis (DAST), interactive analysis (IAST), software composition analysis (SCA), code review requirements, security champions programme, threat modelling. Observable through published security practices, SOC 2 Type II reports, BSIMM (Building Security In Maturity Model) participation, and SAMM assessments. The primary determinant of product vulnerability rate. |
| `supply_chain_blast_radius` | INFERRED_PROXY | product_supply_chain_security | The downstream impact of a compromise: customer count, customer concentration (how many high-value targets), platform architecture (multi-tenant shared infrastructure vs isolated deployments), and data flow architecture. A SaaS CRM serving 100,000 businesses has different blast radius than a cybersecurity vendor serving 500 enterprises, even at similar revenue. Observable through published customer counts, architecture documentation, and market position. |
| `cve_vulnerability_history` | DIRECT_OBSERVABLE | product_supply_chain_security | History of CVEs attributed to the company's products, including severity (CVSS scores), exploitability (CISA KEV listing), time-to-patch, and whether vulnerabilities were discovered internally, by bug bounty, or by external researchers/adversaries. A strong predictor of product security maturity. Observable through NVD, CISA KEV, and vendor security advisories. |
| `cicd_pipeline_security` | INFERRED_PROXY | product_supply_chain_security | Security of the software build and deployment pipeline: build system integrity (reproducible builds, signed artifacts), deployment pipeline access controls, secrets management, infrastructure-as-code scanning. The SolarWinds attack vector was a compromised build system. Observable through published deployment practices, Sigstore/SLSA adoption, and SOC 2 commentary. |
| `dependency_management` | INFERRED_PROXY | product_supply_chain_security | Management of open source and third-party dependencies: SCA tooling, SBOM (Software Bill of Materials) generation, dependency update cadence, and response to upstream vulnerabilities (Log4Shell, Spring4Shell response time as observable indicators). Observable through published SBOM practices, dependency update patterns in public repositories, and vulnerability response timelines. |
| `bug_bounty_programme` | DIRECT_OBSERVABLE | product_supply_chain_security | Existence, scope, and maturity of bug bounty programme. Programmes with broad scope (all customer-facing assets), meaningful payouts (>$10K for critical), and published metrics (bugs found, time-to-fix) indicate mature vulnerability management. Observable through HackerOne/Bugcrowd programme pages and published security reports. |
| `customer_data_processing_scope` | INFERRED_PROXY | product_supply_chain_security | Volume, sensitivity, and regulatory classification of customer data processed. A technology company processing PHI for healthcare customers has HIPAA business associate obligations; one processing EU personal data has GDPR data processor obligations. The regulatory multiplier applies to EACH affected customer's data, creating compound regulatory exposure. Observable through DPAs, privacy policies, compliance certifications (SOC 2, ISO 27001, HIPAA, FedRAMP). |
| `platform_tenancy_architecture` | INFERRED_PROXY | product_supply_chain_security | Multi-tenant vs single-tenant architecture, tenant isolation mechanisms (logical vs physical isolation, shared vs dedicated compute/storage/networking), and cross-tenant vulnerability exposure. Multi-tenant platforms with logical isolation only have "noisy neighbour" and cross-tenant escalation risks that single-tenant deployments do not. Observable through published architecture documentation and SOC 2 reports. |

### Direct Queries (Technology-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_technology` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `secure_sdlc_implemented` | Do you maintain a formal secure software development lifecycle (SSDLC) with automated security testing integrated into your CI/CD pipeline? | `false` → | REFER override: 4. Technology companies shipping code without integrated security testing are systematically producing vulnerable products. |
| `sbom_generated` | Do you generate and maintain Software Bills of Materials (SBOMs) for your products? | `false` → | FLAG. SBOM absence indicates inability to assess exposure to upstream dependency vulnerabilities (Log4Shell scenario). |
| `tenant_isolation_validated` | For multi-tenant platforms: is tenant isolation independently validated through penetration testing or third-party assessment? | `false` → | MODIFIER applied: 1.20. Unvalidated tenant isolation in multi-tenant platforms creates cross-tenant compromise risk affecting all customers simultaneously. |
| `incident_notification_sla` | Do you have documented and contractually committed customer notification SLAs for security incidents? | `false` → | FLAG. Absence of notification SLAs indicates immature incident response and increases third-party liability exposure from delayed disclosure. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0032** (0.32%) — a 60% premium over `cyber_general`'s 0.20%. Reflects the supply chain amplification risk, third-party liability exposure from customer base, and the technology sector's elevated threat targeting.
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `technology_e_and_o`, `media_liability_cyber`
  - `technology_e_and_o` is the critical coverage: technology errors & omissions covering third-party claims arising from security failures in the insured's products or services. This is the primary claim type for technology companies — customers suing because the vendor's product vulnerability caused the customer's breach. Standard cyber policies may exclude professional services/product liability; tech E&O explicitly covers it.
  - `media_liability_cyber` covers claims arising from content-related liabilities (defamation, IP infringement) for technology companies that host or distribute user-generated content.
- **ILF Curves**: Steeper than `cyber_general` above $25M limits. Technology company severity tails are driven by aggregate third-party claims from large customer bases — the cost scales with customer count, not merely with the technology company's own revenue.
- **Deductible**: Moderate minimum deductible ($100K vs $50K in `cyber_general`). Technology companies experience frequent low-severity events (vulnerability disclosures, minor incidents) that should be absorbed; the policy should respond to material events.
- **Sub-sector modifiers**:
  - SaaS Platform (B2B): 1.20 — multi-tenant, customer data processing, supply chain position
  - Cloud Infrastructure Provider: 1.35 — maximum blast radius, all customer workloads exposed
  - Managed Service Provider (MSP): 1.30 — direct access to customer environments, privileged credentials for customer networks (Kaseya scenario)
  - Enterprise Software Vendor: 1.10 — supply chain risk but typically on-premise deployment reduces blast radius
  - Cybersecurity Vendor: 1.15 — ironic premium: security vendors are high-value targets (SolarWinds, FireEye, LastPass) and a breach produces acute reputational damage plus customer exposure
  - Hardware/Semiconductor: 0.85 — lower cyber exposure profile (less customer data, less SaaS blast radius), though firmware supply chain risk exists
  - Consumer Technology: 1.00 — base rate; moderate data exposure, moderate supply chain risk
- **Geographic modifiers**:
  - US: 1.0 (base — deepest litigation exposure, class action risk, SEC cybersecurity disclosure requirements)
  - UK: 0.95 (active ICO enforcement but lower litigation frequency than US)
  - EU: 1.10 (GDPR processor obligations, upcoming Cyber Resilience Act imposing product security requirements)
  - Israel: 1.05 (dense concentration of cybersecurity companies; elevated nation-state targeting of Israeli tech sector)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Microsoft** — Global technology platform
> - Revenue: $236B | Limit: $500M | Score: 856
> - Why: Industry-leading SSDLC (SDL — Security Development Lifecycle, pioneered by Microsoft in 2004), comprehensive bug bounty programme ($13.7M paid in FY2023, 345 researchers, scope covering all customer-facing products), dedicated Microsoft Security Response Centre (MSRC), SBOM generation for all products, SOC 2 Type II + ISO 27001 + FedRAMP High for Azure, independent tenant isolation validation, published SSDF (Secure Software Development Framework) alignment, <24hr mean time to patch for CISA KEV listings, Secure Future Initiative (2023) demonstrates board-level commitment
> - Premium: $236B × 0.0001 × ILF(500M) × 1.20 (SaaS/Cloud) = **~$23.6M base** before modifiers
> - Modifiers: Geographic (US: 1.0), Sub-sector (Cloud: 1.35, blended with SaaS: 1.20 → ~1.28), Strong controls (0.75) → **Net premium: ~$22.6M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Tier B2B SaaS Platform** (composite — HR/payroll SaaS, 15,000 business customers, processing employee PII and payroll data)
> - Revenue: $450M | Limit: $50M | Score: 512
> - Why: SOC 2 Type II compliant, multi-tenant platform with logical tenant isolation (not independently validated — direct query MODIFIER 1.20), SSDLC implemented but partially automated (manual code review, automated SAST but no DAST/IAST), no SBOM generation (direct query FLAG), bug bounty programme via HackerOne but limited scope (primary application only, excludes APIs and mobile), 3 medium-severity CVEs in past 2 years (patched within 30 days), 15,000 customers processing employee PII creates substantial GDPR processor and state privacy law exposure
> - Referral reasons: `ssdlc_maturity <= 45`, `tenant_isolation_validated = false` (MODIFIER), `dependency_management <= 40` (no SBOM), `customer_data_processing_scope >= 70` (high regulatory exposure relative to controls)
> - Premium: $450M × 0.0020 × ILF(50M) × 1.20 (SaaS) = **~$900K base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Distressed MSP** (composite — managed IT services provider, deterioration scenario)
> - Revenue: $85M | Limit: $10M | Score: 203
> - Why: Provides managed IT services to 800+ SMB customers with privileged administrative access to customer networks (RMM tools, domain admin credentials), no formal SSDLC (direct query REFER), no SOC 2 or ISO 27001 certification, RMM platform (ConnectWise ScreenConnect) running unpatched version with known CVE, customer environment access not segmented (single compromised technician credential provides access to all 800 customer environments), 2 ransomware incidents in 18 months (one propagated to 47 customer environments — the exact Kaseya scenario), no bug bounty programme, no SBOM, no documented incident notification SLA, MFA not enabled for administrative access (direct query REFER)
> - Decline triggers: `product_supply_chain_security` group score <= 18, `supply_chain_blast_radius` flagged (800 customers with unsegmented privileged access), `secure_sdlc_implemented = false` (REFER), multiple REFER conditions from direct queries, `breach_history <= 15`

---

## Configuration 5: `cyber_digital_platform`

### The Underwriting Reality

Digital platforms — e-commerce marketplaces, social media networks, online gaming platforms, streaming services, digital advertising networks, gig economy platforms, online travel agencies — occupy a distinct risk position from technology companies. Where `cyber_technology` addresses companies that *build and sell* technology products and services, `cyber_digital_platform` addresses companies whose primary business IS a digital platform connecting users, merchants, content creators, and advertisers. The platform IS the product, and its users are simultaneously its assets, its attack surface, and its liability.

The distinction matters for underwriting because digital platforms face a unique combination of risks that neither `cyber_general` nor `cyber_technology` captures:

1. **User-scale data exposure** — Digital platforms hold personal data on tens of millions to billions of individual users. Facebook's 2019 breach exposed 533 million records; LinkedIn's 2021 scraping incident exposed 700 million profiles; T-Mobile's 2021 breach exposed 76 million records. The severity of a breach scales directly with user count, and user counts for major platforms are measured in hundreds of millions. The notification costs alone (at $1-3 per record for consumer notification, credit monitoring, and call centre support) can reach hundreds of millions of dollars. This is fundamentally different from `cyber_technology` where the exposure is through customer *organisations*, not individual users.

2. **Payment processing at consumer scale** — Digital platforms process consumer payment transactions at massive volume: millions of daily transactions across multiple payment methods (credit cards, digital wallets, stored payment credentials, platform credits, cryptocurrency). The fraud exposure is not the institutional payment fraud of `cyber_financial_services` (SWIFT, wire transfers) but high-volume consumer transaction fraud: stolen payment credentials, account takeover, marketplace fraud (fake merchants, counterfeit goods, non-delivery). Observable through published transaction volumes, payment method documentation, and PCI compliance status.

3. **Content and user-generated liability** — Digital platforms that host user-generated content (social media, marketplaces, forums, review platforms) face content-related cyber liabilities: defamation claims, intellectual property infringement, CSAM (child sexual abuse material) liability, terrorist content distribution, privacy violations from user-posted content. Section 230 provides some protection in the US, but EU Digital Services Act (DSA), UK Online Safety Act, and Australian Online Safety Act impose affirmative moderation obligations with substantial penalties.

4. **Account takeover at scale** — Digital platforms with hundreds of millions of user accounts are targets for credential stuffing attacks (using leaked credentials from other breaches), SIM-swapping, and social engineering. Account takeover (ATO) produces both direct fraud losses (stored payment methods, digital assets, loyalty points) and litigation/regulatory exposure (users suing for failure to protect accounts). Observable through published security features (MFA availability, passkey support), and publicly reported ATO incidents.

5. **Regulatory multiplier effect** — Digital platforms operate across jurisdictions, creating compound regulatory exposure. A single breach may trigger: GDPR notification (EU users), UK GDPR notification (UK users), CCPA notification (California users), LGPD notification (Brazilian users), PIPL notification (Chinese users), and sector-specific obligations (PCI-DSS for payment data, COPPA for platforms with child users). Each jurisdiction has different notification timelines, remediation requirements, and penalty structures.

### Signal Architecture Rationale

**Primary driver: Platform User Security — NEW GROUP (Risk: 0.25, Loss: 0.25, Exposure: 0.25 = 0.75 combined)**

The dominant group, weighted with 0.25 Exposure (the highest Exposure weight across all configurations). This reflects the fundamental reality that digital platform risk scales with *user count and user engagement*, not merely with revenue. A platform with 100 million users at $500M revenue has dramatically different exposure than a B2B SaaS company at $500M revenue with 5,000 corporate customers. Contains signals for user authentication architecture, account security controls, payment fraud prevention, user data minimisation, content moderation capability, and privacy-by-design implementation.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.10, Exposure: 0.05 = 0.30 combined)**

Reduced from `cyber_general`. Technical infrastructure matters (these platforms run massive cloud deployments), but the *platform-specific* risks (account takeover, payment fraud, content liability, user data exposure) are captured in the primary group. Infrastructure is the delivery mechanism, not the risk driver.

**Elevated: Structured Data (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Digital platforms are the most observable entities in the cybersecurity rating ecosystem. SecurityScorecard and BitSight have deep visibility into their public-facing infrastructure (CDNs, APIs, mobile endpoints). Consumer-facing platforms also have observable user-facing security features (MFA, passkeys, security page quality) that provide additional signal.

**Retained: Corporate Footprint (Risk: 0.05, Loss: 0.05, Exposure: 0.05 = 0.15 combined)**

Digital platforms have extensive public-facing security documentation: trust and safety pages, transparency reports, privacy centres. These are informative for large platforms (Meta, Google publish detailed transparency reports) but can be performative for smaller platforms. Low weight but not zero.

**Deprioritised: Network Authority**

Digital platforms have inherently high network authority. The signal is non-discriminatory within this configuration.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `user_authentication_architecture` | INFERRED_PROXY | platform_user_security | Sophistication of user authentication: password-only, MFA availability (SMS, TOTP, hardware key), passkey/FIDO2 support, adaptive/risk-based authentication, session management, and account recovery security. The primary determinant of account takeover (ATO) vulnerability at scale. Observable through published security features, user-facing login flows, and published security documentation. |
| `ato_prevention_capability` | INFERRED_PROXY | platform_user_security | Account takeover prevention controls: credential stuffing detection (rate limiting, bot detection, known-breached-credential checking), anomalous login detection (impossible travel, device fingerprinting), and automated ATO response (session invalidation, forced password reset, account lock). Observable through published security features and incident response to known ATO campaigns. |
| `payment_fraud_controls` | INFERRED_PROXY | platform_user_security | Consumer payment fraud prevention: tokenisation of payment credentials, 3D Secure implementation, real-time fraud scoring, chargeback rate monitoring, and merchant vetting (for marketplace platforms). Observable through published payment security documentation, PCI compliance level, and published chargeback/fraud rates. |
| `user_data_minimisation` | INFERRED_PROXY | platform_user_security | Data minimisation practices: retention policies, data deletion capability (GDPR right to erasure compliance), purpose limitation, and anonymisation/pseudonymisation of analytics data. Platforms that retain all user data indefinitely have unbounded breach severity; platforms with aggressive minimisation cap their exposure. Observable through privacy policies, DPA documentation, and transparency reports. |
| `content_moderation_capability` | INFERRED_PROXY | platform_user_security | For platforms hosting user-generated content: automated content moderation (AI/ML detection), human review capacity, NCMEC/IWF reporting compliance, content appeals process, and DSA/Online Safety Act compliance. Content moderation failures produce regulatory fines (DSA: up to 6% of global turnover), criminal liability (CSAM), and reputational damage. Observable through transparency reports, DSA compliance documentation, and published moderation policies. |
| `privacy_by_design` | INFERRED_PROXY | platform_user_security | Implementation of privacy-by-design principles: consent management platform, cookie/tracking compliance, privacy impact assessments, DPIA (Data Protection Impact Assessment) process, and privacy engineering team. Observable through published privacy documentation, cookie consent implementations, and regulatory filings. |
| `user_base_scale` | DIRECT_OBSERVABLE | platform_user_security | Total registered user count, monthly active users (MAU), daily active users (DAU), and geographic distribution of users. This is the primary exposure scalar: breach severity is directly proportional to affected user count. Observable through published metrics (public company filings, press releases), app store download counts, and web analytics estimates. |
| `api_security_posture` | INFERRED_PROXY | platform_user_security | Security of public-facing APIs: authentication (OAuth 2.0, API keys), rate limiting, input validation, BOLA (Broken Object Level Authorization) protection, and API versioning/deprecation practices. APIs are the primary attack surface for digital platforms — the OWASP API Security Top 10 describes the most common API vulnerabilities. Observable through published API documentation, developer portals, and API security testing results. |

### Direct Queries (Digital Platform-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_digital_platform` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `mfa_available_all_users` | Is multi-factor authentication available to all platform users (not just administrative accounts)? | `false` → | MODIFIER applied: 1.25. Platforms without user-facing MFA are structurally vulnerable to credential stuffing and account takeover at scale. |
| `credential_breach_checking` | Do you check user credentials against known breached credential databases (e.g., Have I Been Pwned, internal breach databases)? | `false` → | FLAG. Absence of breached credential checking means the platform accepts credentials known to be compromised, enabling automated ATO. |
| `data_retention_policy` | Do you maintain and enforce a data retention policy with automated deletion of user data beyond retention periods? | `false` → | MODIFIER applied: 1.15. Indefinite data retention produces unbounded breach severity — every user who ever created an account is affected. |
| `child_user_protections` | If your platform is accessible to users under 18: do you implement age verification and enhanced data protection for minor users? | `false` → | REFER override: 4. COPPA/UK Age Appropriate Design Code/DSA child protection failures produce regulatory fines, criminal liability, and acute reputational damage. |

### Pricing Philosophy

- **Basis**: **User count (MAU)** — THIS IS THE KEY DEPARTURE FROM ALL OTHER CONFIGURATIONS. Digital platform risk scales with user count, not revenue. A platform with 500M users at $1B revenue has 100x the breach notification exposure of a platform with 5M users at $1B revenue. Revenue is used as a secondary basis for overall pricing calibration, but the primary rate driver is user count.
- **Method**: HYBRID — per-user rate PLUS revenue multiplier floor. The per-user component captures breach notification/severity scaling; the revenue floor ensures minimum premium adequacy for high-revenue/low-user-count platforms.
- **Tier 3 (STANDARD) rate**: **$0.015 per MAU** (with $2M minimum premium) OR **0.0025 (0.25%)** of revenue, whichever is greater.
  - Example: A platform with 50M MAU and $800M revenue: per-user = $750K; revenue = $2M → revenue floor applies → $2M base premium.
  - Example: A platform with 200M MAU and $2B revenue: per-user = $3M; revenue = $5M → revenue rate applies → $5M base premium.
  - Example: A platform with 500M MAU and $1B revenue: per-user = $7.5M; revenue = $2.5M → per-user applies → $7.5M base premium. This captures the exposure correctly — 500M users is massive breach exposure regardless of revenue.
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `media_liability_cyber`, `regulatory_defence_cyber`
  - `regulatory_defence_cyber` is new: covers regulatory investigation costs, defence costs, and fines/penalties (where insurable) arising from data protection enforcement actions. Digital platforms face multi-jurisdictional regulatory exposure (GDPR + CCPA + LGPD + PIPL) that produces compound regulatory costs.
  - `media_liability_cyber` covers content-related claims: defamation from user-generated content, IP infringement claims, and privacy-related media claims.
- **ILF Curves**: Very steep above $50M limits. Digital platform severity distributions are bimodal: either small (contained incidents affecting limited users) or catastrophic (full database breach affecting all users). The Equifax settlement ($575M), T-Mobile settlement ($350M), and Meta's GDPR fine (€1.2B) demonstrate the severity ceiling.
- **Deductible**: Moderate minimum deductible ($150K). Digital platforms experience frequent lower-severity events (small-scale ATO campaigns, localised payment fraud, content moderation failures) that should be absorbed.
- **Sub-sector modifiers**:
  - Social Media/UGC Platform: 1.25 — maximum user data exposure, content moderation liability, regulatory scrutiny
  - E-commerce Marketplace: 1.20 — payment fraud exposure, merchant vetting liability, consumer protection regulations
  - Online Gaming Platform: 1.10 — virtual asset/currency fraud, younger user demographics (COPPA/child protection), high ATO targeting
  - Streaming Service: 0.95 — lower payment fraud (subscription model), limited UGC liability, lower data sensitivity
  - Gig Economy/Sharing Platform: 1.15 — worker/contractor data, payment processing, physical safety intersection
  - Digital Advertising Network: 1.10 — tracking/privacy regulatory exposure (ePrivacy, CCPA), advertiser data, brand safety
  - Online Travel Agency: 1.05 — payment card data, PII volume, PCI scope
- **Geographic modifiers**:
  - US: 1.0 (base — class action litigation exposure, CCPA/state privacy laws, FTC enforcement)
  - UK: 1.05 (ICO enforcement, Online Safety Act obligations, UK GDPR)
  - EU: 1.20 (GDPR + DSA + upcoming ePrivacy Regulation — the most aggressive regulatory environment for digital platforms globally; Meta's €1.2B fine demonstrates the ceiling)
  - China: 1.15 (PIPL requirements are prescriptive and enforcement is increasing; data localisation obligations add compliance cost)
  - APAC (ex-China): 0.95 (emerging privacy laws — Japan APPI, South Korea PIPA, India DPDPA — but enforcement is less aggressive than EU)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Booking Holdings** — Global online travel platform (Booking.com, Priceline, Agoda, Kayak)
> - MAU: ~150M | Revenue: $21.4B | Limit: $300M | Score: 798
> - Why: PCI Level 1 compliant across all brands, MFA available for all users (direct query satisfied), comprehensive fraud scoring for all transactions, data retention policy with automated deletion (GDPR compliance documented), SOC 2 Type II certified, robust API security (OAuth 2.0, rate limiting, published security headers), published bug bounty programme via HackerOne (broad scope), no material breaches in 5 years, minimal UGC liability (reviews only, with moderation), GDPR compliance documented with designated DPO and published DPIAs
> - Premium: MAX($0.015 × 150M, $21.4B × 0.0004) × ILF(300M) × 1.05 (OTA) = MAX($2.25M, $8.56M) = **$8.56M base** (revenue applies)
> - Modifiers: Geographic (weighted: US 1.0, EU 1.20 → ~1.08 blended), Sub-sector (OTA: 1.05), Strong controls (0.80) → **Net premium: ~$7.3M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Tier Social Commerce Platform** (composite — social media + marketplace hybrid, 35M MAU, US/EU user base)
> - MAU: 35M | Revenue: $620M | Limit: $50M | Score: 489
> - Why: MFA available but not promoted (only 12% adoption among users), credential breach checking not implemented (direct query FLAG), payment fraud controls adequate but basic (no 3D Secure for all transactions), user data retention policy exists but automated deletion not fully implemented (direct query MODIFIER 1.15), UGC moderation primarily AI-based with limited human review (7-day backlog), no DPIA published, bug bounty programme but narrow scope, 1 ATO incident affecting 200K accounts in past year, DSA compliance in progress but not complete
> - Referral reasons: `ato_prevention_capability <= 40` (no breached credential checking, low MFA adoption), `content_moderation_capability <= 45` (moderation backlog, DSA incomplete), `data_retention_policy = false` (MODIFIER), `user_authentication_architecture <= 50` (low MFA adoption)
> - Premium: MAX($0.015 × 35M, $620M × 0.0016) × ILF(50M) × 1.225 (Social+Marketplace blend) = MAX($525K, $992K) = **$992K base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Distressed Social Platform** (composite — user-generated content platform, deterioration scenario)
> - MAU: 85M | Revenue: $340M | Limit: $25M | Score: 187
> - Why: No MFA available for users (direct query MODIFIER 1.25), password-only authentication with no complexity requirements, no credential breach checking (direct query FLAG), no ATO prevention capability (no rate limiting on login endpoint — active credential stuffing campaigns observed), 3 data breaches in 2 years (most recent: 22M user records exfiltrated, 4-month detection delay), no data retention policy (retaining all data since launch in 2016 — direct query MODIFIER 1.15), content moderation severely under-resourced (DSA compliance notice received from European Commission), child users present on platform with no age verification (direct query REFER), no bug bounty programme, PCI compliance lapsed, API endpoints documented on public forums as vulnerable to BOLA
> - Decline triggers: `platform_user_security` group score <= 18, `user_authentication_architecture <= 10`, `child_user_protections = false` (REFER), multiple MODIFIER stacking (1.25 × 1.15 = 1.44), `breach_history <= 15`

---

## Configuration 6: `cyber_manufacturing`

### The Underwriting Reality

Manufacturing — automotive, aerospace, pharmaceuticals, food & beverage, chemicals, consumer goods, industrial equipment — sits at the intersection of two risk domains that other configurations address separately: **the IT/OT convergence of `cyber_critical_infrastructure` and the supply chain interconnectedness of `cyber_technology`**. But manufacturing has distinct characteristics that warrant its own configuration rather than routing to either of those.

Manufacturing is the most ransomware-targeted sector globally. IBM X-Force's 2023 Threat Intelligence Index ranked manufacturing as the #1 most attacked industry for the third consecutive year, receiving 25.7% of all attacks. The reason is structural: **manufacturers cannot tolerate downtime**. A hospital can divert patients; a bank can process transactions manually; a manufacturer whose production line stops is burning cash at a rate measured in millions per day with no manual alternative. This makes manufacturers the most likely to pay ransoms and the most likely to suffer catastrophic business interruption losses.

The key distinctions from `cyber_critical_infrastructure`:

1. **Production line dependency, not public safety** — Manufacturing OT environments control production processes (CNC machines, robotic assembly, chemical mixing, packaging lines), not public safety-critical systems (power grids, water treatment, pipelines). The consequence of compromise is production stoppage and economic loss, not physical harm to the public. This means the severity distribution is dominated by business interruption, not by bodily injury or environmental contamination.
2. **Just-in-time supply chains** — Modern manufacturing operates on lean/JIT principles with minimal buffer inventory. A production stoppage of 48 hours can propagate through the supply chain: Toyota's single-day production halt following the Kojima Industries cyberattack (March 2022) affected 14 factories and 28 production lines. The insured's BI loss is amplified by contractual penalties, expediting costs, and customer relationship damage.
3. **Intellectual property concentration** — Manufacturing companies hold concentrated IP: product designs, formulations, process specifications, tooling data, and trade secrets. IP theft through cyber espionage (particularly nation-state actors targeting defence, aerospace, and semiconductor manufacturing) produces losses that are difficult to quantify but can be existential — a competitor gaining access to product designs eliminates years of R&D investment.
4. **Legacy OT with business context** — Manufacturing OT is typically older and less secured than critical infrastructure OT because manufacturers lack the regulatory forcing functions (NERC CIP, TSA directives) that drive critical infrastructure investment. Many manufacturers operate PLCs and SCADA systems from the 1990s-2000s with no cybersecurity investment because "the production line works and we can't afford downtime to upgrade."

### Signal Architecture Rationale

**Primary driver: Manufacturing Operations Security — NEW GROUP (Risk: 0.25, Loss: 0.25, Exposure: 0.15 = 0.65 combined)**

Contains signals specific to manufacturing environments: production OT security posture, IT/OT segmentation (shared with `cyber_critical_infrastructure` but contextualised differently), production continuity and recovery capability, IP protection controls, and supply chain cyber resilience. Weight is lower than `cyber_critical_infrastructure`'s OT group (0.65 vs 0.75) because the physical consequence ceiling is lower (economic loss, not public safety), but still dominant.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Retained at near-`cyber_general` levels. Manufacturing IT infrastructure (email, ERP, CAD/CAM systems, corporate networks) is the initial access vector for most manufacturing attacks. Ransomware groups target manufacturing through standard IT vectors (phishing, VPN exploitation, RDP compromise) and then pivot to OT environments. IT security quality directly determines whether an attacker achieves the IT-to-OT pivot.

**Retained: Structured Data (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Third-party ratings are moderately useful for manufacturers. SecurityScorecard and BitSight can assess IT-facing infrastructure, but (as with critical infrastructure) they have limited visibility into OT environments. Useful as a hygiene indicator.

**Retained: Corporate Footprint (Risk: 0.05, Loss: 0.05, Exposure: 0.05 = 0.15 combined)**

Manufacturers vary widely in their public-facing security posture. Large multinationals (Siemens, 3M, Johnson & Johnson) publish detailed security documentation; mid-market manufacturers often have minimal web presence. Low weight but informative for segmentation.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `production_ot_security` | INFERRED_PROXY | manufacturing_operations_security | Overall security posture of production OT environments: PLC/SCADA/DCS security, HMI hardening, OT network monitoring, and OT-specific endpoint protection. Distinct from `cyber_critical_infrastructure`'s OT signals in that the focus is on production continuity rather than safety system integrity. Observable through vendor relationships (Claroty, Dragos, Nozomi), published security architecture, and manufacturing industry certifications (IEC 62443). |
| `it_ot_segmentation_mfg` | INFERRED_PROXY | manufacturing_operations_security | IT/OT network segmentation specific to manufacturing environments. Manufacturing IT/OT segmentation is typically less mature than critical infrastructure because manufacturers lack regulatory mandates. The Purdue Model (ISA-95/IEC 62264) provides the reference architecture, but compliance varies widely. Observable through published architecture, vendor relationships, and IEC 62443 compliance. |
| `production_continuity_capability` | INFERRED_PROXY | manufacturing_operations_security | Ability to maintain or rapidly restore production following a cyber incident: production backup/recovery procedures, manual production fallback capability, production system rebuild time (hours/days/weeks), and tested recovery playbooks. This is the primary severity determinant — the difference between 2 days and 30 days of production downtime at $5M/day is $140M in BI loss. Observable through published business continuity plans, cyber incident response exercises, and insurance claims history. |
| `ip_protection_controls` | INFERRED_PROXY | manufacturing_operations_security | Protection of intellectual property: DLP (Data Loss Prevention) on CAD/CAM systems, access controls on product design databases, network segmentation for R&D environments, and monitoring for data exfiltration. Particularly relevant for defence, aerospace, pharmaceutical, and semiconductor manufacturers where IP loss can be existential. Observable through published IP protection policies, ITAR/EAR compliance documentation, and technology vendor relationships. |
| `supply_chain_cyber_resilience` | INFERRED_PROXY | manufacturing_operations_security | Cyber resilience of the manufacturing supply chain: vendor risk assessment programme, critical supplier identification, supply chain incident response coordination, and buffer inventory/alternative sourcing capability for cyber disruption scenarios. Observable through published supply chain risk management programmes, SEC risk factor disclosures, and industry consortium participation. |
| `erp_system_security` | INFERRED_PROXY | manufacturing_operations_security | Security of ERP systems (SAP, Oracle, Microsoft Dynamics). ERP systems are the nexus of manufacturing IT — they contain production schedules, financial data, customer orders, and supply chain information. ERP compromise can halt production even without OT access by corrupting production schedules, BOM (Bill of Materials) data, or quality records. Observable through ERP platform identification, patch currency, and access control architecture. |
| `iec_62443_compliance` | DIRECT_OBSERVABLE | manufacturing_operations_security | Compliance with IEC 62443 (industrial automation and control systems cybersecurity). The de facto standard for manufacturing OT cybersecurity. Unlike NERC CIP (mandatory for electric utilities), IEC 62443 is voluntary but increasingly required by customers (particularly in automotive and aerospace supply chains). Observable through published certifications, audit reports, and customer requirements. |

### Direct Queries (Manufacturing-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_manufacturing` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `production_ot_segmented` | Are your production OT networks segmented from corporate IT networks? | `false` → | REFER override: 4. Unsegmented IT/OT in manufacturing means ransomware deployed through email phishing directly impacts production systems — the exact scenario driving manufacturing's #1 attack ranking. |
| `production_recovery_tested` | Have you tested your ability to restore production systems from backup following a simulated cyber incident within the last 12 months? | `false` → | MODIFIER applied: 1.25. Untested production recovery means BI duration is unpredictable — the difference between days and months of downtime. |
| `ransomware_playbook` | Do you maintain a ransomware-specific incident response playbook that covers both IT and production environments? | `false` → | FLAG. Manufacturing is the #1 ransomware target sector; absence of a ransomware-specific playbook (as distinct from a generic IR plan) indicates insufficient threat-specific preparation. |
| `itar_ear_controls` | If applicable: do you maintain ITAR/EAR-compliant cybersecurity controls for controlled technical data? | `false` → | REFER override: 3. ITAR/EAR non-compliance for defence/aerospace manufacturers creates regulatory liability AND indicates inadequate protection of the most sensitive IP. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0030** (0.30%) — a 50% premium over `cyber_general`'s 0.20%. Reflects manufacturing's status as the #1 ransomware target, extreme BI sensitivity (JIT supply chains, high daily production value), and structural OT security challenges.
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `business_interruption_cyber`, `contingent_business_interruption_cyber`
  - `business_interruption_cyber` is the dominant coverage for manufacturing — ransomware-driven production stoppage is the primary loss scenario. BI sublimits should be at least 60% of the aggregate limit for manufacturing accounts.
  - `contingent_business_interruption_cyber` (CBI) is new: covers the insured's BI loss arising from a cyber incident at a named supplier or customer. When Toyota's Kojima Industries supplier was attacked, Toyota's own production losses were a CBI claim, not a direct BI claim. CBI is critical for JIT manufacturers with concentrated supply chains.
- **ILF Curves**: Moderate steepness, similar to `cyber_general` up to $25M, then steeper above $50M reflecting catastrophic production stoppage scenarios. The Norsk Hydro ransomware attack (2019) cost $70M+; the JBS Foods attack (2021) cost $11M in ransom alone plus substantial BI.
- **Deductible**: Higher minimum deductible ($200K). Manufacturing BI events are high-severity by nature; the deductible should filter out minor IT incidents that don't affect production.
- **Sub-sector modifiers**:
  - Automotive: 1.20 — JIT supply chains, high daily production value ($10M+/day for major OEMs), complex Tier 1/2/3 supplier dependencies
  - Aerospace & Defence: 1.25 — IP theft targeting (nation-state), ITAR/EAR regulatory obligations, long production cycles (single aircraft worth $100M+)
  - Pharmaceutical: 1.15 — GxP (Good Practice) regulatory requirements for computerised systems, FDA 21 CFR Part 11 compliance, supply chain integrity requirements, high product value
  - Food & Beverage: 1.05 — production continuity critical (perishable goods), but lower IP concentration and simpler OT environments than automotive/aerospace
  - Chemicals: 1.10 — physical safety overlap with critical infrastructure (chemical release risk), but regulated under different frameworks (EPA RMP, CFATS rather than NERC CIP)
  - Consumer Goods/FMCG: 0.95 — moderate OT exposure, lower IP concentration, less complex supply chains
  - Semiconductor: 1.30 — highest sub-sector modifier: extreme cleanroom downtime cost ($50M+/day for leading fabs), concentrated IP (chip designs worth billions in R&D), nation-state targeting (CHIPS Act geopolitics), and complex supply chains
- **Geographic modifiers**:
  - US: 1.0 (base — litigation exposure, SEC cybersecurity disclosure requirements)
  - Germany: 1.05 (Industrie 4.0 creates deep IT/OT integration; BSI IT-Grundschutz requirements for critical manufacturing)
  - EU (ex-Germany): 1.00 (NIS2 covers manufacturing as an "important entity" with moderate obligations)
  - Japan: 0.95 (strong manufacturing cybersecurity culture post-Toyota/Kojima, lower litigation frequency)
  - China: 1.10 (IP theft risk from both external and state-adjacent actors, data localisation under PIPL)
  - APAC (ex-Japan/China): 0.90 (lower regulatory burden, emerging cybersecurity maturity)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Siemens AG** — Global industrial manufacturing and technology conglomerate
> - Revenue: €77.8B | Limit: $400M | Score: 834
> - Why: Industry-leading OT cybersecurity posture (Siemens is both a manufacturer AND an OT security vendor — they practice what they sell), published IEC 62443 compliance across manufacturing operations, comprehensive IT/OT segmentation with Purdue Model implementation, dedicated manufacturing CERT (Siemens ProductCERT), robust IP protection controls (patent portfolio management, DLP, R&D network segmentation), production recovery tested quarterly, published ransomware playbook, Dragos partnership for OT monitoring, comprehensive supply chain cyber risk programme, SOC 2 Type II and ISO 27001 certified, zero material production-impacting cyber incidents
> - Premium: €77.8B × 0.0005 × ILF(400M) = **~$38.9M base** before modifiers
> - Modifiers: Geographic (Germany: 1.05), Sub-sector (Industrial: ~1.10), Strong controls (0.75) → **Net premium: ~$34.0M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Tier Automotive Parts Manufacturer** (composite — Tier 1 automotive supplier, 8 plants, US/Mexico)
> - Revenue: $4.2B | Limit: $75M | Score: 491
> - Why: JIT supplier to 3 major OEMs (Ford, GM, Stellantis), IT/OT partially segmented (firewalled DMZ but shared Active Directory — not fully isolated), SAP ERP system 2 versions behind current (known vulnerabilities), OT network monitoring deployed at 3 of 8 plants only, no IEC 62443 compliance, production recovery procedure documented but last tested 18 months ago (direct query MODIFIER 1.25), ransomware playbook covers IT only (not production — direct query FLAG), IP protection adequate for Tier 1 (ITAR not applicable), supply chain programme exists but focused on quality not cyber
> - Referral reasons: `it_ot_segmentation_mfg <= 40` (shared AD), `production_ot_security <= 45` (partial monitoring), `production_recovery_tested = false` (MODIFIER), `erp_system_security <= 40` (unpatched SAP)
> - Premium: $4.2B × 0.0019 × ILF(75M) × 1.20 (automotive) = **~$9.6M base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Distressed Pharmaceutical Manufacturer** (composite — generic drug manufacturer, deterioration scenario)
> - Revenue: $1.8B | Limit: $25M | Score: 212
> - Why: 2 ransomware incidents in 14 months (most recent: 3-week production shutdown, $45M estimated BI loss, ransom paid), no IT/OT segmentation (flat network — production PLCs accessible from corporate network, direct query REFER), production recovery from latest incident took 21 days (recovery procedures inadequate), no OT network monitoring, ERP system (Oracle) running end-of-support version, 21 CFR Part 11 compliance deficiencies identified by FDA (warning letter issued), no ransomware-specific playbook (direct query FLAG), GxP computerised system validation lapsed for 3 production lines, IT team of 12 responsible for 4 manufacturing sites with no dedicated OT security
> - Decline triggers: `manufacturing_operations_security` group score <= 18, `production_ot_segmented = false` (REFER), `production_continuity_capability <= 15` (21-day recovery), multiple REFER/MODIFIER conditions, `breach_history <= 15` (2 ransomware events in 14 months)

---

## Configuration 7: `cyber_retail`

### The Underwriting Reality

Retail — brick-and-mortar retailers, grocery chains, convenience stores, department stores, specialty retailers, restaurant chains, hospitality and lodging — represents a sector where **the attack surface is physically distributed, the data is payment-card-centric, and the workforce is large, transient, and minimally trained on cybersecurity**. The Target breach (2013, 40M card numbers, $292M in total costs) and Home Depot breach (2014, 56M card numbers, $179M in total costs) remain defining events for the sector, demonstrating that point-of-sale (POS) system compromise at a single retailer can produce exposure measured in tens of millions of payment cards.

Retail's cyber risk profile is distinct from all other configurations:

1. **Distributed physical attack surface** — A retailer with 5,000 stores has 5,000 separate networks, 5,000 sets of POS terminals, 5,000 local management teams with varying security awareness, and 5,000 potential entry points. Each store connects back to corporate infrastructure, often via VPN or MPLS, creating a hub-and-spoke architecture where compromise of any spoke can reach the hub. The physical distribution is the primary structural vulnerability — centralised security controls must be deployed and maintained across thousands of locations with limited local IT capability. Observable through store count, geographic footprint, and published technology architecture.

2. **Payment card data concentration** — Retail is the dominant PCI-DSS industry. The volume of card-present (chip/contactless) and card-not-present (e-commerce) transactions determines PCI scope, compliance burden, and breach severity. A breach exposing payment card data triggers PCI forensic investigation (PFI) requirements, card brand fines (Visa/Mastercard assessments can reach $100K/month), card reissuance costs ($3-10 per card × millions of cards), and fraud loss liability. The severity of a payment card breach scales directly with transaction volume, not with revenue.

3. **E-commerce integration complexity** — The omnichannel transformation has created complex integration between physical and digital channels: buy-online-pickup-in-store (BOPIS), ship-from-store, in-store returns of online purchases, unified loyalty programmes, and shared customer databases across channels. Each integration point is an attack surface. E-commerce platforms process card-not-present (CNP) transactions with higher fraud rates than card-present. Observable through published omnichannel capabilities, e-commerce platform identification, and payment integration architecture.

4. **Large, transient workforce** — Retailers employ hundreds of thousands of workers with high turnover (60-80% annual turnover in food service, 40-60% in general retail). Each employee requires system access (POS, inventory, scheduling), creating massive identity management challenges. Former employees with active credentials, shared POS login credentials, and minimal security training create persistent insider threat and social engineering vulnerability. Observable through employee count, industry turnover benchmarks, and published HR/security training programmes.

5. **Franchise and licensee complexity** — Many retail brands operate through franchise models where the franchisor controls the brand and technology standards but franchisees operate independently. A franchise model creates fragmented security governance: the franchisor may mandate PCI compliance but cannot audit or enforce controls at 30,000 independent franchise locations. Observable through business model documentation, franchise disclosure documents, and published technology mandates.

### Signal Architecture Rationale

**Primary driver: Retail Operations Security — NEW GROUP (Risk: 0.25, Loss: 0.20, Exposure: 0.20 = 0.65 combined)**

Contains signals specific to retail: POS system security and architecture, payment card data handling, store network architecture, e-commerce platform security, loyalty programme data protection, and franchise/licensee security governance. The 0.20 Exposure weight reflects that retail exposure scales with both store count (physical attack surface) and transaction volume (payment card exposure), not merely with revenue.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Retained at near-`cyber_general` levels. Corporate IT infrastructure (email, ERP/merchandising systems, supply chain platforms, HR systems) is the primary initial access vector. Retail IT environments tend to be complex (legacy systems integrated with modern e-commerce platforms) and under-invested (IT budgets as % of revenue are among the lowest across industries).

**Retained: Structured Data (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Third-party ratings are moderately useful. Large retailers have extensive public-facing infrastructure (e-commerce platforms, mobile apps) that rating platforms can assess. PCI compliance status is the most valuable structured data point for retail.

**Retained: Corporate Footprint (Risk: 0.05, Loss: 0.05, Exposure: 0.05 = 0.15 combined)**

Retail companies generally have consumer-facing websites with varying levels of security documentation. Large retailers increasingly publish trust centres; smaller retailers rarely do.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `pos_system_architecture` | INFERRED_PROXY | retail_operations_security | POS terminal type (integrated vs standalone), encryption (P2PE — point-to-point encryption), tokenisation, and POS vendor (Verifone, Ingenico, Square, Toast). P2PE-certified POS systems that encrypt card data at the point of interaction and decrypt only at the processor remove card data from the merchant's environment, dramatically reducing PCI scope and breach severity. Observable through published payment technology, PCI P2PE validation lists, and vendor relationships. |
| `store_network_architecture` | INFERRED_PROXY | retail_operations_security | Network architecture connecting stores to corporate: VPN/MPLS topology, store network segmentation (POS on separate VLAN from store operations), centralised vs decentralised security management, and network monitoring coverage across store estate. The hub-and-spoke architecture is the structural vulnerability — lateral movement from a compromised store to corporate (or between stores) is the primary escalation path. Observable through published architecture, vendor relationships, and PCI ROC (Report on Compliance) scope. |
| `ecommerce_platform_security` | INFERRED_PROXY | retail_operations_security | Security of the e-commerce platform: platform identification (Shopify, Magento/Adobe Commerce, Salesforce Commerce Cloud, custom-built), web application firewall, bot protection, API security, and Magecart/digital skimming protection. E-commerce platforms are targeted by JavaScript injection attacks (Magecart) that capture payment card data in the browser. Observable through technology stack identification, published security features, and web scanning. |
| `payment_data_handling` | INFERRED_PROXY | retail_operations_security | How payment card data flows through the environment: tokenised, encrypted in transit and at rest, stored locally or centralised, retention period, and PCI scope reduction strategies (outsourcing payment processing, SAQ type). Determines breach severity — a retailer that never handles raw card data (fully outsourced, tokenised) has near-zero card breach exposure regardless of other security posture. Observable through PCI compliance documentation, payment processor relationships, and published payment architecture. |
| `loyalty_programme_security` | INFERRED_PROXY | retail_operations_security | Security of customer loyalty/rewards programmes: data collected (PII, purchase history, preferences), account security (password-only, MFA, biometric), fraud detection for points/rewards theft, and data sharing with third parties. Loyalty programme databases are high-value targets containing enriched PII with purchase history. Observable through published loyalty programme terms, app security features, and privacy documentation. |
| `franchise_security_governance` | INFERRED_PROXY | retail_operations_security | For franchise/licensee models: technology standards mandated to franchisees, compliance monitoring and audit mechanisms, incident reporting requirements, and security training mandates. A franchisor's brand is exposed to security failures at any of thousands of independent franchise locations. Observable through franchise disclosure documents, published technology standards, and franchisor security programmes. |
| `workforce_security_controls` | INFERRED_PROXY | retail_operations_security | Security controls for large, transient retail workforce: automated provisioning/deprovisioning (linked to HR system for immediate termination of access), shared credential elimination, security awareness training frequency, and privileged access management for store managers. Observable through published HR/security programmes, technology vendor relationships, and employee count. |

### Direct Queries (Retail-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_retail` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `p2pe_deployed` | Are your point-of-sale terminals PCI P2PE (Point-to-Point Encryption) certified? | `true` → | MODIFIER applied: 0.85. P2PE removes card data from the merchant's PCI scope, dramatically reducing card breach severity. This is a *favourable* modifier — one of the few direct queries that improves pricing. |
| `p2pe_deployed` | (Same question) | `false` → | MODIFIER applied: 1.10. Non-P2PE POS means card data traverses the merchant's network, creating full PCI scope exposure. |
| `ecommerce_skimming_protection` | Do you deploy JavaScript integrity monitoring or Content Security Policy to prevent digital skimming (Magecart-style) attacks on your e-commerce platform? | `false` → | FLAG. E-commerce platforms without skimming protection are vulnerable to JavaScript injection attacks that capture card data in the browser, bypassing server-side security controls. |
| `store_network_segmented` | Are POS networks in stores segmented from store operations networks and corporate access? | `false` → | MODIFIER applied: 1.20. Flat store networks allow lateral movement from any compromised store endpoint (including IoT devices, digital signage, HVAC systems) to POS terminals. |
| `automated_deprovisioning` | Is employee system access automatically deprovisioned when employment is terminated? | `false` → | FLAG. With 40-80% annual workforce turnover, manual deprovisioning guarantees persistent orphaned credentials — the Target breach was enabled by compromised credentials from an HVAC vendor. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0022** (0.22%) — a 10% premium over `cyber_general`'s 0.20%. Retail operates on thin margins (2-5% net margin) so premium must be calibrated to affordability. The modest premium increase reflects payment card exposure and distributed attack surface, offset by the sector's generally lower data sensitivity (payment cards, not PHI or financial records).
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `pci_assessment_coverage`, `business_interruption_cyber`
  - `pci_assessment_coverage` is new: covers PCI forensic investigation (PFI) costs, card brand fines and assessments (Visa/Mastercard penalty assessments for non-compliance and breach), and card reissuance costs. These are retail-specific loss categories that standard cyber policies may not explicitly cover. AIG and Beazley offer this as an explicit coverage extension for retail accounts.
- **ILF Curves**: Moderate steepness, similar to `cyber_general`. Retail severity tails are driven by card breach scale (proportional to transaction volume) and PCI assessments, but the sector's litigation exposure is lower than financial services or technology (consumer class actions for card breaches typically settle for less than healthcare or financial services breaches).
- **Deductible**: Lower minimum deductible ($50K, same as `cyber_general`). Retail operates on thin margins; high deductibles reduce policy value for mid-market retailers where a $200K deductible on a $100M revenue account may exceed annual IT security budget.
- **Sub-sector modifiers**:
  - Grocery/Supermarket: 1.10 — high transaction volume (thousands of transactions per store per day), pharmacy data (HIPAA overlap for grocery+pharmacy combos), loyalty programme data
  - Department Store/General Merchandise: 1.05 — moderate transaction volume, e-commerce integration, large store networks
  - Specialty Retail: 0.95 — smaller store counts, lower transaction volume, simpler technology stacks
  - Restaurant/Food Service: 1.00 — high turnover workforce, but typically simpler technology (POS-focused), franchise model common
  - Hospitality/Lodging: 1.15 — Marriott-scale data exposure (500M+ guest records in 2018 breach), PMS (Property Management System) integration complexity, long-stay data accumulation, loyalty programme data, credit card on file for incidentals
  - Convenience/Fuel: 1.05 — payment at pump creates specific skimming vulnerability, outdoor payment terminals harder to monitor, but smaller data exposure per location
  - Franchise-heavy (>50% franchise): +0.10 additive modifier — reflects security governance fragmentation across independent operators
- **Geographic modifiers**:
  - US: 1.0 (base — PCI enforcement, class action litigation, state breach notification laws)
  - UK: 0.95 (ICO enforcement active but lower litigation frequency; strong Chip & PIN adoption reduces card-present fraud)
  - EU: 1.00 (GDPR applies to customer data, strong payment security regulation via PSD2/SCA reduces CNP fraud)
  - APAC: 0.90 (lower card fraud rates in markets with advanced payment infrastructure — Japan, South Korea, Australia)
  - LATAM: 1.10 (emerging e-commerce markets with less mature payment security, higher card fraud rates)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Costco Wholesale** — US membership warehouse club
> - Revenue: $242B | Limit: $300M | Score: 792
> - Why: PCI Level 1 compliant with P2PE-certified POS terminals across all 861 locations (direct query favourable MODIFIER 0.85), centralised store network architecture with POS on segmented VLAN, limited e-commerce exposure (primarily in-warehouse sales), Costco.com on Salesforce Commerce Cloud with CSP implementation, automated employee provisioning/deprovisioning linked to HR system, minimal franchise exposure (company-operated stores), loyalty data limited to membership records (less enriched than points-based programmes), no material breaches in 10+ years, dedicated retail CISO
> - Premium: $242B × 0.0001 × ILF(300M) × 1.05 (general merchandise) = **~$24.2M base** before modifiers
> - Modifiers: Geographic (US: 1.0), Sub-sector (General: 1.05), P2PE (0.85), Strong controls (0.80) → **Net premium: ~$17.2M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Tier Restaurant Chain** (composite — 2,200 company-owned + 4,800 franchise locations, US/Canada)
> - Revenue: $6.8B | Limit: $50M | Score: 478
> - Why: PCI Level 1 compliant but POS terminals are not P2PE-certified (direct query MODIFIER 1.10), company-owned store networks segmented but franchise locations self-managed (franchise security governance inconsistent), no centralised monitoring of franchise POS networks, e-commerce limited to mobile ordering app (moderate exposure), workforce of 180,000 with 75% annual turnover, automated deprovisioning for company stores but manual process at franchise locations (direct query FLAG), loyalty app with 25M members (PII + purchase history), 1 localised POS compromise at franchise location in past 2 years (contained to 3 locations, 45K cards)
> - Referral reasons: `franchise_security_governance <= 40` (inconsistent franchise controls), `workforce_security_controls <= 45` (manual deprovisioning at franchises), `pos_system_architecture <= 50` (no P2PE), franchise additive modifier +0.10
> - Premium: $6.8B × 0.0014 × ILF(50M) × 1.00 (restaurant) × 1.10 (franchise) = **~$10.5M base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Distressed Specialty Retailer** (composite — fashion retailer, 450 stores + e-commerce, deterioration scenario)
> - Revenue: $2.1B | Limit: $15M | Score: 224
> - Why: 2 breaches in 18 months (POS malware affecting 280 stores — 8.2M cards exposed; followed by Magecart JavaScript injection on e-commerce platform — 340K additional cards), PCI compliance suspended (QSA failed re-assessment), POS terminals non-P2PE on flat store networks (POS on same VLAN as back-office PCs — direct query MODIFIER 1.20), e-commerce platform running outdated Magento 1 (end of life June 2020, no security patches — direct query no skimming protection FLAG), no store network segmentation (direct query MODIFIER 1.20), Visa compliance assessment of $2.8M pending, employee deprovisioning manual with average 14-day lag, CISO resigned post-breach, IT security budget cut 30% as part of cost reduction programme
> - Decline triggers: `retail_operations_security` group score <= 16, `pos_system_architecture <= 10`, `ecommerce_platform_security <= 10` (EOL Magento 1), multiple MODIFIER stacking (1.10 × 1.20 × 1.20 = 1.58), `breach_history <= 12` (2 card breaches in 18 months), PCI compliance suspended

---

## Configuration 8: `cyber_public_sector`

### The Underwriting Reality

Public sector entities — federal/central government agencies, state/provincial governments, municipal/local governments, public school districts, public universities, quasi-governmental bodies (transit authorities, port authorities, housing authorities) — present underwriting challenges that are structurally different from any private sector class. The public sector cyber insurance market is growing rapidly (municipalities now represent ~15% of cyber insurance submissions) driven by the ransomware epidemic: the City of Baltimore (2019, $18M+ in costs), City of Atlanta (2018, $17M+), Costa Rica government (2022, national emergency declared), and the epidemic of school district attacks (>1,600 US school districts hit since 2016).

The fundamental distinctions:

1. **Budget-constrained security** — Public sector IT security spending is structurally constrained by budget processes, legislative appropriations, and political priorities. A municipality's annual IT security budget may be $200K for a 2,000-employee government serving 150,000 residents. The result is predictable: outdated infrastructure, understaffed IT teams, deferred patching, and reliance on legacy systems that cannot be replaced because of budget cycles that operate in 1-2 year increments. This is not poor management — it is a structural feature of public sector funding.

2. **Essential service obligation** — Public sector entities cannot cease operations. A ransomwared municipality must continue providing police dispatch, fire response, emergency medical services, water treatment, and waste collection regardless of whether IT systems function. This creates both extreme BI exposure (the cost of manual workarounds, overtime, and service degradation) and extreme ransom payment pressure (paying the ransom may be the only way to restore services within an acceptable timeframe). Several US municipalities have paid ransoms specifically because the cost of extended manual operations exceeded the ransom demand.

3. **Citizen data at scale** — Public sector entities hold comprehensive data on every resident in their jurisdiction: tax records, voting records, property records, court records, social services records, law enforcement records, public health records, school records. This data is often more sensitive than corporate data because it is *involuntary* — citizens cannot opt out of having their data in government systems. A municipal breach can expose every resident's social security number, property tax assessment, utility billing, parking violations, and court records.

4. **Sovereignty and legal complexity** — Government entities operate under different legal frameworks than private corporations. Sovereign immunity may limit some litigation exposure but also creates unique regulatory obligations: FISMA for US federal agencies, StateRAMP for US state agencies, CMMC for defence contractors interfacing with government, and various state-specific data protection requirements. Tort claims against governments follow different procedures than commercial litigation.

5. **Political dimension** — Cyber incidents at government entities are inherently political events. A mayor's response to a ransomware attack is both an operational decision and a political one. The decision to pay or not pay a ransom may be influenced by political considerations (paying looks weak; extended outages damage re-election prospects). Insurance coverage decisions, deductible levels, and incident response authority must account for political decision-making structures.

### Signal Architecture Rationale

**Primary driver: Public Sector Cyber Posture — NEW GROUP (Risk: 0.25, Loss: 0.20, Exposure: 0.20 = 0.65 combined)**

Contains signals specific to public sector: IT budget adequacy, system modernisation status, citizen data protection, essential service continuity, inter-agency coordination, and compliance with government-specific cybersecurity frameworks. The 0.20 Exposure weight reflects that public sector exposure scales with population served and services provided, not with revenue (which is tax-funded and not a reliable risk proxy).

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Retained at near-`cyber_general` levels. Public sector IT infrastructure is typically the weakest across all sectors — legacy systems, unpatched endpoints, minimal endpoint detection, and outdated network architecture. Technical infrastructure signals are highly discriminatory in public sector because the variance is extreme: federal agencies investing billions in cybersecurity vs. a rural county with one IT person.

**Elevated: Structured Data (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Third-party ratings are useful for public sector entities with significant public-facing infrastructure (government websites, citizen portals, online services). However, many smaller municipalities have minimal public-facing IT, reducing rating platform coverage. SecurityScorecard and BitSight specifically offer public sector benchmarking.

**Deprioritised: Corporate Footprint, Network Authority**

Government websites have inherently high authority (.gov domains) and publish extensive information. Neither signal is discriminatory for public sector cybersecurity posture.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `it_budget_adequacy` | INFERRED_PROXY | public_sector_cyber_posture | IT security spending relative to entity size (population served, employee count, service complexity). Public sector IT security budgets are publicly accessible through published budgets and appropriations. The absolute number matters less than the ratio: $5M cybersecurity budget for a state government serving 10M residents ($0.50/resident) is different from $200K for a city serving 50,000 residents ($4/resident). Observable through published government budgets, IT capital plans, and security-specific appropriations. |
| `system_modernisation_status` | INFERRED_PROXY | public_sector_cyber_posture | Proportion of systems on current/supported platforms vs legacy/end-of-support systems. Public sector is the largest operator of Windows Server 2012/2008, Oracle 11g, and other end-of-support platforms because replacement requires capital appropriation. Observable through published IT modernisation plans, FedRAMP/StateRAMP migration status, and technology procurement records (which are public for government entities). |
| `essential_service_continuity` | INFERRED_PROXY | public_sector_cyber_posture | Continuity of essential services (public safety dispatch, emergency services, water/sewer, courts) during a cyber incident: documented manual procedures, tested failover for critical services, alternate dispatch capabilities, and paper-based backup processes. The primary severity determinant — a municipality that can maintain essential services manually during a ransomware incident has fundamentally different BI exposure than one that cannot. Observable through published COOP (Continuity of Operations Plans) and emergency management documentation. |
| `citizen_data_governance` | INFERRED_PROXY | public_sector_cyber_posture | Governance of citizen data: data classification scheme, access controls (role-based access to law enforcement records, court records, tax records), encryption at rest, data retention/destruction policies, and cross-agency data sharing controls. Government data is involuntary collection — citizens cannot opt out — creating heightened obligation. Observable through published data governance policies, FOI responses, and privacy officer designations. |
| `government_cyber_framework_compliance` | DIRECT_OBSERVABLE | public_sector_cyber_posture | Compliance with government-specific cybersecurity frameworks: NIST CSF adoption, CISA Cybersecurity Performance Goals (CPGs), CIS Controls implementation (MS-ISAC benchmarks), StateRAMP, FedRAMP (for cloud services), CMMC (for defence-related entities). Government entities are subject to specific framework requirements that are distinct from private sector standards. Observable through published compliance documentation, MS-ISAC membership, and audit reports. |
| `inter_agency_coordination` | INFERRED_PROXY | public_sector_cyber_posture | Participation in government cybersecurity coordination: MS-ISAC (Multi-State Information Sharing and Analysis Center) membership, CISA coordination, state fusion centre participation, regional mutual aid agreements for cyber incidents, and participation in CISA tabletop exercises. Public sector entities that coordinate with MS-ISAC and CISA have access to threat intelligence, incident response support, and Albert network monitoring sensors that materially improve their security posture. Observable through published memberships and CISA engagement documentation. |
| `election_system_exposure` | DIRECT_OBSERVABLE | public_sector_cyber_posture | For entities that administer elections: election infrastructure security (voting systems, voter registration databases, election night reporting), EAC certification, CISA election infrastructure security engagement, and published election security plans. Election-related cyber incidents produce political and legal consequences beyond normal breach costs. Observable through election administration responsibilities and CISA Election Infrastructure Information Sharing and Analysis Center (EI-ISAC) membership. |

### Direct Queries (Public Sector-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_public_sector` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `essential_services_continuity_plan` | Do you maintain tested continuity plans for essential services (public safety, emergency dispatch, water/sewer) during a cyber incident? | `false` → | REFER override: 4. Essential service interruption produces immediate public safety consequences and extreme political/legal exposure. |
| `ms_isac_member` | Are you an MS-ISAC (Multi-State Information Sharing and Analysis Center) member or equivalent government cybersecurity coordination participant? | `false` → | MODIFIER applied: 1.15. Non-participation in MS-ISAC means no access to Albert network monitoring sensors, no CISA incident response coordination, and isolation from government-specific threat intelligence. |
| `legacy_system_remediation` | Do you have a funded plan to remediate or replace end-of-support/end-of-life systems within 24 months? | `false` → | FLAG. Legacy systems without remediation plans represent persistent, known vulnerabilities that will not improve. |
| `ransom_payment_authority` | Is there a documented decision-making process and pre-delegated authority for ransom payment decisions during a cyber incident? | `false` → | FLAG. Absence of pre-established ransom payment authority means that during an active incident, decisions require political deliberation (city council votes, board meetings) that delays response and extends business interruption. |

### Pricing Philosophy

- **Basis**: **Operating budget** — NOT revenue. Public sector entities do not generate revenue in the commercial sense. Annual operating budget is the appropriate basis because it reflects entity size, service complexity, and the economic activity under the entity's governance. For entities where budget is not readily available (smaller municipalities), population served × per-capita proxy can be used.
- **Method**: MULTIPLIER on operating budget (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0018** (0.18%) of operating budget — 10% BELOW `cyber_general`'s 0.20%. Despite elevated risk, public sector pricing must reflect: (a) budget constraints — pricing that exceeds IT security budgets will not be purchased, defeating the purpose, (b) lower litigation exposure — sovereign immunity limits (but does not eliminate) some claim types, (c) public mission — insurers benefit from a stable public sector cyber insurance market.
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `business_interruption_cyber`, `regulatory_defence_cyber`
  - `cyber_extortion` is the primary coverage driver for public sector. The ransomware epidemic in municipalities and school districts makes this the most frequently triggered coverage.
  - `regulatory_defence_cyber` covers costs arising from regulatory investigations (state AG inquiries, HHS investigations for entities processing health data, DOE investigations for education entities).
  - Note: `business_interruption_cyber` for public sector measures lost revenue from fee-based services (courts, licensing, permits, parking, utility billing) plus extraordinary expenses (overtime for manual operations, emergency contractor costs, expedited hardware procurement).
- **ILF Curves**: Flatter than private sector above $25M limits. Public sector severity distributions are bounded by the absence of shareholder class actions and limited punitive damages exposure. The severity tail exists (Baltimore: $18M+, Atlanta: $17M+) but is shorter than financial services or technology.
- **Deductible**: Lower minimum deductible ($25K vs $50K in `cyber_general`). Public sector budgets often cannot absorb high deductibles; a $250K deductible on a $50M budget municipality may exceed its entire IT security allocation.
- **Sub-sector modifiers**:
  - Federal/Central Government Agency: 1.30 — maximum data exposure (citizen data at national scale), nation-state targeting, but also highest security investment (FISMA, CDM programme, CISA engagement)
  - State/Provincial Government: 1.15 — statewide citizen data (DMV, tax, health services), moderate security investment, StateRAMP adoption
  - Large Municipality (>250K population): 1.10 — complex service portfolio, moderate IT investment, high ransomware targeting
  - Small/Medium Municipality (<250K population): 1.00 — base rate; limited IT resources but also limited data exposure and simpler technology
  - Public School District: 1.05 — student data (FERPA), COPPA obligations for K-8, high ransomware targeting (1,600+ districts hit since 2016), minimal IT staffing
  - Public University: 1.10 — research data (including federally funded research), student records (FERPA), healthcare data (university hospitals — routes to `cyber_healthcare` if dominant), large and diverse user population
  - Transit/Port/Housing Authority: 0.95 — lower data sensitivity, simpler technology, but some OT exposure (transit signals, port systems)
- **Geographic modifiers**:
  - US: 1.0 (base — the global epicentre of public sector ransomware; state-specific data breach notification laws apply)
  - UK: 0.90 (NCSC provides strong free support to public sector; lower ransomware payment prevalence)
  - EU: 0.95 (NIS2 classifies public administration as essential; ENISA provides sector coordination)
  - Canada: 0.95 (provinces provide cybersecurity support to municipalities; lower litigation frequency)
  - Australia/NZ: 0.90 (ACSC Essential Eight programme provides strong government cybersecurity baseline; lower threat volume)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **State of Virginia (Commonwealth)** — US state government
> - Operating Budget: $75B | Limit: $100M | Score: 782
> - Why: Virginia Information Technologies Agency (VITA) provides centralised IT and cybersecurity for all state agencies, $120M+ annual cybersecurity investment, published NIST CSF alignment, MS-ISAC founding member, CISA Cybersecurity Performance Goals adopted, Albert sensor deployment statewide, SOC operating 24/7, StateRAMP-certified cloud migration programme, legacy system remediation funded and 70% complete, comprehensive COOP plans for essential services tested annually, dedicated CISO reporting to Secretary of Administration, documented ransom payment authority (Governor's emergency powers), inter-agency incident response coordination with Virginia State Police and Virginia National Guard Cyber Unit
> - Premium: $75B × 0.00003 × ILF(100M) × 1.15 (state) = **~$2.6M base** before modifiers
> - Modifiers: Geographic (US: 1.0), Sub-sector (State: 1.15), Strong controls (0.80) → **Net premium: ~$2.4M**

**Tier 3 — STANDARD (Refer):**
> **Mid-Size US City** (composite — 180,000 population, Midwest US)
> - Operating Budget: $680M | Limit: $10M | Score: 465
> - Why: IT department of 22 staff (1 security-focused), $380K annual cybersecurity budget ($2.11/resident), MS-ISAC member (direct query favourable), Albert sensor deployed at network perimeter, 40% of systems running Windows Server 2012 R2 (end of extended support October 2023 — direct query no funded remediation plan, FLAG), essential services continuity plan exists for police/fire dispatch (direct query satisfied) but not tested in 24 months (partial credit), email on Office 365 with MFA (positive signal), but on-premise Active Directory not yet migrated to Azure AD, no dedicated CISO, 1 ransomware incident 3 years ago (contained to Parks & Recreation department, $85K recovery cost)
> - Referral reasons: `it_budget_adequacy <= 40` ($2.11/resident is below MS-ISAC recommended minimum), `system_modernisation_status <= 35` (40% legacy), `essential_service_continuity <= 50` (plan exists but untested)
> - Premium: $680M × 0.0012 × ILF(10M) × 1.10 (large municipality) = **~$898K base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Distressed Small Municipality** (composite — 35,000 population, rural Southern US, deterioration scenario)
> - Operating Budget: $52M | Limit: $3M | Score: 195
> - Why: IT department of 2 staff (no security expertise), $45K annual cybersecurity budget ($1.29/resident), not MS-ISAC member (direct query MODIFIER 1.15), 65% of systems running Windows 7 or Server 2008 (end of support January 2020), no essential services continuity plan (direct query REFER — police dispatch runs on single on-premise server with no failover), no legacy system remediation plan (direct query FLAG), flat network with no segmentation, Active Directory forest last audited in 2017, 2 ransomware incidents in 24 months (first: 911 dispatch offline for 8 hours, reverted to radio; second: all municipal services offline for 12 days, $340K ransom paid from emergency reserves), no COOP/CISO, city council declined cybersecurity budget increase for FY2025
> - Decline triggers: `public_sector_cyber_posture` group score <= 15, `essential_services_continuity_plan = false` (REFER), `system_modernisation_status <= 10` (65% end-of-life), `breach_history <= 15` (2 ransomware incidents in 24 months, ransom paid)

---

## Configuration 9: `cyber_professional_services`

### The Underwriting Reality

Professional services firms — law firms, accounting firms, consulting firms, architecture/engineering firms, recruitment agencies, marketing/advertising agencies, real estate services — represent the largest volume segment of cyber insurance submissions that is poorly served by `cyber_general`. These are not high-hazard risks in the critical infrastructure or technology sense; they are **high-volume, data-rich businesses whose primary cyber exposure is the concentration of client confidential data and the professional liability implications of a breach**.

The Am Law 200 alone holds privileged attorney-client communications, merger & acquisition deal data, litigation strategy documents, intellectual property filings, and regulatory investigation files for the majority of Fortune 500 companies. When a law firm is breached, the exposure is not the firm's own data — it is the *clients'* data, which is often the most sensitive data those clients possess (because clients share their most sensitive matters with counsel). The same dynamic applies to accounting firms (tax returns, audit workpapers, financial statements), consulting firms (strategy documents, competitive intelligence), and engineering firms (design specifications, infrastructure blueprints).

The sector's specific characteristics:

1. **Client data concentration with privilege** — Professional services firms hold client data that is often more sensitive than the data the clients hold internally, because clients share their most confidential matters with their professional advisors. Law firm data is protected by attorney-client privilege; accounting firm data includes tax returns and audit workpapers; consulting firm data includes strategic plans and competitive intelligence. A single breach can expose sensitive data from hundreds of clients simultaneously. The professional privilege/confidentiality obligations create both heightened duty of care and elevated litigation exposure if breached.

2. **Partnership structure governance** — Most professional services firms operate as partnerships (LLPs, general partnerships) or partner-led corporations. Partnership governance creates cybersecurity challenges: technology investment decisions require partner consensus (or at minimum managing partner/executive committee approval), security policies must accommodate partner autonomy (partners resist restrictions on their workflows), and liability exposure flows through to individual partners (in LLPs, partners have limited liability but the firm's assets are fully exposed). The governance structure directly affects security investment decisions.

3. **BYOD and remote work prevalence** — Professional services are inherently mobile and relationship-driven. Partners and staff work from client sites, home offices, airports, and hotels. BYOD (Bring Your Own Device) is common, particularly for senior partners. The firm's data exists on personal devices, in personal cloud storage, and in client-provisioned environments over which the firm has limited control. This distributed data geography means that a firm's "perimeter" is effectively every device used by every professional.

4. **Email as primary workflow** — Unlike technology companies (where code repositories are the crown jewels) or manufacturers (where production systems are critical), professional services firms' primary workflow runs through email. Client communications, document exchange, deal negotiations, and matter management flow through email. Business Email Compromise (BEC) — particularly targeting wire transfer instructions in real estate closings, M&A transactions, and litigation settlements — is the single highest-frequency claim type for professional services firms.

5. **Regulatory complexity by practice area** — The regulatory obligations of a professional services firm depend on which clients they serve and what data they handle: law firms handling healthcare matters have HIPAA obligations; accounting firms have IRS Publication 4557 obligations; firms serving financial institutions may have SOX/GLBA requirements; firms with EU clients have GDPR data processor obligations. The regulatory surface is determined by client portfolio, not by the firm's own industry.

### Signal Architecture Rationale

**Primary driver: Professional Data Security — NEW GROUP (Risk: 0.25, Loss: 0.25, Exposure: 0.15 = 0.65 combined)**

Contains signals specific to professional services: client data classification and protection, matter/engagement management system security, email security depth (BEC prevention), document management system security, BYOD/mobile device management, and partnership governance of cybersecurity investment. The 0.15 Exposure weight (lower than most sector-specific configurations) reflects that professional services exposure scales with client portfolio sensitivity, not merely with firm revenue or headcount.

**Secondary driver: Technical Infrastructure (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Retained at near-`cyber_general` levels. Professional services IT infrastructure (email servers, document management, practice management, VPN/remote access) is the primary attack surface. Professional services firms tend to have moderate IT sophistication — better than public sector, weaker than technology companies.

**Elevated: Corporate Footprint (Risk: 0.10, Loss: 0.05, Exposure: 0.05 = 0.20 combined)**

Elevated from `cyber_general`. Professional services firms' public-facing presence (website, published team credentials, practice area descriptions) provides meaningful signal about the firm's client base, data sensitivity, and practice areas — which directly determine exposure. A law firm listing "M&A", "securities litigation", and "patent prosecution" as practice areas reveals high-sensitivity client data exposure. A firm listing "personal injury" and "family law" has different exposure.

**Retained: Structured Data (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Third-party ratings are moderately useful. Professional services firms with significant public-facing infrastructure (client portals, marketing websites) are visible to rating platforms. However, many smaller firms have minimal digital footprint.

**Deprioritised: Network Authority**

Professional services firms' domain authority is not meaningfully correlated with cybersecurity posture.

### New Signals (Not in `cyber_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `client_data_sensitivity` | INFERRED_PROXY | professional_data_security | Sensitivity profile of client data held: privileged legal communications, financial statements/tax returns, M&A deal data, IP filings, healthcare records, government contracts. Determines both breach severity (notification obligations, litigation exposure) and threat actor targeting (nation-state espionage targeting law firms with government clients). Observable through practice area descriptions, client lists (where published), and industry certifications. |
| `matter_management_security` | INFERRED_PROXY | professional_data_security | Security of practice/matter/engagement management systems: access controls (matter-level permissions, ethical wall/information barrier capability), encryption, audit logging, and integration with document management. For law firms, ethical walls are mandatory when representing clients with conflicting interests — the same technology that enforces ethical walls can enforce security compartmentalisation. Observable through technology platform identification and published security practices. |
| `email_security_depth` | INFERRED_PROXY | professional_data_security | Depth of email security controls: DMARC enforcement (reject policy), advanced phishing protection, BEC detection (particularly for wire transfer instruction modification), email encryption for external communications, and email DLP for sensitive client data. BEC is the #1 claim type for professional services — the average BEC loss for law firms is $150K per event. Observable through DNS records (DMARC, SPF, DKIM), email platform identification, and published email security policies. |
| `document_management_security` | INFERRED_PROXY | professional_data_security | Security of document management systems (iManage, NetDocuments, SharePoint, OpenText): access controls, encryption at rest, audit trail, version control, and external sharing controls. Document management systems contain the firm's work product — legal opinions, audit reports, engineering designs — which is the primary target for data exfiltration. Observable through DMS platform identification and published security features. |
| `byod_mobile_management` | INFERRED_PROXY | professional_data_security | BYOD and mobile device management: MDM/MAM (Mobile Device Management/Mobile Application Management) deployment, containerisation of firm data on personal devices, remote wipe capability, and device compliance policies. Professional services' mobile workforce means firm data exists on devices the firm does not own. Observable through published BYOD policies and technology platform identification. |
| `partnership_cyber_governance` | INFERRED_PROXY | professional_data_security | Governance structure for cybersecurity: CISO/CIO appointment and reporting line, partner executive committee cybersecurity mandate, cybersecurity budget approval process, and incident response authority delegation. Partnership governance can either enable or obstruct cybersecurity investment depending on managing partner commitment. Observable through published leadership structure, CIO/CISO appointment, and firm management structure. |
| `practice_area_risk_profile` | DIRECT_OBSERVABLE | professional_data_security | Risk profile determined by practice areas served: corporate/M&A (high — deal data, material non-public information), litigation (high — litigation strategy, settlement data), IP/patent (high — trade secrets, inventions), tax/estate (medium — financial data, SSNs), personal injury/family law (lower — less attractive to sophisticated threat actors). Observable through published practice areas on firm website. |

### Direct Queries (Professional Services-Specific)

In addition to the 8 direct queries inherited from `cyber_general`, `cyber_professional_services` adds:

| ID | Question | Condition | Action |
|---|---|---|---|
| `email_dmarc_enforced` | Is your email domain configured with DMARC at enforcement level (quarantine or reject policy)? | `false` → | MODIFIER applied: 1.20. Non-enforced DMARC allows domain spoofing, which is the primary vector for BEC attacks targeting the firm's clients (sending fraudulent wire transfer instructions from a spoofed firm email address). |
| `ethical_walls_capability` | For law firms: do you maintain information barrier (ethical wall) capability in your document management and matter management systems? | `false` → | FLAG. Absence of ethical wall capability indicates both regulatory risk (bar association sanctions) and security architecture weakness (inability to compartmentalise access to sensitive matters). |
| `client_data_encrypted_rest` | Is client data encrypted at rest in your document management and matter management systems? | `false` → | MODIFIER applied: 1.15. Unencrypted client data at rest means a database compromise or storage access produces immediate plaintext exposure of all client communications and work product. |
| `wire_transfer_verification` | Do you verify wire transfer instructions through out-of-band confirmation (phone callback, secondary channel) before executing or transmitting wire instructions? | `false` → | MODIFIER applied: 1.25. Wire transfer fraud (BEC targeting closing instructions, settlement payments, trust account transfers) is the single highest-frequency, highest-severity claim type for law firms and real estate services firms. Absence of out-of-band verification means a single spoofed email can produce six-figure losses. |

### Pricing Philosophy

- **Basis**: Revenue — consistent with `cyber_general`
- **Method**: MULTIPLIER on revenue (DECOUPLED limits)
- **Tier 3 (STANDARD) rate**: **0.0022** (0.22%) — a 10% premium over `cyber_general`'s 0.20%. Modest premium reflects the sector's generally moderate severity (most claims are BEC/wire fraud in the $100K-$500K range, with tail events driven by large-scale data breaches at major firms) offset by high frequency (professional services is among the highest-frequency cyber claim sectors).
- **Product types**: `cyber_liability`, `network_security`, `cyber_extortion`, `professional_liability_cyber`, `crime_cyber`
  - `professional_liability_cyber` is the critical coverage: covers third-party claims arising from the firm's failure to protect client data, including breach of fiduciary duty, breach of confidentiality, and professional negligence in data handling. This is distinct from standard professional liability (PI/E&O) which covers errors in professional work product; professional liability cyber specifically covers security failures that expose client data.
  - `crime_cyber` covers BEC/wire fraud losses: funds transfer fraud, social engineering fraud, and invoice manipulation fraud. This is the highest-frequency coverage trigger for professional services.
- **ILF Curves**: Moderate steepness, similar to `cyber_general`. Professional services severity tails are bounded by the firm's client base — even a major Am Law 100 firm breach is unlikely to produce the billion-dollar settlements seen in consumer platform or financial services breaches.
- **Deductible**: Lower minimum deductible ($25K). Professional services firms (particularly smaller law firms and accounting practices) operate on modest margins; deductibles must be calibrated to affordability.
- **Sub-sector modifiers**:
  - Am Law 100/Magic Circle Law Firm: 1.30 — maximum client data sensitivity (Fortune 500 matters, M&A deals, government investigations), nation-state targeting (Chinese state-affiliated actors targeting IP litigation firms), highest professional liability exposure
  - Am Law 200/Large Law Firm: 1.15 — significant client data sensitivity, good but variable security investment
  - Mid-Size Law Firm (50-200 attorneys): 1.00 — base rate; moderate client data, variable security maturity
  - Small Law Firm (<50 attorneys): 0.90 — lower total exposure but also lower security investment; highest BEC frequency per capita
  - Big Four Accounting: 1.25 — massive client data (audit workpapers for public companies, tax returns for thousands of entities), cross-service data exposure (audit, tax, consulting, advisory), regulatory scrutiny (PCAOB oversight)
  - Mid-Tier Accounting Firm: 1.00 — moderate client data, adequate security, lower threat targeting
  - Management Consulting (MBB/Big 4 Advisory): 1.15 — strategy documents, competitive intelligence, client presentation data; sensitive but shorter retention
  - Engineering/Architecture Firm: 0.95 — design data is valuable but less actionable for fraud; lower BEC targeting than law/accounting
  - Recruitment/Staffing Agency: 1.05 — high PII volume (candidate SSNs, background checks, salary data), moderate security maturity
  - Real Estate Services: 1.10 — wire fraud exposure is extreme (single-transaction BEC losses of $500K+ in real estate closings), title company data (PII, financial data, property records)
- **Geographic modifiers**:
  - US: 1.0 (base — deepest litigation exposure, bar association regulatory requirements, state breach notification laws)
  - UK: 1.05 (SRA (Solicitors Regulation Authority) cybersecurity requirements for law firms are among the most prescriptive professional regulatory standards globally; ICO enforcement active against professional services firms; Magic Circle firms are high-value targets)
  - EU: 1.00 (GDPR data processor obligations, bar/professional association requirements vary by jurisdiction)
  - APAC: 0.90 (lower litigation frequency, emerging professional services cyber requirements)
  - Middle East/Africa: 0.85 (lower litigation and regulatory exposure, smaller professional services market, lower threat targeting)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Clifford Chance** — Magic Circle law firm
> - Revenue: £2.1B (~$2.7B) | Limit: $150M | Score: 803
> - Why: Dedicated CISO reporting to Managing Partner, iManage document management with encryption at rest and comprehensive ethical wall capability, DMARC at reject policy across all domains (direct query favourable), advanced BEC detection (Abnormal Security or equivalent), MDM deployed across all partner and associate devices with containerised firm data, matter-level access controls with audit logging, wire transfer verification via phone callback required for all transactions (direct query favourable), SOC 2 Type II certified, ISO 27001 certified, published data classification scheme, cyber insurance programme (demonstrating risk awareness), no material breaches, SRA Cyber Security guidance compliant
> - Premium: £2.1B × 0.0004 × ILF(150M) × 1.30 (Magic Circle) = **~$1.1M base** before modifiers
> - Modifiers: Geographic (UK: 1.05), Sub-sector (Magic Circle: 1.30), Strong controls (0.80), DMARC enforced (favourable) → **Net premium: ~$960K**

**Tier 3 — STANDARD (Refer):**
> **Mid-Size US Law Firm** (composite — 120 attorneys, full-service, 3 offices, handles corporate, litigation, and real estate matters)
> - Revenue: $95M | Limit: $10M | Score: 488
> - Why: Part-time CIO (no CISO), NetDocuments cloud DMS (reasonable baseline security), DMARC at monitoring only (not enforced — direct query MODIFIER 1.20), MFA enabled for remote access but not for all internal systems, BYOD policy exists but MDM not deployed on partner devices (partners refused), ethical walls available but inconsistently applied, wire transfer verification recommended but not mandatory (direct query MODIFIER 1.25 — 2 BEC incidents in 3 years totalling $340K in wire fraud losses), client data not encrypted at rest in legacy on-premise file shares (direct query MODIFIER 1.15), practice areas include corporate M&A, commercial litigation, and real estate (high-sensitivity practice profile)
> - Referral reasons: `email_security_depth <= 40` (DMARC not enforced), `byod_mobile_management <= 35` (no MDM for partners), `wire_transfer_verification = false` (MODIFIER 1.25), `client_data_encrypted_rest = false` (MODIFIER 1.15), cumulative BEC loss history
> - Premium: $95M × 0.0014 × ILF(10M) × 1.00 (mid-size law) = **~$133K base** → Referred for senior review with BEC-specific subjectivities likely

**Tier 5 — DECLINE:**
> **Distressed Small Law Firm** (composite — 18 attorneys, personal injury + real estate + family law, single office, deterioration scenario)
> - Revenue: $8.5M | Limit: $2M | Score: 198
> - Why: No IT staff (outsourced to local MSP with no security specialisation), no DMARC (direct query MODIFIER 1.20), email on Office 365 basic (no advanced threat protection), no MFA (direct query REFER from inherited `cyber_general`), no DMS (documents stored in network file shares with no access controls), no MDM (attorneys use personal devices without any management), no wire transfer verification process (direct query MODIFIER 1.25 — 4 BEC incidents in 2 years totalling $680K in wire fraud from real estate closings), client data unencrypted on file server (direct query MODIFIER 1.15), no encryption on attorney laptops, 1 ransomware incident (attorney clicked phishing email, CryptoLocker encrypted all file shares, $15K ransom paid, backups were also encrypted), real estate practice handling 150+ closings/year with wire transfers averaging $450K
> - Decline triggers: `professional_data_security` group score <= 18, `email_security_depth <= 10` (no DMARC, no ATP), `mfa_enabled = false` (REFER from inherited), multiple MODIFIER stacking (1.20 × 1.25 × 1.15 = 1.73), `breach_history <= 15` (4 BEC + 1 ransomware in 2 years)

---

## Implementation Plan

### Phase 7 Build Sequence

The 9 sector-specific configurations should be implemented in the following sequence, driven by market priority (submission volume × premium potential) and dependency structure:

**Wave 1 — Immediate (Weeks 1-4):**

1. `cyber_healthcare` — Highest regulatory-driven demand; most clearly differentiated from `cyber_general`; HIPAA signal architecture is well-understood and data sources are established.
2. `cyber_technology` — Largest premium pool; technology company submissions are the most poorly served by `cyber_general` because supply chain amplification is completely unpriced.
3. `cyber_professional_services` — Highest submission volume after technology; the BEC/wire fraud signal architecture is relatively simple to implement and produces immediate underwriting improvement.

**Wave 2 — Near-term (Weeks 5-8):**

4. `cyber_financial_services` — High premium per account; complex regulatory signal architecture requires integration with NERC, PCI Council, and SWIFT CSP data sources.
5. `cyber_manufacturing` — Growing demand driven by ransomware epidemic; OT security signals require integration with ICS-specific data sources (Dragos, Claroty ecosystem).
6. `cyber_retail` — High submission volume; PCI and POS security signals are well-established; franchise governance signal is the primary new development.

**Wave 3 — Subsequent (Weeks 9-12):**

7. `cyber_digital_platform` — Complex pricing model (MAU-based) requires pricing engine modification; user-scale signals require new data source integrations (app analytics, web traffic estimation).
8. `cyber_critical_infrastructure` — Lower submission volume but highest per-account complexity; OT/ICS signals share infrastructure with `cyber_manufacturing` (Wave 2 dependency).
9. `cyber_public_sector` — Unique pricing basis (operating budget) requires pricing engine modification; public sector data sources (published budgets, NERC enforcement databases) require new integrations.

### Data Source Requirements by Configuration

| Configuration | New Data Sources Required | Existing Sources Leveraged |
|---|---|---|
| `cyber_healthcare` | HHS Breach Portal, OCR enforcement database, CMS star ratings, state health department registries | SecurityScorecard, BitSight, DNS records, technology stack detection |
| `cyber_financial_services` | SWIFT CSP KYC-SA registry, PCI Council QSA registry, NERC enforcement database (for some), SEC EDGAR (for public companies), OCC/FDIC enforcement actions | SecurityScorecard, BitSight, credit ratings, DNS records |
| `cyber_critical_infrastructure` | NERC CIP enforcement database, TSA pipeline compliance records, NRC 10 CFR 73.54 compliance, EPA Water Sector assessments, CISA sector coordination records | SecurityScorecard, BitSight, technology stack detection |
| `cyber_technology` | NVD/CVE databases, CISA KEV catalogue, HackerOne/Bugcrowd programme data, app store download counts, GitHub/GitLab activity (for SBOM/SSDLC signals) | SecurityScorecard, BitSight, SOC 2 report database, DNS records |
| `cyber_digital_platform` | App analytics platforms (SimilarWeb, Sensor Tower), web traffic estimation (SimilarWeb), DSA compliance registries, PCI compliance, app store data | SecurityScorecard, BitSight, DNS records, WHOIS |
| `cyber_manufacturing` | IEC 62443 certification registries, ITAR/EAR compliance (DDTC), FDA warning letters database, ICS vendor relationship data | SecurityScorecard, BitSight, SEC filings, technology stack detection |
| `cyber_retail` | PCI P2PE validation list, PCI QSA reports, franchise disclosure documents (FDD — publicly available for US franchises), e-commerce platform detection | SecurityScorecard, BitSight, PCI compliance, DNS records |
| `cyber_public_sector` | Published government budgets (USAspending.gov, state budget offices), MS-ISAC membership, CISA CPG compliance data, EAC certification, NERC enforcement | SecurityScorecard, BitSight, government procurement records |
| `cyber_professional_services` | Am Law rankings, SRA (UK) firm data, bar association registries, PCAOB audit firm data, practice area identification from firm websites | SecurityScorecard, BitSight, DNS records (DMARC), technology stack detection |

### Signal Implementation Priority

Across all 9 configurations, there are **62 new sector-specific signals** (not counting the base signals inherited from `cyber_general`). These should be prioritised by:

1. **DIRECT_OBSERVABLE signals first** — These are the easiest to implement because they use publicly available data sources with no inference required: `pci_compliance_depth`, `cve_vulnerability_history`, `nerc_cip_compliance`, `tsa_pipeline_compliance`, `user_base_scale`, `iec_62443_compliance`, `practice_area_risk_profile`, `physical_consequence_ceiling`, `regulatory_examination_history`, `election_system_exposure`, `bug_bounty_programme`.

2. **INFERRED_PROXY signals with established data sources** — Signals where the proxy data is available but requires inference: `email_security_depth` (DNS record analysis), `ecommerce_platform_security` (technology stack detection), `pos_system_architecture` (PCI documentation), `user_authentication_architecture` (observable login flow analysis).

3. **INFERRED_PROXY signals requiring new data integration** — Signals requiring new vendor relationships or data source integrations: OT/ICS signals (Dragos/Claroty data), `swift_controls` (SWIFT CSP data), `production_continuity_capability` (requires submission data), `partnership_cyber_governance` (requires submission data or manual assessment).

### Routing Table Integration

The SIC/NAICS-based routing table (Section 2) must be integrated with the existing `industry_classification` signal in `cyber_general`. Implementation approach:

1. At submission intake, the entity's SIC/NAICS code is matched against the routing table.
2. If a sector-specific configuration matches, the entity is routed to that configuration.
3. If no sector-specific configuration matches, the entity remains in `cyber_general`.
4. The routing decision is logged and auditable — underwriters can override the routing if the automated classification is incorrect (e.g., a healthcare technology company might be better served by `cyber_technology` than `cyber_healthcare` depending on whether its primary exposure is product/supply chain or patient data).
5. Entities that span multiple sectors (e.g., Amazon — technology + retail + cloud infrastructure) should be routed to the configuration reflecting their primary cyber exposure, with manual override capability.

---

## Summary of Deliverables

Phase 7 specifies 9 sector-specific cyber insurance configurations that extend the `cyber_general` base configuration from Phase 5:

| # | Configuration | Primary Group | Combined Weight | New Signals | Direct Queries | Tier 3 Rate | Pricing Basis | Key Product |
|---|---|---|---|---|---|---|---|---|
| 1 | `cyber_healthcare` | `health_data_security` | 0.65 | 8 | 4 | 0.25% | Revenue | `hipaa_regulatory_defence` |
| 2 | `cyber_financial_services` | `financial_system_security` | 0.70 | 8 | 4 | 0.28% | Revenue | `crime_cyber` |
| 3 | `cyber_critical_infrastructure` | `ot_ics_security` | 0.75 | 10 | 5 | 0.35% | Revenue | `bodily_injury_cyber` |
| 4 | `cyber_technology` | `product_supply_chain_security` | 0.70 | 8 | 4 | 0.32% | Revenue | `technology_e_and_o` |
| 5 | `cyber_digital_platform` | `platform_user_security` | 0.75 | 8 | 4 | $0.015/MAU or 0.25% | MAU/Revenue hybrid | `regulatory_defence_cyber` |
| 6 | `cyber_manufacturing` | `manufacturing_operations_security` | 0.65 | 7 | 4 | 0.30% | Revenue | `contingent_bi_cyber` |
| 7 | `cyber_retail` | `retail_operations_security` | 0.65 | 7 | 5 | 0.22% | Revenue | `pci_assessment_coverage` |
| 8 | `cyber_public_sector` | `public_sector_cyber_posture` | 0.65 | 7 | 4 | 0.18% | Operating Budget | `cyber_extortion` |
| 9 | `cyber_professional_services` | `professional_data_security` | 0.65 | 7 | 4 | 0.22% | Revenue | `crime_cyber` |
| | **TOTAL** | | | **70** | **38** | | | |

### Cross-Configuration Consistency

All 9 configurations share the following structural elements inherited from `cyber_general`:

- **Scoring framework**: 0-1000 score, same tier boundaries (PREFERRED >750, STANDARD 400-600, DECLINE <250)
- **8 base direct queries**: `mfa_enabled`, `edr_deployed`, `backup_tested`, `patch_cadence`, `security_training`, `ir_plan_tested`, `pci_scope`, `breach_history`
- **Signal group architecture**: Primary group (sector-specific) + Technical Infrastructure + Structured Data + Corporate Footprint ± sector-specific secondary groups
- **Pricing method**: MULTIPLIER with DECOUPLED limits (except `cyber_digital_platform` which uses a MAU hybrid and `cyber_public_sector` which uses operating budget)
- **Geographic modifiers**: US = 1.0 base across all configurations; EU, UK, APAC modifiers sector-calibrated
- **Example company returns**: Every configuration demonstrates Tier 1 (real company), Tier 3 (composite), and Tier 5 (composite deterioration) to validate scoring calibration

### What Phase 7 Does NOT Do

Phase 7 deliberately excludes:

1. **Aggregation modelling** — The correlation of losses across multiple insureds within a sector (e.g., a single SaaS platform compromise affecting 1,000 insured SMB customers) is a portfolio management concern, not an individual risk pricing concern. This will be addressed in a future phase on portfolio aggregation.
2. **Reinsurance treaty structure** — How sector-specific configurations map to reinsurance programmes (proportional vs excess-of-loss, sector-specific vs cross-sector treaties) is a capital management concern.
3. **Claims validation** — Backtesting the sector-specific configurations against historical claims data requires claims data that is tagged by sector, which most portfolios do not currently maintain. The configurations are designed to be backtestable once claims tagging is implemented.
4. **Dynamic re-routing** — The routing table is static (SIC/NAICS-based). Future work could implement dynamic routing based on the entity's actual risk profile (e.g., routing a healthcare technology company to `cyber_technology` if its product/supply chain exposure exceeds its patient data exposure).

---

## Appendix A: Complete New Signal Registry

All 70 new sector-specific signals across 9 configurations, alphabetised:

| Signal | Configuration | Group | Proxy Tier |
|---|---|---|---|
| `api_security_posture` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `ato_prevention_capability` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `bug_bounty_programme` | `cyber_technology` | product_supply_chain_security | DIRECT_OBSERVABLE |
| `byod_mobile_management` | `cyber_professional_services` | professional_data_security | INFERRED_PROXY |
| `cicd_pipeline_security` | `cyber_technology` | product_supply_chain_security | INFERRED_PROXY |
| `citizen_data_governance` | `cyber_public_sector` | public_sector_cyber_posture | INFERRED_PROXY |
| `client_data_sensitivity` | `cyber_professional_services` | professional_data_security | INFERRED_PROXY |
| `clinical_system_segmentation` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `connected_medical_device_security` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `content_moderation_capability` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `core_banking_resilience` | `cyber_financial_services` | financial_system_security | INFERRED_PROXY |
| `customer_data_processing_scope` | `cyber_technology` | product_supply_chain_security | INFERRED_PROXY |
| `cve_vulnerability_history` | `cyber_technology` | product_supply_chain_security | DIRECT_OBSERVABLE |
| `cyber_insurance_tower` | `cyber_financial_services` | financial_system_security | INFERRED_PROXY |
| `dependency_management` | `cyber_technology` | product_supply_chain_security | INFERRED_PROXY |
| `document_management_security` | `cyber_professional_services` | professional_data_security | INFERRED_PROXY |
| `ecommerce_platform_security` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |
| `ehr_platform_security` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `election_system_exposure` | `cyber_public_sector` | public_sector_cyber_posture | DIRECT_OBSERVABLE |
| `email_security_depth` | `cyber_professional_services` | professional_data_security | INFERRED_PROXY |
| `erp_system_security` | `cyber_manufacturing` | manufacturing_operations_security | INFERRED_PROXY |
| `essential_service_continuity` | `cyber_public_sector` | public_sector_cyber_posture | INFERRED_PROXY |
| `franchise_security_governance` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |
| `government_cyber_framework_compliance` | `cyber_public_sector` | public_sector_cyber_posture | DIRECT_OBSERVABLE |
| `health_data_volume` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `hipaa_compliance_history` | `cyber_healthcare` | health_data_security | DIRECT_OBSERVABLE |
| `ics_scada_vintage` | `cyber_critical_infrastructure` | ot_ics_security | INFERRED_PROXY |
| `iec_62443_compliance` | `cyber_manufacturing` | manufacturing_operations_security | DIRECT_OBSERVABLE |
| `inter_agency_coordination` | `cyber_public_sector` | public_sector_cyber_posture | INFERRED_PROXY |
| `interoperability_security` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `ip_protection_controls` | `cyber_manufacturing` | manufacturing_operations_security | INFERRED_PROXY |
| `it_budget_adequacy` | `cyber_public_sector` | public_sector_cyber_posture | INFERRED_PROXY |
| `it_ot_segmentation` | `cyber_critical_infrastructure` | ot_ics_security | INFERRED_PROXY |
| `it_ot_segmentation_mfg` | `cyber_manufacturing` | manufacturing_operations_security | INFERRED_PROXY |
| `loyalty_programme_security` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |
| `matter_management_security` | `cyber_professional_services` | professional_data_security | INFERRED_PROXY |
| `nerc_cip_compliance` | `cyber_critical_infrastructure` | regulatory_compliance | DIRECT_OBSERVABLE |
| `ot_incident_response` | `cyber_critical_infrastructure` | ot_ics_security | INFERRED_PROXY |
| `partnership_cyber_governance` | `cyber_professional_services` | professional_data_security | INFERRED_PROXY |
| `patient_portal_security` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `payment_data_handling` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |
| `payment_fraud_controls` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `payment_system_architecture` | `cyber_financial_services` | financial_system_security | INFERRED_PROXY |
| `pci_compliance_depth` | `cyber_financial_services` | financial_system_security | DIRECT_OBSERVABLE |
| `phi_encryption` | `cyber_healthcare` | health_data_security | INFERRED_PROXY |
| `physical_consequence_ceiling` | `cyber_critical_infrastructure` | ot_ics_security | DIRECT_OBSERVABLE |
| `platform_tenancy_architecture` | `cyber_technology` | product_supply_chain_security | INFERRED_PROXY |
| `pos_system_architecture` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |
| `practice_area_risk_profile` | `cyber_professional_services` | professional_data_security | DIRECT_OBSERVABLE |
| `privacy_by_design` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `production_continuity_capability` | `cyber_manufacturing` | manufacturing_operations_security | INFERRED_PROXY |
| `production_ot_security` | `cyber_manufacturing` | manufacturing_operations_security | INFERRED_PROXY |
| `redundancy_manual_override` | `cyber_critical_infrastructure` | ot_ics_security | INFERRED_PROXY |
| `regulatory_examination_history` | `cyber_financial_services` | financial_system_security | DIRECT_OBSERVABLE |
| `safety_instrumented_system` | `cyber_critical_infrastructure` | ot_ics_security | INFERRED_PROXY |
| `scada_network_monitoring` | `cyber_critical_infrastructure` | ot_ics_security | INFERRED_PROXY |
| `sector_specific_regulation` | `cyber_critical_infrastructure` | regulatory_compliance | INFERRED_PROXY |
| `ssdlc_maturity` | `cyber_technology` | product_supply_chain_security | INFERRED_PROXY |
| `store_network_architecture` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |
| `supply_chain_blast_radius` | `cyber_technology` | product_supply_chain_security | INFERRED_PROXY |
| `supply_chain_cyber_resilience` | `cyber_manufacturing` | manufacturing_operations_security | INFERRED_PROXY |
| `swift_controls` | `cyber_financial_services` | financial_system_security | INFERRED_PROXY |
| `system_modernisation_status` | `cyber_public_sector` | public_sector_cyber_posture | INFERRED_PROXY |
| `transaction_fraud_controls` | `cyber_financial_services` | financial_system_security | INFERRED_PROXY |
| `tsa_pipeline_compliance` | `cyber_critical_infrastructure` | regulatory_compliance | DIRECT_OBSERVABLE |
| `user_authentication_architecture` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `user_base_scale` | `cyber_digital_platform` | platform_user_security | DIRECT_OBSERVABLE |
| `user_data_minimisation` | `cyber_digital_platform` | platform_user_security | INFERRED_PROXY |
| `vendor_concentration_risk` | `cyber_financial_services` | financial_system_security | INFERRED_PROXY |
| `workforce_security_controls` | `cyber_retail` | retail_operations_security | INFERRED_PROXY |

**Distribution**: 15 DIRECT_OBSERVABLE / 55 INFERRED_PROXY

---

## Appendix B: Complete Direct Query Registry

All 38 sector-specific direct queries across 9 configurations (in addition to the 8 base queries inherited from `cyber_general`):

| Configuration | Query ID | Action if `false` | Type |
|---|---|---|---|
| `cyber_healthcare` | `hipaa_risk_assessment_current` | REFER override: 4 | Mandatory control |
| `cyber_healthcare` | `phi_encrypted_rest` | MODIFIER 1.20 | Security control |
| `cyber_healthcare` | `medical_device_inventory` | FLAG | Visibility |
| `cyber_healthcare` | `patient_portal_mfa` | MODIFIER 1.15 | Security control |
| `cyber_financial_services` | `swift_csp_compliant` | REFER override: 4 | Mandatory control |
| `cyber_financial_services` | `real_time_fraud_monitoring` | MODIFIER 1.25 | Security control |
| `cyber_financial_services` | `third_party_risk_programme` | FLAG | Risk management |
| `cyber_financial_services` | `segregation_of_duties` | MODIFIER 1.15 | Security control |
| `cyber_critical_infrastructure` | `ot_network_segmented` | REFER override: 4 | Mandatory control |
| `cyber_critical_infrastructure` | `sis_independent` | REFER override: 4 | Safety-critical |
| `cyber_critical_infrastructure` | `ot_patching_programme` | MODIFIER 1.30 | Security control |
| `cyber_critical_infrastructure` | `manual_override_capability` | FLAG + MODIFIER 1.20 | Safety control |
| `cyber_critical_infrastructure` | `cisa_coordination` | FLAG | Coordination |
| `cyber_technology` | `secure_sdlc_implemented` | REFER override: 4 | Mandatory control |
| `cyber_technology` | `sbom_generated` | FLAG | Visibility |
| `cyber_technology` | `tenant_isolation_validated` | MODIFIER 1.20 | Security control |
| `cyber_technology` | `incident_notification_sla` | FLAG | Process maturity |
| `cyber_digital_platform` | `mfa_available_all_users` | MODIFIER 1.25 | Security control |
| `cyber_digital_platform` | `credential_breach_checking` | FLAG | Security control |
| `cyber_digital_platform` | `data_retention_policy` | MODIFIER 1.15 | Data governance |
| `cyber_digital_platform` | `child_user_protections` | REFER override: 4 | Regulatory |
| `cyber_manufacturing` | `production_ot_segmented` | REFER override: 4 | Mandatory control |
| `cyber_manufacturing` | `production_recovery_tested` | MODIFIER 1.25 | Continuity |
| `cyber_manufacturing` | `ransomware_playbook` | FLAG | Preparedness |
| `cyber_manufacturing` | `itar_ear_controls` | REFER override: 3 | Regulatory |
| `cyber_retail` | `p2pe_deployed` (true) | MODIFIER 0.85 (favourable) | Security control |
| `cyber_retail` | `p2pe_deployed` (false) | MODIFIER 1.10 | Security control |
| `cyber_retail` | `ecommerce_skimming_protection` | FLAG | Security control |
| `cyber_retail` | `store_network_segmented` | MODIFIER 1.20 | Security control |
| `cyber_retail` | `automated_deprovisioning` | FLAG | Access control |
| `cyber_public_sector` | `essential_services_continuity_plan` | REFER override: 4 | Safety-critical |
| `cyber_public_sector` | `ms_isac_member` | MODIFIER 1.15 | Coordination |
| `cyber_public_sector` | `legacy_system_remediation` | FLAG | Remediation |
| `cyber_public_sector` | `ransom_payment_authority` | FLAG | Governance |
| `cyber_professional_services` | `email_dmarc_enforced` | MODIFIER 1.20 | Security control |
| `cyber_professional_services` | `ethical_walls_capability` | FLAG | Regulatory |
| `cyber_professional_services` | `client_data_encrypted_rest` | MODIFIER 1.15 | Security control |
| `cyber_professional_services` | `wire_transfer_verification` | MODIFIER 1.25 | Fraud prevention |

**Distribution**: 8 REFER / 15 MODIFIER / 15 FLAG

---

## Appendix C: Pricing Rate Summary

| Configuration | Tier 3 Rate | vs `cyber_general` | Min Deductible | Pricing Basis |
|---|---|---|---|---|
| `cyber_general` (Phase 5) | 0.20% | — | $50K | Revenue |
| `cyber_healthcare` | 0.25% | +25% | $75K | Revenue |
| `cyber_financial_services` | 0.28% | +40% | $250K | Revenue |
| `cyber_critical_infrastructure` | 0.35% | +75% | $500K | Revenue |
| `cyber_technology` | 0.32% | +60% | $100K | Revenue |
| `cyber_digital_platform` | $0.015/MAU or 0.25% | +25% (rev component) | $150K | MAU/Revenue hybrid |
| `cyber_manufacturing` | 0.30% | +50% | $200K | Revenue |
| `cyber_retail` | 0.22% | +10% | $50K | Revenue |
| `cyber_public_sector` | 0.18% | -10% | $25K | Operating Budget |
| `cyber_professional_services` | 0.22% | +10% | $25K | Revenue |

---

## Appendix D: New Product Type Registry

Product types introduced by sector-specific configurations (not available in `cyber_general`):

| Product Type | Introduced By | Description |
|---|---|---|
| `hipaa_regulatory_defence` | `cyber_healthcare` | Regulatory investigation costs, defence costs, and fines arising from HHS/OCR enforcement actions for HIPAA violations |
| `crime_cyber` | `cyber_financial_services`, `cyber_professional_services` | Fraudulent electronic fund transfers, social engineering fraud (BEC), unauthorised transaction losses |
| `bodily_injury_cyber` | `cyber_critical_infrastructure` | Bodily injury and property damage arising from cyber-physical incidents (water contamination, explosion, chemical release) |
| `technology_e_and_o` | `cyber_technology` | Third-party claims arising from security failures in the insured's technology products or services |
| `media_liability_cyber` | `cyber_technology`, `cyber_digital_platform` | Content-related claims: defamation, IP infringement, privacy violations from hosted/distributed content |
| `contingent_business_interruption_cyber` | `cyber_manufacturing` | Insured's BI loss from cyber incident at named supplier/customer (supply chain BI) |
| `pci_assessment_coverage` | `cyber_retail` | PCI forensic investigation costs, card brand fines/assessments, card reissuance costs |
| `regulatory_defence_cyber` | `cyber_digital_platform`, `cyber_public_sector` | Multi-jurisdictional regulatory investigation costs, defence, and insurable fines |
| `professional_liability_cyber` | `cyber_professional_services` | Third-party claims for breach of fiduciary duty, confidentiality breach, professional negligence in data handling |

---

## Appendix E: Sub-Sector Modifier Summary

Complete listing of all sub-sector modifiers across configurations:

| Configuration | Sub-Sector | Modifier | Rationale (abbreviated) |
|---|---|---|---|
| **Healthcare** | Hospital System (>500 beds) | 1.20 | Maximum PHI volume, complex clinical systems |
| | Hospital System (<500 beds) | 1.05 | Moderate PHI, simpler systems |
| | Health Insurer/Payer | 1.15 | Population-scale claims data |
| | Pharma/Biotech | 0.90 | Clinical trial data, less patient care data |
| | Ambulatory/Outpatient | 0.85 | Lower data volume, simpler systems |
| | Digital Health/Telehealth | 1.10 | Technology + healthcare hybrid risk |
| **Financial Services** | (No sub-sector modifiers — addressed via signal weights) | — | — |
| **Critical Infrastructure** | Electric (Transmission) | 1.30 | Grid stability, NERC CIP |
| | Electric (Distribution) | 1.10 | Consumer impact, lower interconnect |
| | Oil & Gas (Pipeline) | 1.25 | Colonial Pipeline severity |
| | Oil & Gas (Upstream/Refining) | 1.15 | Physical safety risk |
| | Water/Wastewater | 1.05 | Public safety but lower value targets |
| | Telecommunications | 0.90 | IT-based, less OT exposure |
| | Transportation (Rail) | 1.10 | PTC systems, FRA-regulated |
| | Transportation (Aviation) | 1.20 | FAA requirements, flight systems |
| **Technology** | SaaS Platform (B2B) | 1.20 | Multi-tenant, customer data |
| | Cloud Infrastructure | 1.35 | Maximum blast radius |
| | MSP | 1.30 | Privileged customer access |
| | Enterprise Software | 1.10 | Supply chain but on-premise |
| | Cybersecurity Vendor | 1.15 | High-value target, reputational |
| | Hardware/Semiconductor | 0.85 | Lower cyber exposure |
| | Consumer Technology | 1.00 | Base rate |
| **Digital Platform** | Social Media/UGC | 1.25 | Max user data, content liability |
| | E-commerce Marketplace | 1.20 | Payment fraud, merchant vetting |
| | Online Gaming | 1.10 | Virtual assets, younger users |
| | Streaming Service | 0.95 | Subscription model, lower risk |
| | Gig Economy | 1.15 | Worker data, payments |
| | Digital Advertising | 1.10 | Privacy/tracking exposure |
| | Online Travel Agency | 1.05 | Payment data, PII volume |
| **Manufacturing** | Automotive | 1.20 | JIT, high daily production value |
| | Aerospace & Defence | 1.25 | IP theft, ITAR, long cycles |
| | Pharmaceutical | 1.15 | GxP, FDA compliance |
| | Food & Beverage | 1.05 | Perishable, simpler OT |
| | Chemicals | 1.10 | Physical safety overlap |
| | Consumer Goods/FMCG | 0.95 | Moderate exposure |
| | Semiconductor | 1.30 | Extreme downtime cost, IP |
| **Retail** | Grocery/Supermarket | 1.10 | High transaction volume, pharmacy |
| | Department Store | 1.05 | Moderate transaction, e-commerce |
| | Specialty Retail | 0.95 | Smaller footprint |
| | Restaurant/Food Service | 1.00 | Base, franchise common |
| | Hospitality/Lodging | 1.15 | Guest records, PMS complexity |
| | Convenience/Fuel | 1.05 | Pump skimming vulnerability |
| | Franchise-heavy (>50%) | +0.10 | Additive, governance fragmentation |
| **Public Sector** | Federal/Central Government | 1.30 | National-scale data, nation-state |
| | State/Provincial | 1.15 | Statewide citizen data |
| | Large Municipality (>250K) | 1.10 | Complex services, moderate IT |
| | Small/Medium Municipality | 1.00 | Base rate |
| | Public School District | 1.05 | Student data, FERPA, high targeting |
| | Public University | 1.10 | Research + student + healthcare |
| | Transit/Port/Housing Authority | 0.95 | Lower data, some OT |
| **Professional Services** | Am Law 100/Magic Circle | 1.30 | Max sensitivity, nation-state |
| | Am Law 200/Large Law | 1.15 | Significant client data |
| | Mid-Size Law (50-200) | 1.00 | Base rate |
| | Small Law (<50) | 0.90 | Lower exposure, higher BEC/capita |
| | Big Four Accounting | 1.25 | Audit workpapers, cross-service |
| | Mid-Tier Accounting | 1.00 | Base rate |
| | Management Consulting | 1.15 | Strategy documents |
| | Engineering/Architecture | 0.95 | Design data, lower BEC |
| | Recruitment/Staffing | 1.05 | Candidate PII volume |
| | Real Estate Services | 1.10 | Wire fraud exposure |

---

## Appendix F: Geographic Modifier Summary

| Configuration | US | UK | EU | APAC | Other |
|---|---|---|---|---|---|
| `cyber_healthcare` | 1.0 | 0.90 | 1.05 | 0.85 | — |
| `cyber_financial_services` | 1.0 | 1.10 | 1.15 | 0.95 | — |
| `cyber_critical_infrastructure` | 1.0 | 1.05 | 1.10 | 0.95 | ME: 1.25 |
| `cyber_technology` | 1.0 | 0.95 | 1.10 | — | Israel: 1.05 |
| `cyber_digital_platform` | 1.0 | 1.05 | 1.20 | 0.95 | China: 1.15 |
| `cyber_manufacturing` | 1.0 | — | 1.00 | 0.90 | Germany: 1.05, Japan: 0.95, China: 1.10 |
| `cyber_retail` | 1.0 | 0.95 | 1.00 | 0.90 | LATAM: 1.10 |
| `cyber_public_sector` | 1.0 | 0.90 | 0.95 | 0.90 | Canada: 0.95 |
| `cyber_professional_services` | 1.0 | 1.05 | 1.00 | 0.90 | ME/Africa: 0.85 |

---

## Appendix G: Configuration Architecture Cross-Reference

How each configuration re-weights the standard signal groups from `cyber_general`:

| Group | `cyber_general` | Healthcare | Fin Svcs | Critical Infra | Technology | Digital Platform | Manufacturing | Retail | Public Sector | Prof Svcs |
|---|---|---|---|---|---|---|---|---|---|---|
| **Sector-specific** | — | 0.65 | 0.70 | 0.75 + 0.30¹ | 0.70 | 0.75 | 0.65 | 0.65 | 0.65 | 0.65 |
| **Technical Infra** | 0.45 | 0.40 | 0.40 | 0.25 | 0.40 | 0.30 | 0.40 | 0.40 | 0.40 | 0.40 |
| **Structured Data** | 0.25 | 0.25 | 0.35 | 0.25 | 0.35 | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 |
| **Corporate Footprint** | 0.15 | 0.15 | ↓ | ↓ | 0.15 | 0.15 | 0.15 | 0.15 | ↓ | 0.20 |
| **Network Authority** | 0.10 | ↓ | 0.30 | ↓ | ↓ | ↓ | — | — | ↓ | ↓ |

¹ Critical Infrastructure has two sector-specific groups: `ot_ics_security` (0.75) and `regulatory_compliance` (0.30)

Note: Weights across Risk/Loss/Exposure dimensions do not sum to 1.0 within a configuration because they are applied as relative weights within each dimension, not as a single allocation. The combined weights shown are the sum of (Risk + Loss + Exposure) weights for each group.

---

## Appendix H: Example Company Cross-Reference

All 27 example company returns across 9 configurations:

| Tier | Configuration | Entity | Revenue/Budget | Limit | Score | Outcome |
|---|---|---|---|---|---|---|
| **T1** | Healthcare | Cleveland Clinic | $14.8B | $200M | 823 | Auto-Approve |
| **T1** | Financial Services | JPMorgan Chase | $158B | $500M | 889 | Auto-Approve |
| **T1** | Critical Infrastructure | Dominion Energy | $14.4B | $250M | 812 | Auto-Approve |
| **T1** | Technology | Microsoft | $236B | $500M | 856 | Auto-Approve |
| **T1** | Digital Platform | Booking Holdings | $21.4B | $300M | 798 | Auto-Approve |
| **T1** | Manufacturing | Siemens AG | €77.8B | $400M | 834 | Auto-Approve |
| **T1** | Retail | Costco Wholesale | $242B | $300M | 792 | Auto-Approve |
| **T1** | Public Sector | State of Virginia | $75B budget | $100M | 782 | Auto-Approve |
| **T1** | Professional Services | Clifford Chance | £2.1B | $150M | 803 | Auto-Approve |
| **T3** | Healthcare | Regional Health System | $2.8B | $50M | 512 | Refer |
| **T3** | Financial Services | Mid-Tier Regional Bank | $2.1B | $50M | 534 | Refer |
| **T3** | Critical Infrastructure | Mid-Tier Pipeline | $3.2B | $100M | 498 | Refer |
| **T3** | Technology | Mid-Tier SaaS | $450M | $50M | 512 | Refer |
| **T3** | Digital Platform | Social Commerce | $620M | $50M | 489 | Refer |
| **T3** | Manufacturing | Auto Parts Manufacturer | $4.2B | $75M | 491 | Refer |
| **T3** | Retail | Restaurant Chain | $6.8B | $50M | 478 | Refer |
| **T3** | Public Sector | Mid-Size US City | $680M budget | $10M | 465 | Refer |
| **T3** | Professional Services | Mid-Size Law Firm | $95M | $10M | 488 | Refer |
| **T5** | Healthcare | Distressed Rural Hospital | $320M | $5M | 218 | Decline |
| **T5** | Financial Services | Distressed Fintech | $890M | $25M | 241 | Decline |
| **T5** | Critical Infrastructure | Distressed Water Utility | $180M | $10M | 198 | Decline |
| **T5** | Technology | Distressed MSP | $85M | $10M | 203 | Decline |
| **T5** | Digital Platform | Distressed Social Platform | $340M | $25M | 187 | Decline |
| **T5** | Manufacturing | Distressed Pharma Mfg | $1.8B | $25M | 212 | Decline |
| **T5** | Retail | Distressed Specialty Retailer | $2.1B | $15M | 224 | Decline |
| **T5** | Public Sector | Distressed Municipality | $52M budget | $3M | 195 | Decline |
| **T5** | Professional Services | Distressed Small Law Firm | $8.5M | $2M | 198 | Decline |

**Score calibration observation**: Tier 1 scores range 782-889 (all >750 PREFERRED threshold); Tier 3 scores range 465-534 (all within 400-600 STANDARD band); Tier 5 scores range 187-241 (all <250 DECLINE threshold). This confirms consistent scoring calibration across all 9 configurations against the same tier boundaries.

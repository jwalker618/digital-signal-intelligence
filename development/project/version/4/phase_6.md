# Phase 6: Professional Indemnity Coverage Expansion — Full Spectrum Configuration Suite

## Context & Motivation

Professional Indemnity is the most heterogeneous coverage class in commercial insurance. Unlike energy (where risk is fundamentally physical) or cyber (where risk is fundamentally digital), PI risk spans *advisory*, *regulatory*, *fiduciary*, *design*, *transactional*, and *reputational* dimensions — and the relative importance of each dimension shifts radically depending on the profession being insured.

A securities law firm and a structural engineering practice share almost nothing actuarially. The law firm's risk is driven by lateral partner churn, conflict-of-interest failures, and class action exposure. The engineering firm's risk is driven by structural failure claims, PE license compliance, and project concentration. Yet today, DSI has only two PI configurations attempting to price all of it: `pi_general` for corporate practices and `pi_sme` for small firms.

This is equivalent to the pre-Phase 5 energy coverage — one general model trying to serve an entire market that is, in actuarial reality, a dozen distinct markets.

### Why This Matters for Production & Demo

1. **Production Pipeline Readiness**: PI submissions represent the highest volume coverage class in the DSI pipeline. Brokers submitting law firms, accounting practices, and engineering consultancies expect the system to understand their profession's specific risk drivers. A general model that weights "regulatory_standing" identically for a Big 4 audit firm and a solo real estate appraiser will produce pricing that no underwriter trusts.

2. **Demo Credibility**: When demonstrating DSI to professional lines underwriters at Lloyd's, Beazley, or Hiscox, the system must show it *understands* that a PCAOB inspection deficiency is qualitatively different from a building code violation. A single configuration cannot make this distinction. An underwriter who sees the same signal weights applied to PricewaterhouseCoopers and a three-person architecture firm will immediately question the model's credibility.

3. **Multiplexer Demonstration**: With thirteen PI configurations at varying `model_specificity` levels (1-4), PI joins energy as a definitive showcase for the V4 multiplexer's intelligent routing. The `profession_segment` pre-routing field — analogous to energy's `operation_segment` — enables precise configuration selection.

4. **Regulatory Alignment**: Professional liability is the most heavily regulated segment of commercial insurance. Different professions face different regulatory regimes (SRA for solicitors, PCAOB for auditors, PE boards for engineers, FCA for financial advisers). Profession-specific configurations allow DSI to encode these regulatory realities directly into signal architecture, rather than treating all regulatory signals as interchangeable.

### Why Not Medical Malpractice?

Medical malpractice is deliberately excluded from the PI coverage expansion. Med-mal is a separate coverage line with fundamentally different characteristics:

- **Bodily injury component** — PI is a financial loss coverage; med-mal has bodily injury and wrongful death elements
- **Consent and standard-of-care dynamics** — Med-mal claims turn on clinical standards, informed consent, and patient expectations that have no analogue in professional services
- **Policy form differences** — Med-mal uses occurrence-based and claims-made forms with fundamentally different tail structures
- **Regulatory regime** — Medical licensing boards operate under different statutory frameworks than professional licensing bodies

Med-mal will be addressed in a dedicated coverage expansion phase, not shoehorned into PI.

---

## The Thirteen-Configuration Architecture

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

### Routing Logic

The multiplexer evaluates routing constraints in descending specificity order. The first configuration whose constraints are satisfied wins. `profession_segment` is an optional input field (see Appendix G.1) — when provided, it enables specific routing; when absent, submissions default to `pi_general`.

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

### Key Design Decisions

1. **Geographic variance via modifiers, not separate configs** — US plaintiff-friendly jurisdiction loading, UK SRA/FCA regulatory overlay, EU mandatory PI requirements handled as jurisdiction modifiers within each config. Otherwise we would need 40+ configurations.
2. **`profession_segment` as pre-routing field** — Mirrors energy's `operation_segment`. Optional input. When absent, routes to `pi_general`.
3. **`sub_profession_type` as secondary routing** — For legal (SECURITIES, CORPORATE_MA, PLAINTIFF, etc.) and accounting (AUDIT_PUBLIC, AUDIT_PRIVATE, TAX, ADVISORY, etc.) where intra-profession variance is significant.
4. **pi_accounting and pi_management_consulting reuse existing 7 groups** — No new signal group needed; adjusted weights and a few new signals added to existing groups suffice.
5. **All other configs introduce exactly one new profession-specific group** — Keeps the architecture clean and consistent with Phase 5's pattern.
6. **Pricing: all new configs use DECOUPLED** — Only `pi_sme` uses BUNDLED. New configs use MULTIPLIER on revenue with profession-specific rate tables.

---

## Configuration 1: `pi_legal_large`

### The Underwriting Reality

Large law firms — the AmLaw 200, Magic Circle, and their international equivalents — represent the single highest-severity segment in professional indemnity. A securities class action defense gone wrong can produce a $500M+ malpractice claim. A conflict-of-interest failure in a $10B merger can generate losses that dwarf the firm's entire annual revenue.

These firms are also the most commercially valuable PI submissions. A top-50 US law firm might pay $5-15M annually in PI premium. They demand — and deserve — a pricing model that understands the specific risk drivers of large legal practice:

1. **Lateral partner movement** — The single biggest driver of claims frequency in large firms. A lateral hire brings legacy clients, legacy conflicts, and legacy exposure from their prior firm. The "prior acts" tail is where the bodies are buried.
2. **Practice area mix** — A firm with 60% securities litigation has fundamentally different exposure than one with 60% real estate transactions. The `sub_profession_type` categorical modifier captures this, but the `partner_practice_mix` group goes deeper.
3. **Conflict-of-interest systems** — Large firms handle thousands of matters simultaneously across jurisdictions. The sophistication of their conflict-checking systems is directly predictive of claim frequency.
4. **Client trust account compliance** — Mishandling of IOLTA/client trust accounts is the fastest path to bar disciplinary action and malpractice claims. It is observable, binary, and highly predictive.

### Signal Architecture Rationale

**Primary driver: Regulatory Standing (Risk: 0.20, Loss: 0.20, Exposure: 0.10 = 0.50 combined)**

For large law firms, regulatory standing is the bedrock signal. Bar disciplinary history, malpractice record, and peer review results are publicly available and directly predictive. PCAOB standing is irrelevant here but `specialty_certification` and `peer_review` carry elevated weight.

**Secondary driver: Firm Stability (Risk: 0.20, Loss: 0.15, Exposure: 0.20 = 0.55 combined)**

Large firms face existential risk from partner departures. The collapse of Dewey & LeBoeuf (2012) and Brobeck, Phleger & Harrison (2003) demonstrated that partner exodus can destroy a firm faster than any malpractice claim. Tenure, partner stability, and succession planning are critical signals.

**New group: Partner Practice Mix (Risk: 0.10, Loss: 0.10, Exposure: 0.25 = 0.45 combined)**

This group captures the specific tail-risk drivers of large legal practice. The high exposure weight (0.25) reflects the concentration risk inherent in large-firm practice — a single mega-matter can represent catastrophic exposure.

**Deprioritised: Corporate Footprint**

Large law firms have excellent websites. Their marketing quality tells us nothing about their malpractice risk. Corporate footprint weight is reduced to (0.05 / 0.05 / 0.10).

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `lateral_hire_volume` | INFERRED_PROXY | partner_practice_mix | Rate of lateral partner additions; higher churn = legacy claims risk from prior acts |
| `prior_acts_coverage` | DIRECT_OBSERVABLE | partner_practice_mix | Prior acts tail coverage status — gap in tail = uncovered legacy exposure |
| `conflict_system_quality` | INFERRED_PROXY | partner_practice_mix | Conflict-of-interest screening system sophistication; failure = dual-representation claims |
| `trust_account_compliance` | DIRECT_OBSERVABLE | partner_practice_mix | Client trust/IOLTA account compliance; violations are disciplinary-level signals |
| `class_action_exposure` | INFERRED_PROXY | partner_practice_mix | Exposure from class action representation/defense; single-matter concentration risk |
| `partner_departure_rate` | DIRECT_OBSERVABLE | partner_practice_mix | Partner departure rate; key tail exposure driver and firm stability indicator |
| `matter_concentration` | INFERRED_PROXY | partner_practice_mix | Single-matter revenue concentration; >15% from one matter = concentration risk |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0028** (0.28%). Approximately 55% premium over `pi_general`'s 0.0018, reflecting the severity exposure inherent in large legal practice.
- **Limit Configuration**: **DECOUPLED** — large law firms purchase bespoke tower structures. Base limit reference: $5,000,000 with $250,000 deductible.
- **Min Premium**: $100,000 (vs $25,000 for `pi_general`)
- **Product types**: `professional_liability`, `errors_omissions`
- **ILF characteristics**: Steeper than general for limits above $10M, reflecting securities litigation tail risk.

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Kirkland & Ellis** (AmLaw #1 by revenue)
> - Revenue: $7.2B | Limit: $50M | Score: 847
> - Why: Best-in-class conflict systems, low partner departure rate, clean disciplinary record, prior acts fully covered, diversified practice mix across PE, restructuring, and litigation
> - Premium: $7.2B × 0.0012 = $8.64M base → sub_profession modifier (CORPORATE_MA: 1.25) → firm_size modifier (MAJOR: 0.85) → jurisdiction modifier (US: 1.05) → **~$9.6M net**

**Tier 3 — STANDARD:**
> **White & Case** (AmLaw top-50, international)
> - Revenue: $2.8B | Limit: $25M | Score: 582
> - Why: Recent lateral hiring surge (12 partners in 18 months), moderate matter concentration in cross-border arbitration, adequate conflict systems, clean regulatory standing
> - Premium: $2.8B × 0.0028 = $7.84M base → sub_profession modifier (CORPORATE_MA: 1.25) → firm_size modifier (MAJOR: 0.85) → **~$8.3M net**

**Tier 5 — DECLINE:**
> **Mid-tier firm with partner exodus** (composite profile)
> - Revenue: $180M | Limit: $10M | Score: 198
> - Why: 8 of 22 equity partners departed in 12 months, trust account irregularities under investigation, prior acts gap from failed merger, 3 pending malpractice suits, bar disciplinary proceeding against managing partner
> - Decline triggers: firm_stability group score <= 15, regulatory_standing score <= 20, partner_departure_rate <= 10

---

## Configuration 2: `pi_legal_specialist`

### The Underwriting Reality

Specialist and plaintiff law firms operate in a fundamentally different economic model from large corporate firms. A securities plaintiff boutique — five partners, $30M in revenue — may have a single case worth $500M in contingent fees. A personal injury plaintiff firm may have 200 active cases, each with a different statute of limitations deadline. A white-collar defense specialist may represent a single client in a multi-year DOJ investigation.

The risk drivers are completely different from `pi_legal_large`:

1. **Case concentration** — A specialist firm may derive 40%+ of revenue from a single case or client. If that case goes wrong (missed deadline, conflict, malpractice), the claim can exceed the firm's total revenue.
2. **Contingency fee exposure** — Plaintiff firms that work on contingency have different exposure profiles. A failed case produces no revenue but full malpractice exposure. The contingency-to-hourly ratio is a direct loss predictor.
3. **Statute of limitations tracking** — Missing a statute of limitations deadline is the #1 cause of legal malpractice claims by frequency. The sophistication of a firm's docketing and deadline-tracking system is directly predictive.
4. **Trial success rate** — For litigation specialists, win/loss record is a quality proxy. A firm with consistently poor outcomes faces both malpractice exposure and adverse selection (they attract desperate clients with weak cases).

### Signal Architecture Rationale

**Primary driver: Regulatory Standing (Risk: 0.25, Loss: 0.20, Exposure: 0.10 = 0.55 combined)**

Specialist practitioners face disproportionate regulatory scrutiny. A securities plaintiff attorney drawing SEC attention, a criminal defense attorney with bar complaints — these are high-signal events.

**Secondary driver: Litigation History (Risk: 0.15, Loss: 0.20, Exposure: 0.15 = 0.50 combined)**

For specialist firms, their own litigation history (malpractice suits, fee disputes, regulatory enforcement) is the most directly predictive loss signal. Elevated loss weight reflects severity.

**New group: Case Portfolio (Risk: 0.10, Loss: 0.10, Exposure: 0.35 = 0.55 combined)**

The case portfolio group captures the unique concentration and tail risk of specialist practice. The extremely high exposure weight (0.35) reflects the reality that a single case can define a specialist firm's entire risk profile.

**Deprioritised: Technical Infrastructure, Corporate Footprint**

Specialist firms are small. Their website quality and email authentication are noise. These groups receive minimal weight (0.05 each).

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `case_concentration` | INFERRED_PROXY | case_portfolio | Single-case exposure as % of revenue; >25% triggers concentration flag |
| `contingency_fee_ratio` | DIRECT_OBSERVABLE | case_portfolio | Contingency vs hourly fee mix; high contingency = asymmetric exposure |
| `trial_success_rate` | INFERRED_PROXY | case_portfolio | Win/loss record as quality proxy; consistently poor outcomes = adverse selection |
| `statute_tracking_compliance` | INFERRED_PROXY | case_portfolio | SOL/deadline tracking system effectiveness; failures are the #1 malpractice claim |
| `case_value_distribution` | INFERRED_PROXY | case_portfolio | Distribution of case values; fat tail = severity concentration risk |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0032** (0.32%). The highest legal rate, reflecting concentration risk and the severity tail of specialist practice.
- **Limit Configuration**: **DECOUPLED** — $1,000,000 base limit with $50,000 deductible.
- **Min Premium**: $25,000
- **Product types**: `professional_liability`, `errors_omissions`
- **Sub-profession modifiers**: Securities (1.40), Personal Injury Plaintiff (1.30), Corporate M&A (1.25), Trusts & Estates (1.20), Environmental (1.20), Tax (1.15), Bankruptcy (1.15), Healthcare (1.15), IP (1.15), Plaintiff Litigation (1.15), Real Estate (1.10), Employment (1.10), Insurance Coverage (1.05), General Practice (1.05), General Litigation (1.00), PI Defense (0.95), Family (0.90), Criminal (0.85)

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Wachtell, Lipton, Rosen & Katz** (elite M&A specialist)
> - Revenue: $1.1B | Limit: $25M | Score: 891
> - Why: Pristine disciplinary record, zero malpractice history, best-in-class conflict systems, no partner departures in 5 years, diversified mega-deal portfolio, all hourly billing (no contingency exposure)
> - Premium: $1.1B × 0.0015 = $1.65M base → sub_profession modifier (CORPORATE_MA: 1.25) → firm_size modifier (MEDIUM: 0.95) → **~$1.96M net**

**Tier 3 — STANDARD:**
> **Plaintiff securities boutique** (composite profile)
> - Revenue: $45M | Limit: $5M | Score: 552
> - Why: 60% contingency fee revenue, moderate case concentration (top 3 cases = 35% of revenue), adequate statute tracking, one prior malpractice settlement (5 years ago), active bar standing
> - Premium: $45M × 0.0032 = $144,000 base → sub_profession modifier (SECURITIES: 1.40) → firm_size modifier (SMALL: 1.00) → **~$201,600 net**

**Tier 5 — DECLINE:**
> **Solo practitioner with bar issues** (composite profile)
> - Revenue: $800K | Limit: $1M | Score: 165
> - Why: Active bar disciplinary proceeding (trust account violations), 2 pending malpractice suits, missed statute of limitations on $5M case, 95% contingency practice, no malpractice insurance for prior 12 months
> - Decline triggers: regulatory_standing group score <= 10, statute_tracking_compliance <= 5

---

## Configuration 3: `pi_audit`

### The Underwriting Reality

Public company audit is the highest-severity segment in all of professional indemnity — and it is not close. When an audit firm signs an unqualified opinion on financial statements that later prove materially misstated, the resulting securities class action names the auditor alongside the company's officers and directors. The settlement exposure can reach billions.

Arthur Andersen's collapse after Enron (2002) remains the defining case study: a single engagement failure destroyed an 89-year-old firm with 85,000 employees. More recently, PCAOB inspection deficiencies at mid-tier audit firms have led to SEC enforcement actions, client restatements, and malpractice suits that threaten firm survival.

The audit PI market is unique in several respects:

1. **PCAOB inspection regime** — Public company audit firms are subject to periodic PCAOB inspections that produce publicly available deficiency reports. These are the single most predictive data source in PI — a firm with a high Part I deficiency rate is statistically more likely to face restatement-driven claims.
2. **Securities litigation exposure** — When an audit client faces a securities class action, the auditor is almost always a co-defendant. The firm's exposure is not limited to its own errors — it extends to its client's misconduct.
3. **Partner rotation requirements** — SOX Section 203 mandates audit partner rotation every 5 years. Compliance quality with this requirement correlates with overall audit quality.
4. **Fee concentration** — A mid-tier audit firm deriving 20%+ of fees from a single public company client faces catastrophic concentration risk.

### Signal Architecture Rationale

**Primary driver: Regulatory Standing (Risk: 0.30, Loss: 0.30, Exposure: 0.15 = 0.75 combined)**

This is the highest regulatory_standing weight in the entire DSI platform, and deliberately so. For audit firms, the PCAOB inspection regime produces granular, publicly available, directly predictive data. A firm with zero Part I deficiencies is qualitatively different from one with a 40% deficiency rate.

**Secondary driver: Audit Quality (Risk: 0.20, Loss: 0.20, Exposure: 0.40 = 0.80 combined)**

The new `audit_quality` group has the highest exposure weight (0.40) of any new group introduced in Phase 6. This reflects the concentration risk inherent in audit practice — a single restatement at a large public company client can produce a claim that exceeds the firm's total annual revenue.

**Deprioritised: Network Authority, Corporate Footprint**

For audit firms, peer rankings and website quality are noise. What matters is PCAOB findings and restatement history. These groups receive minimal weight.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `pcaob_inspection_deficiency_rate` | DIRECT_OBSERVABLE | audit_quality | PCAOB Part I/II inspection findings rate — the single most predictive audit signal |
| `restatement_rate` | DIRECT_OBSERVABLE | audit_quality | Audit client financial restatement frequency — direct loss predictor |
| `going_concern_accuracy` | INFERRED_PROXY | audit_quality | Going-concern opinion accuracy — false negatives indicate quality failure |
| `sec_enforcement_exposure` | DIRECT_OBSERVABLE | audit_quality | SEC enforcement actions against firm/partners — severity driver |
| `audit_client_concentration` | INFERRED_PROXY | audit_quality | Single-client fee dependency; >15% from one client = concentration risk |
| `audit_partner_rotation_compliance` | DIRECT_OBSERVABLE | audit_quality | SOX 203 partner rotation compliance; non-compliance = systemic quality issue |
| `securities_litigation_exposure` | INFERRED_PROXY | audit_quality | Exposure from audit client securities suits — tail risk driver |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0045** (0.45%). The highest rate in the PI suite, reflecting the extreme severity tail of public company audit. This is 2.5x `pi_general`'s rate.
- **Limit Configuration**: **DECOUPLED** — $10,000,000 base limit with $500,000 deductible. Large base limit reflects the minimum programme sizes for audit firms with public company clients.
- **Min Premium**: $250,000
- **Product types**: `professional_liability`, `errors_omissions`
- **Sub-profession modifiers**: Public Company Audit (1.50), Valuation Advisory (1.35), M&A Advisory (1.30), Private Company Audit (1.25), Forensic (1.20), Estate Tax (1.20), Corporate Tax (1.10), General Practice (1.00), Individual Tax (0.90), Bookkeeping (0.80)

### Example Company Returns

**Tier 1 — PREFERRED:**
> **PricewaterhouseCoopers** (Big 4)
> - Revenue: $53.0B (global) | Limit: $50M | Score: 872
> - Why: Zero PCAOB Part I deficiencies in last inspection cycle, negligible restatement rate, full partner rotation compliance, diversified client base (no client >2% of fees), best-in-class quality management system
> - Premium: $53.0B × 0.0020 = $106M base → sub_profession modifier (AUDIT_PUBLIC: 1.50) → firm_size modifier (MAJOR: 0.85) → geographic diversification modifier (0.80) → **~$108M net** (global programme)

**Tier 2 — STANDARD PLUS:**
> **BDO USA** (mid-tier, top-10 US)
> - Revenue: $2.4B | Limit: $25M | Score: 712
> - Why: Low PCAOB deficiency rate, one client restatement in 3 years (minor), adequate partner rotation, moderate client concentration (top client ~5% of fees), clean SEC enforcement record
> - Premium: $2.4B × 0.0030 = $7.2M base → sub_profession modifier (AUDIT_PUBLIC: 1.50) → firm_size modifier (LARGE: 0.90) → **~$9.7M net**

**Tier 5 — DECLINE:**
> **Mid-tier firm post-restatement scandal** (composite profile)
> - Revenue: $300M | Limit: $10M | Score: 142
> - Why: PCAOB Part I deficiency rate of 45%, three client restatements in 18 months, SEC enforcement action pending against engagement partner, going-concern opinion missed on client that filed bankruptcy 6 months later, top client represents 22% of audit fees
> - Decline triggers: audit_quality group score <= 15, pcaob_inspection_deficiency_rate <= 10, restatement_rate <= 15

---

## Configuration 4: `pi_accounting`

### The Underwriting Reality

Non-audit accounting — tax advisory, bookkeeping, forensic accounting, estate planning — is the quiet workhorse of the PI market. These firms represent the highest volume of PI submissions in the accounting segment, but with fundamentally lower severity than audit. A tax opinion that results in IRS penalties produces a claim in the hundreds of thousands, not the hundreds of millions.

The `pi_accounting` configuration exists because these firms should not be priced using audit-grade signal weights. A 50-person regional CPA firm doing tax returns and bookkeeping has entirely different risk drivers than a Big 4 audit practice:

1. **Tax opinion quality** — The quality of tax opinions (aggressive vs conservative, documentation quality) directly predicts IRS examination outcomes and subsequent malpractice claims.
2. **IRS examination track record** — Client audit outcomes are publicly observable through litigation records and produce a direct loss signal.
3. **Engagement complexity** — Estate planning, M&A advisory, and forensic engagements have higher severity tails than routine tax compliance. The complexity mix matters.
4. **Regulatory standing** — State board of accountancy disciplinary actions are publicly available and directly predictive, but the regulatory regime is lighter than PCAOB.

### Signal Architecture Rationale

**No new signal group.** The `pi_accounting` configuration reuses the existing 7 scored groups from `pi_general` with adjusted weights, plus 3 new signals added to existing groups. This is a deliberate architectural decision — non-audit accounting does not have a single dominant risk dimension that warrants a new group.

**Primary driver: Regulatory Standing (Risk: 0.25, Loss: 0.25, Exposure: 0.10 = 0.60 combined)**

State board disciplinary history and CE compliance are the primary signals. Weight matches `pi_general` because the regulatory framework is similar but less severe than audit.

**Secondary driver: Practice Quality (Risk: 0.20, Loss: 0.20, Exposure: 0.20 = 0.60 combined)**

Elevated above `pi_general` because for accounting firms, the quality of work product (tax opinions, financial statements, forensic reports) is directly observable through client outcomes and regulatory examination results.

**Elevated: Litigation History (Risk: 0.10, Loss: 0.20, Exposure: 0.20 = 0.50 combined)**

Accounting firms face a higher frequency of fee disputes and malpractice claims than most PI segments. Litigation history carries elevated loss and exposure weight.

### New Signals (Added to existing groups)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `tax_opinion_quality` | INFERRED_PROXY | practice_quality | Quality of tax opinions issued; aggressive positions correlate with IRS challenge rate |
| `irs_examination_track` | DIRECT_OBSERVABLE | regulatory_standing | Client IRS examination outcomes; high challenge success rate = quality indicator |
| `estate_planning_complexity` | INFERRED_PROXY | practice_quality | Engagement complexity distribution; high-complexity estate work has longer severity tail |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0022** (0.22%). Approximately 22% above `pi_general`'s rate, reflecting the specific regulatory exposure of accounting practice without the catastrophic tail of audit.
- **Limit Configuration**: **DECOUPLED** — $1,000,000 base limit with $25,000 deductible.
- **Min Premium**: $15,000
- **Product types**: `professional_liability`, `errors_omissions`

### Example Company Returns

**Tier 1 — PREFERRED:**
> **RSM US** (top-10, tax advisory focus)
> - Revenue: $3.2B | Limit: $10M | Score: 823
> - Why: Clean state board record across all jurisdictions, low IRS challenge rate on client returns, diversified practice (tax 45%, advisory 30%, bookkeeping 25%), strong staff retention, robust engagement quality procedures
> - Premium: $3.2B × 0.0010 = $3.2M base → sub_profession modifier (CORPORATE_TAX: 1.10) → firm_size modifier (MAJOR: 0.85) → **~$2.99M net**

**Tier 3 — STANDARD:**
> **Regional CPA firm** (composite profile)
> - Revenue: $12M | Limit: $2M | Score: 561
> - Why: One state board citation (CE non-compliance, resolved), moderate IRS challenge rate, concentration in individual tax returns (lower severity), adequate staff retention, 2 fee dispute claims in 5 years
> - Premium: $12M × 0.0022 = $26,400 base → sub_profession modifier (TAX_INDIVIDUAL: 0.90) → firm_size modifier (SMALL: 1.00) → **~$23,760 net**

**Tier 5 — DECLINE:**
> **Firm with IRS penalties** (composite profile)
> - Revenue: $5M | Limit: $1M | Score: 201
> - Why: State board suspended 2 partners' licenses (improper tax shelter promotion), IRS imposed $2M in preparer penalties, 4 active malpractice suits from clients with disallowed deductions, E&O insurance non-renewed by prior carrier
> - Decline triggers: regulatory_standing group score <= 15, irs_examination_track <= 10

---

## Configuration 5: `pi_architecture`

### The Underwriting Reality

Architecture PI is defined by latent defect exposure. Unlike a legal malpractice claim that crystallises within months, an architectural design defect may not manifest for 10-15 years after building completion. A structural inadequacy, waterproofing failure, or code non-compliance discovered a decade after occupancy produces a claim against the original architect — who may have long since moved on to other projects.

This long-tail exposure shapes every aspect of the underwriting model:

1. **Design defect claims history** — The single most predictive signal. Architects with prior design defect claims have demonstrably higher recurrence rates, because the root causes (inadequate peer review, complexity overreach, insufficient site assessment) are systemic.
2. **Building code compliance track record** — Code violations are publicly recorded and directly observable. An architect with a pattern of code rejections has systemic quality issues that predict future claims.
3. **Project complexity** — A firm designing single-family residences has fundamentally different exposure than one designing hospitals or high-rise towers. The complexity distribution of the portfolio is a primary exposure driver.
4. **Sustainability certification** — LEED/BREEAM certification track record serves as a quality proxy. Firms that successfully achieve certification demonstrate systematic design processes that reduce defect probability.

### Signal Architecture Rationale

**Primary driver: Design Quality (Risk: 0.25, Loss: 0.30, Exposure: 0.45 = 1.00 combined)**

The new `design_quality` group has the highest combined weight of any new group in Phase 6. This reflects the reality that in architecture PI, the quality of the design work IS the risk. Everything else — regulatory standing, firm stability, corporate footprint — is secondary to whether the firm produces buildings that work.

**Secondary driver: Regulatory Standing (Risk: 0.15, Loss: 0.15, Exposure: 0.05 = 0.35 combined)**

Architectural licensing boards are less aggressive than legal bar associations or PCAOB, but license status and disciplinary history remain important signals.

**Deprioritised: Technical Infrastructure, Corporate Footprint**

Architecture firms' cybersecurity posture and website quality are weak predictors of design quality. Minimal weight.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `design_defect_claims` | DIRECT_OBSERVABLE | design_quality | Historical design defect claim frequency — the primary loss predictor |
| `building_code_compliance` | DIRECT_OBSERVABLE | design_quality | Code compliance track record; pattern violations = systemic quality issues |
| `project_complexity_score` | INFERRED_PROXY | design_quality | Average project complexity rating; hospitals > high-rise > residential |
| `latent_defect_exposure` | INFERRED_PROXY | design_quality | Long-tail defect claim exposure; 10-15 year discovery period |
| `sustainability_certification` | DIRECT_OBSERVABLE | design_quality | LEED/BREEAM certification track record as design quality proxy |
| `construction_phase` | DIRECT_OBSERVABLE | design_quality | Categorical: project lifecycle stage affects exposure profile |

The `construction_phase` signal is categorical:

| Category | Label | Applied |
|---|---|---|
| PRE_CONSTRUCTION | Pre-Construction / Design | 1.30 |
| CONSTRUCTION | Under Construction | 1.20 |
| COMMISSIONING | Commissioning | 1.10 |
| EARLY_OPERATION | Early Operation (<3 years) | 1.05 |
| MATURE_OPERATION | Mature Operation (3+ years) | 0.90 |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0026** (0.26%). Moderate rate reflecting the long-tail but generally manageable severity of architecture PI. Higher than `pi_general` due to latent defect tail.
- **Limit Configuration**: **DECOUPLED** — $1,000,000 base limit with $25,000 deductible.
- **Min Premium**: $15,000
- **Product types**: `professional_liability`, `errors_omissions`
- **Sub-profession modifiers**: Structural Design (1.35), Healthcare Facilities (1.25), High-Rise Construction (1.20), Commercial (1.10), Institutional (1.05), Multi-Family Residential (1.00), Single-Family Residential (0.90), Interior Design (0.85)

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Gensler** (world's largest architecture firm)
> - Revenue: $1.9B | Limit: $10M | Score: 835
> - Why: Zero design defect claims in 5 years, exemplary code compliance record, LEED-certified portfolio (85%+ of projects), diversified project types (commercial 40%, institutional 25%, residential 20%, other 15%), strong peer review processes, mature succession planning
> - Premium: $1.9B × 0.0012 = $2.28M base → sub_profession modifier (COMMERCIAL: 1.10) → firm_size modifier (MAJOR: 0.85) → **~$2.13M net**

**Tier 3 — STANDARD:**
> **Mid-size architecture firm** (composite profile)
> - Revenue: $18M | Limit: $2M | Score: 568
> - Why: One design defect claim (waterproofing failure, $350K settlement), adequate code compliance, limited LEED experience, concentrated in multi-family residential, moderate staff retention, 15-year firm with stable leadership
> - Premium: $18M × 0.0026 = $46,800 base → sub_profession modifier (RESIDENTIAL_MULTI: 1.00) → firm_size modifier (SMALL: 1.00) → **~$46,800 net**

**Tier 5 — DECLINE:**
> **Firm with latent defect history** (composite profile)
> - Revenue: $6M | Limit: $1M | Score: 178
> - Why: Three active design defect claims (two involving structural inadequacy in high-rise projects), two building code violation patterns (fire egress, ADA compliance), license under review in primary jurisdiction, prior PI carrier non-renewed, no peer review process
> - Decline triggers: design_quality group score <= 15, design_defect_claims <= 10, building_code_compliance <= 15

---

## Configuration 6: `pi_engineering`

### The Underwriting Reality

Engineering PI carries the highest severity exposure in the design & construction segment — and among the highest in all of PI. When a bridge fails, a dam breaches, or a building foundation settles, the consequences are not just financial — they involve bodily injury, public infrastructure failure, and regulatory enforcement that can destroy an engineering firm.

The 2018 Morandi Bridge collapse in Genoa (43 fatalities), the 2021 Champlain Towers South collapse in Surfside (98 fatalities), and countless less-publicised geotechnical and structural failures demonstrate that engineering errors carry catastrophic severity potential. The malpractice claims that follow these events routinely exceed $100M.

Key risk drivers for engineering PI:

1. **Structural failure history** — Any prior structural failure or deficiency claim is a dominant signal. The root causes (inadequate soil investigation, design calculation errors, peer review failures) are systemic and predictive.
2. **PE license compliance** — Professional Engineer licenses are jurisdiction-specific and strictly enforced. A firm practising without proper PE licensure in a jurisdiction faces both malpractice exposure and regulatory sanctions.
3. **Project size concentration** — An engineering firm with 40% of revenue from a single infrastructure project faces catastrophic concentration risk if that project fails.
4. **Infrastructure project exposure** — Public infrastructure work (bridges, dams, highways, water treatment) carries a higher duty of care than private commercial work, producing higher severity claims.

### Signal Architecture Rationale

**Primary driver: Engineering Quality (Risk: 0.35, Loss: 0.35, Exposure: 0.50 = 1.20 combined)**

The highest combined group weight in all of Phase 6. Engineering quality IS the risk. A firm's structural failure history, PE compliance, and geotechnical claim frequency are near-deterministic predictors of future loss.

**Secondary driver: Regulatory Standing (Risk: 0.20, Loss: 0.15, Exposure: 0.05 = 0.40 combined)**

PE licensing boards are active enforcement bodies. License status is binary and publicly observable.

**Deprioritised: Network Authority, Corporate Footprint, Technical Infrastructure**

For engineering firms, peer rankings and website quality are noise compared to their structural failure history and PE compliance. Minimal weights.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `structural_failure_history` | DIRECT_OBSERVABLE | engineering_quality | Structural failure/deficiency claims — the primary severity signal |
| `pe_license_compliance` | DIRECT_OBSERVABLE | engineering_quality | PE license status across operating jurisdictions; gaps = regulatory exposure |
| `geotechnical_claim_frequency` | DIRECT_OBSERVABLE | engineering_quality | Geotechnical failure claims; soil/foundation failures are high-severity |
| `infrastructure_project_exposure` | INFERRED_PROXY | engineering_quality | Public infrastructure involvement; higher duty of care = higher severity |
| `project_size_concentration` | INFERRED_PROXY | engineering_quality | Single-project revenue concentration; >20% = catastrophic concentration risk |
| `remediation_cost_history` | DIRECT_OBSERVABLE | engineering_quality | Past environmental remediation cost exposure from design failures |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0032** (0.32%). The highest Design & Construction rate, reflecting structural failure severity. Comparable to `pi_legal_specialist` and significantly above `pi_architecture`.
- **Limit Configuration**: **DECOUPLED** — $2,000,000 base limit with $50,000 deductible.
- **Min Premium**: $20,000
- **Product types**: `professional_liability`, `errors_omissions`
- **Sub-profession modifiers**: Structural Engineering (1.40), Geotechnical Engineering (1.35), Environmental Engineering (1.25), Civil Engineering (1.15), Mechanical Engineering (1.10), Electrical Engineering (1.05), Surveying (1.00), Consulting Only (0.90)

### Example Company Returns

**Tier 1 — PREFERRED:**
> **AECOM** (global infrastructure leader)
> - Revenue: $14.4B | Limit: $25M | Score: 812
> - Why: Zero structural failure claims in 10 years, full PE licensure in all operating jurisdictions, diversified across civil, environmental, and mechanical disciplines, best-in-class peer review processes, low project concentration (top project <3% of revenue)
> - Premium: $14.4B × 0.0015 = $21.6M base → sub_profession modifier (CIVIL: 1.15) → firm_size modifier (MAJOR: 0.85) → **~$21.1M net**

**Tier 3 — STANDARD:**
> **Mid-tier structural engineering firm** (composite profile)
> - Revenue: $25M | Limit: $5M | Score: 543
> - Why: One geotechnical claim (foundation settlement, $800K settlement, 4 years ago), full PE compliance, moderate project concentration (top project 15% of revenue), adequate peer review, 25-year firm history with stable partnerships
> - Premium: $25M × 0.0032 = $80,000 base → sub_profession modifier (STRUCTURAL: 1.40) → firm_size modifier (SMALL: 1.00) → **~$112,000 net**

**Tier 5 — DECLINE:**
> **Firm with bridge/infrastructure failure** (composite profile)
> - Revenue: $8M | Limit: $2M | Score: 132
> - Why: Structural failure claim from bridge rehabilitation project ($15M claim pending), PE license suspended in primary state, second geotechnical claim from foundation design (ongoing litigation), 35% of revenue from single government contract now terminated, no peer review documentation
> - Decline triggers: engineering_quality group score <= 10, structural_failure_history <= 5, pe_license_compliance <= 15

---

## Configuration 7: `pi_technology`

### The Underwriting Reality

Technology consulting and systems integration PI occupies a unique position in the professional indemnity landscape. Unlike legal or audit PI where claims arise from advisory failures, technology PI claims arise from *delivery* failures — failed ERP implementations, botched cloud migrations, data breaches during managed service engagements, and systems that simply do not work as specified.

The IT services market has produced some of the largest PI claims in history. Accenture's failed $1B+ Hertz website rebuild, Deloitte's NHS e-referral system delays, and countless SAP/Oracle implementation failures that produced nine-figure claims demonstrate that technology delivery risk is real and severe.

Key risk drivers:

1. **Project failure rate** — IT projects have a well-documented failure rate. The Standish Group's CHAOS reports consistently show that 20-30% of large IT projects are abandoned or fail to deliver value. A firm's historical project failure rate is the primary loss predictor.
2. **SLA compliance** — For managed services and outsourcing engagements, SLA adherence is directly observable and predictive. Chronic SLA misses indicate systemic delivery issues.
3. **Data breach exposure** — Technology firms handle client data at scale. A breach during a managed service engagement produces both direct liability and regulatory exposure (GDPR, CCPA, PCI-DSS).
4. **Technology stack currency** — Firms building on outdated technology stacks (legacy COBOL, unsupported frameworks) have higher failure rates than those using current, supported platforms.

### Signal Architecture Rationale

**Primary driver: Delivery Quality (Risk: 0.15, Loss: 0.20, Exposure: 0.35 = 0.70 combined)**

The new `delivery_quality` group captures what makes technology PI unique — the risk is in the delivery, not the advice. The high exposure weight (0.35) reflects project concentration risk.

**Elevated: Technical Infrastructure (Risk: 0.15, Loss: 0.20, Exposure: 0.15 = 0.50 combined)**

For the first time in PI, `technical_infrastructure` is a primary signal group. Technology firms' own cybersecurity posture, development practices, and infrastructure quality are directly predictive of their ability to deliver secure solutions to clients. A technology consultancy with weak email authentication and no breach response plan is more likely to cause a data breach at a client site.

**Secondary driver: Regulatory Standing (Risk: 0.15, Loss: 0.10, Exposure: 0.05 = 0.30 combined)**

Technology firms face lighter regulatory oversight than legal or accounting practices. Regulatory standing weight is reduced from `pi_general`.

**Deprioritised: Corporate Footprint**

Technology firms' marketing quality is uncorrelated with delivery quality. Minimal weight.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `project_failure_rate` | INFERRED_PROXY | delivery_quality | IT project abandonment/failure rate — the primary loss predictor |
| `sla_compliance` | DIRECT_OBSERVABLE | delivery_quality | Service level agreement adherence for managed services engagements |
| `data_breach_exposure` | DIRECT_OBSERVABLE | delivery_quality | Client data handling practices and breach history |
| `technology_stack_currency` | INFERRED_PROXY | delivery_quality | Tech stack currency; outdated platforms = higher failure and security risk |
| `implementation_methodology` | INFERRED_PROXY | delivery_quality | Structured methodology adherence (ITIL, Agile maturity, CMMI level) |
| `client_data_encryption` | DIRECT_OBSERVABLE | delivery_quality | Client data encryption standards at rest and in transit |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0022** (0.22%). Moderate rate reflecting the frequency-driven loss profile of technology PI. Lower than legal or engineering because individual claim severity is generally lower (project value caps exposure).
- **Limit Configuration**: **DECOUPLED** — $2,000,000 base limit with $50,000 deductible.
- **Min Premium**: $20,000
- **Product types**: `professional_liability`, `errors_omissions`

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Accenture** (global technology and consulting)
> - Revenue: $64.1B | Limit: $50M | Score: 802
> - Why: Structured delivery methodology (CMMI Level 5), low project failure rate (<5%), comprehensive data security framework, diversified client base, strong SLA compliance record, robust breach response capability
> - Premium: $64.1B × 0.0010 = $64.1M base → firm_size modifier (MAJOR: 0.85) → geographic diversification modifier (0.80) → **~$43.6M net** (global programme)

**Tier 3 — STANDARD:**
> **Mid-tier systems integrator** (composite profile)
> - Revenue: $80M | Limit: $5M | Score: 558
> - Why: Two project delays >6 months in past 3 years (no abandonments), adequate SLA compliance (92%), one minor data exposure incident (promptly remediated), ITIL-certified operations, moderate client concentration (top client 12% of revenue)
> - Premium: $80M × 0.0022 = $176,000 base → firm_size modifier (MEDIUM: 0.95) → **~$167,200 net**

**Tier 5 — DECLINE:**
> **Firm with failed ERP implementation litigation** (composite profile)
> - Revenue: $15M | Limit: $2M | Score: 189
> - Why: Active $25M lawsuit from failed SAP implementation (client alleging fraud and gross negligence), second client dispute over failed cloud migration, data breach at managed services client (PII of 500K individuals), no structured methodology documentation, SLA compliance at 68%
> - Decline triggers: delivery_quality group score <= 15, project_failure_rate <= 10, data_breach_exposure <= 10

---

## Configuration 8: `pi_financial_advisory`

### The Underwriting Reality

Financial advisory PI — covering wealth managers, independent financial advisers (IFAs), registered investment advisers (RIAs), and pension consultants — is defined by regulatory intensity and mis-selling exposure. Unlike other PI segments where claims arise from professional errors, financial advisory claims frequently arise from *suitability failures* — recommending investments that are inappropriate for the client's risk tolerance, time horizon, or financial circumstances.

The UK PPI (Payment Protection Insurance) mis-selling scandal, which ultimately cost the industry £50B+ in redress, demonstrated that financial advisory exposure can be systemic. In the US, the DOL fiduciary rule debates and SEC Regulation Best Interest have created an evolving regulatory landscape that directly affects claims frequency.

Key risk drivers:

1. **Suitability compliance** — The FCA (UK), SEC (US), and equivalent regulators mandate that advice be suitable for the client. Suitability failures are the #1 cause of financial advisory PI claims by frequency.
2. **Complaint rate per AUM** — Complaints per assets under management is a normalised quality metric. A firm with 50 complaints per $1B AUM has a fundamentally different risk profile than one with 5 complaints per $1B.
3. **Regulatory examination results** — SEC examination findings and FCA supervisory actions are directly predictive. Firms with "material weaknesses" in compliance frameworks face elevated claims risk.
4. **Churning indicators** — Excessive trading (churning) in client accounts generates both regulatory enforcement and PI claims. Observable through turnover ratios and commission income patterns.

### Signal Architecture Rationale

**Primary driver: Regulatory Standing (Risk: 0.25, Loss: 0.25, Exposure: 0.15 = 0.65 combined)**

Financial advisory is the most heavily regulated PI segment after audit. FCA/SEC examination results, enforcement actions, and compliance framework assessments are rich, publicly available data sources.

**Secondary driver: Advisory Quality (Risk: 0.10, Loss: 0.10, Exposure: 0.30 = 0.50 combined)**

The new `advisory_quality` group captures the profession-specific risk drivers. The high exposure weight (0.30) reflects the potential for systemic mis-selling exposure — a flawed advice model applied to thousands of clients creates correlated claims.

**Elevated: Practice Quality (Risk: 0.15, Loss: 0.20, Exposure: 0.10 = 0.45 combined)**

Client outcomes, complaint history, and fee disputes are critical signals for financial advisers. Elevated loss weight reflects the direct correlation between poor advice and measurable client financial loss.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `suitability_compliance` | DIRECT_OBSERVABLE | advisory_quality | Investment suitability compliance record — the primary claims driver |
| `complaint_per_aum` | DIRECT_OBSERVABLE | advisory_quality | Complaints normalised per AUM; high ratio = systemic quality issues |
| `regulatory_exam_results` | DIRECT_OBSERVABLE | advisory_quality | SEC/FCA examination findings; material weaknesses are severe signals |
| `churning_indicators` | INFERRED_PROXY | advisory_quality | Excessive trading indicators; high turnover = churning exposure |
| `fee_transparency_score` | INFERRED_PROXY | advisory_quality | Fee disclosure quality; opaque fees generate mis-selling claims |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0028** (0.28%). Elevated rate reflecting the regulatory intensity and mis-selling tail. Matches `pi_legal_large` — financial advisory severity is comparable to large legal practice for systemic mis-selling scenarios.
- **Limit Configuration**: **DECOUPLED** — $2,000,000 base limit with $50,000 deductible.
- **Min Premium**: $25,000
- **Product types**: `professional_liability`, `errors_omissions`

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Vanguard Personal Advisor Services** (RIA, fee-only)
> - Revenue: $1.8B (advisory segment) | Limit: $25M | Score: 856
> - Why: Fee-only model (no commission-driven suitability risk), zero SEC examination deficiencies, lowest complaint-per-AUM in industry, no churning indicators, exemplary fee transparency, robust suitability documentation
> - Premium: $1.8B × 0.0012 = $2.16M base → firm_size modifier (MAJOR: 0.85) → fee_model modifier (0.85, fee-only) → **~$1.56M net**

**Tier 3 — STANDARD:**
> **Regional RIA** (composite profile)
> - Revenue: $22M | Limit: $5M | Score: 571
> - Why: Two client complaints in past year (resolved without payout), SEC examination with minor findings (documentation gaps), moderate fee transparency, commission income at 30% of revenue (suitability risk indicator), adequate compliance framework
> - Premium: $22M × 0.0028 = $61,600 base → firm_size modifier (SMALL: 1.00) → **~$61,600 net**

**Tier 5 — DECLINE:**
> **IFA with mis-selling history** (composite profile)
> - Revenue: $5M | Limit: $2M | Score: 156
> - Why: FCA enforcement action for unsuitable pension transfer advice (£2M fine), 45 client complaints pending (pension mis-selling), high churning indicators (average portfolio turnover 4x/year), regulatory examination rated "seriously deficient", E&O insurance non-renewed
> - Decline triggers: advisory_quality group score <= 10, suitability_compliance <= 5, regulatory_exam_results <= 10

---

## Configuration 9: `pi_management_consulting`

### The Underwriting Reality

Management consulting PI is the lowest-severity segment in the PI suite — and this is by design. Strategy and management advisory firms provide *advice*, not deliverables. When a client follows McKinsey's recommendation to enter a new market and it fails, the causal chain between advice and loss is long, attenuated, and difficult to prove in court.

This does not mean management consulting PI is trivial. The claims that do arise tend to follow specific patterns:

1. **Scope creep litigation** — Engagement scope ambiguity is the #1 source of management consulting claims. When a client believes the consultant promised a specific outcome and the consultant believed they were providing options analysis, the resulting dispute produces either a malpractice claim or a fee dispute.
2. **Deliverable acceptance** — The rate at which clients accept deliverables without dispute is a direct quality signal. High rejection rates indicate systematic communication or quality issues.
3. **Advice-outcome correlation** — For strategy consultants, the correlation between their recommendations and client outcomes is a long-term quality proxy. Firms whose clients consistently underperform after implementing recommendations face elevated claims risk.
4. **Fee disputes** — Management consulting generates a disproportionate share of PI fee dispute claims, because the value of advice is inherently subjective.

### Signal Architecture Rationale

**No new signal group.** Like `pi_accounting`, the management consulting configuration reuses the existing 7 scored groups with adjusted weights. Management consulting does not have a single dominant profession-specific risk dimension — the risk is distributed across practice quality, firm stability, and corporate footprint.

**Primary driver: Practice Quality (Risk: 0.20, Loss: 0.25, Exposure: 0.15 = 0.60 combined)**

Elevated above all other configurations because for management consultants, the quality of advice and client satisfaction are the primary claims drivers. Three new signals are added to this group.

**Elevated: Firm Stability (Risk: 0.20, Loss: 0.15, Exposure: 0.20 = 0.55 combined)**

Management consulting firms are heavily dependent on key personnel. Partner departures, practice leader turnover, and succession planning are critical stability indicators.

**Elevated: Corporate Footprint (Risk: 0.10, Loss: 0.10, Exposure: 0.20 = 0.40 combined)**

Unusually for PI, corporate footprint carries meaningful weight for management consultants. Thought leadership, publication quality, and industry recognition are genuine quality signals in a profession where reputation IS the product.

**Deprioritised: Regulatory Standing**

Management consulting faces minimal professional regulation. There is no equivalent of bar associations, PCAOB, or PE licensing boards. Regulatory standing weight is reduced to (0.15 / 0.15 / 0.05).

### New Signals (Added to existing groups)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `engagement_scope_clarity` | INFERRED_PROXY | practice_quality | Scope definition quality in engagement letters; ambiguity = dispute risk |
| `deliverable_acceptance_rate` | DIRECT_OBSERVABLE | practice_quality | Client deliverable acceptance rate; high rejection = quality issues |
| `client_outcome_correlation` | INFERRED_PROXY | practice_quality | Advice-to-outcome correlation over time; weak correlation = adverse selection |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0015** (0.15%). The lowest rate in the PI suite, reflecting the attenuated causal chain and generally lower severity of management consulting claims. Below `pi_general`'s rate.
- **Limit Configuration**: **DECOUPLED** — $1,000,000 base limit with $50,000 deductible.
- **Min Premium**: $25,000
- **Product types**: `professional_liability`, `errors_omissions`

### Example Company Returns

**Tier 1 — PREFERRED:**
> **McKinsey & Company** (elite strategy consulting)
> - Revenue: $16.0B | Limit: $25M | Score: 868
> - Why: Best-in-class engagement scoping processes, 98% deliverable acceptance rate, zero malpractice claims in 5 years, strong partner stability, exemplary thought leadership, diversified across industries and geographies
> - Premium: $16.0B × 0.0006 = $9.6M base → firm_size modifier (MAJOR: 0.85) → geographic diversification modifier (0.80) → **~$6.5M net**

**Tier 3 — STANDARD:**
> **Mid-tier strategy firm** (composite profile)
> - Revenue: $60M | Limit: $5M | Score: 582
> - Why: One scope dispute (settled for $200K, 2 years ago), 88% deliverable acceptance rate, moderate client concentration (top 3 clients = 40% of revenue), adequate engagement scoping, two partner departures in 3 years
> - Premium: $60M × 0.0015 = $90,000 base → firm_size modifier (MEDIUM: 0.95) → **~$85,500 net**

**Tier 5 — DECLINE:**
> **Firm with advice-failure litigation** (composite profile)
> - Revenue: $12M | Limit: $2M | Score: 212
> - Why: Active $8M lawsuit alleging negligent advice (client followed cost-reduction recommendation, subsequently lost key customers), two additional fee disputes totalling $1.5M, deliverable acceptance rate at 62%, 4 of 8 partners departed in 18 months, prior PI carrier non-renewed
> - Decline triggers: practice_quality group score <= 15, firm_stability group score <= 20

---

## Configuration 10: `pi_real_estate`

### The Underwriting Reality

Real estate and valuation PI covers surveyors, property valuers, estate agents, and appraisers — professionals whose core service is opining on the value of property. When a valuation is wrong, the consequences flow directly and measurably to the party who relied on it.

The 2008 financial crisis demonstrated the systemic risk of negligent valuation at industrial scale. Inflated property valuations underpinned trillions of dollars in mortgage lending. The resulting wave of negligent misstatement claims against valuers and appraisers overwhelmed the PI market. While the systemic risk has receded, the fundamental exposure remains: **a valuation is a number, and when the number is wrong, the loss is the difference**.

Key risk drivers:

1. **Valuation accuracy** — Historical accuracy of valuations versus realised transaction prices is the primary quality signal. A valuer who consistently over-values by 15%+ has a systemic calibration problem.
2. **Negligent misstatement claims** — Claims arising from negligent misstatement in valuation reports are directly observable and highly predictive. The duty of care extends to all parties who reasonably rely on the valuation.
3. **Property type concentration** — A firm concentrated in commercial real estate valuations has different exposure than one focused on residential. Commercial valuations carry higher individual claim severity.
4. **RICS/Appraisal Institute compliance** — Professional body compliance (RICS in the UK, Appraisal Institute in the US) is a quality proxy. Non-compliant firms face both regulatory and malpractice exposure.

### Signal Architecture Rationale

**Primary driver: Valuation Quality (Risk: 0.20, Loss: 0.25, Exposure: 0.40 = 0.85 combined)**

The new `valuation_quality` group captures what makes real estate PI unique — the risk is in the accuracy of the opinion. The very high exposure weight (0.40) reflects the concentration risk inherent in valuation work — a single negligent valuation on a £50M commercial property can produce a claim that exceeds the firm's annual revenue.

**Secondary driver: Regulatory Standing (Risk: 0.20, Loss: 0.20, Exposure: 0.10 = 0.50 combined)**

RICS and Appraisal Institute disciplinary proceedings are publicly available and predictive. Professional body compliance is essential for market access.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `valuation_accuracy` | DIRECT_OBSERVABLE | valuation_quality | Historical valuation accuracy vs realised prices — the primary quality signal |
| `negligent_misstatement_history` | DIRECT_OBSERVABLE | valuation_quality | Negligent misstatement claims; directly predictive of future claims |
| `property_type_concentration` | INFERRED_PROXY | valuation_quality | Concentration in specific property types; commercial > residential severity |
| `market_knowledge_currency` | INFERRED_PROXY | valuation_quality | Local market expertise currency; stale knowledge = valuation errors |
| `rics_compliance` | DIRECT_OBSERVABLE | valuation_quality | RICS (UK) / Appraisal Institute (US) compliance; non-compliance = exposure |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0022** (0.22%). Moderate rate reflecting the frequency of valuation disputes balanced against generally manageable individual claim severity.
- **Limit Configuration**: **DECOUPLED** — $1,000,000 base limit with $25,000 deductible.
- **Min Premium**: $10,000
- **Product types**: `professional_liability`, `errors_omissions`

### Example Company Returns

**Tier 1 — PREFERRED:**
> **CBRE Valuation & Advisory** (global leader)
> - Revenue: $2.1B (valuation segment) | Limit: $25M | Score: 841
> - Why: Valuation accuracy within 5% of realised prices (industry best), zero negligent misstatement claims in 5 years, RICS-compliant across all jurisdictions, diversified across property types (commercial 40%, industrial 25%, residential 20%, land 15%), robust quality assurance processes
> - Premium: $2.1B × 0.0010 = $2.1M base → firm_size modifier (MAJOR: 0.85) → geographic diversification modifier (0.85) → **~$1.52M net**

**Tier 3 — STANDARD:**
> **Regional surveyor** (composite profile)
> - Revenue: $3.5M | Limit: $1M | Score: 554
> - Why: Valuation accuracy within 12% (adequate), one negligent misstatement claim (settled for £150K, 3 years ago), RICS-compliant, concentrated in residential valuations (75%), adequate market knowledge, 20-year practice history
> - Premium: $3.5M × 0.0022 = $7,700 base → min premium floor → **$10,000 net** (minimum premium applies)

**Tier 5 — DECLINE:**
> **Firm with negligent valuation history** (composite profile)
> - Revenue: $1.2M | Limit: $1M | Score: 168
> - Why: Three negligent misstatement claims in 4 years (two still open), systematic over-valuation pattern (average +22% vs realised), RICS membership under review, concentrated in commercial property in declining market, valuation methodology not updated for 5 years
> - Decline triggers: valuation_quality group score <= 15, valuation_accuracy <= 10, negligent_misstatement_history <= 10

---

## Configuration 11: `pi_environmental`

### The Underwriting Reality

Environmental consulting PI is defined by its extraordinarily long tail. A Phase I/II environmental site assessment conducted today may not face a claim for 15-20 years — when contamination is discovered that the original assessment failed to identify. The statute of limitations for environmental claims often runs from the date of *discovery*, not the date of the assessment, creating open-ended exposure that no other PI segment faces.

The CERCLA (Superfund) framework adds a unique dimension: environmental consultants can be named as Potentially Responsible Parties (PRPs) if their advice contributed to contamination decisions. This is not merely PI exposure — it is environmental liability exposure that can reach into the hundreds of millions.

Key risk drivers:

1. **Contamination assessment accuracy** — The accuracy of Phase I/II environmental site assessments is the primary quality signal. A consultant who misses contamination that is later discovered faces both malpractice and CERCLA exposure.
2. **Regulatory compliance track record** — Environmental regulations are complex, jurisdiction-specific, and frequently amended. A consultant's track record of regulatory compliance advice accuracy is directly predictive.
3. **Remediation effectiveness** — For firms advising on contaminated site remediation, the effectiveness of their remediation strategies (measured by regulatory closure rates) is a quality proxy.
4. **CERCLA/Superfund exposure** — Direct involvement in Superfund sites creates tail exposure that can persist for decades. The number and severity of Superfund site involvements is a critical exposure signal.

### Signal Architecture Rationale

**Primary driver: Environmental Assessment Quality (Risk: 0.35, Loss: 0.30, Exposure: 0.45 = 1.10 combined)**

The new `environmental_assessment_quality` group has the second-highest combined weight in Phase 6 (after `engineering_quality`). This reflects the extreme long-tail exposure and the direct causal chain between assessment quality and loss outcome.

**Secondary driver: Regulatory Standing (Risk: 0.20, Loss: 0.20, Exposure: 0.10 = 0.50 combined)**

Environmental consulting operates under a complex, multi-jurisdictional regulatory framework. EPA, state environmental agencies, and international equivalents produce enforcement data that is directly predictive.

**Deprioritised: Network Authority, Corporate Footprint, Technical Infrastructure**

Environmental consulting is a technical discipline where the quality of the science matters, not the quality of the marketing. Minimal weights for non-technical groups.

### New Signals (Not in `pi_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `contamination_assessment_accuracy` | DIRECT_OBSERVABLE | environmental_assessment_quality | Phase I/II assessment accuracy — the primary loss predictor |
| `regulatory_compliance_track` | DIRECT_OBSERVABLE | environmental_assessment_quality | Environmental regulation compliance advice accuracy |
| `remediation_effectiveness` | INFERRED_PROXY | environmental_assessment_quality | Remediation advice effectiveness measured by regulatory closure rates |
| `long_tail_exposure` | INFERRED_PROXY | environmental_assessment_quality | Latent contamination discovery risk; 15-20 year tail |
| `cercla_superfund_exposure` | DIRECT_OBSERVABLE | environmental_assessment_quality | CERCLA/Superfund site involvement; PRP designation exposure |

### Pricing Philosophy

- **Basis**: Revenue
- **Method**: MULTIPLIER on revenue
- **Tier 3 rate**: **0.0030** (0.30%). Elevated rate reflecting the extraordinary long-tail exposure and CERCLA severity potential. Among the highest rates in the PI suite.
- **Limit Configuration**: **DECOUPLED** — $2,000,000 base limit with $50,000 deductible.
- **Min Premium**: $20,000
- **Product types**: `professional_liability`, `errors_omissions`

### Example Company Returns

**Tier 1 — PREFERRED:**
> **ERM Group** (global environmental consultancy leader)
> - Revenue: $1.2B | Limit: $25M | Score: 828
> - Why: Exemplary assessment accuracy (zero missed contamination findings in reviewed portfolio), clean EPA enforcement record, 95%+ remediation regulatory closure rate, diversified across assessment types and geographies, no active Superfund PRP designations, ISO 14001-certified operations
> - Premium: $1.2B × 0.0014 = $1.68M base → firm_size modifier (MAJOR: 0.85) → geographic diversification modifier (0.85) → **~$1.21M net**

**Tier 3 — STANDARD:**
> **Regional environmental consultant** (composite profile)
> - Revenue: $8M | Limit: $2M | Score: 547
> - Why: One missed contamination finding (Phase I assessment, client claim settled for $400K, 5 years ago), adequate regulatory compliance track record, remediation closure rate at 78%, moderate CERCLA exposure (advisory role on 2 Superfund sites), concentrated in one state jurisdiction
> - Premium: $8M × 0.0030 = $24,000 base → firm_size modifier (SMALL: 1.00) → **~$24,000 net**

**Tier 5 — DECLINE:**
> **Firm with Superfund liability** (composite profile)
> - Revenue: $3M | Limit: $2M | Score: 145
> - Why: Named as PRP on two active Superfund sites (combined estimated liability $25M+), three missed contamination claims in 7 years, EPA enforcement action for negligent site assessment methodology, remediation closure rate at 45%, state environmental license under review
> - Decline triggers: environmental_assessment_quality group score <= 10, cercla_superfund_exposure <= 5, contamination_assessment_accuracy <= 15

---

## Implementation Plan

### Step 1: Configuration Generation via Builder

Each new configuration will be generated using the Coverage Builder with carefully constructed `CoverageSpec` objects. The builder handles:
- Signal selection and weight calculation
- Three-layer weight normalisation (Risk + Loss + Exposure = 1.0 per dimension)
- Tier band generation (respecting the chosen tier_strategy)
- ILF curve and deductible factor generation
- YAML serialisation and validation

However, the builder's output will be treated as a **starting point, not a final product**. Each configuration requires manual refinement because:
1. New signals (lateral_hire_volume, pcaob_inspection_deficiency_rate, structural_failure_history, etc.) are not in the builder's signal library
2. Pricing rates must be calibrated to market reality, not generated algorithmically
3. Score conditions and referral thresholds need domain-specific tuning
4. Profession-specific categorical modifiers require manual definition

### Step 2: Manual Refinement & New Signal Integration

After builder generation, each configuration will be manually enhanced:
- Inject new domain-specific signals into the signal_registry
- Calibrate tier band thresholds to market pricing benchmarks
- Add domain-specific direct queries
- Tune score_conditions at both signal and group level
- Validate weight normalisation after all modifications
- Define profession-specific categorical modifiers (sub_profession_type, construction_phase, etc.)

### Step 3: Documentation Generation

Run `doc_generator.py` to produce `logic.md` for each configuration. Then supplement with:
- **Narrative documentation** (the "why" behind each configuration) — embedded directly in the phase document and configuration comments
- **Example company profiles** — real-world submission scenarios showing the model producing credible output
- **Pricing validation** — theoretical premium calculations at each tier to verify actuarial reasonableness

### Step 4: Validation & Cross-Configuration Testing

- Run the builder's `validate` command against each generated config
- Verify multiplexer routing: ensure every combination of `profession_segment` + `sub_profession_type` + `revenue` routes to the intended configuration
- Verify no routing gaps: every valid PI submission must match at least `pi_general`
- Verify pricing continuity: a submission at the boundary between two configurations should produce comparable (not wildly different) premiums
- Verify weight normalisation: R/L/E each sum to 1.0 for every configuration

---

## Summary of Deliverables

| # | Deliverable | Description |
|---|---|---|
| 1 | `pi_legal_large` config.yaml | Large law firm configuration |
| 2 | `pi_legal_specialist` config.yaml | Specialist/plaintiff law firm configuration |
| 3 | `pi_audit` config.yaml | Public company audit configuration |
| 4 | `pi_accounting` config.yaml | Non-audit accounting configuration |
| 5 | `pi_architecture` config.yaml | Architecture & landscape design configuration |
| 6 | `pi_engineering` config.yaml | Structural, civil, geotechnical engineering configuration |
| 7 | `pi_technology` config.yaml | IT consulting & systems integration configuration |
| 8 | `pi_financial_advisory` config.yaml | Wealth management & IFA configuration |
| 9 | `pi_management_consulting` config.yaml | Strategy & management advisory configuration |
| 10 | `pi_real_estate` config.yaml | Surveyors, valuers, estate agents configuration |
| 11 | `pi_environmental` config.yaml | Environmental consulting configuration |
| 12 | Updated `pi/config.yaml` | All 13 configurations in PI coverage |
| 13 | Updated `logic.md` | Auto-generated documentation for all 13 models |
| 14 | Signal registry updates | All new signals registered in `signal_architecture/signals/` |
| 15 | Narrative documentation | This phase document serves as the detailed narrative |
| 16 | Seed data updates | `seed_dsi_bench.py` expanded with entries for all 13 configurations |

### Signal Registry Confirmation

All new domain-specific signals introduced across the eleven new configurations will be added to the signal registry at `signal_architecture/signals/inference/functions/pi/signals.py`. This includes:

- **pi_legal_large (7 new):** `lateral_hire_volume`, `prior_acts_coverage`, `conflict_system_quality`, `trust_account_compliance`, `class_action_exposure`, `partner_departure_rate`, `matter_concentration`
- **pi_legal_specialist (5 new):** `case_concentration`, `contingency_fee_ratio`, `trial_success_rate`, `statute_tracking_compliance`, `case_value_distribution`
- **pi_audit (7 new):** `pcaob_inspection_deficiency_rate`, `restatement_rate`, `going_concern_accuracy`, `sec_enforcement_exposure`, `audit_client_concentration`, `audit_partner_rotation_compliance`, `securities_litigation_exposure`
- **pi_accounting (3 new):** `tax_opinion_quality`, `irs_examination_track`, `estate_planning_complexity`
- **pi_architecture (6 new):** `design_defect_claims`, `building_code_compliance`, `project_complexity_score`, `latent_defect_exposure`, `sustainability_certification`, `construction_phase`
- **pi_engineering (6 new):** `structural_failure_history`, `pe_license_compliance`, `geotechnical_claim_frequency`, `infrastructure_project_exposure`, `project_size_concentration`, `remediation_cost_history`
- **pi_technology (6 new):** `project_failure_rate`, `sla_compliance`, `data_breach_exposure`, `technology_stack_currency`, `implementation_methodology`, `client_data_encryption`
- **pi_financial_advisory (5 new):** `suitability_compliance`, `complaint_per_aum`, `regulatory_exam_results`, `churning_indicators`, `fee_transparency_score`
- **pi_management_consulting (3 new):** `engagement_scope_clarity`, `deliverable_acceptance_rate`, `client_outcome_correlation`
- **pi_real_estate (5 new):** `valuation_accuracy`, `negligent_misstatement_history`, `property_type_concentration`, `market_knowledge_currency`, `rics_compliance`
- **pi_environmental (5 new):** `contamination_assessment_accuracy`, `regulatory_compliance_track`, `remediation_effectiveness`, `long_tail_exposure`, `cercla_superfund_exposure`

**Total new signals: 58.** Each will have a stub inference function registered in the metadata registry for demo/testing, with full extractor integrations phased in during subsequent implementation.

---

## Review Resolution Matrix

Review findings from the initial PI general model are addressed by the expanded architecture.

| # | Review Finding | Resolution |
|---|---|---|
| 1.1 | Single PI model cannot distinguish legal from engineering risk | **Resolved** — 11 profession-specific configurations with distinct signal architectures |
| 1.2 | Audit firms underpriced relative to severity exposure | **Resolved** — `pi_audit` has dedicated pricing at 2.5x general rate with audit_quality group |
| 2.1 | Incomplete weight distributions for profession variants | **Appendix B** — Complete R/L/E tables for all 11 configs |
| 2.2 | Missing profession-specific signal groups | **Configurations 1-11** — 9 new groups introduced, 2 configs reuse existing groups |
| 2.3 | Missing tier band specifications per profession | **Appendix C** — Full 5-tier bands for all 11 configs with profession-specific rates |
| 3.1 | Small practice routing gap for specialised professions | **Appendix G** — `pi_sme` catches revenue ≤ $50M practices; profession_segment enables specific routing |
| 3.2 | `profession_segment` pre-routing undefined | **Appendix G** — Optional input field enabling specific routing, mirroring energy's operation_segment |
| 4.1 | Signal specs incomplete for profession variants | **Appendix D** — Full signal tables with inference functions for all 58 new signals |
| 5.1 | Pricing anchors missing per profession | **Appendix F** — Base limit/deductible for all configs |
| 5.2 | ILF curves missing for high-severity professions | **Appendix F** — Key ILF tables for audit and engineering |
| 6.1 | Direct queries not profession-specific | **Appendix E** — Profession-specific queries per config |
| 6.2 | MVI per config missing | **Appendix H** — Full MVI specs for all configs |
| 7.1 | Seed data plan for profession variants | **Appendix I** — Expanded to all 13 configurations |

---

## Appendix A: The Professional Services Value Chain — Thirteen Configurations

```
ADVISORY SERVICES
├── LEGAL
│   ├── pi_legal_large ──────── Top-tier corporate/commercial (AmLaw 200, Magic Circle)
│   └── pi_legal_specialist ── Specialist/plaintiff/niche practices
│
├── FINANCIAL & ADVISORY
│   ├── pi_financial_advisory ── Wealth management, IFAs, RIAs, pension advisers
│   └── pi_management_consulting ── Strategy & management advisory
│
└── TECHNOLOGY
    └── pi_technology ────────── IT consulting, systems integration, managed services

ASSURANCE & COMPLIANCE
├── ACCOUNTING & AUDIT
│   ├── pi_audit ─────────────── Public company audit (Big 4, mid-tier)
│   └── pi_accounting ────────── Non-audit: tax, advisory, bookkeeping
│
└── ENVIRONMENTAL
    └── pi_environmental ──────── EIA, contaminated land, remediation advisory

DESIGN & CONSTRUCTION
├── pi_architecture ───────────── Architecture & landscape design
└── pi_engineering ────────────── Structural, civil, geotechnical engineering

VALUATION
└── pi_real_estate ──────────── Surveyors, valuers, estate agents

CROSS-CUTTING
├── pi_general ──────────────── Universal fallback (revenue > $50M)
└── pi_sme ──────────────────── Small practices (revenue ≤ $50M, BUNDLED)
```

Together, these thirteen configurations can price:
- A $7B AmLaw #1 law firm's global programme (routed to `pi_legal_large`)
- A $45M securities plaintiff boutique (routed to `pi_legal_specialist`)
- A $53B Big 4 audit firm (routed to `pi_audit`)
- A $12M regional CPA practice (routed to `pi_accounting`)
- A $1.9B global architecture firm (routed to `pi_architecture`)
- A $14B infrastructure engineering firm (routed to `pi_engineering`)
- A $64B technology consultancy (routed to `pi_technology`)
- A $1.8B wealth management firm (routed to `pi_financial_advisory`)
- A $16B strategy consultancy (routed to `pi_management_consulting`)
- A $2.1B property valuation firm (routed to `pi_real_estate`)
- A $1.2B environmental consultancy (routed to `pi_environmental`)
- A $500K solo practitioner (routed to `pi_sme`)
- A $200M multi-discipline professional services firm (routed to `pi_general`)

No commercially relevant professional services submission falls outside this matrix.

---

## Appendix B: Complete Three-Layer Weight Distributions

Every configuration must satisfy the DSI constraint: **Risk weights sum to 1.0, Loss weights sum to 1.0, Exposure weights sum to 1.0** across all groups. The tables below provide the complete distributions for each new configuration.

### Reference: `pi_general` (Existing)

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.15 | 0.10 | 0.05 |
| regulatory_standing | 0.25 | 0.25 | 0.10 |
| firm_stability | 0.15 | 0.15 | 0.20 |
| practice_quality | 0.15 | 0.20 | 0.15 |
| technical_infrastructure | 0.10 | 0.10 | 0.10 |
| corporate_footprint | 0.10 | 0.05 | 0.25 |
| litigation_history | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### B.1: `pi_legal_large`

Firm stability is elevated because partner departures can destroy large firms (Dewey & LeBoeuf). The partner_practice_mix group carries high exposure weight (0.25) reflecting single-matter concentration risk. Regulatory standing is reduced slightly from general — large firms have compliance departments that prevent most regulatory issues.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Partner_practice_mix added (8 groups, not 7) with high exposure weight
- Corporate Footprint Exposure reduced from 0.25 to 0.10 (large firm websites are noise)
- Firm Stability Risk +0.05 (partner exodus risk)

### B.2: `pi_legal_specialist`

Case portfolio dominates exposure (0.35) because a single case can define a specialist firm's entire risk profile. Litigation history elevated because specialist firms' own malpractice history is highly predictive. Practice quality elevated in loss weight because work quality directly drives outcomes.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Case_portfolio added with highest exposure weight (0.35) of any legal config
- Technical Infrastructure and Corporate Footprint minimised (specialist firms are small)
- Litigation History Loss +0.05 (own malpractice history is dominant predictor)

### B.3: `pi_audit`

Regulatory standing has the highest combined weight (0.75) of any PI configuration — reflecting PCAOB inspection regime. Audit quality exposure weight (0.40) reflects catastrophic concentration risk from single-client restatements.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Regulatory Standing Risk +0.05, Loss +0.05 (PCAOB is the most intensive regulatory regime in PI)
- Audit Quality added with extremely high exposure weight (0.40)
- Network Authority minimised (peer rankings irrelevant for audit quality)
- Corporate Footprint minimised

### B.4: `pi_accounting`

No new group — uses 7 existing groups with rebalanced weights. Practice quality elevated because work product quality (tax opinions, financial statements) is directly observable through client outcomes.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| regulatory_standing | 0.25 | 0.25 | 0.10 |
| firm_stability | 0.15 | 0.15 | 0.20 |
| practice_quality | 0.20 | 0.20 | 0.20 |
| technical_infrastructure | 0.10 | 0.10 | 0.10 |
| corporate_footprint | 0.10 | 0.05 | 0.15 |
| litigation_history | 0.10 | 0.20 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Practice Quality Risk +0.05, Exposure +0.05 (tax opinion quality is observable)
- Litigation History Loss +0.05, Exposure +0.05 (fee disputes and malpractice are frequent)
- Corporate Footprint Exposure -0.10 (less relevant than general)

### B.5: `pi_architecture`

Design quality dominates — the highest combined new group weight in Phase 6. Exposure weight of 0.45 reflects latent defect long-tail (10-15 year discovery period).

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Design Quality added with highest exposure weight (0.45) — latent defect tail
- Regulatory Standing reduced (architectural licensing is less aggressive than legal/audit)
- Technical Infrastructure and Corporate Footprint minimised

### B.6: `pi_engineering`

Engineering quality has the highest combined weight (1.20) of any group in Phase 6. Exposure weight of 0.50 reflects catastrophic severity from structural failures.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Engineering Quality dominates all three dimensions (structural failure IS the risk)
- Network Authority minimised (peer rankings irrelevant vs PE compliance)
- Corporate Footprint minimised

### B.7: `pi_technology`

Technical infrastructure is elevated for the first time in PI — a technology firm's own security posture predicts client delivery quality. Delivery quality has high exposure weight (0.35) reflecting project concentration.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Technical Infrastructure Loss +0.10, Risk +0.05 (own security predicts client delivery)
- Delivery Quality added with high exposure weight (0.35)
- Regulatory Standing reduced (lighter regulatory oversight)
- Corporate Footprint minimised

### B.8: `pi_financial_advisory`

Regulatory standing matches audit-level importance (0.65 combined) — FCA/SEC oversight is intensive. Advisory quality exposure weight (0.30) reflects systemic mis-selling potential.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Advisory Quality added with high exposure weight (0.30) — systemic mis-selling risk
- Regulatory Standing Exposure +0.05 (FCA/SEC intensive oversight)
- Corporate Footprint minimised

### B.9: `pi_management_consulting`

No new group — uses 7 existing groups with rebalanced weights. Practice quality is the primary driver (0.60 combined). Corporate footprint is elevated because reputation IS the product in management consulting.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.15 | 0.10 | 0.10 |
| regulatory_standing | 0.15 | 0.15 | 0.05 |
| firm_stability | 0.20 | 0.15 | 0.20 |
| practice_quality | 0.20 | 0.25 | 0.15 |
| technical_infrastructure | 0.10 | 0.10 | 0.15 |
| corporate_footprint | 0.10 | 0.10 | 0.20 |
| litigation_history | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Practice Quality Loss +0.05, Risk +0.05 (advice quality is the primary driver)
- Corporate Footprint Exposure -0.05 but Risk +0.00 (reputation matters, but less than general's 0.25 exposure)
- Regulatory Standing reduced (minimal professional regulation)
- Firm Stability elevated (key-person dependency)

### B.10: `pi_real_estate`

Valuation quality dominates exposure (0.40) — a single negligent valuation can exceed annual revenue. Regulatory standing elevated because RICS/Appraisal Institute compliance is essential for market access.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Valuation Quality added with high exposure weight (0.40) — single-valuation concentration risk
- Technical Infrastructure and Corporate Footprint minimised
- Regulatory Standing maintained (RICS/Appraisal Institute enforcement is active)

### B.11: `pi_environmental`

Environmental assessment quality dominates all three dimensions — the second-highest combined group weight in Phase 6. Exposure weight of 0.45 reflects the extraordinary 15-20 year long tail and CERCLA exposure.

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
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Environmental Assessment Quality dominates (CERCLA tail + 15-20 year discovery period)
- Network Authority minimised (peer rankings irrelevant for environmental science quality)
- Corporate Footprint minimised
- Technical Infrastructure minimised

---

## Appendix C: Risk Tier Band Specifications

Each configuration defines five risk tiers with score bands, actions, and rates. The Tier 3 rate is the reference rate discussed in the configuration narratives; other tiers scale from this anchor.

### C.1: `pi_legal_large`

Large law firm rates reflect severity exposure from securities litigation and class action representation. Tier 1 rates reward firms with best-in-class conflict systems and clean disciplinary records.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0012 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0018 |
| 3 | STANDARD | 500–649 | REFER | 0.0028 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0042 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0065 |

### C.2: `pi_legal_specialist`

The highest legal rates, reflecting case concentration risk and contingency fee exposure. The gap between Tier 3 and Tier 4 is wider than general, reflecting rapid risk deterioration in specialist practice.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0015 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0022 |
| 3 | STANDARD | 500–649 | REFER | 0.0032 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0048 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0075 |

### C.3: `pi_audit`

The highest rates in the PI suite — reflecting catastrophic severity from securities class actions. Tier 5 rate of 0.0110 means a $1B audit firm would face $11M in premium before modifiers — effectively uninsurable, which is the intended outcome.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0020 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0030 |
| 3 | STANDARD | 500–649 | REFER | 0.0045 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0070 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0110 |

### C.4: `pi_accounting`

Moderate rates reflecting manageable severity. Non-audit accounting claims are typically in the $100K–$1M range, with rare outliers for aggressive tax shelter opinions.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0010 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0015 |
| 3 | STANDARD | 500–649 | REFER | 0.0022 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0035 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0055 |

### C.5: `pi_architecture`

Moderate rates reflecting long-tail but generally manageable severity. Construction-phase submissions receive a categorical modifier per the `construction_phase` signal.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0012 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0018 |
| 3 | STANDARD | 500–649 | REFER | 0.0026 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0040 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0060 |

### C.6: `pi_engineering`

Among the highest PI rates, reflecting structural failure severity. The gap between Tier 4 and Tier 5 is the widest in PI because marginal engineering risks deteriorate into catastrophic territory rapidly.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0015 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0022 |
| 3 | STANDARD | 500–649 | REFER | 0.0032 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0050 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0080 |

### C.7: `pi_technology`

Moderate rates reflecting frequency-driven loss profile. Technology PI claims are generally capped by project value, limiting severity. Auto-approve thresholds match general.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0010 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0015 |
| 3 | STANDARD | 500–649 | REFER | 0.0022 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0035 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0055 |

### C.8: `pi_financial_advisory`

Elevated rates reflecting regulatory intensity and systemic mis-selling exposure. Matches `pi_legal_large` rates — financial advisory severity is comparable for systemic scenarios.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0012 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0018 |
| 3 | STANDARD | 500–649 | REFER | 0.0028 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0042 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0065 |

### C.9: `pi_management_consulting`

The lowest rates in the PI suite — reflecting attenuated causal chain between advice and loss. Auto-approve extends to Tier 2 because management consulting claims rarely produce catastrophic outcomes.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0006 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0010 |
| 3 | STANDARD | 500–649 | REFER | 0.0015 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0024 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0038 |

### C.10: `pi_real_estate`

Moderate rates reflecting valuation dispute frequency balanced against generally manageable severity. Property market downturns generate claim surges.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0010 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0015 |
| 3 | STANDARD | 500–649 | REFER | 0.0022 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0035 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0055 |

### C.11: `pi_environmental`

Elevated rates reflecting extraordinary long-tail exposure and CERCLA severity potential. Among the highest in the PI suite, behind only audit and engineering.

| Tier | Label | Score Band | Action | Rate (× Revenue) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0014 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0020 |
| 3 | STANDARD | 500–649 | REFER | 0.0030 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0046 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0072 |

---

## Appendix D: Complete Signal Specifications

Each new signal is defined with the full specification required by the builder and runtime: inference function, proxy tier, group, correlation direction, expectation level, and source. Signals retained from `pi_general` are not repeated here — only new signals introduced by each configuration.

### D.1: `pi_legal_large` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `lateral_hire_volume` | `lateral_hire_volume_basefunction` | INFERRED_PROXY | partner_practice_mix | score | negative | EXPECTED |
| `prior_acts_coverage` | `prior_acts_coverage_basefunction` | DIRECT_OBSERVABLE | partner_practice_mix | score | positive | REQUIRED |
| `conflict_system_quality` | `conflict_system_quality_basefunction` | INFERRED_PROXY | partner_practice_mix | score | positive | REQUIRED |
| `trust_account_compliance` | `trust_account_compliance_basefunction` | DIRECT_OBSERVABLE | partner_practice_mix | score | positive | REQUIRED |
| `class_action_exposure` | `class_action_exposure_basefunction` | INFERRED_PROXY | partner_practice_mix | score | negative | EXPECTED |
| `partner_departure_rate` | `partner_departure_rate_basefunction` | DIRECT_OBSERVABLE | partner_practice_mix | score | negative | REQUIRED |
| `matter_concentration` | `matter_concentration_basefunction` | INFERRED_PROXY | partner_practice_mix | score | negative | EXPECTED |

**Retained from `pi_general` (all signals).** Total signal count: **+7** from general base.

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `trust_account_compliance` | 25 | <= | REFER | 5 | Trust account violations — disciplinary-level |
| `trust_account_compliance` | 45 | <= | REFER | 4 | Trust account compliance concerns |
| `prior_acts_coverage` | 30 | <= | REFER | 5 | Prior acts coverage gap — uninsured tail |
| `prior_acts_coverage` | 50 | <= | REFER | 4 | Prior acts coverage inadequacy |
| `partner_departure_rate` | 20 | <= | REFER | 4 | High partner departure rate |
| `conflict_system_quality` | 30 | <= | REFER | 4 | Inadequate conflict screening |
| `matter_concentration` | 25 | <= | FLAG | null | Single-matter concentration >25% of revenue |
| `class_action_exposure` | 30 | <= | FLAG | null | High class action exposure |

### D.2: `pi_legal_specialist` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `case_concentration` | `case_concentration_basefunction` | INFERRED_PROXY | case_portfolio | score | negative | REQUIRED |
| `contingency_fee_ratio` | `contingency_fee_ratio_basefunction` | DIRECT_OBSERVABLE | case_portfolio | score | negative | REQUIRED |
| `trial_success_rate` | `trial_success_rate_basefunction` | INFERRED_PROXY | case_portfolio | score | positive | EXPECTED |
| `statute_tracking_compliance` | `statute_tracking_compliance_basefunction` | INFERRED_PROXY | case_portfolio | score | positive | REQUIRED |
| `case_value_distribution` | `case_value_distribution_basefunction` | INFERRED_PROXY | case_portfolio | score | negative | EXPECTED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `statute_tracking_compliance` | 20 | <= | REFER | 5 | SOL tracking failures — #1 malpractice cause |
| `statute_tracking_compliance` | 40 | <= | REFER | 4 | Statute tracking deficiencies |
| `case_concentration` | 20 | <= | REFER | 4 | Extreme case concentration (>40% from single case) |
| `case_concentration` | 35 | <= | FLAG | null | Elevated case concentration |
| `contingency_fee_ratio` | 25 | <= | FLAG | null | Very high contingency ratio (>80%) |
| `trial_success_rate` | 25 | <= | FLAG | null | Poor trial success rate |

### D.3: `pi_audit` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `pcaob_inspection_deficiency_rate` | `pcaob_inspection_deficiency_rate_basefunction` | DIRECT_OBSERVABLE | audit_quality | score | positive | REQUIRED |
| `restatement_rate` | `restatement_rate_basefunction` | DIRECT_OBSERVABLE | audit_quality | score | positive | REQUIRED |
| `going_concern_accuracy` | `going_concern_accuracy_basefunction` | INFERRED_PROXY | audit_quality | score | positive | EXPECTED |
| `sec_enforcement_exposure` | `sec_enforcement_exposure_basefunction` | DIRECT_OBSERVABLE | audit_quality | score | positive | REQUIRED |
| `audit_client_concentration` | `audit_client_concentration_basefunction` | INFERRED_PROXY | audit_quality | score | negative | REQUIRED |
| `audit_partner_rotation_compliance` | `audit_partner_rotation_compliance_basefunction` | DIRECT_OBSERVABLE | audit_quality | score | positive | REQUIRED |
| `securities_litigation_exposure` | `securities_litigation_exposure_basefunction` | INFERRED_PROXY | audit_quality | score | negative | EXPECTED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `pcaob_inspection_deficiency_rate` | 20 | <= | REFER | 5 | High PCAOB deficiency rate — systemic quality failure |
| `pcaob_inspection_deficiency_rate` | 40 | <= | REFER | 4 | Elevated PCAOB deficiency rate |
| `restatement_rate` | 25 | <= | REFER | 5 | Multiple client restatements |
| `restatement_rate` | 45 | <= | REFER | 4 | Client restatement concerns |
| `sec_enforcement_exposure` | 20 | <= | REFER | 5 | SEC enforcement action |
| `audit_client_concentration` | 25 | <= | REFER | 4 | High client fee concentration (>15%) |
| `audit_partner_rotation_compliance` | 30 | <= | REFER | 4 | Partner rotation non-compliance |
| `securities_litigation_exposure` | 30 | <= | FLAG | null | Elevated securities litigation exposure |
| `going_concern_accuracy` | 30 | <= | FLAG | null | Going-concern opinion accuracy concerns |

### D.4: `pi_accounting` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `tax_opinion_quality` | `tax_opinion_quality_basefunction` | INFERRED_PROXY | practice_quality | score | positive | EXPECTED |
| `irs_examination_track` | `irs_examination_track_basefunction` | DIRECT_OBSERVABLE | regulatory_standing | score | positive | REQUIRED |
| `estate_planning_complexity` | `estate_planning_complexity_basefunction` | INFERRED_PROXY | practice_quality | score | negative | OPTIONAL |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `irs_examination_track` | 20 | <= | REFER | 5 | IRS preparer penalties or enforcement |
| `irs_examination_track` | 40 | <= | REFER | 4 | Elevated IRS challenge rate |
| `tax_opinion_quality` | 30 | <= | FLAG | null | Aggressive tax position quality concerns |

### D.5: `pi_architecture` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `design_defect_claims` | `design_defect_claims_basefunction` | DIRECT_OBSERVABLE | design_quality | score | positive | REQUIRED |
| `building_code_compliance` | `building_code_compliance_basefunction` | DIRECT_OBSERVABLE | design_quality | score | positive | REQUIRED |
| `project_complexity_score` | `project_complexity_score_basefunction` | INFERRED_PROXY | design_quality | score | negative | EXPECTED |
| `latent_defect_exposure` | `latent_defect_exposure_basefunction` | INFERRED_PROXY | design_quality | score | negative | EXPECTED |
| `sustainability_certification` | `sustainability_certification_basefunction` | DIRECT_OBSERVABLE | design_quality | score | positive | OPTIONAL |
| `construction_phase` | `construction_phase_basefunction` | DIRECT_OBSERVABLE | design_quality | metadata.construction_phase | — | REQUIRED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `design_defect_claims` | 20 | <= | REFER | 5 | Multiple design defect claims |
| `design_defect_claims` | 40 | <= | REFER | 4 | Design defect claim history |
| `building_code_compliance` | 25 | <= | REFER | 4 | Pattern code violations |
| `building_code_compliance` | 40 | <= | FLAG | null | Code compliance concerns |
| `latent_defect_exposure` | 25 | <= | FLAG | null | Elevated latent defect exposure |
| `project_complexity_score` | 20 | <= | FLAG | null | High project complexity concentration |

### D.6: `pi_engineering` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `structural_failure_history` | `structural_failure_history_basefunction` | DIRECT_OBSERVABLE | engineering_quality | score | positive | REQUIRED |
| `pe_license_compliance` | `pe_license_compliance_basefunction` | DIRECT_OBSERVABLE | engineering_quality | score | positive | REQUIRED |
| `geotechnical_claim_frequency` | `geotechnical_claim_frequency_basefunction` | DIRECT_OBSERVABLE | engineering_quality | score | positive | REQUIRED |
| `infrastructure_project_exposure` | `infrastructure_project_exposure_basefunction` | INFERRED_PROXY | engineering_quality | score | negative | EXPECTED |
| `project_size_concentration` | `project_size_concentration_basefunction` | INFERRED_PROXY | engineering_quality | score | negative | EXPECTED |
| `remediation_cost_history` | `remediation_cost_history_basefunction` | DIRECT_OBSERVABLE | engineering_quality | score | positive | EXPECTED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `structural_failure_history` | 15 | <= | REFER | 5 | Structural failure claim — catastrophic signal |
| `structural_failure_history` | 35 | <= | REFER | 4 | Structural deficiency concerns |
| `pe_license_compliance` | 20 | <= | REFER | 5 | PE license gap or suspension |
| `pe_license_compliance` | 40 | <= | REFER | 4 | PE compliance deficiencies |
| `geotechnical_claim_frequency` | 25 | <= | REFER | 5 | Multiple geotechnical failures |
| `geotechnical_claim_frequency` | 40 | <= | REFER | 4 | Geotechnical claim concerns |
| `project_size_concentration` | 25 | <= | FLAG | null | High single-project concentration |
| `infrastructure_project_exposure` | 30 | <= | FLAG | null | High public infrastructure exposure |

### D.7: `pi_technology` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `project_failure_rate` | `project_failure_rate_basefunction` | INFERRED_PROXY | delivery_quality | score | positive | REQUIRED |
| `sla_compliance` | `sla_compliance_basefunction` | DIRECT_OBSERVABLE | delivery_quality | score | positive | REQUIRED |
| `data_breach_exposure` | `data_breach_exposure_basefunction` | DIRECT_OBSERVABLE | delivery_quality | score | positive | REQUIRED |
| `technology_stack_currency` | `technology_stack_currency_basefunction` | INFERRED_PROXY | delivery_quality | score | positive | EXPECTED |
| `implementation_methodology` | `implementation_methodology_basefunction` | INFERRED_PROXY | delivery_quality | score | positive | EXPECTED |
| `client_data_encryption` | `client_data_encryption_basefunction` | DIRECT_OBSERVABLE | delivery_quality | score | positive | REQUIRED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `data_breach_exposure` | 20 | <= | REFER | 5 | Active data breach or inadequate controls |
| `data_breach_exposure` | 40 | <= | REFER | 4 | Data security concerns |
| `project_failure_rate` | 25 | <= | REFER | 4 | High project failure rate |
| `project_failure_rate` | 40 | <= | FLAG | null | Elevated project failure rate |
| `sla_compliance` | 30 | <= | REFER | 4 | Chronic SLA non-compliance |
| `client_data_encryption` | 25 | <= | REFER | 4 | Inadequate client data encryption |
| `technology_stack_currency` | 30 | <= | FLAG | null | Outdated technology stack |

### D.8: `pi_financial_advisory` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `suitability_compliance` | `suitability_compliance_basefunction` | DIRECT_OBSERVABLE | advisory_quality | score | positive | REQUIRED |
| `complaint_per_aum` | `complaint_per_aum_basefunction` | DIRECT_OBSERVABLE | advisory_quality | score | positive | REQUIRED |
| `regulatory_exam_results` | `regulatory_exam_results_basefunction` | DIRECT_OBSERVABLE | advisory_quality | score | positive | REQUIRED |
| `churning_indicators` | `churning_indicators_basefunction` | INFERRED_PROXY | advisory_quality | score | positive | EXPECTED |
| `fee_transparency_score` | `fee_transparency_score_basefunction` | INFERRED_PROXY | advisory_quality | score | positive | EXPECTED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `suitability_compliance` | 15 | <= | REFER | 5 | Suitability enforcement action |
| `suitability_compliance` | 35 | <= | REFER | 4 | Suitability compliance concerns |
| `regulatory_exam_results` | 20 | <= | REFER | 5 | Material regulatory exam deficiency |
| `regulatory_exam_results` | 40 | <= | REFER | 4 | Regulatory exam findings |
| `complaint_per_aum` | 25 | <= | REFER | 4 | High complaint rate per AUM |
| `churning_indicators` | 25 | <= | REFER | 4 | Churning indicators present |
| `fee_transparency_score` | 30 | <= | FLAG | null | Fee transparency concerns |

### D.9: `pi_management_consulting` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `engagement_scope_clarity` | `engagement_scope_clarity_basefunction` | INFERRED_PROXY | practice_quality | score | positive | EXPECTED |
| `deliverable_acceptance_rate` | `deliverable_acceptance_rate_basefunction` | DIRECT_OBSERVABLE | practice_quality | score | positive | EXPECTED |
| `client_outcome_correlation` | `client_outcome_correlation_basefunction` | INFERRED_PROXY | practice_quality | score | positive | OPTIONAL |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `engagement_scope_clarity` | 25 | <= | REFER | 4 | Poor engagement scope definition |
| `deliverable_acceptance_rate` | 30 | <= | FLAG | null | Low deliverable acceptance rate |
| `client_outcome_correlation` | 25 | <= | FLAG | null | Weak advice-to-outcome correlation |

### D.10: `pi_real_estate` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `valuation_accuracy` | `valuation_accuracy_basefunction` | DIRECT_OBSERVABLE | valuation_quality | score | positive | REQUIRED |
| `negligent_misstatement_history` | `negligent_misstatement_history_basefunction` | DIRECT_OBSERVABLE | valuation_quality | score | positive | REQUIRED |
| `property_type_concentration` | `property_type_concentration_basefunction` | INFERRED_PROXY | valuation_quality | score | negative | EXPECTED |
| `market_knowledge_currency` | `market_knowledge_currency_basefunction` | INFERRED_PROXY | valuation_quality | score | positive | EXPECTED |
| `rics_compliance` | `rics_compliance_basefunction` | DIRECT_OBSERVABLE | valuation_quality | score | positive | REQUIRED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `valuation_accuracy` | 20 | <= | REFER | 5 | Systematic over/under-valuation |
| `valuation_accuracy` | 40 | <= | REFER | 4 | Valuation accuracy concerns |
| `negligent_misstatement_history` | 20 | <= | REFER | 5 | Multiple negligent misstatement claims |
| `negligent_misstatement_history` | 40 | <= | REFER | 4 | Negligent misstatement claim history |
| `rics_compliance` | 25 | <= | REFER | 4 | RICS/Appraisal Institute non-compliance |
| `property_type_concentration` | 25 | <= | FLAG | null | High property type concentration |

### D.11: `pi_environmental` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `contamination_assessment_accuracy` | `contamination_assessment_accuracy_basefunction` | DIRECT_OBSERVABLE | environmental_assessment_quality | score | positive | REQUIRED |
| `regulatory_compliance_track` | `regulatory_compliance_track_basefunction` | DIRECT_OBSERVABLE | environmental_assessment_quality | score | positive | REQUIRED |
| `remediation_effectiveness` | `remediation_effectiveness_basefunction` | INFERRED_PROXY | environmental_assessment_quality | score | positive | EXPECTED |
| `long_tail_exposure` | `long_tail_exposure_basefunction` | INFERRED_PROXY | environmental_assessment_quality | score | negative | EXPECTED |
| `cercla_superfund_exposure` | `cercla_superfund_exposure_basefunction` | DIRECT_OBSERVABLE | environmental_assessment_quality | score | negative | REQUIRED |

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `contamination_assessment_accuracy` | 15 | <= | REFER | 5 | Missed contamination findings |
| `contamination_assessment_accuracy` | 35 | <= | REFER | 4 | Assessment accuracy concerns |
| `cercla_superfund_exposure` | 15 | <= | REFER | 5 | Active Superfund PRP designation |
| `cercla_superfund_exposure` | 35 | <= | REFER | 4 | Superfund site involvement |
| `regulatory_compliance_track` | 25 | <= | REFER | 4 | Regulatory compliance deficiencies |
| `remediation_effectiveness` | 30 | <= | FLAG | null | Low remediation closure rate |
| `long_tail_exposure` | 25 | <= | FLAG | null | Elevated long-tail discovery risk |

---

## Appendix E: Direct Queries per Configuration

Direct queries are binary questions answered before signal execution. Each configuration has 4-7 queries tuned to its profession segment. Queries inherited from `pi_general` are marked with *(inherited)*.

### E.1: `pi_legal_large`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice claims? *(inherited)* | REFER | 4 | Pending claims |
| `disciplinary_pending` | Any pending disciplinary proceedings against any partner? *(inherited)* | REFER | 4 | Disciplinary |
| `coverage_declined` | Has any PI coverage been declined or non-renewed in past 3 years? *(inherited)* | REFER | 5 | Prior non-renewal |
| `trust_account_issue` | Any trust account/IOLTA irregularities or investigations in past 5 years? | REFER | 5 | Trust account — highest severity |
| `lateral_wave` | Have >20% of equity partners been lateral hires in the past 2 years? | FLAG | null | High lateral volume flag |
| `mega_matter` | Any single matter representing >15% of firm revenue? | FLAG | null | Matter concentration flag |
| `class_action_lead` | Is the firm lead counsel in any class action with >$1B exposure? | FLAG | null | Catastrophic exposure flag |

### E.2: `pi_legal_specialist`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice claims? *(inherited)* | REFER | 4 | Pending claims |
| `disciplinary_pending` | Any pending disciplinary proceedings? *(inherited)* | REFER | 4 | Disciplinary |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `sol_missed` | Any missed statute of limitations or filing deadlines in past 5 years? | REFER | 5 | SOL miss — highest frequency malpractice cause |
| `single_case_majority` | Does any single case represent >30% of annual revenue? | REFER | 4 | Extreme case concentration |
| `bar_complaint` | Any bar complaints (beyond pending disciplinary) in past 3 years? | FLAG | null | Bar complaint flag |

### E.3: `pi_audit`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice claims? *(inherited)* | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `pcaob_deficiency` | Any Part I.A or Part II PCAOB deficiencies in last inspection cycle? | REFER | 4 | PCAOB deficiency |
| `client_restatement` | Any audit client financial restatement in past 3 years? | REFER | 4 | Client restatement |
| `sec_investigation` | Any SEC investigation or enforcement action involving the firm or partners? | REFER | 5 | SEC enforcement |
| `independence_violation` | Any audit independence violations (partner financial interest, non-audit services) in past 5 years? | REFER | 5 | Independence violation |
| `going_concern_miss` | Any audit client bankruptcy within 12 months of clean opinion? | REFER | 4 | Going-concern miss |

### E.4: `pi_accounting`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice claims? *(inherited)* | REFER | 4 | Pending claims |
| `disciplinary_pending` | Any pending state board disciplinary proceedings? *(inherited)* | REFER | 4 | Disciplinary |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `irs_preparer_penalty` | Any IRS preparer penalties or sanctions in past 5 years? | REFER | 5 | IRS penalties |
| `tax_shelter_involvement` | Any involvement in listed or reportable tax transactions? | REFER | 4 | Tax shelter exposure |

### E.5: `pi_architecture`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened design defect or malpractice claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `code_violation_pattern` | Any pattern of building code violations (>2 in 3 years) in any jurisdiction? | REFER | 4 | Code violation pattern |
| `structural_concern` | Any structural adequacy concerns raised by building officials on current projects? | REFER | 5 | Active structural concern |
| `license_issue` | Any architectural license under review, suspended, or revoked? | REFER | 5 | License issue |
| `latent_defect_discovery` | Any latent defect discovered on a project completed >5 years ago? | FLAG | null | Long-tail defect flag |

### E.6: `pi_engineering`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened structural failure or malpractice claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `structural_failure` | Any structural failure, collapse, or life-safety incident attributable to firm design in past 10 years? | REFER | 5 | Structural failure — catastrophic |
| `pe_license_issue` | Any PE license suspended, revoked, or under investigation in any jurisdiction? | REFER | 5 | PE license issue |
| `geotechnical_failure` | Any geotechnical failure (foundation, slope stability, bearing capacity) attributable to firm work? | REFER | 5 | Geotechnical failure |
| `public_infrastructure` | Does firm design critical public infrastructure (bridges, dams, water treatment)? | FLAG | null | Higher duty of care flag |

### E.7: `pi_technology`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice or breach of contract claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `project_abandonment` | Any client project abandoned or terminated for cause in past 3 years? | REFER | 4 | Project abandonment |
| `data_breach` | Any data breach involving client data in past 5 years? | REFER | 5 | Data breach — severe |
| `regulatory_investigation` | Any regulatory investigation (GDPR, CCPA, PCI-DSS) related to firm services? | REFER | 4 | Regulatory investigation |
| `sla_litigation` | Any SLA-related litigation or arbitration in past 3 years? | FLAG | null | SLA dispute flag |

### E.8: `pi_financial_advisory`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice or mis-selling claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `regulatory_action` | Any SEC/FCA enforcement action or fine in past 5 years? | REFER | 5 | Regulatory enforcement |
| `suitability_complaints` | Any suitability-related client complaints or FINRA arbitrations in past 3 years? | REFER | 4 | Suitability complaints |
| `churning_allegation` | Any churning or excessive trading allegations (client or regulatory)? | REFER | 5 | Churning — severe |
| `pension_transfer` | Does the firm advise on DB pension transfers (UK) or 401k rollovers (US)? | FLAG | null | High-risk advice type flag |

### E.9: `pi_management_consulting`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice or breach of contract claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `scope_dispute` | Any engagement scope disputes or fee disputes >$500K in past 3 years? | REFER | 4 | Scope dispute |
| `client_outcome_failure` | Any client alleging significant adverse outcome from following firm advice? | FLAG | null | Outcome allegation flag |

### E.10: `pi_real_estate`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened negligent misstatement or valuation claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `valuation_challenge` | Any valuation challenged or overturned by court or tribunal in past 5 years? | REFER | 4 | Valuation challenged |
| `rics_disciplinary` | Any RICS/Appraisal Institute disciplinary action or investigation? | REFER | 5 | Professional body action |
| `mortgage_fraud` | Any involvement in transactions subsequently identified as mortgage fraud? | REFER | 5 | Mortgage fraud exposure |
| `market_downturn_exposure` | Is >50% of portfolio in a single market segment currently in downturn? | FLAG | null | Market concentration flag |

### E.11: `pi_environmental`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `pending_claims` | Any pending or threatened malpractice or negligent assessment claims? | REFER | 4 | Pending claims |
| `coverage_declined` | Has any PI coverage been declined or non-renewed? *(inherited)* | REFER | 5 | Prior non-renewal |
| `missed_contamination` | Any instance of contamination discovered that firm's prior assessment failed to identify? | REFER | 5 | Missed contamination — severe |
| `superfund_prp` | Is the firm named as a PRP on any active CERCLA/Superfund site? | REFER | 5 | Superfund PRP — catastrophic |
| `epa_enforcement` | Any EPA enforcement action related to firm's assessment or remediation advice? | REFER | 4 | EPA enforcement |
| `long_tail_claim` | Any claim arising from assessment work completed >10 years ago? | FLAG | null | Long-tail claim flag |

---

## Appendix F: Pricing Anchors & ILF Curves

### F.1: Pricing Anchor References

Each DECOUPLED configuration must specify `base_limit_reference` and `base_deductible_reference` — the limit/deductible combination at which the Tier 3 rate applies without ILF or deductible factor adjustment.

| Configuration | Limit Type | Base Limit Reference | Base Deductible Reference | Min Premium |
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

**Note on audit/legal_large anchors:** The $10M and $5M base limits reflect minimum programme sizes. No underwriter writes a $500K audit PI programme for a public company audit firm. The $500K and $250K deductibles match typical programme structures for these segments.

### F.2: ILF Curves — `pi_audit`

Audit ILF curves are the steepest in the PI suite, reflecting the catastrophic securities litigation tail. Property/BI equivalent for PI is the securities class action tail.

**Professional Liability (securities class action tail, 40% steeper than general):**

| Limit | Factor |
|---|---|
| $10,000,000 | 1.0 |
| $25,000,000 | 2.0 |
| $50,000,000 | 3.5 |
| $100,000,000 | 6.0 |
| $250,000,000 | 12.5 |
| $500,000,000 | 22.0 |

**Deductible factors (audit):**

| Deductible | Factor |
|---|---|
| $250,000 | 1.15 |
| $500,000 | 1.0 |
| $1,000,000 | 0.90 |
| $2,500,000 | 0.80 |
| $5,000,000 | 0.70 |
| $10,000,000 | 0.60 |

### F.3: ILF Curves — `pi_engineering`

Engineering ILF curves reflect structural failure severity. Steeper than general above $5M reflecting catastrophic infrastructure claims.

**Professional Liability (structural failure tail, 30% steeper than general):**

| Limit | Factor |
|---|---|
| $2,000,000 | 1.0 |
| $5,000,000 | 2.2 |
| $10,000,000 | 3.8 |
| $25,000,000 | 7.0 |
| $50,000,000 | 12.0 |
| $100,000,000 | 20.0 |

**Deductible factors (engineering):**

| Deductible | Factor |
|---|---|
| $25,000 | 1.20 |
| $50,000 | 1.0 |
| $100,000 | 0.90 |
| $250,000 | 0.80 |
| $500,000 | 0.72 |
| $1,000,000 | 0.65 |

### F.4: ILF Curves — `pi_legal_large`

Large law firm ILF curves reflect securities litigation tail. Steeper than general for limits above $10M.

**Professional Liability (securities/class action tail, 25% steeper than general):**

| Limit | Factor |
|---|---|
| $5,000,000 | 1.0 |
| $10,000,000 | 1.8 |
| $25,000,000 | 3.5 |
| $50,000,000 | 6.0 |
| $100,000,000 | 10.5 |
| $250,000,000 | 19.0 |

**Deductible factors (legal_large):**

| Deductible | Factor |
|---|---|
| $100,000 | 1.20 |
| $250,000 | 1.0 |
| $500,000 | 0.90 |
| $1,000,000 | 0.82 |
| $2,500,000 | 0.72 |
| $5,000,000 | 0.62 |

### F.5: Worked Example Corrections

The Phase 6 narrative worked examples use "rate-on-line" figures that already incorporate the revenue-to-limit relationship. To clarify:

- **Kirkland & Ellis (legal_large T1):** $7.2B revenue × 0.0012 (T1 rate) = $8.64M base → ILF adjustment for $50M limit is applied where limit exceeds base → sub_profession modifier 1.25 → firm_size modifier 0.85 → jurisdiction modifier 1.05 → **~$9.6M net** (consistent with narrative)
- **PricewaterhouseCoopers (audit T1):** $53.0B revenue × 0.0020 (T1 rate) = $106M base → sub_profession modifier 1.50 → firm_size modifier 0.85 → geographic diversification 0.80 → **~$108M net** (consistent)
- **AECOM (engineering T1):** $14.4B revenue × 0.0015 (T1 rate) = $21.6M → sub_profession modifier 1.15 → firm_size modifier 0.85 → **~$21.1M net** (consistent)

**Note:** All other configurations use general PI ILF curves with profession-specific adjustments documented in the config.yaml implementation.

---

## Appendix G: Routing Resolution

This appendix addresses routing edge cases and the `profession_segment` pre-routing mechanism.

### G.1: `profession_segment` as a Pre-Routing Field

**Resolution: Optional input field.**

Add `profession_segment` to `minimum_viable_input.optional` for all PI configurations. When provided by the submitter, it enables specific routing. When absent, submissions default to `pi_general`.

This mirrors how underwriters actually work — they know whether a submission is a law firm or an engineering practice before assessing the risk. The `primaryprofessional_classification_basefunction` inference function still runs during signal execution (for the `profession_type` categorical modifier), but routing uses the input value if provided.

**Updated routing logic:**

```
IF input.profession_segment IS PROVIDED:
    Route by specificity, using input.profession_segment for segment constraints
ELSE:
    Route to pi_general (specificity 1, catches all)

IF profession_segment constraint is met AND revenue/sub_profession constraints are met:
    Route to specific config
ELSE:
    Fallback to pi_general
```

### G.2: Small-Practice Routing Gap Closure

**Gap:** Revenue ≤ $50M AND employee_count > 200 matches neither `pi_sme` nor any specialist configuration without `profession_segment`.

**Resolution:** `pi_general` has no lower revenue bound — its routing constraint is `revenue > $50000000`, but practices below this threshold that don't match `pi_sme` (e.g., 250-employee firms with $40M revenue) should still be priced. Lower `pi_general`'s revenue threshold to $10M. Practices with revenue < $10M and > 200 employees are not commercially viable PI submissions.

**Updated routing constraints (thirteen-configuration architecture):**

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
| `pi_general` | 1 | `revenue > 10000000` *(lowered from $50M)* | — |

### G.2.1: Design & Construction Sub-Profession Routing

The Design & Construction segment introduces a secondary routing dimension: `sub_profession_type`. When `profession_segment == DESIGN_CONSTRUCTION`, the multiplexer evaluates `sub_profession_type` to route to architecture or engineering:

```
IF profession_segment == DESIGN_CONSTRUCTION:
    IF sub_profession_type IN [ARCHITECTURE, LANDSCAPE, INTERIOR_DESIGN]:
        → pi_architecture (specificity 3)
    ELIF sub_profession_type IN [STRUCTURAL, GEOTECHNICAL, CIVIL, MECHANICAL, ELECTRICAL, ENVIRONMENTAL_ENG]:
        → pi_engineering (specificity 3)
    ELSE:
        → pi_general (fallback)
```

`sub_profession_type` is required for Design & Construction routing. When absent, the submission routes to `pi_general` — pricing an architect as an engineer (or vice versa) would be worse than a general price.

### G.3: Specificity Tie-Breaking

When a submission matches both a specialist config (e.g., `pi_accounting`) and `pi_sme` at specificity 2, the multiplexer breaks the tie by:

1. **Signal completeness** — the specialist config will have higher completeness for profession-specific signals
2. **Commercial value** — the specialist config produces more accurate pricing

**Deliberate design decision:** An accounting firm should be priced as an accounting firm, not as a generic SME. The multiplexer's existing tie-breaking logic produces the correct behavior without modification.

### G.4: Legal Revenue Threshold

**Acknowledged:** A law firm with $120M revenue routes to `pi_legal_large` rather than `pi_legal_specialist`. This is acceptable because:

- Law firms with >$100M revenue are invariably multi-practice corporate/commercial firms (AmLaw 200 or equivalent)
- True specialist boutiques rarely exceed $100M in revenue — Wachtell at $1.1B is the extreme outlier, and it has the risk profile of a large firm
- If `profession_segment == LEGAL` is provided without revenue data, the submission routes to `pi_legal_specialist` (specificity 3, which matches before `pi_general`)

---

## Appendix H: Minimum Viable Input per Configuration

### H.1: `pi_legal_large`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD (minimum $5,000,000)
    - field: revenue
      description: Annual firm revenue in USD (must exceed $100,000,000)
  optional:
    - field: profession_segment
      description: "LEGAL (enables routing)"
    - field: sub_profession_type
      description: "Primary practice: SECURITIES, CORPORATE_MA, LITIGATION_GENERAL, etc."
    - field: partner_count
      description: Number of equity partners
    - field: office_count
      description: Number of offices
    - field: lateral_hires_24m
      description: Number of lateral partner hires in past 24 months
```

### H.2: `pi_legal_specialist`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "LEGAL (enables routing)"
    - field: sub_profession_type
      description: "Specialty: SECURITIES, PERSONAL_INJURY_PLAINTIFF, CORPORATE_MA, FAMILY, etc."
    - field: attorney_count
      description: Number of attorneys
    - field: contingency_percentage
      description: Percentage of revenue from contingency fees
```

### H.3: `pi_audit`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD (minimum $10,000,000)
    - field: revenue
      description: Annual firm revenue in USD
    - field: sub_profession_type
      description: "AUDIT_PUBLIC or AUDIT_PRIVATE (required for routing)"
  optional:
    - field: profession_segment
      description: "ACCOUNTING (enables routing)"
    - field: public_audit_clients
      description: Number of public company audit clients
    - field: pcaob_registered
      description: Whether firm is PCAOB-registered (boolean)
    - field: largest_audit_client_revenue
      description: Revenue of largest audit client (concentration metric)
```

### H.4: `pi_accounting`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "ACCOUNTING (enables routing)"
    - field: sub_profession_type
      description: "TAX_CORPORATE, TAX_INDIVIDUAL, ADVISORY_VALUATION, FORENSIC, BOOKKEEPING, etc."
    - field: cpa_count
      description: Number of licensed CPAs
    - field: tax_return_volume
      description: Annual tax return volume
```

### H.5: `pi_architecture`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "DESIGN_CONSTRUCTION (enables routing)"
    - field: sub_profession_type
      description: "ARCHITECTURE, LANDSCAPE, INTERIOR_DESIGN"
    - field: construction_phase
      description: "PRE_CONSTRUCTION, CONSTRUCTION, COMMISSIONING, EARLY_OPERATION, MATURE_OPERATION"
    - field: licensed_architects
      description: Number of licensed architects
    - field: primary_project_type
      description: "COMMERCIAL, RESIDENTIAL_MULTI, HIGH_RISE, HEALTHCARE_FACILITIES, INSTITUTIONAL, etc."
```

### H.6: `pi_engineering`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "DESIGN_CONSTRUCTION (enables routing)"
    - field: sub_profession_type
      description: "STRUCTURAL, GEOTECHNICAL, CIVIL, MECHANICAL, ELECTRICAL, ENVIRONMENTAL_ENG"
    - field: pe_license_count
      description: Number of PE licenses held across jurisdictions
    - field: infrastructure_percentage
      description: Percentage of revenue from public infrastructure projects
```

### H.7: `pi_technology`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "TECHNOLOGY (enables routing)"
    - field: service_type
      description: "SYSTEMS_INTEGRATION, MANAGED_SERVICES, CONSULTING, DEVELOPMENT, CLOUD_MIGRATION"
    - field: employee_count
      description: Number of employees
    - field: client_data_volume
      description: "Volume of client data handled: LOW, MEDIUM, HIGH, CRITICAL"
```

### H.8: `pi_financial_advisory`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "FINANCIAL_ADVISORY (enables routing)"
    - field: aum
      description: Assets under management in USD
    - field: fee_model
      description: "FEE_ONLY, FEE_BASED, COMMISSION, HYBRID"
    - field: regulatory_registrations
      description: "SEC_RIA, FINRA, FCA, BOTH"
    - field: client_count
      description: Number of advisory clients
```

### H.9: `pi_management_consulting`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "MANAGEMENT_CONSULTING (enables routing)"
    - field: engagement_type
      description: "STRATEGY, OPERATIONS, DIGITAL, ORGANIZATIONAL, IMPLEMENTATION"
    - field: partner_count
      description: Number of partners/principals
    - field: avg_engagement_value
      description: Average engagement value in USD
```

### H.10: `pi_real_estate`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "REAL_ESTATE_VALUATION (enables routing)"
    - field: valuation_type
      description: "COMMERCIAL, RESIDENTIAL, INDUSTRIAL, LAND, MIXED"
    - field: annual_valuation_volume
      description: Number of valuations completed annually
    - field: professional_body
      description: "RICS, APPRAISAL_INSTITUTE, ASA, BOTH"
```

### H.11: `pi_environmental`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Firm name (domain optional for discovery)
    - field: product_type
      description: "One of: professional_liability, errors_omissions"
    - field: limit
      description: Requested limit in USD
    - field: revenue
      description: Annual firm revenue in USD
  optional:
    - field: profession_segment
      description: "ENVIRONMENTAL (enables routing)"
    - field: service_type
      description: "PHASE_I_II, REMEDIATION_ADVISORY, EIA, CONTAMINATED_LAND, COMPLIANCE_ADVISORY"
    - field: superfund_sites
      description: Number of active Superfund site involvements
    - field: assessment_volume
      description: Annual Phase I/II assessment volume
```

**Note:** `pi_sme` MVI is unchanged from the existing configuration — it requires `client_name`, `product_type`, and `revenue`, with optional `profession_segment` and `employee_count`.

---

## Appendix I: Seed Data Plan

Each new configuration requires seed entries at minimum Tier 1, 3, and 5 to support demo, integration testing, and multiplexer routing validation. The following plan uses the example companies already profiled in the Phase 6 narrative, supplemented by representative composites for new segments.

| Configuration | Tier 1 | Tier 3 | Tier 5 |
|---|---|---|---|
| `pi_legal_large` | Kirkland & Ellis | White & Case | Mid-tier firm with partner exodus (composite) |
| `pi_legal_specialist` | Wachtell, Lipton, Rosen & Katz | Plaintiff securities boutique (composite) | Solo practitioner with bar issues (composite) |
| `pi_audit` | PricewaterhouseCoopers | BDO USA | Mid-tier firm post-restatement scandal (composite) |
| `pi_accounting` | RSM US | Regional CPA firm (composite) | Firm with IRS penalties (composite) |
| `pi_architecture` | Gensler | Mid-size architecture firm (composite) | Firm with latent defect history (composite) |
| `pi_engineering` | AECOM | Mid-tier structural engineering firm (composite) | Firm with bridge/infrastructure failure (composite) |
| `pi_technology` | Accenture | Mid-tier systems integrator (composite) | Firm with failed ERP implementation litigation (composite) |
| `pi_financial_advisory` | Vanguard Personal Advisor | Regional RIA (composite) | IFA with mis-selling history (composite) |
| `pi_management_consulting` | McKinsey & Company | Mid-tier strategy firm (composite) | Firm with advice-failure litigation (composite) |
| `pi_real_estate` | CBRE Valuation & Advisory | Regional surveyor (composite) | Firm with negligent valuation history (composite) |
| `pi_environmental` | ERM Group | Regional environmental consultant (composite) | Firm with Superfund liability (composite) |

**Total new seed entries: 33** (3 per configuration × 11 configurations).

**Extended seed entries (Tier 2 and 4 where profiled):**

| Configuration | Tier 2 | Tier 4 |
|---|---|---|
| `pi_legal_large` | — | Firm with recent trust account citation (composite) |
| `pi_legal_specialist` | — | Practitioner with elevated contingency ratio (composite) |
| `pi_audit` | BDO USA | — |
| `pi_accounting` | — | Firm with state board citation (composite) |
| `pi_architecture` | — | Firm with single code violation (composite) |
| `pi_engineering` | — | Firm with single geotechnical claim (composite) |
| `pi_technology` | — | Firm with SLA compliance issues (composite) |
| `pi_financial_advisory` | — | RIA with minor SEC findings (composite) |
| `pi_management_consulting` | — | Firm with scope dispute history (composite) |
| `pi_real_estate` | — | Surveyor with moderate accuracy variance (composite) |
| `pi_environmental` | — | Consultant with single missed contamination (composite) |

Each seed entry will follow the established format:

```python
{
    "entity_name": "...",
    "domain": "...",
    "ticker": "...",
    "coverage": "professional_indemnity",
    "configuration": "pi_legal_large",  # per config
    "tier": 1,
    "decision": "approve",
    "premium": ...,
    "revenue": ...,
    "industry": "...",
    "size_band": "...",
    "geography": "...",
    "description": "...",
    "signal_profile": "pi_legal_large_excellent",  # new profile per config
    "product_type": "...",
    "limit": ...,
    "deductible": ...,
}
```

New signal profiles to create (3 per configuration, 33 total):
- `pi_legal_large_excellent`, `pi_legal_large_standard`, `pi_legal_large_distressed`
- `pi_legal_specialist_excellent`, `pi_legal_specialist_standard`, `pi_legal_specialist_distressed`
- `pi_audit_excellent`, `pi_audit_standard`, `pi_audit_catastrophic`
- `pi_accounting_excellent`, `pi_accounting_standard`, `pi_accounting_distressed`
- `pi_architecture_excellent`, `pi_architecture_standard`, `pi_architecture_distressed`
- `pi_engineering_excellent`, `pi_engineering_standard`, `pi_engineering_catastrophic`
- `pi_technology_excellent`, `pi_technology_standard`, `pi_technology_distressed`
- `pi_financial_advisory_excellent`, `pi_financial_advisory_standard`, `pi_financial_advisory_distressed`
- `pi_management_consulting_excellent`, `pi_management_consulting_standard`, `pi_management_consulting_distressed`
- `pi_real_estate_excellent`, `pi_real_estate_standard`, `pi_real_estate_distressed`
- `pi_environmental_excellent`, `pi_environmental_standard`, `pi_environmental_catastrophic`

### I.1: Seed Data Validation Requirements

Each seed entry must pass the following validation checks before inclusion in `seed_dsi_bench.py`:

1. **Routing validation** — The seed's `profession_segment` and `sub_profession_type` (where applicable) must route to the correct configuration via the multiplexer
2. **Tier consistency** — The seed's signal profile must produce a DSI score within the expected tier band for that configuration (per Appendix C)
3. **Pricing consistency** — The seed's premium must be within 20% of the pricing anchor × modifier calculation for its tier
4. **Weight verification** — The signal profile's group scores, when weighted by the configuration's three-layer weights (per Appendix B), must produce the expected overall score
5. **Product type validity** — The seed's `product_type` must be in the configuration's allowed product types

### I.2: `seed_dsi_bench.py` Expansion Plan

The seed script will be expanded to accommodate all thirteen PI configurations:

```
Current state:  pi_general + pi_sme only (existing)
Phase 6 adds:   11 new configurations × 3-5 seed entries each = 33-55 new entries
Total PI:       ~40-60 seed entries across 13 configurations
```

**Implementation approach:**
- Group seed entries by configuration in the script
- Each configuration block includes a comment referencing the narrative example it represents
- Signal profiles are defined in a separate `PI_SIGNAL_PROFILES` dictionary
- Routing validation tests are added as assertions at the end of the script to verify each seed routes to its intended configuration

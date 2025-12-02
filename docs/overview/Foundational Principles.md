# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Foundational Principles

| Item | Value |
|-|-|
|Version|1.0|
|Date|November 2025|
|Classification|Core Principles|

---

### Introduction

Digital Signal Intelligence (DSI) is a methodology for insurance underwriting that replaces traditional document-based analysis with observable digital signals. It is designed for today's market but architected for an Agentic AI future where autonomous systems require structured, predictable, machine-readable inputs.

Traditional insurance underwriting relies on unstructured documentation: application forms, broker submissions, questionnaires, and supporting documents. These vary wildly in format, completeness, and reliability. This variability has created cumbersome operating models with high processing costs and low straight-through processing (STP) rates.

DSI inverts this approach. Rather than asking companies to describe themselves, we observe what they do. Rather than requesting documentation, we analyse their digital footprint. Rather than trusting self-reported data, we verify through external signals.

The result is a pricing methodology that can operate autonomously, at scale, with high STP rates and low cost per bind.

---

### Foundational Concepts

#### The PageRank Insight

Google's PageRank algorithm transformed web search by recognising that the structure of links between pages revealed more about page quality than the content itself. A page linked to by many authoritative pages was likely authoritative itself, regardless of what it claimed about itself.

DSI applies this insight to insurance underwriting. The network of relationships surrounding a company—who trusts them, who partners with them, who references them, who transacts with them—reveals risk quality more reliably than self-reported information.

This network analysis extends beyond first-degree relationships. Just as PageRank computed authority through multi-hop link analysis, DSI builds deep relationship graphs: customers of customers, suppliers to suppliers, networks of networks. The deeper the quality signal propagates through the graph, the stronger the inference.

#### Behavioral Inference

Observable behavior predicts future behavior. How a company maintains its digital infrastructure, what it publishes, how it presents itself, what roles it hires for, and how it engages with regulators and industry bodies reveals organisational culture and risk management maturity.

These signals are difficult to fake at scale. A company can claim strong security practices, but its actual TLS configuration, exposed services, and patch discipline are observable. A company can claim strong governance, but its board composition, committee structure, and regulatory filings are public.

#### Parent-to-Subsidiary Inference

The behavior of a parent organisation is a reliable proxy for the behavior of its subsidiaries and assets. A shipping company with strong operational discipline across its fleet is unlikely to have rogue vessels operating to different standards. A financial institution with robust governance culture is unlikely to have divisions operating without controls.

This principle allows DSI to assess risk at the organisational level without requiring asset-by-asset analysis, enabling scalable underwriting for complex portfolios.

---

### The Ten Principles of DSI

#### Principle 1: External Observability

**All primary signals must be obtainable without cooperation from the insured.**

DSI signals are collected through external observation: web crawling, API queries, public database lookups, and digital telemetry. If a signal requires the insured to provide documentation, submit forms, or grant access, it is not a primary DSI signal.

This does not preclude all insured interaction (see Principle 7), but the core risk assessment must be possible through observation alone.

#### Principle 2: Machine Readability

**All signals must be extractable and processable by automated systems without human interpretation.**

Every signal in a DSI model must have a defined collection method, data format, and scoring algorithm. No signal may require subjective judgment in its collection or initial processing.

This enables autonomous operation and ensures consistency across assessments.

#### Principle 3: Network Authority

**Relationship patterns reveal quality.**

Who trusts, references, partners with, certifies, and transacts with an entity is a powerful signal of that entity's quality. These network signals follow PageRank principles:

- **Inbound authority:** Being trusted by high-quality entities increases score
- **Outbound selectivity:** Associating only with high-quality partners is positive
- **Network centrality:** Being well-connected in quality networks is positive
- **Isolation:** Operating outside recognized networks is a negative signal
- **Deep propagation:** Quality signals that persist through multiple relationship hops are stronger

Network authority signals are particularly valuable because they are difficult to fabricate and represent the aggregated judgment of multiple external parties.

#### Principle 4: Behavioral Inference Over Self-Reporting

**Observable behavior is preferred to stated intentions.**

When both a self-reported claim and an observable behavior are available, DSI weights the observable behavior more heavily. Examples:

- Claimed security certification vs. observable security implementation
- Stated governance practices vs. public board composition and filings
- Reported operational standards vs. observable telemetry patterns

Self-reported information is not excluded but is treated as lower-confidence data requiring corroboration.

#### Principle 5: Absence as Signal

**What is missing is as informative as what is present.**

The absence of expected digital presence is a valid and important signal:

- A public company without an investor relations page
- A technology company without a security disclosure page
- A regulated entity without visible compliance infrastructure
- A large employer without job postings or career pages
- A vessel operator without AIS transmission in expected patterns

Absence signals must be carefully calibrated—the expectation must be reasonable for the entity type and industry.

#### Principle 6: Structured Data Utilisation

**Pre-structured authoritative data sources are efficient signals.**

Ratings, scores, and indices from authoritative third-party providers (S&P, Moody's, MSCI, classification societies, regulatory bodies) are valid DSI signals. We use their conclusions as authority signals rather than recreating their analysis.

The principle: if a recognised authority has already assessed an aspect of risk and published a structured output, we can incorporate that output as a signal of network authority (the rating agency's judgment) rather than raw data requiring interpretation.

#### Principle 7: Minimal Direct Inquiry

**Direct questions are permitted but strictly constrained.**

Some critical risk factors cannot be externally observed. For these, DSI permits minimal direct inquiry under strict constraints:

| Constraint | Requirement |
|------------|-------------|
| Volume | Maximum 5-10 questions per line of business |
| Format | Binary (Yes/No) or simple categorical answers |
| Importance | Must address factors critical to risk assessment |
| Submission | Digital only (API or structured form) |
| Verification | Independent verification where practical |
| Treatment | Declarations subject to policy terms |

These questions are optional inputs. A DSI model must be capable of producing a risk assessment without them, though the assessment may have lower confidence or require additional margin.

Misrepresentation in direct inquiry responses is subject to standard policy terms regarding material misstatement, providing natural enforcement through policy cancellation risk.

#### Principle 8: Organisational-Level Assessment

**Parent behavior indicates subsidiary and asset behavior.**

DSI assesses risk at the organisational level. The premise: an organisation's culture, governance, and operational discipline propagate throughout its operations. A well-managed parent is likely to have well-managed subsidiaries and assets.

This enables scalable assessment without requiring individual analysis of every vessel, facility, subsidiary, or policy. Asset-specific telemetry (AIS, satellite imagery) is used to validate organizational behavior patterns, not to price individual assets.

#### Principle 9: Simplicity in Scoring

**Signal → Score → Tier → Price**

DSI models must follow a clear, auditable logic flow:

1. **Collect signals** from defined sources using defined methods
2. **Score signals** using defined algorithms to produce normalized values
3. **Weight and combine** signals to produce composite scores
4. **Assign tier** based on composite score thresholds
5. **Determine price** from tier-based pricing with limited adjustments

Complex modifier stacks that compound unpredictably are prohibited. Every pricing output must be explainable by reference to the signals that drove it.

#### Principle 10: Agentic Readiness

**Design for autonomous operation.**

Every component of a DSI model must be executable by an AI agent without human interpretation:

- Signal sources must be programmatically accessible
- Scoring rules must be algorithmic
- Decision logic must be deterministic
- Exceptions must have defined handling procedures

The goal is not merely automation of current processes but architecture for a future where AI agents conduct underwriting autonomously, with human oversight focused on model governance rather than individual risk decisions.

---

### Signal Taxonomy

DSI signals are categorised into seven types. All pricing models must identify which signal types they employ and document the specific signals within each type.

#### Type 1: Network Authority Signals

Signals derived from an entity's position in networks of trust, partnership, and transaction. These signals should be analysed to maximum practical depth, building relationship graphs that extend beyond first-degree connections.

| Signal Class | Description | Collection Method |
|--------------|-------------|-------------------|
| Customer relationships | Who purchases from the entity | Case studies, customer logos, testimonials on website |
| Supplier relationships | Who supplies to the entity | Disclosed partnerships, supply chain publications |
| Partnership networks | Formal partnership arrangements | Partnership announcements, alliance memberships |
| Industry body membership | Participation in industry associations | Member directories of trade associations, ISACs |
| Certification authority | Who certifies the entity | Certification body registries, published certificates |
| Banking/financial relationships | Quality of financial partners | Bond issuances, credit facility announcements |
| Academic/research citations | References in academic literature | Citation databases, research publications |
| Peer network position | Centrality in industry relationship graph | Computed from aggregated relationship data |
| Second-degree relationships | Quality of entities connected to direct relationships | Graph traversal of collected network data |

#### Type 2: Technical Infrastructure Signals

Signals derived from observable technical implementation.

| Signal Class | Description | Collection Method |
|--------------|-------------|-------------------|
| Web security configuration | TLS, certificates, security headers | Automated scanning (SSL Labs methodology) |
| DNS configuration | DNSSEC, email authentication | DNS queries |
| Network exposure | Open ports, exposed services | Port scanning, Shodan/Censys |
| Software currency | Versions of detected software | Banner grabbing, fingerprinting |
| Cloud/hosting infrastructure | Hosting providers, CDN usage | DNS analysis, header inspection |
| API/integration presence | Public APIs, developer resources | Website crawling, API directory presence |

#### Type 3: Asset Telemetry Signals

Signals derived from digital telemetry of physical assets, used for behavioral pattern analysis at the organisational level.

| Signal Class | Description | Collection Method |
|--------------|-------------|-------------------|
| Vessel tracking | AIS patterns, port calls, routes | AIS data providers |
| Aircraft tracking | Flight patterns, utilization | ADS-B data, flight tracking services |
| Facility monitoring | Activity patterns, condition | Satellite imagery analysis |
| IoT/sensor data | Connected device telemetry | Where available via API |

**Constraint:** Asset telemetry is used to assess organizational behavior patterns, not to price individual assets. The question is "how does this organisation operate its assets?" not "what is this specific asset worth?"

#### Type 4: Structured Data Feed Signals

Signals derived from authoritative third-party data providers.

| Signal Class | Description | Collection Method |
|--------------|-------------|-------------------|
| Credit ratings | S&P, Moody's, Fitch ratings | Rating agency publications/APIs |
| ESG scores | MSCI, Sustainalytics scores | ESG data provider feeds |
| Industry classifications | SIC, NAICS codes | Registry data, D&B |
| Market data | Stock price, volatility, short interest | Market data feeds |
| Classification society status | Vessel/facility classification | Classification society registries |

**Constraint:** We use published ratings/scores as signals, not underlying documentation. The rating itself is the signal.

#### Type 5: Corporate Digital Footprint Signals

Signals derived from analysis of an entity's own digital presence.

| Signal Class | Description | Collection Method |
|--------------|-------------|-------------------|
| Website structure | Pages present and absent | Web crawling, sitemap analysis |
| Content quality | Depth, recency, professionalism | NLP analysis of published content |
| Document publications | Annual reports, investor materials | Document extraction and analysis |
| Job postings | Roles advertised, requirements | Career page crawling, job board APIs |
| Leadership visibility | Executive profiles, board composition | Website extraction, LinkedIn |
| Policy publications | Privacy policy, terms, security.txt | Targeted page retrieval |
| Press releases | Company-issued announcements | News/PR section crawling |

**Constraint:** We analyse the company's own published content, not third-party commentary about them.

#### Type 6: Public Record Signals

Signals derived from regulatory filings, legal records, and government databases.

| Signal Class | Description | Collection Method |
|--------------|-------------|-------------------|
| Securities filings | 10-K, 10-Q, 8-K, proxy statements | SEC EDGAR |
| Court records | Litigation history | PACER, state court databases |
| Regulatory actions | Enforcement, penalties | Agency databases |
| Corporate registry | Structure, officers, filings | Companies House, state registries |
| Patent/IP filings | Innovation, IP portfolio | USPTO, EPO |
| Permit/license records | Operating authorizations | Agency databases |
| Breach/incident disclosures | Required breach notifications | HHS, state AG databases |

#### Type 7: Direct Inquiry Signals (Optional)

Signals derived from minimal, structured questions to the insured.

| Constraint | Requirement |
|------------|-------------|
| Volume | Maximum 5-10 questions per line of business |
| Format | Binary (Yes/No) or simple categorical |
| Importance | Must be critical to risk assessment |
| Submission | Digital only (API or structured form) |
| Verification | Independent verification where practical, but not required |
| Treatment | Declarations subject to policy terms |

Direct inquiry signals are optional. Models must function without them, potentially with reduced confidence or increased margin.

---

### News and Media Content

#### Permitted Sources

| Source Type | Description | Usage |
|-------------|-------------|-------|
| Company-issued press releases | The entity's own announcements | Primary content analysis |
| Regulatory news feeds | Official announcements from regulators (SEC, FCA, etc.) | Enforcement and action monitoring |
| Industry body publications | Announcements from trade associations and standards bodies | Industry context |

#### Future Consideration

General journalistic content may be incorporated in future iterations when:

- Quantification methodology moves beyond simple sentiment analysis
- Cost structures are acceptable
- Source bias can be adequately characterized and adjusted for
- Editorial opinion can be distinguished from factual reporting

#### Excluded Sources

| Source Type | Reason for Exclusion |
|-------------|---------------------|
| Paid news content | Editorial independence questionable |
| Social media sentiment | Noisy, gameable, unreliable |
| Unverified blog content | No authority verification |
| Opinion pieces and editorial commentary | Subjective, potentially biased |

---

### Model Architecture

Every DSI pricing model must conform to the following architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SIGNAL COLLECTION LAYER                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Network  │ │Technical │ │ Corporate│ │  Public  │    ...     │
│  │Authority │ │  Infra   │ │ Footprint│ │ Records  │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SIGNAL SCORING LAYER                       │
│         Each signal → Normalised score (0-100)                  │
│         Defined algorithm, no subjective judgment               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COMPOSITE SCORING LAYER                      │
│         Weighted combination → Composite score (0-1000)         │
│         Category weights defined per line of business           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TIER ASSIGNMENT LAYER                      │
│         Score thresholds → Risk tier (1-5)                      │
│         Tier determines underwriting action                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PRICING LAYER                             │
│         Tier + Industry + Size → Base price                     │
│         Limited adjustments for critical factors only           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DECISION LAYER                            │
│         Tier 1-2: Auto-approve                                  │
│         Tier 3:   Auto-approve with conditions                  │
│         Tier 4:   Manual review                                 │
│         Tier 5:   Decline or heavy manual review                │
└─────────────────────────────────────────────────────────────────┘
```

---

### Risk Tiers

All DSI models use a standardised five-tier risk classification:

| Tier | Score Range | Classification | Underwriting Action |
|------|-------------|----------------|---------------------|
| 1 | 800-1000 | Preferred | Auto-approve, preferred pricing |
| 2 | 650-799 | Standard | Auto-approve, standard pricing |
| 3 | 500-649 | Elevated | Auto-approve with conditions |
| 4 | 350-499 | High Risk | Manual review required |
| 5 | 0-349 | Critical | Decline or senior review |

Tier thresholds may be adjusted per line of business based on risk characteristics, but the five-tier structure and decision logic must be maintained.

---

### Confidence and Data Sufficiency

Every DSI assessment must include a confidence score reflecting signal availability:

| Signal Coverage | Confidence Level | Treatment |
|-----------------|------------------|-----------|
| ≥85% of defined signals available | High (≥0.90) | Full automation eligible |
| 70-84% of defined signals available | Medium (0.75-0.89) | Automation with margin adjustment |
| 55-69% of defined signals available | Low (0.60-0.74) | Manual review recommended |
| <55% of defined signals available | Insufficient (<0.60) | Manual underwriting required |

Low confidence does not mean decline—it means the DSI assessment has insufficient data for full automation and should be supplemented with traditional methods or direct inquiry.

---

### Implementation Requirements

#### Model Documentation

Each DSI pricing model must include documentation covering:

1. **Signal inventory:** Complete list of signals used, categorised by type
2. **Collection methods:** How each signal is obtained
3. **Scoring algorithms:** How each signal is converted to a 0-100 score
4. **Weight justification:** Why each signal receives its assigned weight
5. **Composite calculation:** How category and overall scores are computed
6. **Tier thresholds:** Score ranges for each tier (if different from default)
7. **Pricing tables:** Base prices by tier, industry, and size
8. **Decision rules:** Specific conditions for each tier's underwriting action
9. **Direct inquiry questions:** If used, the specific questions and their scoring
10. **Confidence calculation:** How signal coverage translates to confidence

#### Validation Checklist

For each DSI pricing model, verify:

- [ ] All signals are externally observable or from permitted direct inquiry
- [ ] All signals have defined collection methods that are programmatically executable
- [ ] All signals have defined scoring algorithms with no subjective judgment
- [ ] Signal weights are defined and justified
- [ ] Composite score calculation is documented
- [ ] Tier thresholds are defined
- [ ] Pricing by tier is defined
- [ ] Decision rules by tier are defined
- [ ] Confidence calculation is implemented
- [ ] Direct inquiry questions (if any) meet all constraints
- [ ] News/media sources (if any) are from permitted categories
- [ ] Model can operate without direct inquiry signals
- [ ] All components are executable by AI agent without human interpretation
- [ ] Network authority signals include deep graph analysis where practical

---

### Governance

#### Model Changes

Changes to DSI pricing models must be documented with:

- Rationale for change
- Impact assessment
- Validation against principles
- Approval record

#### Principle Changes

Changes to DSI Principles require:

- Business justification
- Impact assessment across all models
- Senior approval
- Version increment of this document

---

### Appendix: Line of Business Considerations

Different lines of business emphasise different signal types. The following provides guidance on signal type relevance by line:

| Signal Type | Cyber | D&O | Marine | Energy | FI |
|-------------|-------|-----|--------|--------|-----|
| Network Authority | High | High | Medium | Medium | High |
| Technical Infrastructure | Critical | Low | Low | Medium | Medium |
| Asset Telemetry | Low | None | Critical | High | None |
| Structured Data Feeds | Medium | High | High | High | Critical |
| Corporate Digital Footprint | High | High | Medium | Medium | High |
| Public Records | Medium | Critical | High | High | Critical |
| Direct Inquiry | Medium | Low | Low | Medium | Low |

This guidance informs model design but does not preclude use of any signal type where relevant.

---

### Appendix: Example Direct Inquiry Questions

The following illustrates appropriate direct inquiry questions by line of business. These are examples, not requirements.

#### Cyber Insurance (Maximum 10)

1. Is multi-factor authentication enabled for all remote access? (Yes/No)
2. Do all employees complete annual cyber security training? (Yes/No)
3. Do you process Protected Health Information (PHI)? (Yes/No)
4. Do you store payment card data (PCI scope)? (Yes/No)
5. Do you have a documented incident response plan? (Yes/No)
6. Is endpoint detection and response (EDR) deployed on all endpoints? (Yes/No)
7. Are backups maintained offline or immutable? (Yes/No)
8. Have you experienced a material cyber incident in the past 3 years? (Yes/No)

#### D&O Insurance (Maximum 5)

1. Are there any pending or threatened securities claims? (Yes/No)
2. Any regulatory investigations in the past 24 months? (Yes/No)
3. Any planned M&A, restructuring, or capital raising in the next 12 months? (Yes/No)
4. Is the company currently in compliance with all debt covenants? (Yes/No)
5. Any executive departures under investigation or dispute in past 12 months? (Yes/No)

#### Marine Insurance (Maximum 5)

1. Total number of vessels in owned/operated fleet? (Numeric)
2. Any vessels detained by port state control in past 36 months? (Yes/No)
3. Any total losses or major casualties in past 5 years? (Yes/No)
4. Is the fleet managed by a third-party technical manager? (Yes/No)
5. Any vessels currently trading to sanctioned regions? (Yes/No)

#### Energy Insurance (Maximum 8)

1. Primary operations type? (Upstream/Midstream/Downstream/Renewable)
2. Any OSHA recordable incidents in past 12 months? (Yes/No)
3. Any environmental enforcement actions in past 5 years? (Yes/No)
4. Any facilities in hurricane/typhoon exposed zones? (Yes/No)
5. Is predictive maintenance implemented across major equipment? (Yes/No)
6. Any facilities older than 30 years without major refurbishment? (Yes/No)
7. Any current decommissioning obligations? (Yes/No)
8. Percentage of revenue from renewable/transition energy? (Categorical)

#### Financial Institutions (Maximum 6)

1. Primary institution type? (Bank/Insurance/Asset Management/Other)
2. Any regulatory enforcement actions in past 3 years? (Yes/No)
3. Any material litigation pending or threatened? (Yes/No)
4. Is the institution systemically important (G-SIB/D-SIB designated)? (Yes/No)
5. Any senior executive departures related to compliance in past 24 months? (Yes/No)
6. Has the institution passed all regulatory stress tests? (Yes/No)

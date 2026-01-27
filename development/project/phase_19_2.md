# Phase 19.2: Interactive DSI Demo — "Interact with DSI"

## Purpose

Pivot from the passive "Learn about DSI" presentation (which duplicates content available in pitch deck, white paper, and vision paper) to a high-value **interactive demonstration** that lets users experience DSI's functionality firsthand.

The goal: **Show, don't tell.**

## Strategic Rationale

| Approach | Value | Problem |
|----------|-------|---------|
| Learn about DSI | Low | Duplicates existing materials; passive consumption |
| **Interact with DSI** | **High** | Demonstrates unique capability; creates memorable experience |

An interactive demo creates:
- **Proof of concept** — demonstrates the system works, not just that the theory is sound
- **Differentiation** — no competitor can show this because no competitor has built it
- **Engagement** — active participation creates stronger impression than passive reading
- **Credibility** — "seeing is believing" for skeptical insurance executives

---

## Core Interactive Experiences

### The DSI Journey

The five modules are **not independent tools** — they form a connected narrative that demonstrates DSI's complete capability chain:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE DSI JOURNEY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │ DISCOVER │───►│UNDERSTAND│───►│ PREDICT  │───►│ DECIDE   │            │
│   │          │    │          │    │          │    │          │            │
│   │ Signal   │    │ Three    │    │ What-If  │    │Underwrite│            │
│   │ Discovery│    │ Layer    │    │ Engine   │    │ Engine   │            │
│   └──────────┘    └──────────┘    └────┬─────┘    └──────────┘            │
│                                        │                                   │
│                                        ▼                                   │
│                                  ┌──────────┐                              │
│                                  │PORTFOLIO │                              │
│                                  │ IMPACT   │                              │
│                                  │          │                              │
│                                  │ Steering │                              │
│                                  └──────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Stage | Module | Question Answered |
|-------|--------|-------------------|
| **Discover** | Live Signal Discovery | "What can DSI see about this organisation?" |
| **Understand** | Three Layer Assessment | "How does DSI interpret what it sees?" |
| **Predict** | What-If Engine | "What happens if conditions change?" |
| **Decide** | Underwriting Engine | "How does DSI reach a decision?" |
| **Portfolio Impact** | Portfolio Steering | "What are the consequences for the portfolio?" |

### Connected Flow

Users can experience modules independently, **or** follow the guided journey:

1. **Start**: Enter a company → Watch signals extract (Discovery)
2. **Explore**: See how signals feed the three layers (Understanding)
3. **Stress-Test**: Apply a shock scenario (Prediction)
4. **See Consequence**: View portfolio-level impact of the shock (Portfolio Impact)
5. **Full Workflow**: Run the complete underwriting cycle (Decision)

The What-If Engine and Portfolio Steering are **tightly integrated** — a shock triggered in What-If automatically flows into Portfolio Steering to show consequences. This is not two separate experiences; it is **propagation followed by consequence**.

---

### Module 1: Live Signal Discovery
**"Enter a domain. Watch DSI see what you cannot."**

#### Concept
User enters a company name and/or domain hint. The demo simulates DSI's discovery and signal extraction process in real-time, visualising signals appearing across the seven canonical categories.

#### User Experience
1. **Input**: Simple text field — "Enter company name or domain"
2. **Discovery Animation**: Domain resolution, corporate identity matching, confidence building
3. **Signal Cascade**: Signals appear in real-time across 7 category columns
4. **Organisational Graph**: Watch the graph form as signals connect
5. **Output**: Summary card with composite score, tier, and key findings

#### Key Moments
- Signals appearing with confidence scores (0.72, 0.89, etc.)
- "Absence signals" highlighted when expected signals are missing
- Network authority connections forming between entities
- The "aha moment" when the system finds something unexpected

#### Why It's Compelling
This is the core DSI thesis made tangible: **external observability**. The user sees information about a company that the company never provided. This is viscerally different from every other insurance tool.

#### Technical Scope
- Pre-computed signal datasets for ~10-15 real companies
- Animated signal extraction (timed reveals matching realistic API latencies)
- Interactive Organisational Graph visualisation (zoomable, clickable nodes)
- Real-time score calculation display

#### Deep Interactivity Features
- **Signal Drill-Down**: Click any signal to see raw source, extraction method, confidence breakdown
- **Graph Exploration**: Pan, zoom, click nodes to see entity details and relationships
- **Comparison Mode**: Run two companies side-by-side to see signal differences
- **Category Filtering**: Toggle signal categories on/off to see impact on scores
- **Export View**: Show what an audit trail export would contain

---

### Module 2: Three Layer Assessment
**"Risk. Exposure. Loss. Independent. Measurable. Deterministic."**

#### Concept
Interactive visualisation of DSI's three-layer assessment model. Users can explore how signals contribute to each layer independently, and see how the layers combine for a unified decision.

#### User Experience
1. **Layer Selection**: Three distinct visual layers (Risk / Exposure / Loss)
2. **Signal Inspection**: Click any signal to see its contribution to each layer
3. **Layer Independence**: Demonstrate same signal can affect layers differently
4. **Aggregation View**: Watch layers combine into final assessment

#### Visual Design
```
┌─────────────────────────────────────────────────────────┐
│                    RISK LAYER                           │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐              │
│  │ 82  │ │ 67  │ │ 91  │ │ 45  │ │ 78  │  → 782/1000  │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘   Tier 2     │
├─────────────────────────────────────────────────────────┤
│                   EXPOSURE LAYER                        │
│  ┌─────┐ ┌─────┐ ┌─────┐                              │
│  │ Med │ │ 38  │ │ 3   │  → Medium Band               │
│  └─────┘ └─────┘ └─────┘    Moderate Complexity       │
├─────────────────────────────────────────────────────────┤
│                    LOSS LAYER                           │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                      │
│  │ 28  │ │ 42  │ │Stbl │ │Tech │  → Low Propensity    │
│  └─────┘ └─────┘ └─────┘ └─────┘                       │
└─────────────────────────────────────────────────────────┘
```

#### Key Moments
- Clicking a signal and seeing it contribute differently to each layer
- Seeing tier override triggers activate
- Watching confidence propagate through the system
- The moment the three layers combine into a single decision

#### Why It's Compelling
Traditional underwriting conflates these three assessments into one subjective judgment. DSI separates them into **independent, measurable, auditable dimensions**. This demonstrates rigour and transparency.

#### Deep Interactivity Features
- **Signal Weight Adjustment**: Drag sliders to change signal weights, watch scores recalculate live
- **Tier Threshold Editor**: Adjust tier boundaries to see how decisions change
- **Signal Contribution Waterfall**: Visual breakdown of how each signal contributes to composite score
- **Override Trigger Inspector**: Click tier overrides to see exact conditions that would trigger them
- **Confidence Sensitivity**: Toggle between high/medium/low confidence scenarios

---

### Modules 3 & 4: What-If Engine + Portfolio Steering (Integrated)
**"Simulate the shock. See the consequence."**

#### Design Principle: Propagation → Consequence

These two modules are **tightly coupled**. They represent a single experience in two phases:

| Phase | Module | Function |
|-------|--------|----------|
| **Propagation** | What-If Engine | "What happens to this organisation if X occurs?" |
| **Consequence** | Portfolio Steering | "What does that mean for my portfolio?" |

The user triggers a shock in What-If, watches it propagate through the Organisational Graph, then the view **automatically transitions** to Portfolio Steering to show portfolio-level consequences. This is not two separate tools — it is **one continuous simulation**.

---

#### Part A: The What-If Engine (Propagation)
**"Simulate the future. Before it happens."**

##### Concept
From the Vision Paper: *"Because the World Model understands the structure of the portfolio, it can simulate exogenous shocks before they happen."*

Users select scenarios and watch their impact propagate through an organisation.

##### Scenarios
1. **Critical Vulnerability Discovered** — "A zero-day affects your primary cloud provider"
2. **Leadership Departure** — "The CISO resigns unexpectedly"
3. **Regulatory Action** — "New compliance requirement in 90 days"
4. **Market Shock** — "Major competitor suffers data breach"
5. **Supply Chain Event** — "Key vendor experiences outage"
6. **Acquisition Announced** — "Company announces major acquisition"

##### User Experience
1. **Baseline State**: View current organisation state (from Discovery)
2. **Scenario Selection**: Choose from predefined scenarios
3. **Propagation Animation**: Watch impact ripple through the Organisational Graph
4. **Metric Changes**: See scores, tiers, and prices adjust in real-time
5. **Transition Prompt**: "See portfolio impact →"

##### Key Moments
- The cascade effect as a shock propagates through connected nodes
- Watching a Tier 2 risk become Tier 4 due to revealed dependencies
- Seeing which signals are most affected by each scenario type
- The "ah yes" moment when the simulation reveals non-obvious risk

##### Deep Interactivity Features
- **Custom Scenario Builder**: Define custom shocks beyond the presets (e.g., "AWS us-east-1 outage")
- **Severity Slider**: Adjust shock magnitude and watch impact scale proportionally
- **Time Horizon Control**: Simulate immediate impact vs. 30/60/90 day propagation
- **Intervention Testing**: Apply hypothetical mitigations and see reduced impact
- **Multi-Company View**: Run same scenario against multiple companies simultaneously

---

#### Part B: Portfolio Steering (Consequence)
**"Every shock has portfolio consequences. See them before they materialise."**

##### Concept
Portfolio Steering shows the **downstream consequences** of What-If scenarios. When a shock degrades an organisation's risk profile, what does that mean for portfolio concentration, aggregate exposure, and capital requirements?

##### Connection to What-If
```
WHAT-IF ENGINE                              PORTFOLIO STEERING
┌─────────────────────────┐                ┌─────────────────────────┐
│                         │                │                         │
│  Scenario: AWS Outage   │                │  Portfolio Impact:      │
│                         │                │                         │
│  ┌───┐                  │                │  AWS Correlation: 31%   │
│  │ A │──► degraded      │  ────────►     │  Affected Risks: 12     │
│  └───┘                  │  "See          │  Aggregate Exposure: ↑  │
│                         │  Impact"       │  Capital Required: +$2M │
│  Tier 2 → Tier 4        │                │                         │
│                         │                │  [Remediation Options]  │
└─────────────────────────┘                └─────────────────────────┘
```

##### User Experience
1. **Automatic Transition**: After What-If shock, view shifts to portfolio
2. **Affected Risks Highlighted**: Which portfolio risks share the vulnerability?
3. **Aggregate Metrics**: Total exposure increase, concentration change
4. **Capital Impact**: What additional capital is required?
5. **Remediation Options**: What portfolio actions could reduce exposure?

##### Visual Design
```
PORTFOLIO BEFORE SHOCK               PORTFOLIO AFTER SHOCK
┌──────────────────┐                ┌──────────────────┐
│  ● ●   ●  ●     │                │  ● ●   ●  ●     │
│    ●  ●    ●    │                │    ◉  ◉    ◉    │ ← affected
│  ●    ●  ●   ●  │   AWS OUTAGE   │  ●    ◉  ●   ◉  │
│    ●     ●  ●   │   ─────────►   │    ●     ◉  ◉   │
│  ●   ●  ●       │                │  ●   ●  ●       │
└──────────────────┘                └──────────────────┘

Aggregate Risk Score: 724           Aggregate Risk Score: 681 ↓
AWS Concentration: 23%              AWS Concentration: 23% (EXPOSED)
Projected Loss Increase: —          Projected Loss Increase: +$4.2M
```

##### Key Moments
- Seeing how many portfolio risks share the same vulnerability
- The aggregate exposure number changing in real-time
- Capital impact quantified in dollars
- The strategic question: "Is our portfolio resilient to this shock?"

##### Why the Integration is Compelling
Traditional risk management treats scenario analysis and portfolio management as separate disciplines. DSI shows them as **one continuous process**: simulate a shock, see it propagate, understand the portfolio consequence. This is the World Model operating at scale.

##### Deep Interactivity Features
- **Shock Inheritance**: Automatically receives shock state from What-If Engine
- **Portfolio Composition Editor**: Add/remove risks, see how it changes resilience
- **Concentration Threshold Tuning**: Adjust acceptable limits, see breach warnings
- **Correlation Explorer**: Click any two risks to see shared vulnerabilities
- **Efficient Frontier Visualisation**: See portfolio on risk-return plot
- **Remediation Simulator**: Test portfolio changes that would reduce exposure
- **Historical Replay**: Show how past shocks would have affected the portfolio

---

### Module 5: The Underwriting Engine
**"47 seconds. Zero touch. Full audit trail."**

#### Concept
Walk through the complete end-to-end DSI workflow for a single submission. The "worked example" from the white paper, made interactive.

#### User Experience
1. **Phase A — Discovery**: Enter minimal input, watch entity resolution
2. **Phase B — Instantiation**: Model version created, configuration loaded
3. **Phase C — Signals**: Parallel extraction across all categories (animated)
4. **Phase D — Assessment**: Three layers calculated simultaneously
5. **Phase E — Pricing**: Base rate → modifiers → final premium
6. **Phase F — Decision**: AUTO-APPROVE / REFER / DECLINE

#### Visual Design
A stepped workflow with expandable detail at each phase:

```
[✓] Discovery          ──► TechFlow Solutions Inc. (95% confidence)
[✓] Instantiation      ──► Cyber Model v2.4.1 loaded
[✓] Signals            ──► 35/35 extracted (12.3s)
[✓] Assessment         ──► Tier 2 | Medium | Low Propensity
[✓] Pricing            ──► $20,250 ($5M limit)
[●] Decision           ──► AUTO-APPROVE

Total Processing Time: 47 seconds
Audit Trail: 142 data points persisted
```

#### Key Moments
- Watching signals extract in parallel (not sequential)
- Seeing the "no human intervention" reality
- The final decision appearing with full transparency
- Clicking into any step to see complete audit trail

#### Why It's Compelling
This is the **operational proof**. Not theory — execution. The user sees a complete underwriting cycle in under a minute with zero manual steps.

#### Deep Interactivity Features
- **Phase Expansion**: Click any phase to see full detail (not just summary)
- **Signal-Level Inspection**: Drill into any extracted signal to see source and method
- **Modifier Playground**: Adjust modifiers manually to see pricing impact
- **Decision Override Simulation**: "What if confidence was 0.65 instead of 0.87?"
- **Audit Trail Browser**: Navigate complete audit trail with search and filter
- **Comparison Run**: Run same company through different model versions
- **Speed Control**: Slow down or speed up the animation to examine steps

---

## Implementation Strategy

### Recommended Approach: Pre-computed Real Data

For a demo, real-time API calls are unnecessary and introduce failure modes. However, the underlying data must be **real and verifiable**.

#### Data Collection Phase (Critical)
Before building the UI, we must:
1. **Select 10-15 real companies** from the target list
2. **Extract actual signals** from observable sources (DNS lookups, SSL cert analysis, job board scraping, SEC filings, LinkedIn, web archive, etc.)
3. **Document sources** for every signal — if challenged, we can prove provenance
4. **Calculate real assessments** using the DSI methodology against real data
5. **Validate outputs** — do the scores and decisions make intuitive sense?

#### Demo Execution
1. **Pre-computed Datasets**: Real signal data for 10-15 companies, extracted and validated
2. **Animated Reveals**: Simulate real-time extraction with timed animations matching realistic latencies
3. **Deterministic Outputs**: All calculations produce consistent, pre-validated results
4. **Rich Interactivity**: Focus development effort on compelling UX, not backend integration

#### Why This Matters
If a user types "Cloudflare" and sees signals that don't match Cloudflare's actual digital footprint, the demo loses all credibility. The data must be **defensible under scrutiny**.

### Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DEMO APPLICATION                          │
├─────────────────────────────────────────────────────────────┤
│  Landing / Orientation                                       │
│    └── Module Selection                                      │
│          ├── Live Signal Discovery                          │
│          ├── Three Layer Assessment                         │
│          ├── The What-If Engine                             │
│          ├── Portfolio Steering                             │
│          └── The Underwriting Engine                        │
├─────────────────────────────────────────────────────────────┤
│  Shared Components                                           │
│    ├── Organisational Graph Visualiser                      │
│    ├── Signal Category Display                              │
│    ├── Score/Tier/Confidence Components                     │
│    ├── Animated Number Counters                             │
│    └── Audit Trail Panel                                    │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (Pre-computed Real Data)                         │
│    ├── Real Company Profiles (10-15 verified)               │
│    ├── Signal Definitions (7 categories, sourced)           │
│    ├── Scenario Definitions (6 scenarios, realistic)        │
│    ├── Portfolio Compositions (real company mixes)          │
│    └── Source Documentation (provenance for all data)       │
└─────────────────────────────────────────────────────────────┘
```

### Existing Assets to Retain

From the current dsi-demo-v2.html:
- Landing page design and visual identity
- Color palette (#0B3954 navy, #0599AD teal, #E8E3DA cream)
- Typography and general styling
- Header/navigation framework
- Footer

---

## Module Priority Matrix

| Module | Impact | Complexity | Recommendation |
|--------|--------|------------|----------------|
| Live Signal Discovery | Very High | Medium | **Build First** — The "wow" moment |
| Underwriting Engine | High | Low | Build Second — Operational proof |
| Three Layer Assessment | High | Medium | Build Third — Methodological rigour |
| What-If + Portfolio Steering | Very High | High | Build Fourth — **Integrated experience** |

**Note**: What-If Engine and Portfolio Steering are built as a single integrated module (Propagation → Consequence). They share state, visuals transition automatically, and should not be separated.

### Minimum Viable Demo

If time-constrained, the following subset delivers maximum impact:

1. **Live Signal Discovery** — This is the "wow" moment; users see what DSI can observe
2. **Underwriting Engine** — This is the operational proof; 47 seconds, zero touch

These two modules demonstrate DSI's core value proposition.

### Full Journey Demo

For maximum impact, the complete journey should be experienced in sequence:

1. **Discovery** → 2. **Understanding** → 3. **Prediction + Consequence** → 4. **Decision**

This tells the complete DSI story: we see → we understand → we predict → we decide.

---

## Demo Company Profiles

### Approach: Real Companies

Per design decision, demo companies should be **real, publicly observable entities** to maximise credibility. Fictional companies feel like mockups and undermine the demo's persuasive power.

### Selection Criteria

Companies selected for the demo must:
1. Have substantial, verifiable digital footprint
2. Be publicly traded or have significant public presence (enables data verification)
3. Represent diverse industries to show DSI's cross-coverage applicability
4. Include a range of risk profiles (excellent → poor)
5. Demonstrate different coverage types and geographic complexity

### Target Company Portfolio

| Sector | Company | Domain | Demo Purpose |
|--------|---------|--------|--------------|
| **Technology / SaaS** | Cloudflare | cloudflare.com | Primary worked example — excellent digital signals |
| **Technology / SaaS** | Atlassian | atlassian.com | Rich digital footprint, Australian HQ |
| **Fintech** | Klarna | klarna.com | European fintech, regulatory complexity |
| **Insurance / Reinsurance** | Markel | markel.com | Meta demo — assess an insurer |
| **Insurance / Specialty** | Beazley | beazley.com | Lloyd's market, specialty lines |
| **Cybersecurity** | CrowdStrike | crowdstrike.com | Excellent risk profile expected |
| **Cybersecurity** | Palo Alto Networks | paloaltonetworks.com | Enterprise security vendor |
| **Aerospace** | Boeing | boeing.com | Recent quality issues, complex signals |
| **Aerospace / Engineering** | Rolls Royce | rolls-royce.com | UK-based, defence & civil aerospace |
| **Energy (State-Owned)** | Petrobras | petrobras.com.br | Brazilian state-owned, complex governance |
| **Energy (State-Owned)** | Pemex | pemex.com | Mexican state-owned, different risk profile |
| **Traditional Manufacturing** | Caterpillar | caterpillar.com | Heavy industry, lower digital intensity |
| **Retail / E-commerce** | Shopify | shopify.com | B2B/B2C platform, high digital presence |

### Why This Selection

| Company Type | Demonstrates |
|--------------|--------------|
| **Tech Leaders** (Cloudflare, Atlassian, CrowdStrike) | Rich signal density, excellent risk profiles |
| **Fintechs** (Klarna) | Regulatory complexity, European jurisdiction |
| **Insurers** (Markel, Beazley) | Meta demonstration — DSI assessing insurers |
| **Aerospace** (Boeing, Rolls Royce) | Complex industrial signals, supply chain depth |
| **State-Owned Energy** (Petrobras, Pemex) | Governance signals, emerging market complexity |
| **Traditional Industry** (Caterpillar) | Different signal mix, lower digital intensity |

### Data Accuracy Requirements

For each company profile, signal data must be:
- **Verifiable**: Derived from actually observable sources (DNS, SSL certs, job postings, SEC filings, etc.)
- **Current**: Reflects present state, not historical
- **Defensible**: If challenged, we can explain where each signal came from
- **Complete**: All 7 canonical categories populated where signals exist

---

## Company Profile Framework

### Purpose

A standardised framework for creating company profiles enables:
1. **Rapid addition** of new companies on request
2. **Consistency** across all demo profiles
3. **Quality assurance** — checklist ensures nothing is missed
4. **Maintainability** — clear structure for updates

### Standard Profile Schema

```json
{
  "meta": {
    "company_name": "string",
    "legal_entity": "string",
    "domain": "string",
    "ticker": "string | null",
    "headquarters": "string",
    "industry_sic": "string",
    "profile_created": "date",
    "profile_updated": "date",
    "data_sources": ["array of source URLs/references"]
  },

  "discovery": {
    "domain_confidence": "number (0-1)",
    "entity_resolution_method": "string",
    "corporate_structure": {
      "parent": "string | null",
      "subsidiaries": ["array"],
      "jurisdictions": ["array"]
    }
  },

  "signals": {
    "network_authority": {
      "signals": [...],
      "category_score": "number (0-100)",
      "confidence": "number (0-1)"
    },
    "technical_infrastructure": {...},
    "corporate_digital_footprint": {...},
    "behavioural": {...},
    "public_record": {...},
    "structured_data_feeds": {...},
    "direct_inquiry": {...}
  },

  "three_layer_assessment": {
    "risk_layer": {
      "composite_score": "number (0-1000)",
      "risk_tier": "number (1-5)",
      "confidence": "number (0-1)",
      "tier_overrides": [...],
      "referral_flags": [...],
      "modifiers": [...]
    },
    "exposure_layer": {
      "exposure_band": "string",
      "complexity_category": "string",
      "confidence": "number (0-1)"
    },
    "loss_layer": {
      "loss_propensity": "number (0-100)",
      "severity_propensity": "number (0-100)",
      "trend_band": "string",
      "cohort": "string"
    }
  },

  "pricing": {
    "coverage_type": "string",
    "limit_requested": "number",
    "base_rate": "number",
    "modifiers_applied": [...],
    "final_premium": "number"
  },

  "decision": {
    "outcome": "AUTO-APPROVE | REFER | DECLINE",
    "rationale": "string",
    "processing_time_seconds": "number",
    "audit_trail_count": "number"
  },

  "scenarios": {
    "vulnerability_shock": {...},
    "leadership_departure": {...},
    "regulatory_action": {...}
  }
}
```

### Profile Creation Checklist

When adding a new company, complete the following:

#### Phase 1: Discovery Research
- [ ] Verify primary domain ownership (WHOIS, DNS)
- [ ] Confirm legal entity name (corporate registry)
- [ ] Map corporate structure (subsidiaries, parent)
- [ ] Identify key jurisdictions

#### Phase 2: Signal Extraction
- [ ] **Network Authority**: Backlinks, partnerships, certifications, industry memberships
- [ ] **Technical Infrastructure**: SSL/TLS analysis, DNS records, technology stack, cloud providers
- [ ] **Corporate Digital Footprint**: Website structure, careers page, leadership visibility, content recency
- [ ] **Behavioural**: Hiring patterns, news sentiment, social media activity, change velocity
- [ ] **Public Record**: SEC filings, regulatory actions, litigation, patents
- [ ] **Structured Data**: Credit ratings, ESG scores, financial data
- [ ] **Direct Inquiry**: (mark as N/A for demo — no direct questions asked)

#### Phase 3: Assessment Calculation
- [ ] Calculate composite risk score using signal weights
- [ ] Determine risk tier from score
- [ ] Evaluate tier override conditions
- [ ] Calculate exposure band and complexity
- [ ] Compute loss propensity scores
- [ ] Assign cohort

#### Phase 4: Pricing & Decision
- [ ] Apply base rate for tier
- [ ] Apply all applicable modifiers
- [ ] Calculate final premium
- [ ] Determine decision outcome
- [ ] Document rationale

#### Phase 5: Scenario Modelling
- [ ] Model vulnerability shock impact
- [ ] Model leadership departure impact
- [ ] Model at least one sector-specific scenario

#### Phase 6: Quality Assurance
- [ ] All signal sources documented
- [ ] Scores pass sanity check (do they make sense?)
- [ ] Decision is defensible
- [ ] Profile reviewed by second person

### Adding a New Company (Quick Guide)

1. **Create profile file**: `profiles/{company_domain}.json`
2. **Run discovery**: Collect entity and domain data
3. **Extract signals**: Use standard sources list
4. **Calculate scores**: Apply DSI methodology
5. **Model scenarios**: At least 3 per company
6. **Validate**: Run through checklist
7. **Test in demo**: Verify rendering and interactions

---

## Success Criteria

The interactive demo is successful when:

1. **Visceral Understanding**: Users "get it" without reading the white paper
2. **Differentiation**: Clear that this is not another data enrichment tool
3. **Credibility**: The demo feels like a real system, not a mockup
4. **Memorability**: Users remember and can describe the experience
5. **Discussion Catalyst**: Creates questions and conversations

---

## Design Decisions (Confirmed)

| Decision | Resolution | Rationale |
|----------|------------|-----------|
| **Company Selection** | Real companies where possible | Credibility is paramount; fictional companies feel like mockups |
| **Interactivity Depth** | Deep | Let users feel the technology and the opportunity |
| **Mobile Support** | Desktop only | Acceptable constraint for executive demo context |
| **Branding** | Consistent but understated | Generate branding present but not the driver of engagement |
| **Data Accuracy** | As accurate as possible | Made-up data undermines impact enormously |

---

## Next Steps

1. Finalise module priority and scope
2. Design data schema for demo company profiles
3. Create JSON datasets for selected companies
4. Build Module 1 (Live Signal Discovery)
5. Build Module 2 (Underwriting Engine)
6. Iterate based on feedback
7. Add remaining modules as time permits

---

**This phase represents a strategic pivot from presentation to demonstration — from telling the DSI story to letting users experience it.**

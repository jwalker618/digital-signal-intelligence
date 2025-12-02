# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$
##  Agent Interaction Specification
### Minimum Viable Requirements for Processing

| Item | Value |
|-|-|
|Version|1.0|
|Date|November 2025|
|Classification|Technical Specification|

---

## Executive Summary

Traditional insurance applications require lots of inputs. DSI requires **4 data points** and **5 - 10 optional confirmations**. Everything else comes from observable signals.

**The DSI interaction paradigm:**

| Traditional | DSI |
|-------------|-----|
| "Tell us everything" | "We already know. Confirm these 6 things." |
| 50-200 questions | 4 required + 5 - 10 optional |
| Days/weeks to complete | Minutes |
| Manual review every submission | 75-85% straight-through |

---

## The Minimum Viable Interaction

### Required Data (4 items)

These are the ONLY mandatory inputs:

| Data Point | Format | Purpose |
|------------|--------|---------|
| **1. Entity Identifier** | Company name OR domain OR registration number | Triggers signal collection |
| **2. Coverage Type** | Dropdown selection | Routes to appropriate model |
| **3. Desired Limit** | Currency + amount | Calculates premium |
| **4. Effective Date** | Date | Policy period |

That's it. Four fields. Everything else is either:
- **Observable** (we find it ourselves)
- **Confirmable** (we show them what we found, they confirm)
- **Optional inquiry** (6 questions max for things we genuinely can't observe)

And if required DSI only requires the Entity Identifier and Effective Date and can auto-generate scenarios incorporating all coverage types and limit profiles.

### Direct Inquiry (6 questions maximum)

Questions address ONLY information that cannot be observed externally:

| Question | Why We Ask | Auto-Trigger |
|----------|------------|--------------|
| 1. Pending/threatened claims? | Not public until filed | Always |
| 2. Pending regulatory action? | May not be announced | Always |
| 3. Coverage declined/non-renewed? | Confidential | Always |
| 4. Material change planned? | Future state unknown | Conditional |
| 5. Ownership change? | May not be filed yet | Conditional |
| 6. Coverage-specific question | Varies by line | Conditional |

**Critical:** These are Yes/No questions with optional detail field. Not essays.

---

## User Journey: Three Paths

### Path 1: Straight-Through (Target: 75-85%)

```
User Action              System Action                    Time
─────────────────────────────────────────────────────────────────
Enter company name  →    Signal collection begins         2 sec
Select coverage     →    Route to model                   instant
Enter limit         →    Premium calculation              instant
Enter date          →    Policy period set                instant
Answer 6 Y/N        →    Risk assessment                  instant
                    ←    Display: Score, Tier, Premium
Click "Bind"        →    Policy issued                    instant
─────────────────────────────────────────────────────────────────
                         TOTAL TIME: ~3 minutes
```

**Criteria for straight-through:**
- DSI Score ≥ 650 (Tier 1 or 2)
- No red flags triggered
- No "Yes" answers to critical inquiries
- Signal coverage ≥ 70%

### Path 2: Referred for Review (Target: 15-25%)

```
User Action              System Action                    Time
─────────────────────────────────────────────────────────────────
[Same as Path 1]    →    [Same as Path 1]                 3 min
                    ←    Display: "Referred for Review"
                         Underwriter notification
Underwriter review  →    Manual assessment                1-4 hrs
                    ←    Quote or Decline
User accepts        →    Policy issued
─────────────────────────────────────────────────────────────────
                         TOTAL TIME: Same day (usually)
```

**Referral triggers:**
- DSI Score 350-649 (Tier 3-4)
- Any red flag present
- "Yes" to critical inquiry
- Signal coverage < 70%
- Limit exceeds auto-bind authority

### Path 3: Decline (Target: 5-10%)

```
User Action              System Action                    Time
─────────────────────────────────────────────────────────────────
[Same as Path 1]    →    [Same as Path 1]                 3 min
                    ←    Display: "Unable to offer terms"
                         Reason summary provided
─────────────────────────────────────────────────────────────────
                         TOTAL TIME: ~3 minutes
```

**Decline triggers:**
- DSI Score < 350 (Tier 5)
- Critical red flag (e.g., EU Safety List for aerospace)
- Automatic decline override triggered

---

## Market-Specific Workflows

### US Market (Direct / Retail)

**Channel Options:**
1. **Carrier Direct Portal** — Insured self-service
2. **Broker Portal** — Broker on behalf of client
3. **API Integration** — Embedded in broker systems

**Workflow:**

```
┌────────────────────────────────────────────────────────────────┐
│  US DIRECT WORKFLOW                                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ PORTAL      │ →  │ DSI ENGINE   │ →  │ DECISION        │    │
│  │             │    │              │    │                 │    │
│  │ • Entity ID │    │ • Signals    │    │ • APPROVE       │    │
│  │ • Coverage  │    │ • Score      │    │ • REFER         │    │
│  │ • Limit     │    │ • Tier       │    │ • DECLINE       │    │
│  │ • 6 Y/N     │    │ • Premium    │    │                 │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                │
│  Auto-bind authority: $10M-$50M depending on coverage line     │
│  Target straight-through rate: 75%                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Regulatory Considerations:**
- Surplus lines filings handled by broker (if applicable)
- State-specific policy forms auto-selected
- Licensing verification automated

### Lloyd's Market (Broker-Intermediated)

**Channel:**
Lloyd's broker places on behalf of client → Syndicate underwrites

**Key Insight:** Lloyd's is moving toward digital placement. DSI accelerates this by providing pre-populated risk assessments that brokers and syndicates can review.

**Workflow:**

```
┌────────────────────────────────────────────────────────────────┐
│  LLOYD'S WORKFLOW                                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ BROKER      │ →  │ DSI ENGINE   │ →  │ SYNDICATE       │    │
│  │ SUBMISSION  │    │              │    │ REVIEW          │    │
│  │             │    │ Pre-populates│    │                 │    │
│  │ • Entity ID │    │ risk slip    │    │ • Accept DSI    │    │
│  │ • Coverage  │    │ with signals │    │   assessment    │    │
│  │ • Limit     │    │ and score    │    │ • Override      │    │
│  │ • 6 Y/N     │    │              │    │ • Decline       │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                │
│  Tier 1-2: Auto-quote with syndicate stamp                     │
│  Tier 3-4: Underwriter review before quote                     │
│  Tier 5: Decline or exceptional referral                       │
│                                                                │
│  Integration: PPL (Placing Platform Limited) / Blueprint Two   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Lloyd's-Specific Considerations:**
- MRC (Market Reform Contract) auto-generated
- Line slip percentages calculated
- Following market functionality (leaders set terms)
- Integration with Lloyd's Bridge / Whitespace

### Singapore Market (Regional Hub)

**Channel:**
Mix of direct placement and treaty business for APAC region

**Workflow:**

```
┌────────────────────────────────────────────────────────────────┐
│  SINGAPORE WORKFLOW                                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ SUBMISSION  │ →  │ DSI ENGINE   │ →  │ DECISION        │    │
│  │ (Local or   │    │              │    │                 │    │
│  │  Regional)  │    │ • Regional   │    │ • Direct bind   │    │
│  │             │    │   signal     │    │ • Cedant to     │    │
│  │ • Entity ID │    │   sources    │    │   treaty        │    │
│  │ • Coverage  │    │ • Multi-     │    │ • Facultative   │    │
│  │ • Limit     │    │   currency   │    │   referral      │    │
│  │ • 6 Y/N     │    │ • MAS        │    │                 │    │
│  └─────────────┘    │   compliance │    └─────────────────┘    │
│                     └──────────────┘                           │
│                                                                │
│  Regional signal sources: ACRA (SG), ASIC (AU), SSM (MY), etc. │
│  Currency: SGD, USD, AUD, HKD, CNY, JPY                        │
│  Treaty: Automatic cession for Tier 1-2 below threshold        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Singapore-Specific Considerations:**
- MAS regulatory compliance
- Regional data source integration (company registries across APAC)
- Multi-currency premium calculation
- Treaty vs facultative routing
- Regional reinsurance panel relationships

---

## Technical Architecture

### API Endpoint Design

```
POST /api/v1/quote
Content-Type: application/json

{
  "entity": {
    "identifier": "acme-corp.com",          // Domain, name, or reg number
    "identifier_type": "domain"              // domain | name | registration
  },
  "coverage": {
    "type": "cyber",                         // cyber | fi | energy | marine | do | pi | aerospace
    "limit": 10000000,                       // In base currency units
    "currency": "USD",
    "deductible": "standard",                // standard | elevated | custom
    "effective_date": "2025-02-01",
    "term_months": 12
  },
  "direct_inquiry": {
    "pending_claims": false,
    "regulatory_action": false,
    "coverage_declined": false,
    "material_change": false,
    "ownership_change": false,
    "coverage_specific": null                // Coverage-line specific question
  },
  "market": "us",                            // us | lloyds | singapore
  "broker_code": "BRK001"                    // Optional
}
```

### Response Structure

```json
{
  "quote_id": "QT-2025-001234",
  "status": "APPROVED",                      // APPROVED | REFERRED | DECLINED
  "assessment": {
    "composite_score": 847,
    "tier": 1,
    "tier_label": "Preferred",
    "confidence": 0.92,
    "signal_coverage": 0.88
  },
  "pricing": {
    "gross_premium": 125000,
    "currency": "USD",
    "rate": 0.00125,
    "tier_modifier": 0.75,
    "taxes_and_fees": 8750,
    "total_payable": 133750
  },
  "coverage": {
    "limit": 10000000,
    "deductible": 100000,
    "sublimits": {
      "business_interruption": 5000000,
      "ransomware": 2500000
    }
  },
  "flags": {
    "green": ["SOC 2 Type II certified", "No breach history", "Strong security posture"],
    "red": [],
    "amber": ["Recent acquisition may affect coverage"]
  },
  "validity": {
    "quote_valid_until": "2025-01-15T23:59:59Z",
    "bind_by": "2025-01-31T23:59:59Z"
  },
  "next_actions": {
    "can_bind": true,
    "bind_endpoint": "/api/v1/bind/QT-2025-001234",
    "requires_signature": true,
    "documents_required": []
  }
}
```

### Referral Response

```json
{
  "quote_id": "QT-2025-001235",
  "status": "REFERRED",
  "assessment": {
    "composite_score": 584,
    "tier": 3,
    "tier_label": "Elevated Risk",
    "confidence": 0.78,
    "signal_coverage": 0.72
  },
  "referral": {
    "reason": "Tier 3 risk with amber flags requires underwriter review",
    "assigned_to": "underwriting-team-cyber",
    "expected_response": "4 hours",
    "reference": "REF-2025-00456"
  },
  "flags": {
    "green": ["Long operating history"],
    "red": [],
    "amber": ["Recent data breach disclosed", "Security score below threshold"]
  }
}
```

---

## User Interface Specifications

### Minimal Input Form

```
┌────────────────────────────────────────────────────────────────┐
│  GET A QUOTE IN UNDER 3 MINUTES                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Company Name or Website                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ acme-corp.com                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ✓ Found: ACME Corporation (Delaware)                          │
│                                                                │
│  Coverage Type                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Cyber Insurance                                    ▼    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  Limit Required                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ $10,000,000                                        ▼    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  Effective Date                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ February 1, 2025                                   📅   │  │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│                        [ Continue → ]                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Confirmation Screen (What We Found)

```
┌─────────────────────────────────────────────────────────────────┐
│  WE'VE ASSESSED YOUR RISK                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ACME Corporation                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                                 │
│  Risk Score: 847/1000                    Tier: PREFERRED        │
│  ████████████████████░░░░                                       │
│                                                                 │
│  What we found:                                                 │
│  ✓ SOC 2 Type II certified (verified via SecurityScorecard)     │
│  ✓ No known data breaches (verified via HaveIBeenPwned)         │
│  ✓ Strong email authentication (DMARC enforced)                 │
│  ✓ Current TLS configuration (A+ rating)                        │
│  ✓ No adverse litigation (PACER search)                         │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  Please confirm the following:                      Yes   No    │
│  ─────────────────────────────────────────────────────────────  │
│  1. Any pending or threatened claims?               ○     ●     │
│  2. Any pending regulatory action?                  ○     ●     │
│  3. Coverage declined in last 3 years?              ○     ●     │
│  4. Major system changes planned (12 months)?       ○     ●     │
│  5. M&A activity planned or in progress?            ○     ●     │
│  6. Significant vendor changes planned?             ○     ●     │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│                        [ Get Quote → ]                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Quote Delivery

```
┌─────────────────────────────────────────────────────────────────┐
│  YOUR QUOTE IS READY                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ACME Corporation — Cyber Insurance                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                                 │
│  ┌──────────────────────┐   ┌──────────────────────┐            │
│  │                      │   │                      │            │
│  │  ANNUAL PREMIUM      │   │  LIMIT               │            │
│  │  $125,000            │   │  $10,000,000         │            │
│  │                      │   │                      │            │
│  │  + Taxes: $8,750     │   │  Retention: $100,000 │            │
│  │  ─────────────────   │   │                      │            │
│  │  Total: $133,750     │   │                      │            │
│  │                      │   │                      │            │
│  └──────────────────────┘   └──────────────────────┘            │
│                                                                 │
│  Coverage Highlights:                                           │
│  • First-party breach response: Full limit                      │
│  • Business interruption: $5M sublimit                          │
│  • Ransomware: $2.5M sublimit (with co-insurance)               │
│  • Regulatory defense: Full limit                               │
│                                                                 │
│  Quote valid until: January 15, 2025                            │
│                                                                 │
│  ┌───────────────────┐  ┌───────────────────────────────────┐   │
│  │  Download Quote   │  │        Bind Coverage Now →        │   │
│  │       PDF         │  │                                   │   │
│  └───────────────────┘  └───────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Operational Metrics

### Target Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Straight-through rate | 70-80% | Quotes bound without referral |
| Quote response time | < 30 seconds | API response time |
| End-to-end time (STP) | < 5 minutes | User enters data → policy issued |
| Referral turnaround | < 4 hours | Referral → decision |
| Signal coverage | > 75% average | Signals collected vs. available |
| Accuracy vs. loss ratio | < 5% deviation | Predicted tier vs. actual loss |

### Efficiency Gains

| Traditional Process | DSI Process | Improvement |
|--------------------|-------------|-------------|
| 50-200 questions | 4 required + 6 Y/N | 95% reduction |
| 3-5 days quote turnaround | 30 seconds - 4 hours | 99% faster |
| 100% manual review | 20-30% manual review | 70-80% automation |
| Broker-dependent data | Signal-based data | Higher quality |
| Inconsistent pricing | Algorithmic pricing | Consistent |

---

## Implementation Checklist

### Phase 1: Core Platform
- [ ] Entity resolution service (domain → company → signals)
- [ ] Signal collection pipeline
- [ ] DSI scoring engine
- [ ] Quote API endpoint
- [ ] Basic UI (4 fields + 6 questions)

### Phase 2: Market Integration
- [ ] US direct binding capability
- [ ] Lloyd's PPL/Whitespace integration
- [ ] Singapore MAS compliance module
- [ ] Multi-currency support

### Phase 3: Optimisation
- [ ] Referral workflow automation
- [ ] Underwriter dashboard
- [ ] Performance analytics
- [ ] Model calibration loop

---

*This specification defines the minimum viable interaction for DSI-based insurance placement across US, Lloyd's, and Singapore markets.*

# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Agent Interaction: Minimum Viable Requirements

| Item | Value |
|-|-|
|Version|1.0|
|Date|November 2025|
|Classification|Technical Specification|

---

### Executive Summary

Traditional insurance models require lots of inputs. 
**DSI can operate using only one: the Entity (Client) Identifier.** Using this value a prospective premium across multiple coverages and limit bandings is generated for review. Everything else comes from observable signals.

**The DSI interaction paradigm:**

|Item| Traditional | DSI |
|-|-|-|
|**Method**| Tell us everything | We can observe your behavior directly |
|**Inputs**| 50-200 questions, forms, surverys etc. | 1 required |
|**Timeframe**| Days/weeks to complete | Minutes |
|**Process Efficiency**| Manual review every submission | 75-85% straight-through |

---

### The Minimum Viable Interaction

#### Required Data (1 item)

There is ONLY ONE mandatory input: 
| Data Point | Format | Purpose |
|------------|--------|---------|
| **1. Entity Identifier** | Company name OR domain OR registration number | Triggers signal collection |

That's it. One field. Everything else is either:
- **Observable** (we find it ourselves)
- **Confirmable** (we show them what we found, they confirm)
- **Configurable** (we preset limit-bandings by coverage to be auto-generated)
- **Optional** (questions for the few things we genuinely can't observe or specific limit requirements)

The three optional inputs are:
| Data Point | Format | Purpose |
|------------|--------|---------|
| **2. Coverage Type** | Dropdown selection | Routes to appropriate model |
| **3. Desired Limit** | Currency + amount | Calculates premium |
| **4. Effective Date** | Date | Policy period |

#### Direct Inquiry (5 - 10 questions maximum)

Questions address ONLY information that cannot be observed externally:

For example, 
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

### User Journey: Three Paths

#### Path 1 & 3: Straight-Through (Target: 75-85%)

```
User Action              System Action                    Time
─────────────────────────────────────────────────────────────────
Enter company name  →    Signal collection begins         2 sec
Specific config     →    Policy period set                instant
                    →    Specific coverage set            instant
                    →    Specific limit set               instant 
                    →    Risk assessment                  instant
Persist             ←    Capture: Score, Tier, Premium    instant
Workflow - accept   →    Display: "Appetite matched"      instant
                    →    Policy issued                    instant
Workflow - decline  →    Display: "Appetite unmatched"    instant
                    →    Declinature summary provided     instant
─────────────────────────────────────────────────────────────────
                         TOTAL TIME: ~<3 minutes
```

**Criteria for straight-through acceptance:**
- DSI Score ≥ 650 (Tier 1 or 2), configurable
- No red flags triggered
- No "Yes" answers to critical inquiries
- Signal coverage ≥ 70%

**Criteria for straight-through declinatures:**
- DSI Score < 350 (Tier 5)
- Critical red flag (e.g., EU Safety List for aerospace)
- Automatic decline override triggered

#### Path 2: Referred for Review (Target: 15-25%)

```
User Action              System Action                    Time
─────────────────────────────────────────────────────────────────
[Same as Path 1]    →    [Same as Path 1]                 ~<3 min
Workflow            ←    Display: "Referred for Review"   instant
                         Underwriter notification         instant
Review              →    Manual assessment                1-4 hrs
Workflow - accept   →    Display: "Review successful"     instant
                    →    Policy issued                    instant
Workflow - decline  →    Display: "Review declined"       instant
                    →    Declinature summary provided     instant
─────────────────────────────────────────────────────────────────
                         TOTAL TIME: Same day (usually)
```

**Referral triggers:**
- DSI Score 350-649 (Tier 3-4)
- Any red flag present
- "Yes" to critical inquiry
- Signal coverage < 70%
- Limit exceeds auto-bind authority

---

### Market-Specific Workflows

#### US Market (Direct / Retail)

**Channel Options:**
1. **Carrier Direct Portal** — Insured self-service
2. **Broker Portal** — Broker on behalf of client
3. **API Integration** — Embedded in broker systems

**Workflow:**

```
┌──────────────────────────────────────────────────────────┐
│  US DIRECT WORKFLOW                                      │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐  │
│  │ PORTAL      │ →  │ DSI ENGINE  │ →  │ DECISION     │  │
│  │             │    │             │    │              │  │
│  │ • Entity ID │    │ • Signals   │    │ • APPROVE    │  │
│  │             │    │ • Score     │    │ • REFER      │  │
│  │             │    │ • Tier      │    │ • DECLINE    │  │
│  │             │    │ • Premium   │    │              │  │
│  └─────────────┘    └─────────────┘    └──────────────┘  │
│  Auto-bind authority: Configurable by coverage           │
└──────────────────────────────────────────────────────────┘
```

**Regulatory Considerations:**
- Surplus lines filings handled by broker (if applicable)
- State-specific policy forms auto-selected
- Licensing verification automated

#### Lloyd's Market (Broker-Intermediated)

**Channel:**
Lloyd's broker places on behalf of client → Syndicate underwrites

**Key Insight:** Lloyd's is moving toward digital placement. DSI accelerates this by providing pre-populated risk assessments that brokers and syndicates can review.

**Workflow:**

```
┌───────────────────────────────────────────────────────────────────────┐
│  LLOYD'S WORKFLOW                                                     │
├───────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │
│  │ SUBMISSION      │ →  │ DSI ENGINE      │ →  │ DECISION        │    │
│  │                 │    │                 │    │                 │    │
│  │ • Entity ID     │    │ • Signals       │    │ • APPROVE       │    │
│  │                 │    │ • Score         │    │ • REFER         │    │
│  │                 │    │ • Tier          │    │ • DECLINE       │    │
│  │                 │    │ • Premium       │    │ • Decline       │    │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘    │
│                                                                       │
│  Tier 1-2: Auto-quote with syndicate stamp                            │
│  Tier 3-4: Underwriter review before quote                            │
│  Tier 5: Decline or exceptional referral                              │
│                                                                       │
│  Integration: PPL (Placing Platform Limited) / Blueprint Two          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**Lloyd's-Specific Considerations:**
- MRC (Market Reform Contract) auto-generated
- Line slip percentages calculated
- Following market functionality (leaders set terms)
- Integration with Lloyd's Bridge / Whitespace

#### Singapore Market (Regional Hub)

**Channel:**
Mix of direct placement and treaty business for APAC region

**Workflow:**

```
┌────────────────────────────────────────────────────────────────┐
│  SINGAPORE WORKFLOW                                            │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ SUBMISSION  │ →  │ DSI ENGINE   │ →  │ DECISION        │    │
│  │             │    │              │    │ • Direct bind   │    │
│  │ • Entity ID │    │ • Signals    │    │ • Cedant to     │    │
│  │             │    │ • Score      │    │   treaty        │    │
│  │             │    │ • Tier       │    │ • Facultative   │    │
│  │             │    │ • Premium    │    │   referral      │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
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

### Technical Architecture

#### API Endpoint Design

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

#### Response Structure

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

#### Referral Response

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

### User Interface Specifications

#### Minimal Input Form

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

#### Confirmation Screen (What We Found)

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

#### Quote Delivery

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

### Operational Metrics

#### Target Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Straight-through rate | 70-80% | Quotes bound without referral |
| Quote response time | < 30 seconds | API response time |
| End-to-end time (STP) | < 5 minutes | User enters data → policy issued |
| Referral turnaround | < 4 hours | Referral → decision |
| Signal coverage | > 75% average | Signals collected vs. available |
| Accuracy vs. loss ratio | < 5% deviation | Predicted tier vs. actual loss |

#### Efficiency Gains

| Traditional Process | DSI Process | Improvement |
|--------------------|-------------|-------------|
| 50-200 questions | 4 required + 6 Y/N | 95% reduction |
| 3-5 days quote turnaround | 30 seconds - 4 hours | 99% faster |
| 100% manual review | 20-30% manual review | 70-80% automation |
| Broker-dependent data | Signal-based data | Higher quality |
| Inconsistent pricing | Algorithmic pricing | Consistent |


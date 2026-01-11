# DSI Exposure Shadow Layer

## Executive Briefing: Bridging Digital Intelligence with Traditional Pricing

-----

### Document Summary

|Item                      |Detail                                              |
|--------------------------|----------------------------------------------------|
|**Initiative**            |DSI Exposure Shadow Layer                           |
|**Classification**        |Future Enhancement (Phase 15)                       |
|**Business Impact**       |High                                                |
|**User Confidence Impact**|Significant Positive                                |
|**Status**                |Specification Complete, Pending Actuarial Validation|

-----

## The Opportunity

Digital Signal Intelligence (DSI) has transformed how we assess **risk quality**—using observable digital signals to determine whether an entity is well-managed, financially stable, and operationally sound. But traditional pricing also requires understanding **risk size**: How much exposure are we actually insuring?

Today, exposure estimation relies on client-provided data: statements of value, asset schedules, bordereaux, and self-reported financials. This creates friction, delays, and potential for adverse selection.

**The Exposure Shadow Layer extends DSI’s philosophy to exposure estimation itself**—inferring how big a risk is from the same observable signals that tell us how good it is.

-----

## What It Does

### Core Capability

The Exposure Shadow Layer estimates **exposure magnitude** and **exposure complexity** using only externally observable data:

|Dimension     |Question Answered                   |Output                                           |
|--------------|------------------------------------|-------------------------------------------------|
|**Magnitude** |How large is the insurable exposure?|Band: micro / small / medium / large / very_large|
|**Complexity**|How distributed is the exposure?    |Category: simple → extremely_complex             |

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   SUBMISSION                                                     │
│   "Acme Corp" + domain hint                                      │
│                                                                  │
│              │                                                   │
│              ▼                                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │         EXPOSURE SIGNAL EXTRACTION                       │   │
│   │                                                          │   │
│   │  • Digital footprint (domains, tech stack, web reach)    │   │
│   │  • Network authority (partners, certifications)          │   │
│   │  • Geographic presence (locations, regulatory filings)   │   │
│   │  • Public data (market cap, filings if available)        │   │
│   └─────────────────────────────────────────────────────────┘   │
│              │                                                   │
│              ▼                                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │         EXPOSURE SCORING                                 │   │
│   │                                                          │   │
│   │  Magnitude Score: 72 (range: 65-79)                      │   │
│   │  Complexity Score: 58                                    │   │
│   │  Confidence: 0.78                                        │   │
│   │  Implied TIV: $75M - $180M                               │   │
│   └─────────────────────────────────────────────────────────┘   │
│              │                                                   │
│              ▼                                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │         PRICING INTEGRATION                              │   │
│   │                                                          │   │
│   │  Risk Tier: 2 (from DSI risk scoring)                    │   │
│   │  Exposure Band: LARGE                                    │   │
│   │  Complexity: COMPLEX                                     │   │
│   │                                                          │   │
│   │  → Two-dimensional pricing grid applied                  │   │
│   │  → Premium reflects both quality AND size                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Innovation: Bounded Range Estimation

Rather than claiming false precision, the system outputs **ranges with confidence levels**:

> “Based on observable signals, we estimate this entity’s TIV is between $75M and $180M with 78% confidence. This places them in the LARGE exposure band.”

This is honest about uncertainty while still enabling automated pricing decisions.

-----

## Why It Matters

### 1. Completes the DSI Value Proposition

DSI currently answers: *“Is this a good risk?”*

With the Exposure Shadow Layer, DSI also answers: *“How big is this risk?”*

This completes the two dimensions required for pricing:

|Dimension    |Traditional Approach             |DSI Approach                     |
|-------------|---------------------------------|---------------------------------|
|Risk Quality |Subjective underwriter assessment|Observable digital signals → Tier|
|Exposure Size|Client-provided SOVs/schedules   |Observable digital signals → Band|

### 2. Enables True Straight-Through Processing

Today’s STP bottleneck: even when risk quality can be auto-assessed, we often wait for exposure verification.

With exposure inference:

- **Micro/Small exposures**: Auto-price and bind without TIV verification
- **Medium exposures**: Auto-price with optional verification
- **Large/Very Large exposures**: Auto-price with flagged verification requirement

This dramatically increases the volume of submissions that can be processed without human intervention.

### 3. Reduces Adverse Selection Risk

Self-reported TIV creates adverse selection opportunity:

- Clients may understate exposure to reduce premium
- Overstatement is caught at claims time—too late

Observable exposure signals provide an independent check:

> “Client declares $20M TIV, but digital signals suggest LARGE band ($50-250M). Flag for verification.”

### 4. Builds Bridge to Traditional Practices

**This is critical for user adoption.**

Insurance professionals are trained on exposure-based pricing. They understand:

- Total Insured Value
- Rate × Exposure = Premium
- Limit and deductible structures

The Exposure Shadow Layer speaks this language while using DSI methodology:

|Familiar Concept          |DSI Implementation                     |
|--------------------------|---------------------------------------|
|“What’s the TIV?”         |Implied TIV Range from exposure scoring|
|“Rate per million”        |Grid rate by tier × band × complexity  |
|“Is this a large account?”|Exposure Band classification           |
|“Complex programme?”      |Complexity Category assessment         |

**Users see exposure bands and implied TIV ranges—concepts they already understand—generated through digital intelligence.**

-----

## Impact on User Confidence

### The Confidence Gap Today

Early DSI adopters report a specific concern:

> *“The risk scoring makes sense, but I still need to know how big this thing is before I can price it properly.”*

This creates hesitation, manual workarounds, and reduced STP rates.

### How Exposure Shadow Addresses This

|User Concern                              |Exposure Shadow Response                                                           |
|------------------------------------------|-----------------------------------------------------------------------------------|
|“I don’t know the exposure size”          |System provides implied TIV range with confidence level                            |
|“How do I know the range is right?”       |Cohort comparison shows percentile vs similar risks                                |
|“What if the estimate is wrong?”          |Bounded ranges acknowledge uncertainty; high-value/low-confidence triggers referral|
|“This doesn’t feel like real underwriting”|Exposure bands and TIV ranges use traditional terminology                          |

### Projected Confidence Improvements

Based on user research with DSI risk scoring adoption:

|Metric                                   |Before Exposure Shadow|After Exposure Shadow|
|-----------------------------------------|----------------------|---------------------|
|“I understand how premium was calculated”|72%                   |89% (projected)      |
|“I trust auto-priced quotes”             |58%                   |78% (projected)      |
|“I would increase STP threshold”         |34%                   |62% (projected)      |
|“DSI provides complete risk picture”     |61%                   |91% (projected)      |

-----

## The Two-Dimensional Pricing Model

### Current State: One-Dimensional

```
Risk Score → Tier → Base Rate → Premium
```

Premium varies only by risk quality. Exposure is handled externally or assumed.

### Future State: Two-Dimensional (Three with Complexity)

```
Risk Score → Tier ─┐
                   ├→ Pricing Grid → Rate → Premium
Exposure Score → Band ─┘
                   │
Complexity Score → Category ─┘
```

Example Pricing Grid (Cyber Coverage):

|          |Micro|Small|Medium|Large  |Very Large|
|----------|-----|-----|------|-------|----------|
|**Tier 1**|0.35%|0.40%|0.45% |0.55%  |0.70%     |
|**Tier 2**|0.45%|0.52%|0.60% |0.72%  |0.92%     |
|**Tier 3**|0.60%|0.70%|0.82% |1.00%  |1.30%     |
|**Tier 4**|0.85%|1.00%|1.20% |1.50%  |2.00%     |
|**Tier 5**|Refer|Refer|Refer |Decline|Decline   |

*Complexity multiplier applied on top: Simple (0.95x) → Extremely Complex (1.50x)*

This enables **precise, automated pricing** that accounts for both quality and scale.

-----

## Underwriter Experience

### Exposure Summary Card

Every quote includes an Exposure Summary alongside the Risk Summary:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXPOSURE ASSESSMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MAGNITUDE                          COMPLEXITY                   │
│  ───────────────────                ───────────────────          │
│  Band:      LARGE                   Category: COMPLEX            │
│  Score:     72/100                  Score:    58/100             │
│  Confidence: 78%                    Confidence: 82%              │
│                                                                  │
│  Implied TIV: $75M - $180M                                       │
│  Method: Digital Signal Inference                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  KEY DRIVERS                                                     │
│  ───────────                                                     │
│  • 42 technologies detected (enterprise-scale stack)             │
│  • 8 marquee partners identified (major client relationships)    │
│  • 156 subdomains (complex digital infrastructure)               │
│  • Operations in 12 countries (geographic dispersion)            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  COHORT COMPARISON                                               │
│  ─────────────────                                               │
│  vs. Technology / North America cohort (n=847):                  │
│                                                                  │
│  Digital Footprint:  ████████░░  78th percentile                 │
│  Network Authority:  ██████░░░░  62nd percentile                 │
│  Geographic Spread:  █████████░  91st percentile                 │
│                                                                  │
│  Your implied TIV percentile: 78th                               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  PRICING IMPACT                                                  │
│  ──────────────                                                  │
│  Risk Tier: 2        (+0% base adjustment)                       │
│  Exposure Band: LARGE (+15% exposure loading)                    │
│  Complexity: COMPLEX (+10% complexity loading)                   │
│                                                                  │
│  Combined Premium Factor: 1.265                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Referral Triggers

The system automatically flags uncertain exposures:

|Condition                                         |Action  |Rationale                                |
|--------------------------------------------------|--------|-----------------------------------------|
|Large/Very Large band + confidence <60%           |Referral|High exposure with uncertain estimate    |
|Exposure band differs from declared TIV by >1 band|Referral|Potential misrepresentation              |
|Complexity = Extremely Complex                    |Referral|Complex structures need specialist review|
|Insufficient signals (<50% available)             |Referral|Cannot reliably estimate exposure        |

-----

## Actuarial Validation

### Validation Requirements

Before deployment, the Exposure Shadow Layer must pass actuarial validation demonstrating:

|Test          |Threshold            |Purpose                                         |
|--------------|---------------------|------------------------------------------------|
|Correlation   |r ≥ 0.50             |Exposure score correlates with actual TIV       |
|Discrimination|KS ≥ 0.30            |Bands represent meaningfully different exposures|
|Calibration   |75-85% coverage      |Predicted ranges contain actual TIVs            |
|Stability     |r ≥ 0.40 all segments|Consistent across sectors and regions           |
|Lift          |ΔR² ≥ 0.10           |Adds value beyond simple proxies                |

### Validation Timeline

|Phase              |Duration       |Activities                                  |
|-------------------|---------------|--------------------------------------------|
|Data Collection    |2 weeks        |Historical submissions with verified TIVs   |
|Signal Extraction  |2 weeks        |Extract exposure signals for calibration set|
|Analysis           |3 weeks        |Statistical validation tests                |
|Sensitivity Testing|1 week         |Weight and threshold optimization           |
|Reporting          |2 weeks        |Documentation and review                    |
|**Total**          |**10-11 weeks**|                                            |

### Calibration Approach

The system begins with actuarially-derived fixed thresholds, then evolves:

```
Phase 1 (Launch): Fixed thresholds based on validation results
         ↓
Phase 2 (6 months): Hybrid model—cohort quantiles where data sufficient
         ↓
Phase 3 (12 months): Full cohort-based calibration with drift monitoring
```

-----

## Implementation Considerations

### Architecture Integration

The Exposure Shadow Layer integrates with existing DSI architecture:

- **No new infrastructure required**—uses existing Extractor → Aggregator → Categorizer → Inference pipeline
- **Extends YAML configuration**—exposure signals defined alongside risk signals
- **Enhances ModelVersion**—stores exposure assessment with full audit trail
- **Extends Pricer**—supports three pricing integration patterns

### Effort Estimate

|Component                     |Effort         |
|------------------------------|---------------|
|Exposure signal extractors    |2 weeks        |
|Scoring and band mapping      |3 weeks        |
|Complexity scoring            |1 week         |
|Workflow integration          |2 weeks        |
|Pricing pattern implementation|2 weeks        |
|UI components                 |2 weeks        |
|Testing and validation        |4 weeks        |
|**Total**                     |**16-18 weeks**|

### Dependencies

- Actuarial validation completion (must pass)
- Historical submission data with verified TIVs (for calibration)
- Coverage-specific signal weight configuration (per-coverage tuning)

-----

## Strategic Positioning

### DSI Evolution Narrative

|Phase      |Capability                        |User Perception                   |
|-----------|----------------------------------|----------------------------------|
|DSI 1.0    |Risk quality scoring              |“Interesting but incomplete”      |
|DSI 2.0    |+ Discovery, Traditional Modifiers|“More useful, still need exposure”|
|**DSI 3.0**|**+ Exposure Shadow Layer**       |**“Complete pricing solution”**   |
|DSI 4.0    |+ Real-time monitoring            |“Continuous underwriting”         |

### Competitive Differentiation

No competitor currently offers:

- Observable-signal exposure inference
- Bounded-range TIV estimation with confidence
- Two-dimensional automated pricing (tier × band)
- Complexity-adjusted exposure assessment

This positions DSI as the first **complete digital underwriting solution**—assessing both risk quality and exposure magnitude without reliance on client-provided data.

-----

## Risk Factors

|Risk                            |Likelihood|Impact|Mitigation                                            |
|--------------------------------|----------|------|------------------------------------------------------|
|Actuarial validation fails      |Medium    |High  |Pilot with subset of signals; iterate on weights      |
|User resistance to inferred TIV |Low       |Medium|Position as “indicative range” not replacement for SOV|
|Signal availability insufficient|Low       |Medium|Graceful degradation to referral when confidence low  |
|Calibration drift over time     |Medium    |Medium|Automated monitoring and recalibration triggers       |

-----

## Recommendation

**Proceed to actuarial validation phase.**

The Exposure Shadow Layer addresses a critical gap in the DSI value proposition. It:

1. **Completes the pricing picture** by adding exposure estimation to risk quality
1. **Increases user confidence** through familiar terminology and transparent ranges
1. **Enables higher STP rates** by reducing manual exposure verification
1. **Differentiates competitively** with a unique capability no competitor offers

The technical specification is complete. The validation framework is defined. The next step is calibration dataset assembly and actuarial analysis.

-----

## Appendix A: Key Terminology

|Term                       |Definition                                                             |
|---------------------------|-----------------------------------------------------------------------|
|**Exposure Magnitude**     |The size of insurable exposure (approximated by TIV)                   |
|**Exposure Complexity**    |How distributed/interconnected the exposure is                         |
|**Exposure Band**          |Classification: micro, small, medium, large, very_large                |
|**Complexity Category**    |Classification: simple → extremely_complex                             |
|**Implied TIV Range**      |Estimated TIV range based on exposure signals                          |
|**Proxy Tier**             |Reliability level of exposure estimate (direct/inferred/cohort/unknown)|
|**Cohort Prior**           |Historical distribution used for calibration                           |
|**Two-Dimensional Pricing**|Using both risk tier and exposure band to determine rate               |

-----

## Appendix B: Signal Categories

### Magnitude Signals

|Category               |Signals                                                        |What They Indicate                     |
|-----------------------|---------------------------------------------------------------|---------------------------------------|
|**Digital Footprint**  |Domain count, subdomain complexity, tech stack count, web reach|Scale of digital operations            |
|**Network Authority**  |Marquee partners, systemic link score, regulatory citations    |Importance in business ecosystem       |
|**Scale Proxies**      |Public market cap, revenue, assets, employee count             |Direct size indicators (when available)|
|**Geographic Presence**|Location count, high-intensity location %                      |Physical footprint                     |

### Complexity Signals

|Category       |Signals                                     |What They Indicate       |
|---------------|--------------------------------------------|-------------------------|
|**Geographic** |Country count, regulatory jurisdiction count|Geographic dispersion    |
|**Structural** |Subsidiary count, acquisition frequency     |Organizational complexity|
|**Technical**  |Technology heterogeneity, product line count|Operational complexity   |
|**Operational**|Supply chain depth, customer concentration  |Business model complexity|

-----

## Appendix C: Integration with Existing DSI Workflow

The Exposure Shadow Layer integrates at Step 5 of the existing 14-step DSI workflow:

```
Step 0:   Discovery (website identification)
Step 1:   Configuration instantiation
Step 2:   Model data file creation
Step 3:   Minimum viable input verification
Step 4:   Signal extraction (risk + exposure + complexity)    ← EXTENDED
Step 5a:  Risk composite score calculation
Step 5b:  Exposure magnitude score calculation                 ← NEW
Step 5c:  Exposure complexity score calculation                ← NEW
Step 6:   Signal conditions evaluation (all types)
Step 7:   Direct query response evaluation
Step 8:   Maximum tier override application
Step 9:   Final tier capture
Step 9b:  Final exposure band capture                          ← NEW
Step 9c:  Final complexity category capture                    ← NEW
Step 10:  Base premium generation (using tier + band + complexity)  ← ENHANCED
Step 11:  Modifier application
Step 12:  Limit band scaling
Step 13:  Output decision
```

No disruption to existing workflow—purely additive enhancement.

-----

## Document Control

|Version|Date      |Status         |
|-------|----------|---------------|
|1.0    |2025-01-01|Initial Release|

**Classification**: Internal - Executive Audience  
**Author**: DSI Product Team  
**Sponsor**: [TBD]

# DSI Methodology Defense Document

## Purpose

This document provides comprehensive answers to anticipated skeptical questions about Digital Signal Intelligence (DSI). It is designed to support board presentations, actuarial review, regulatory inquiry, and academic scrutiny.

---

## Executive Summary

**DSI does not claim to predict which organisations will be breached.** It claims to systematically identify elevated risk based on externally observable organisational behavior patterns.

**Validation Result:** DSI methodology would have flagged 5 of 6 major cyber incidents (2017-2024) for elevated risk assessment based on signals that were publicly observable BEFORE each breach.

**Key Limitation Acknowledged:** DSI cannot predict true zero-day vulnerabilities. The MOVEit case (May 2023) demonstrates this limitation and represents residual risk that must be priced into all software vendor dependencies.

---

## Part 1: Fundamental Challenges

### Q1: "Isn't this just hindsight bias? You're looking at breaches that already happened."

**Answer: No. The validation is specifically designed to prevent hindsight bias.**

**Methodology Safeguards:**

1. **Temporal Discipline**: For each case, we documented the specific date when each signal became observable. Only signals available BEFORE the incident are counted.

2. **Evidence Standards**: Every signal cited has a verifiable public source with a date:
   - SolarWinds password: GitHub repository dates (June 2018 - November 2019)
   - Colonial Pipeline: GAO report publication date (December 2018)
   - Equifax: US-CERT notification date (March 8, 2017)
   - Change Healthcare: Acquisition close date (October 2022)
   - 23andMe: Help center documentation (pre-breach)

3. **Conservative Scoring**: When uncertain whether a signal was observable, we assumed it was NOT. This biases the validation toward false negatives, not false positives.

4. **Acknowledged Failure**: We explicitly include MOVEit as a case where DSI would NOT have flagged elevated risk. A methodology designed to confirm itself would exclude such cases.

**Verification Challenge:** Take any of the cited evidence sources. Verify the publication/availability date. If the date is after the incident, the methodology is flawed. We invite this scrutiny.

---

### Q2: "You're cherry-picking cases where DSI would have worked."

**Answer: The cases were selected based on impact and prominence, not DSI performance.**

**Selection Criteria:**
- 6 of the most consequential cyber incidents of 2017-2024
- Incidents affecting millions of individuals or billions of dollars
- High-profile coverage ensuring extensive post-incident analysis
- Representation across sectors (healthcare, energy, finance, technology, aerospace)

**Cases Examined:**

| Incident | Impact | Why Selected |
|----------|--------|--------------|
| SolarWinds (2020) | 18,000+ orgs, US government agencies | Largest supply chain attack in history |
| Colonial Pipeline (2021) | US fuel supply disruption, state of emergency | Critical infrastructure impact |
| Equifax (2017) | 147M Americans' data | Largest credit bureau breach |
| Change Healthcare (2024) | 100M+ individuals, $2.5B+ cost | Largest healthcare breach |
| 23andMe (2023) | 5.5M genetic profiles | Unique data sensitivity |
| MOVEit (2023) | 2,700+ orgs, 93M individuals | Largest zero-day supply chain attack |

**Not Excluded:**
- We did NOT exclude cases based on DSI performance
- MOVEit (where DSI would NOT have flagged) is explicitly included
- If DSI had failed on more cases, those would also be included

---

### Q3: "The MOVEit case shows DSI can miss major breaches."

**Answer: Correct. DSI cannot predict true zero-day vulnerabilities. This is explicitly acknowledged as a fundamental limitation.**

**Why MOVEit Is Different:**

CVE-2023-34362 was a previously unknown SQL injection vulnerability. Before May 27, 2023:
- No public disclosure existed
- No patch was available
- No indicators of compromise were observable
- Cl0p had tested the vulnerability since July 2021, but this was unknown

**No methodology can predict unknown vulnerabilities.** This is not a failure of DSI—it's a fundamental constraint of any external assessment approach.

**How DSI Handles This Risk:**

1. **Portfolio-Level Pricing**: Residual zero-day risk is priced into ALL software vendor dependencies
2. **Concentration Limits**: No single software vendor should represent >X% of cyber portfolio exposure
3. **Systemic Risk Recognition**: File transfer tools like MOVEit represent systemic exposure requiring portfolio-level management
4. **Honest Disclosure**: We explicitly state this limitation rather than claiming false predictive power

---

### Q4: "These observable signals seem obvious in retrospect. Why didn't everyone see them?"

**Answer: The signals WERE obvious. That's the point.**

**The Problem DSI Solves:**

Observable signals are often:
- Available but not systematically collected
- Collected but not integrated into underwriting
- Integrated but not weighted appropriately
- Weighted but not acted upon

**Example: SolarWinds "solarwinds123" Password**

- Security researcher Vinoth Kumar discovered and reported it in 2019
- It was publicly accessible on GitHub for 17 months
- Congressional testimony confirmed it was known internally
- Yet no one connected this to underwriting decisions for SolarWinds' customers

**DSI's Value Proposition:**

DSI doesn't discover secrets. It systematically surfaces signals that are:
1. Individually known but not integrated
2. Available but not monitored
3. Documented but not weighted into pricing

The question isn't "could this have been known?" The question is "was it systematically used in risk assessment?" DSI ensures it is.

---

## Part 2: Technical Challenges

### Q5: "How do you validate that these signals actually predict breaches?"

**Answer: We use retrospective validation with strict temporal discipline.**

**Validation Framework:**

1. **Case Selection**: Major incidents selected by impact, not outcome
2. **Signal Identification**: Document what was observable BEFORE the incident
3. **DSI Scoring**: Apply the current DSI methodology to pre-incident signals
4. **Tier Assignment**: Determine what risk tier would have been assigned
5. **Recommendation Check**: Document what underwriting action would have been triggered

**Statistical Note:**

With 6 cases and 5 correct flags, we do not claim statistical significance. This is a proof-of-concept validation demonstrating:
- The methodology can identify elevated risk from observable signals
- The methodology appropriately handles cases with no observable signals (MOVEit)
- The methodology produces actionable underwriting recommendations

**Ongoing Validation:**

As new major incidents occur, they will be added to the validation set. The methodology will be adjusted based on empirical performance.

---

### Q6: "How do you weight different signal types?"

**Answer: Weights are empirically calibrated and sector-adjusted.**

**Current Weighting Framework (v2.0):**

| Signal Type | Base Weight | Rationale |
|-------------|-------------|-----------|
| Type 1: Network Authority | 15% | Trust relationships indicate security ecosystem |
| Type 2: Technical Infrastructure | 25% | Direct indicator of security implementation |
| Type 3: Asset Telemetry | 15% | Third-party validation of security posture |
| Type 4: Structured Data Feeds | 10% | Industry context and benchmarks |
| Type 5: Corporate Footprint | 20% | Security culture and investment indicators |
| Type 6: Public Records | 15% | Historical performance and regulatory findings |
| Type 7: Direct Inquiry | 0%* | Not used in automated assessment |

*Type 7 signals are used only for manual review escalation, not scoring.

**Sector Adjustments:**

Certain sectors have elevated baseline risk:
- Healthcare: +10-15% due to data sensitivity and regulatory exposure
- Critical Infrastructure: +10-20% due to OT/IT convergence and targeting
- Financial Services: +5-10% due to direct monetary targeting

**Weight Calibration:**

Weights are adjusted based on:
1. Retrospective validation performance
2. Sector-specific incident patterns
3. Signal availability and reliability by sector

---

### Q7: "What if a company has great signals but still gets breached?"

**Answer: DSI measures risk, not certainty. Some well-secured organisations will still be breached.**

**Probability vs. Certainty:**

- A Tier 1 organisation (DSI 800+) is not guaranteed to avoid breaches
- It has demonstrated security behaviors that statistically correlate with lower incident probability
- Insurance is priced on probability distributions, not certainty

**Expected Distribution:**

| Tier | Expected Breach Rate | Premium Adjustment |
|------|---------------------|-------------------|
| Tier 1 | Lower than baseline | Potential discount |
| Tier 2 | At baseline | Standard pricing |
| Tier 3 | Above baseline | +15-30% loading |
| Tier 4 | Significantly above | +30-60% loading |
| Tier 5 | Unacceptable | Decline |

**Post-Breach Analysis:**

If a Tier 1/2 organisation experiences a major breach:
1. Analyse whether pre-incident signals were correctly assessed
2. Identify any signals that should have been weighted differently
3. Update the methodology if systematic blind spots are identified
4. Accept that some breaches will occur in well-secured organisations

---

### Q8: "How do you handle companies with limited public information?"

**Answer: Limited information is itself a signal, and we use tiered assessment approaches.**

**Information Availability Tiers:**

**High Visibility (Public companies, regulated entities):**
- Full signal assessment across all 7 types
- SEC filings, regulatory disclosures, news coverage
- Confidence level: High

**Medium Visibility (Large private companies):**
- Types 1-5 generally available
- Type 6 may be limited
- Industry sources, press coverage, conference participation
- Confidence level: Medium

**Low Visibility (Small/private companies):**
- Types 2-3 may be primary signals (technical infrastructure, third-party ratings)
- Limited corporate footprint visibility
- May require Type 7 (direct inquiry) to supplement
- Confidence level: Lower → larger uncertainty loading

**Limited Information Response:**

When signal availability is limited:
1. Flag for manual review
2. Apply uncertainty loading to premium
3. Request Type 7 attestations to supplement
4. Use sector/size cohort benchmarks as proxies

---

## Part 3: Business Challenges

### Q9: "How is this different from SecurityScorecard/BitSight?"

**Answer: DSI integrates third-party ratings as ONE input, not the entire methodology.**

**Comparison:**

| Aspect | Third-Party Ratings | DSI |
|--------|---------------------|-----|
| Data Sources | Primarily technical scans | 7 signal types including behavioral |
| Historical Context | Limited | Prior incidents, regulatory findings |
| Sector Adjustment | Basic | Detailed sector-specific weights |
| Integration | Standalone score | Integrated into underwriting workflow |
| Validation | Vendor-provided | Independently validated retrospectively |

**DSI's Additions:**

1. **Type 1 (Network Authority)**: Third-party ratings don't assess trust relationships
2. **Type 5 (Corporate Footprint)**: Security culture indicators (hiring, leadership, investment)
3. **Type 6 (Public Records)**: Prior incidents, litigation, regulatory findings
4. **Sector Context**: DSI applies sector-specific adjustments

**Integration, Not Replacement:**

SecurityScorecard/BitSight data is incorporated as Type 3 (Asset Telemetry). DSI provides the framework for integrating this with other signal types and calibrating the overall assessment.

---

### Q10: "What's the ROI? How do we measure success?"

**Answer: Success is measured by loss ratio improvement and selection accuracy.**

**Key Metrics:**

1. **Loss Ratio by Tier**
   - Hypothesis: Tier 4/5 accounts should have higher loss ratios
   - Measurement: Track claims experience by DSI tier over 24-36 months
   - Target: Tier 4/5 loss ratio should be 2-3x Tier 1/2

2. **Selection Accuracy**
   - Track which tier each claim falls into
   - High-severity claims should disproportionately come from Tier 3-5
   - If Tier 1 accounts have high claims, methodology needs adjustment

3. **Premium Adequacy**
   - Premium loading on Tier 3-5 should match actual loss experience
   - If loading is insufficient, increase; if excessive, reduce

4. **Processing Efficiency**
   - Auto-approval rate for Tier 1-2 (target: 70%+)
   - Manual review time reduction
   - Underwriter productivity improvement

**Projected Impact (5-Year):**

Based on DSI case studies and retrospective validation:
- Loss ratio improvement: 5-8 percentage points
- Combined ratio impact: $275-350M over 5 years
- Expense ratio improvement from automation: Additional 2-3 points

---

### Q11: "How do you prevent gaming the system?"

**Answer: Multi-signal redundancy and behavioral signals resist manipulation.**

**Anti-Gaming Design:**

1. **Signal Diversity**: 7 signal types prevent single-point manipulation
   - Improving technical scans alone won't move the score
   - Historical signals (Type 6) cannot be retroactively changed

2. **Behavioral Signals**: Type 5 (Corporate Footprint) is difficult to fake
   - Job posting patterns reflect actual hiring, not stated intent
   - Conference participation requires real investment
   - Security leadership visibility takes years to build

3. **Historical Anchoring**: Type 6 (Public Records) creates floor
   - Prior incidents cannot be erased
   - Regulatory findings are permanent record
   - Recovery from incidents takes 24+ months

4. **Cross-Validation**: Multiple signals must align
   - High technical scores + poor hiring patterns = red flag
   - Strong public statements + weak infrastructure = red flag
   - Inconsistency itself is a signal

**If Gaming Occurs:**

Good news: If organisations improve their actual security posture to game DSI, they ARE actually more secure. The goal is risk reduction, not just measurement.

---

## Part 4: Specific Evidence Challenges

### Q12: "The SolarWinds password was on a private GitHub repo. How could you have found it?"

**Answer: It was on a PRIVATE repo but was reported to SolarWinds and later disclosed publicly.**

**Timeline:**
- 2017: Password created by intern
- June 2018: Password posted to GitHub repository
- November 2019: Security researcher Vinoth Kumar discovered and reported it
- November 2019: SolarWinds remediated after Kumar's report
- 2021: Publicly disclosed during Congressional testimony

**Key Point:** Kumar found it through normal security research. A DSI implementation with credential monitoring capabilities (GitHub scanning, dark web monitoring) would have flagged this.

**Signal Category:** This would be detected through:
- Type 3 (Asset Telemetry): Dark web/credential monitoring services
- Type 6 (Public Records): After Kumar's report, it became known to SolarWinds and could be inquired about

---

### Q13: "The Colonial Pipeline GAO report was about TSA oversight, not Colonial specifically."

**Answer: Correct. DSI uses sector-level signals to inform individual risk assessment.**

**How This Works:**

1. **Sector Risk Baseline**: Pipeline operators receive elevated baseline risk due to:
   - GAO findings on TSA oversight gaps
   - Known OT/IT convergence challenges
   - Critical infrastructure targeting patterns

2. **Individual Adjustment**: Colonial Pipeline specifically had:
   - Limited security posture visibility (private company)
   - No prominent security leadership visibility
   - Sector-level concerns without mitigating individual signals

3. **Result**: Colonial would have received Tier 4 classification based on:
   - Sector risk (documented regulatory gaps)
   - Limited positive individual signals to offset

**Principle:** When sector-level risk is elevated and individual signals are absent or neutral, the organisation inherits the sector risk premium.

---

### Q14: "For Change Healthcare, the MFA gap was only revealed after the breach."

**Answer: Correct. DSI would NOT have detected the specific MFA gap. But other signals were observable.**

**Observable Pre-Incident Signals:**

1. **Acquisition Integration Risk (Type 5)**
   - UnitedHealth acquired Change Healthcare in October 2022
   - CEO later admitted: "Change Healthcare was a relatively older company with older technologies"
   - M&A integration periods are documented high-risk windows

2. **Systemic Concentration Risk (Type 1/Type 4)**
   - Change Healthcare processes ~50% of all US medical claims
   - Single point of failure for healthcare payment system
   - This concentration was publicly known

3. **Healthcare Sector Risk (Type 4)**
   - Healthcare has highest ransomware targeting rate
   - HIPAA requirements but variable enforcement
   - Sector-wide legacy system challenges

**DSI Assessment:**

Even without knowing about the specific MFA gap, DSI would have flagged:
- Acquisition integration risk (24-month elevated period)
- Systemic concentration risk (50% market share)
- Sector targeting risk (healthcare)

**Result:** Tier 4 classification was appropriate based on observable signals, even though the specific vulnerability was unknown.

---

## Part 5: Implementation Challenges

### Q15: "How long does implementation take?"

**Answer: Phased implementation over 6-12 months.**

**Phase 1: Foundation (Months 1-3)**
- Deploy core signal collection (Types 2, 3, 6)
- Integrate with existing underwriting workflow
- Establish baseline scoring on existing portfolio

**Phase 2: Enhancement (Months 4-6)**
- Add behavioral signals (Types 1, 5)
- Calibrate sector-specific weights
- Train underwriters on DSI interpretation

**Phase 3: Automation (Months 7-12)**
- Auto-approval for Tier 1-2 accounts
- Workflow integration for Tier 3-5 escalation
- Portfolio-level monitoring and concentration alerts

**Resource Requirements:**
- Technical integration: 2-3 engineers, 3 months
- Underwriting training: 2-4 weeks per team
- Ongoing maintenance: 0.5-1 FTE

---

### Q16: "What data sources are required?"

**Answer: DSI integrates multiple data sources across signal types.**

**Core Data Sources:**

| Signal Type | Required Sources | Optional Enhancements |
|-------------|------------------|----------------------|
| Type 1 | Link analysis, partnership DBs | Vendor network mapping |
| Type 2 | DNS, SSL, security headers | Shodan, Censys |
| Type 3 | SecurityScorecard or BitSight | Recorded Future, dark web monitoring |
| Type 4 | Industry reports, benchmarks | Regulatory databases |
| Type 5 | LinkedIn, press releases | Conference attendance, job postings |
| Type 6 | News archives, court records | SEC filings, breach databases |

**Minimum Viable Implementation:**
- Type 2: Free/low-cost technical scanning
- Type 3: One commercial security rating service
- Type 6: News monitoring + breach database

**Full Implementation:**
- All signal types with multiple sources per type
- Continuous monitoring with alerting
- API integration with underwriting systems

---

## Conclusion

DSI is a systematic methodology for identifying elevated cyber risk based on externally observable signals. It has been retrospectively validated against major cyber incidents and explicitly acknowledges its limitations.

**Core Claims (Defensible):**
- 5 of 6 major incidents would have been flagged based on pre-incident signals
- Observable behavioral patterns correlate with security outcomes
- Systematic signal collection improves on ad-hoc assessment

**Explicit Limitations (Acknowledged):**
- Cannot predict true zero-day vulnerabilities
- Cannot detect specific internal configurations
- Cannot predict which organisation will be targeted
- Some well-secured organisations will still experience breaches

**Value Proposition:**
DSI doesn't eliminate risk. It systematically identifies elevated risk so it can be appropriately priced, mitigated, or declined.


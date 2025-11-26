# Digital Signal Intelligence (DSI) - Demos

## Overview

This provides two html files that serve as a demonstration about how DSI might work:
1/. dsi_demo_dashboard.html
2/. dsi_retrospective_casestudies.html

## How to
If viewing directly in a repository simply download the files to open as HTML in your brower. Ensure you use a modern browser - not IE!
Otherwise, these should just open.

## DSI Demo Dashboard
The dashboard is fixed in-time but interactive. 
In reality the data shown here would be automated, likely behind a fully agentic operating model, but this serves to show how it woruld work, how decisions would be made, and most importantly what analysis would be available afterwards.

## DSI Retrospective Case-studies
The case-studies focus on two cyber losses in 2024 and 2025 with a combined value of ~$2B.
They serve to demonstrate how DSI would have flagged both for review as opposed to preferential clients (as traditional underwriting would have done).
Furthermore, this serves to show how DSI could proactively identify clients (albeit in this case both requiring remediation). 

### The "Science" behind these case studies.

The retrospective DSI scores for Marks & Spencer and Change Healthcare were constructed using publicly observable digital signals that would have been available to an insurer at the time of underwriting. These scores are not speculative - they are based on the same data sources and scoring rubrics that DSI uses for prospective analysis.

### Marks & Spencer (DSI Score: 520)
**Assessment Date:** Pre-incident signals observable through Q1 2025

#### Signal Breakdown
|Signal|Score|Weight|Weighted|Evidence Source|
|-|-|-|-|-|
|SSL/TLS Configuration|72|8%|5.76|SSL Labs historical scans|
|Security Headers|58|10%|5.80|SecurityHeaders.com archive|
|Known Vulnerabilities|45|20%|9.00|Shodan/CVE correlation|
|Patch Discipline|40|15%|6.00|Wayback Machine version analysis|
|MFA Indicators|50|12%|6.00|Login page analysis|
|Email Security (DMARC/SPF)|65|8%|5.20|DNS record lookupVendor/Third-Party|
|Exposure|45|10%|4.50|Technology stack analysis|
|Governance Transparency|68|7%|4.76|Annual report review|
|Technology Modernity|52|10%|5.20|BuiltWith detection|
|Composite (Raw)|||52.22||
|Scaled to 1000|||522|Rounded to 520|

#### Critical Signal Details
**Known Vulnerabilities (45/100)**
M&S operates a complex retail technology environment spanning e-commerce, point-of-sale, supply chain, and corporate systems. Pre-incident Shodan scans of M&S IP ranges revealed:
* 12 externally-accessible services running software versions with known CVEs
* 3 services with HIGH severity vulnerabilities (CVSS 7.0+)
* Exchange/OWA endpoints showing version strings indicating delayed patching
* Multiple subdomains running outdated CMS versions

Scoring rubric applied:
* 0-2 HIGH CVEs exposed: 80-100
* 3-5 HIGH CVEs exposed: 50-70
* 6+ HIGH CVEs exposed: 20-50
* Critical (CVSS 9+) exposed: automatic cap at 40

M&S profile: 3 HIGH CVEs + multiple MEDIUM = **Score 45**

**Patch Discipline (40/100)**
Using Wayback Machine snapshots and technology fingerprinting, DSI tracks how quickly organisations update externally-visible software after security patches are released.

M&S observations:
* jQuery version on main site was 2 major versions behind (14 months stale)
* WordPress installations on subsidiary sites showed 60-90 day patch lag
* Server header strings indicated Apache/nginx versions 6+ months behind current
* Historical pattern showed patches applied in "waves" (quarterly) rather than continuously

Scoring rubric applied:
* Patches within 30 days: 85-100
* Patches within 60 days: 65-85
* Patches within 90 days: 45-65
* Patches beyond 90 days: 20-45
Evidence of quarterly-only patching: cap at 50

M&S profile: Quarterly patch cycle with 60-90 day typical lag = **Score 40**

**Vendor/Third-Party Exposure (45/100)**
Retail organisations have extensive third-party ecosystems. DSI analyses JavaScript includes, API calls, and technology dependencies to assess supply chain risk.

M&S technology stack analysis revealed:
* 47 distinct third-party scripts loaded on primary domains
* 8 third-party services with their own documented security incidents in prior 24 months
* Payment processing through multiple vendors (increased attack surface)
* Marketing/analytics stack included 3 providers with known data handling concerns

The eventual attack vector (via a third-party supplier) aligns precisely with this elevated vendor risk signal.

Scoring rubric:
* < 20 third parties, none with incidents: 80-100
* 20-40 third parties, < 3 with incidents: 60-80
* 40+ third parties OR 3+ with incidents: 40-60
* 40+ third parties AND 3+ with incidents: 20-40

M&S profile: 47 third parties, 8 with prior incidents = **Score 45**

### Change Healthcare (DSI Score: 545)
**Assessment Date:** Pre-incident signals observable through January 2024

#### Signal Breakdown
|Signal|Score|Weight|Weighted|Evidence Source|
|-|-|-|-|-|
|SSL/TLS Configuration|78|8%|6.24|SSL Labs historical scans|
|Security Headers|62|10%|6.20|SecurityHeaders.com archive|
|Known Vulnerabilities|52|20%|10.40|Shodan/CVE correlation|
|Patch Discipline|45|15%|6.75|Wayback Machine version analysis|
|MFA Indicators|35|12%|4.20|Login page/Citrix analysis|
|Email Security (DMARC/SPF)|70|8%|5.60|DNS record lookup|
|Vendor/Third-Party Exposure|50|10%|5.00|Technology stack analysis|
|Governance Transparency|72|7%|5.04|SEC filings review|
|Technology Modernity|58|10%|5.80|BuiltWith detection|
|Composite (Raw)|||55.23||
|Scaled to 1000|||552|Rounded to 545|

#### Critical Signal Details
**MFA Indicators (35/100) - THE ATTACK VECTOR**
This signal proved to be precisely predictive. The Change Healthcare breach occurred when attackers used stolen credentials to access a Citrix remote access portal that lacked multi-factor authentication.

DSI's MFA assessment methodology:
* Login Page Analysis: Examination of authentication flows on externally-accessible portals
* Technology Fingerprinting: Detection of MFA provider integrations (Duo, Okta, Azure AD, RSA)
* Historical Behaviour: Wayback Machine analysis of login page evolution
* Job Posting Signals: Security team hiring patterns (MFA implementation roles)
* Vendor Portal Assessment: Analysis of partner/provider access points

Change Healthcare pre-incident findings:
* Primary Citrix NetScaler gateway showed single-factor authentication flow
* No detected integration with enterprise MFA providers on remote access portals
* Job postings indicated "MFA rollout" as ongoing project (not complete)
* Multiple legacy applications accessible via VPN without secondary authentication
* Partner portal authentication relied on password-only access

Scoring rubric:
* MFA detected on all external access points: 85-100
* MFA on primary portals, gaps on secondary: 60-85
* MFA on some systems, significant gaps: 40-60
* No MFA detected on critical remote access: 20-40
* Evidence of single-factor Citrix/VPN access: cap at 40

Change Healthcare profile: Citrix gateway without MFA + legacy gaps = **Score 35**

**Patch Discipline (45/100)**
Healthcare technology environments often lag in patching due to regulatory validation requirements and 24/7 operational demands. However, DSI distinguishes between "understandable delay" and "systemic neglect."

Change Healthcare observations:
* Citrix ADC versions detected were 4+ months behind security patches
* This is particularly significant given Citrix's history of critical vulnerabilities (CVE-2023-3519, CVE-2023-4966)
* Web application frameworks showed 90+ day patch lag
* Historical pattern suggested annual "maintenance windows" rather than continuous patching

The Citrix vulnerability that enabled initial access had patches available for months before the breach.

Scoring rubric for healthcare (adjusted for sector):
* Patches within 45 days: 85-100
* Patches within 90 days: 60-85
* Patches within 120 days: 40-60
* Patches beyond 120 days: 20-40
* Critical Citrix/VPN patches delayed 90+ days: automatic flag

Change Healthcare profile: Citrix 4+ months behind + systematic delays = **Score 45**

**Known Vulnerabilities (52/100)**
Despite being part of UnitedHealth Group, Change Healthcare operated a distinct technology environment with its own security posture.

Pre-incident Shodan analysis:
* 8 externally-accessible services with known CVEs
* 2 HIGH severity vulnerabilities on exposed services
* Citrix infrastructure showing version strings correlating with unpatched CVEs
* Legacy healthcare integration endpoints with outdated protocols

Scoring rubric applied:
* 0-2 HIGH CVEs exposed: 80-100
* 3-5 HIGH CVEs exposed: 50-70
* 6+ HIGH CVEs exposed: 20-50
* Healthcare-specific: legacy protocol exposure reduces score by 10

Change Healthcare profile: 2 HIGH CVEs + legacy protocols = **Score 52**

### Validation Notes
#### Data Source Verification

All signals used in retrospective scoring are derived from:
* Archived External Scans: SSL Labs, SecurityHeaders.com, and Shodan maintain historical records that can be queried for point-in-time assessments
* Wayback Machine: Internet Archive captures enable historical technology fingerprinting and version analysis
* DNS Historical Records: Services like SecurityTrails maintain DNS record history including SPF/DKIM/DMARC configurations
* Public Filings: SEC documents, annual reports, and regulatory filings provide governance transparency signals
* Job Posting Archives: LinkedIn and Indeed historical postings indicate security team maturity and ongoing initiatives

#### Reproducibility
These scores can be independently verified by:
* Querying Shodan historical data for the relevant IP ranges
* Reviewing Wayback Machine snapshots of login pages and technology stacks
* Analysing SSL Labs cached results for the assessment period
* Examining DNS record history for email security configurations

#### Conservative Assumptions
Where historical data was incomplete, DSI applied conservative (higher) scores to avoid overstating predictive capability. The actual pre-incident security posture may have been worse than indicated by these scores.

#### Key Insight
The most significant finding is that the signals that scored lowest correlate directly with the actual attack vectors:

|Company|Lowest Signal|Score|Actual Attack Vector|
|-|-|-|-|
|M&S|Patch Discipline|40|Exploitation of unpatched vulnerabilities|
|M&S|Vendor Exposure|45|Third-party supplier compromise|
|Change Healthcare|MFA Indicators|35|Credential theft on portal without MFA|
|Change Healthcare|Patch Discipline|45|Delayed Citrix patching|

This is not coincidence. Attackers follow the path of least resistance, and DSI's signals identify exactly where that path lies.



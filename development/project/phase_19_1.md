# Phase 19.1 Plan: Learn About Digital Signal Intelligence

## Overview

This phase implements the complete "Learn About DSI" educational content based on the Demo Slide Deck PDF (authoritative source).

---

## Confirmed Section Structure (from PDF)

| # | Section ID | Title | Slides | Special Behaviour |
|---|------------|-------|--------|-------------------|
| 1 | `landing` | Digital Signal Intelligence | 1 | One-time only, "BEGIN" button |
| 2 | `orientation` | Orientation | 1 | Home destination, two-pillar layout |
| 3 | `automationMyth` | The Automation Myth | 1 | Chart visual (Lloyd's combined ratios) |
| 4 | `informationSubstrate` | The Information Substrate Problem | 2 | **ANIMATION** between slides 1→2 |
| 5 | `coreThesis` | Digital Signal Intelligence: The Core Thesis | 1 | Two properties explanation |
| 6 | `whyNow` | Digital Signal Intelligence: Why Now? | 5 | "Go to:" intra-section navigation |
| 7 | `foundationalPrinciples` | Foundational Principles | 1 | 10 principles grid |
| 8 | `endToEndArchitecture` | End-to-End Model Architecture | 1+5 | **WORKED EXAMPLE** mini-sequence |
| 9 | `threeLayerAssessment` | Three Layer Assessment | 1+3 | Expandable Risk/Exposure/Loss details |
| 10 | `signalArchitecture` | Signal Architecture | 1+1 | **CASE STUDIES** mini-sequence |
| 11 | `competitiveDifferentiation` | Competitive Differentiation | 1 | Comparison table |
| 12 | `market` | The Market | 1 | World map visual |
| 13 | `economicImpact` | Economic Impact | 1+1 | **THREE BUTTONS** → same detail view |
| 14 | `conclusion` | Conclusion | 1 | Final summary, no Next |

**Total: 14 sections, ~23 distinct slide views**

---

## Hard Constraints

### Visual Identity
- Background: `#0B3954` (deep blue)
- Teal interactive elements: `#39D3BA`
- White content box for all pages except Landing and Orientation
- Full viewport background

### Interaction Semantics
- Teal (`#39D3BA`) = button
- Teal in blue background = section navigation (Back/Next chevrons)
- Teal in white box = intra-section navigation or special action
- Landing page is one-time only (no return after "BEGIN")

### Layout Components
1. **Header bar**: Full width, "Home" button (left), Generate logo (right), solid `#0B3954`
2. **Main background**: Full viewport `#0B3954`
3. **White content box**: Centered, max-width responsive, rounded corners, shadow
4. **Footer**: "© John Walker. All rights reserved."

---

## Detailed Slide Specifications

### 1. Landing (`landing`)
**Slide 1 of 1** - Full blue background, no white box
- Generate logo (top-left)
- Title: "Digital Signal Intelligence"
- Subtitle: "A New Information Substrate for Insurance"
- Abstract text
- IP Statement
- **"BEGIN"** button (teal) → navigates to Orientation
- Footer: "© John Walker. All rights reserved."

**Behaviour**: No header bar. Cannot return after clicking BEGIN.

---

### 2. Orientation (`orientation`)
**Slide 1 of 1** - Full blue background, no white box
- Header bar with Home button + Generate logo
- Title: "Digital Signal Intelligence"
- Subtitle: "A New Information Substrate for Insurance"
- Two side-by-side white cards:
  - **Left card**: "Learn about DSI" (lightbulb icon) - lists topics
  - **Right card**: "Interact with DSI" (hand/touch icon) - lists modules
- Footer

**Behaviour**: Home always returns here. Cards are clickable to navigate.

---

### 3. The Automation Myth (`automationMyth`)
**Slide 1 of 1** - White content box
- Title: "The Automation Myth"
- Subtitle: "Decades of Poor Returns"
- Body text about Lloyd's combined ratios
- **Chart visual**: Line graph showing 20-year performance with:
  - Break-even line (dashed)
  - 10 Year Average line
  - "A 2.49% return over a decade" callout
- Summary text:
  - "The core assumption is that traditional underwriting inputs can be automated."
  - "This assumption is incorrect."
  - "The inputs themselves are the constraint." (teal highlight)
- Back/Next chevrons

---

### 4. The Information Substrate Problem (`informationSubstrate`)
**Slide 1 of 2** - White content box
- Title: "The Information Substrate Problem"
- Subtitle: "An Insurmountable Issue"
- Body: "Traditional Insurance inputs exist in infinite formats with no canonical schema nor deterministic structure."
- **Visual**: Teal circle with "You'll recognise the maelstrom" text
- Back/Next chevrons

**Slide 2 of 2** - White content box
- Same title/subtitle
- **Visual**: Complex chaotic network diagram (documents, spreadsheets, emails, etc.)
- Body text:
  - "No extraction system, including modern or future AI models, can consistently transform these..."
  - "A system built on these inputs cannot achieve deterministic automation."
  - "Autonomous underwriting requires the information substrate to change." (teal highlight)
- Back/Next chevrons

**SPECIAL ANIMATION**: Transition from slide 1→2 should animate the circle expanding into the chaotic network.

---

### 5. The Core Thesis (`coreThesis`)
**Slide 1 of 1** - White content box
- Title: "Digital Signal Intelligence"
- Subtitle: "The Core Thesis"
- Body text explaining two properties:
  1. "How well it is managed"
  2. "How it behaves over time"
- "DSI replaces them with observable digital signals." (teal highlight)
- Extended explanation paragraph
- Back/Next chevrons

---

### 6. Why Now? (`whyNow`)
**5 slides with "Go to:" intra-section navigation**

**Slide 1 - A Revolutionary Insight**
- Title: "Digital Signal Intelligence: Why Now?"
- Intro: "DSI is not an experiment..."
- Subsection: "A REVOLUTIONARY INSIGHT"
- Table with The Challenge/The Solution/The Result (PageRank story)
- Back chevron | "Go to: Graph Propagation" button

**Slide 2 - Graph Propagation**
- Same title/intro
- Subsection: "GRAPH PROPAGATION"
- Three-column comparison: Consumer Finance (FICO), Recorded Future, Palantir/JP Morgan
- Back chevron | "Go to: The Birth of Modern AI" button

**Slide 3 - The Birth of Modern AI**
- Same title/intro
- Subsection: "THE BIRTH OF MODERN AI"
- Table: The Evolution, The Connection, The Link (Transformers)
- Back chevron | "Go to: The Next Frontier" button

**Slide 4 - The Next Frontier**
- Same title/intro
- Subsection: "THE NEXT FRONTIER"
- World Models explanation
- Back chevron | "Go to: The Bottom Line" button

**Slide 5 - The Bottom Line**
- Same title/intro
- Subsection: "THE BOTTOM LINE"
- Four points: Not Experimental, Scale, Reach, Predictive Power
- Back/Next chevrons (Next goes to foundationalPrinciples)

---

### 7. Foundational Principles (`foundationalPrinciples`)
**Slide 1 of 1** - White content box
- Title: "Foundational Principles"
- Subtitle: "Ensuring Consistent and Autonomous Operations"
- Intro text
- Two-column grid of 10 principles (1-5 left, 6-10 right)
- Tagline: "Ensuring consistency, objectivity, and agentic readiness in every assessment." (teal)
- Back/Next chevrons

---

### 8. End-to-End Model Architecture (`endToEndArchitecture`)
**Main Slide + 5 Worked Example slides**

**Main Slide**
- Title: "End-to-End Model Architecture"
- Subtitle: "Structured Workflow"
- Body text about 6 phases, 14 steps
- **Visual**: Pipeline diagram (Discovery → Instantiation → Signals/Three Layer/Pricing → Decision)
- Post-bind signal loop note (teal)
- **"See a worked example"** button
- Back/Next chevrons

**Worked Example Slide 1 - Discovery & Instantiation**
- Title remains "End-to-End Model Architecture: Structured Workflow"
- Label: "Worked Example"
- "Exit example" button (top-right)
- Shows submission: "TechFlow with domain hint TechFlow.io"
- Discovery phase details
- Model Instantiation details
- "Go to: Next Step" button

**Worked Example Slide 2 - Signals**
- Signals phase: "Parallel extraction including 35 cyber-specific signals"
- "Go to: Next Step" | "Exit example"

**Worked Example Slide 3 - Three Layer Assessment**
- Three Layer details:
  - Composite Score: 782/1000 → Tier 2
  - Exposure Band: Medium ($10M-$50M TIV)
  - Complexity Score: Moderate
  - Loss Propensity: Low (28/100)
  - Severity Propensity: Moderate (42/100)
- "Go to: Next Step" | "Exit example"

**Worked Example Slide 4 - Pricing**
- Pricing details:
  - Final Premium ($5M limit): $20,250
  - Base Rate: 0.45% of Limit
  - Loss Modifier: 0.90
- "Go to: Next Step" | "Exit example"

**Worked Example Slide 5 - Decision**
- Full pipeline visual with Decision outcome:
  - AUTO-APPROVE (Tier 2, confidence 0.87, no triggers)
  - Total processing time: 47 seconds
  - Full audit trail persisted
- Next chevron | "Exit example"

---

### 9. Three Layer Assessment (`threeLayerAssessment`)
**Main Slide + 3 Detail slides**

**Main Slide**
- Title: "Three Layer Assessment"
- Subtitle: "Decoupling Complexity for Absolute Clarity"
- Body explaining separation of analytical dimensions
- Three expandable rows with "+" buttons:
  - **Risk**: "Utilising a PageRank-inspired digital signal citation framework..."
  - **Exposure**: "A deterministic inference of an organisation's exposure..."
  - **Loss**: "Correlating real-time signal behaviours with historical loss patterns..."
- Tagline (teal)
- Back/Next chevrons

**Risk Analysis Detail**
- "Exit detail" button
- Title: "Risk Analysis"
- 6 dimensions listed with explanations
- Back/Next chevrons

**Loss Correlation Layer Detail**
- "Exit detail" button
- Title: "Loss Correlation Layer"
- 4 dimensions with cohort explanation
- Back/Next chevrons

**Exposure Shadow Layer Detail**
- "Exit detail" button
- Title: "Exposure Shadow Layer"
- 2 dimensions listed
- Back/Next chevrons

---

### 10. Signal Architecture (`signalArchitecture`)
**Main Slide + 1 Case Studies slide**

**Main Slide**
- Title: "Signal Architecture"
- Subtitle: "Canonical Categorisation"
- Body about 7 canonical categories
- **Visual**: 7 grey boxes (Network Authority, Technical Infrastructure, Corporate Footprint, Behaviour, Public Record, Structured Data, Direct Inquiry) flowing into "Risk Profile" circle
- **"See how signals would have caught historic losses"** button
- Tagline (teal)
- Back/Next chevrons

**Retrospective Case Studies Slide**
- "Exit case-studies" button
- Title: "Retrospective Case-Studies"
- Explanation about canonical categories
- 5 case study cards in 2 columns:
  - Marine: Shadow Fleet (DECLINE)
  - Energy: Deepwater Horizon (REFER + LOAD)
  - Financial Institutions: SVB (DECLINE)
  - Cyber: SolarWinds (DECLINE)
  - Aerospace: Boeing 737 MAX (REFER)
- Next chevron

---

### 11. Competitive Differentiation (`competitiveDifferentiation`)
**Slide 1 of 1** - White content box
- Title: "Competitive Differentiation"
- Subtitle: "Why the Traditional Model Fails Where DSI Wins"
- Body intro
- **Comparison table** (5 rows):
  | Feature | Traditional | Digital Signal Intelligence |
  |---------|-------------|----------------------------|
  | Input | Submissions (PDFs, Excel, Word) | Digital Ecosystem |
  | Process | Manual, OCR, NLP | Deterministic Processing |
  | Integrity | High "Manual Noise" ratio | Zero-Touch, Audit-Persistent |
  | Adjustment | Subjective Overrides | Rule-Based Deterministic Modifiers |
  | Scalability | Limited by manual "Stare & Compare" | Unlimited Agentic Readiness |
- Two closing statements (second in teal)
- Back/Next chevrons

---

### 12. The Market (`market`)
**Slide 1 of 1** - White content box
- Title: "The Market"
- Subtitle: "A $1.8 Trillion Global Market — Ready for a New Substrate"
- Body about universal digital footprint
- Coverage list: PI, FI, D&O, Cyber, Aerospace, Marine, Energy
- **Visual**: World map made of people + network lines
- AI Builder note
- Tagline (teal)
- Back/Next chevrons

---

### 13. Economic Impact (`economicImpact`)
**Main Slide + 1 Detail slide**

**Main Slide**
- Title: "Economic Impact"
- Subtitle: "Improvements across the board"
- Projections disclaimer
- Three metric rows with "See the details" buttons:
  - **Expense Ratio**: "~22 points reduction"
  - **Loss Ratio**: "6-12 points improvement"
  - **Operational Metrics**: "logarithmic vs linear scaling"
- Bottom line: "$130M–$170M in improved profit" (teal)
- Back/Next chevrons

**Detail Slide** (opened by ANY of the 3 buttons)
- "−" close button (returns to main)
- Same title/subtitle
- **Full metrics table**:
  | Cohort | Metric | Traditional | DSI Target |
  |--------|--------|-------------|------------|
  | Expense Ratio | Staff Costs | 12% | 4% |
  | ... | Office and Infrastructure | 8% | 2% |
  | ... | Administration | 4% | 1% |
  | ... | Brokerage and Commissions | 11% | 6% |
  | ... | Total | 35% | 13% |
  | Loss Ratio | Loss Signal Correlation | - | 4-8 points |
  | ... | Continuous Calibration | - | 2-4 points |
  | ... | Total | - | 6-12 points |
  | Operational | Cost per submission | $150-650 | <$10 |
  | ... | Straight-through rate | 5-15% | 60-80% |
  | ... | Time to quote | 3-10 days | <60 seconds |
  | ... | Scalability | Linear (headcount) | Logarithmic (compute) |

---

### 14. Conclusion (`conclusion`)
**Slide 1 of 1** - White content box
- Title: "Conclusion"
- Subtitle: "The Future of Insurance is Agentic"
- "Digital Signal Intelligence externally observable, machine-readable signals enable:"
- Bullet list (6 items)
- Statement about insurers reducing headcount
- DSI value proposition (teal)
- World Model closing paragraph
- Back chevron only (no Next)

---

## Navigation Logic

### Global Functions
```javascript
goToSection(sectionId, slideIndex = 0)  // Navigate to section
goToNextSection()                        // Next in sequence
goToPreviousSection()                    // Previous in sequence
goToSlide(sectionId, slideIndex)         // Specific slide
goToNextSlideInSection()                 // Next slide within section
goToPreviousSlideInSection()             // Previous slide within section
```

### Section Order
```javascript
const SECTIONS = [
  'landing',            // 0 - not in main nav
  'orientation',        // 1 - Home destination
  'automationMyth',     // 2
  'informationSubstrate', // 3
  'coreThesis',         // 4
  'whyNow',             // 5
  'foundationalPrinciples', // 6
  'endToEndArchitecture',   // 7
  'threeLayerAssessment',   // 8
  'signalArchitecture',     // 9
  'competitiveDifferentiation', // 10
  'market',             // 11
  'economicImpact',     // 12
  'conclusion'          // 13
];
```

### Special Navigation Rules
- Landing → Orientation (one-way)
- Home button → Orientation (never Landing)
- "Exit example/detail/case-studies" → Returns to parent slide
- Conclusion has no Next (end of Learn About DSI)

---

## Implementation Phases

### Phase 19.1.A: Foundation
1. HTML structure with header, main, footer
2. Navigation state machine
3. Section/slide routing
4. CSS for blue background, white content box
5. Header with Home button + logo placeholder

### Phase 19.1.B: Landing & Orientation
1. Landing page (full blue, BEGIN button)
2. Orientation page (two-pillar cards)
3. One-way navigation from Landing

### Phase 19.1.C: Simple Single-Slide Sections
1. `automationMyth` (with chart)
2. `coreThesis`
3. `foundationalPrinciples` (10-item grid)
4. `competitiveDifferentiation` (table)
5. `market` (visual placeholder)
6. `conclusion`

### Phase 19.1.D: Information Substrate (with animation)
1. Two slides with circle → network transition
2. Animation implementation

### Phase 19.1.E: Why Now (5-slide sequence)
1. Five slides with "Go to:" buttons
2. Intra-section navigation

### Phase 19.1.F: End-to-End Architecture (worked example)
1. Main slide with pipeline visual
2. Five worked example slides
3. Entry/exit navigation

### Phase 19.1.G: Three Layer Assessment (expandable)
1. Main slide with 3 expandable rows
2. Three detail slides
3. Open/close mechanics

### Phase 19.1.H: Signal Architecture (case studies)
1. Main slide with 7-category visual
2. Case studies slide
3. Entry/exit navigation

### Phase 19.1.I: Economic Impact (detail toggle)
1. Main slide with 3 buttons
2. Detail table slide
3. All buttons open same detail

---

## Approval Checklist

- [ ] Section structure confirmed (14 sections)
- [ ] Slide counts confirmed per section
- [ ] Special behaviours understood
- [ ] Navigation logic approved
- [ ] Ready to proceed with implementation

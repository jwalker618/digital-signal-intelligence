# Phase 19.2.1 — World Model Enhancements
### Extending the Interactive Demo to Demonstrate True World Model Capability

## Purpose

Phase 19.2 delivered a compelling interactive demo showcasing DSI’s core capabilities: discovery, assessment, simulation, portfolio impact, and underwriting.

Phase 19.2.1 elevates the demo by introducing the defining characteristics of a proprietary **World Model**. It transforms the demo from a set of interactive modules into a living, evolving simulation where the user is an active agent, not just an observer.

The goal: **Make the user feel the World Model — not just see its outputs.**

---

# 1. Temporal Dynamics Layer  
### “Organisations are not snapshots — they are trajectories.”

## Objective  
Introduce time as a first‑class dimension. Allow users to see how profiles evolve and, critically, allow them to **audit the past**.

## Features

### 1.1 Temporal Playback  
A timeline slider (e.g., 12–24 months) that animates:

- Hiring trends  
- Tech stack changes  
- Network authority shifts  
- Behavioural anomalies  
- Loss propensity drift  
- Cohort migration  

### 1.2 Time‑Travel Audit (“Versioned Reality”)  
A compliance and claims‑defence feature that operationalises temporal truth.

- **Revert Button**: User selects a historical policy inception date.  
- **World State Restoration**: The entire UI (signals, scores, graphs) reverts to *exactly* what was known at that moment.  
- **Delta Overlay**: Highlights *“What we knew then”* vs. *“What we know now”*.  
  - Example: “At time of underwriting, the Log4j vulnerability was unknown.”

## Why It Matters  
This proves the model is a **record of truth**.  
It answers the hardest question in claims disputes:  
**“What was the state of the world when you signed the contract?”**

---

# 2. Agency & Feedback Layer  
### “The world reacts to you. This is two‑way causality.”

## Objective  
Demonstrate that the World Model understands the insurer is an **agent** within the system.  
Show the second‑order effects of the user’s decisions.

## Features

### 2.1 Price Elasticity Simulation  
- User adjusts the “Margin / Load” slider.  
- The **Win Probability** metric updates in real time based on competitive density.  
- Demonstrates commercial consequence of pricing decisions.

### 2.2 Broker Sentiment Loop  
- Declining multiple risks from the same broker reduces a **Broker Relationship Signal**.  
- Future submission flow volume decreases (e.g., −5%).  
- Shows that underwriting decisions influence future deal flow.

## Why It Matters  
This is the moment the user realises the system isn’t just a calculator — it’s a **strategy engine**.

---

# 3. Causal Pathways Layer  
### “Not correlation. Causation.”

## Objective  
Reveal the causal structure of the World Model.  
Show *why* shocks propagate the way they do.

## Features

### 3.1 Causal Chain Visualisation  
When a shock occurs, highlight:

- The causal path (A → B → C)  
- Mediating signals  
- Amplifiers and dampeners  
- **Root Cause Explorer**: Click a degraded score to see the originating event  
  - Example: “Score degraded due to upstream cloud provider outage.”

## Why It Matters  
This differentiates DSI from “black box” AI.  
It provides **explanatory AI** that underwriters can trust.

---

# 4. Counterfactual Simulation Layer  
### “Explore alternate futures.”

## Objective  
Allow users to explore “what could have happened” — moving beyond prediction into simulation.

## Features

### 4.1 Counterfactual Toggles  
Simulate alternate histories:

- “What if the CISO had not resigned?”  
- “What if the vulnerability had been patched earlier?”  
- “What if we had applied the Secure Gateway warranty?”  

### 4.2 Counterfactual Graph Overlay  
Visualise divergence between:

- **Actual Path** (Crisis)  
- **Counterfactual Path** (Stability)  

Quantifies the value of risk mitigation.

## Why It Matters  
This reframes the insurer as a **risk partner**, not just a payer.

---

# 5. Emergent Behaviour Layer  
### “Risk emerges from interactions. Capital pays for it.”

## Objective  
Reveal system‑level behaviours, anchored in **financial consequence**.

## Features

### 5.1 Capital‑Anchored Cluster Detection  
- Graph identifies hidden clusters (e.g., “Shared Dependency: AWS us‑east‑1”).  
- Immediately displays **Capital Impact**:  
  - “New correlation detected. Portfolio Capital Requirement increased by $4.2M.”

### 5.2 Systemic Fragility Index  
A real‑time gauge showing how “brittle” the portfolio is to cascading failure.

## Why It Matters  
It moves the conversation from “tech” to **balance sheet protection**.

---

# 6. Stateful Memory Layer & Active Learning  
### “The model learns. It evolves. You teach it.”

## Objective  
Carry state forward across modules and prove the system gets smarter with human interaction.

## Features

### 6.1 Persistent State  
If a risk is downgraded in Module 3 (Simulation), it remains downgraded in Module 5 (Underwriting).  
The system has **memory**.

### 6.2 Active Learning (“Teacher Mode”)  
- User right‑clicks a signal and marks it as “Incorrect.”  
- The system acknowledges the correction.  
- **Brain Update**:  
  - “Source reliability downgraded. Re‑assessing confidence scores for 14 other portfolio companies using this source…”

## Why It Matters  
This turns the “black box” problem into a **co‑pilot** solution.

---

# 7. Two‑Way Causality (Explicit Definition)

A true World Model must simulate:

1. **How the world affects the insurer**  
2. **How the insurer affects the world**

This includes:

- Pricing decisions  
- Declines and referrals  
- Broker relationships  
- Portfolio composition  
- Market behaviour  
- Regulatory changes  

Every action the user takes alters the state of the world, which in turn alters future decisions.

This is the leap from *model* to **World Model**.

---

# 8. Second‑Order Effects (Illustrative Example)

A decline decision triggers:

1. Decline →  
2. Broker sentiment decreases →  
3. Submission flow reduces →  
4. Selection bias increases →  
5. Portfolio volatility rises →  
6. Capital requirement increases  

This demonstrates **compounding causal chains**.

---

# 9. Integration Summary

Phase 19.2.1 augments the base demo with these specific “World Model” loops:

| Module | Enhancement | User “Aha!” Moment |
|--------|-------------|--------------------|
| **Discover** | Active Learning | “I can teach it. It gets smarter.” |
| **Understand** | Time‑Travel Audit | “It can defend any decision I made.” |
| **Predict** | Causal Pathways | “It explains *why* the risk is changing.” |
| **Decide** | Market Reaction | “It understands the commercial consequences.” |
| **Portfolio** | Capital Anchoring | “It protects the balance sheet.” |

---

# 10. Development Sequence

Phase 19.2.1 should be executed **after** Phase 19.2 is complete.

Recommended order:

1. Temporal Dynamics Layer  
2. Causal Pathways Layer  
3. Counterfactual Simulation Layer  
4. Emergent Behaviour Layer  
5. Stateful Memory & Active Learning Layer  

Each layer is modular and can be added incrementally.

---

# 11. Success Criteria

Phase 19.2.1 is successful when the user concludes:

1. **It is Alive** — the system reacts to them.  
2. **It is Accountable** — it can prove what it knew in the past.  
3. **It is Teachable** — it improves via expert input.  

This shifts perception from **“Advanced Analytics Tool”** to **“Insurance Operating System.”**


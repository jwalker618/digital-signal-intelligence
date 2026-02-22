# Phase 4: Adaptive Intelligence, Causal World Model Integration, and Production UI

## Context & Objectives
With the foundational architecture, Rust-based Organisational Graph, and Multiplexer natively executing, Version 4 transitions DSI from a static pricing engine to an adaptive, learning system with a fully realized user interface.

This phase focuses on four pillars:
1. **Telemetry & Causal Capture**: Storing temporal graph snapshots and interaction metadata for downstream AI use.
2. **In-Process ML Retuning**: Rigorous, explainable automation for optimizing `config.yaml` weights and identifying signal gaps.
3. **API Expansion**: Enhancing the FastAPI layer to support seamless, real-time analytics and World Model interaction.
4. **Frontend Build-out**: Constructing the production Single Page Application (SPA) for underwriters and actuaries.

---

## Pillar 1: Data Storage & Causal World Model Capture
*Goal: Correctly store and capture all interactions/relationships to enable in-process retuning and World Model simulations.*

Currently, DSI captures `ModelVersionRecord` and `AuditLog`. To power the Causal World Model, we need to capture **Temporal Graph Snapshots** and **Counterfactual Telemetry**.

### 1.1 Temporal Graph Snapshots
Instead of merely saving the final PageRank score, we must persist the state of the `organisational_graph` at the exact moment of binding. 
* **Mechanism**: When a submission is converted to a bound quote, serialize the Rust graph output (nodes, edges, derivatives) and push to a scalable storage layer (e.g., PostgreSQL JSONB or a dedicated Graph DB like Neo4j).
* **Why**: When a loss occurs 12 months later, the ML engine needs to reconstruct the exact network topology that existed at bind to understand *why* the loss propagated.

### 1.2 Feedback Loop & Interaction Telemetry
We must capture *why* an underwriter deviated from the DSI recommendation to identify gaps in the signal registry.
* **Implementation**: Expand the `Referral` and `AuditLog` schemas to include `override_telemetry`.
* **Example Capture**:

```json
  {
    "submission_id": "sub-123",
    "dsi_recommended_tier": 2,
    "underwriter_assigned_tier": 4,
    "reason_code": "UNOBSERVED_RISK",
    "underwriter_notes": "Client uses legacy mainframe not exposed to public internet, but disclosed in meeting."
  }
```

Impact: The ML engine parses UNOBSERVED_RISK logs to flag areas where a new Signal Extractor is required.

## Pillar 2: Rigorous In-Process AI / ML Retuning
Goal: Ensure all ML retuning is rigorous, valuable, and maintains actuarial explainability (via YAML config modification).

We will not use "black box" ML. Instead, ML will act as a co-pilot that suggests rigorous re-weightings to the deterministic config.yaml files.

### 2.1 The Automated Configuration Optimization Engine (ACOE)
Expand the existing analytics.signal_analytics.SignalPerformance module.

The Process:

1. The ACOE continuously runs a Gradient Boosting model (like XGBoost) in the background, treating the 50+ signals as features and actual loss_ratio as the target.
2. It calculates feature importance and partial dependence.
3. It compares its findings against the current config.yaml weights (e.g., if the YAML weights network_authority at 0.15, but ACOE finds it holds 0.30 of the predictive power).

**The Output: The engine generates a proposed patch to the config.yaml.**

```yaml
# ACOE Proposed Change for cyber_general
network_authority:
  risk:
    weight: 0.15 -> 0.22  # +0.07 (Confidence: 94%, Gini Lift: +0.03)
```

### 2.2 Signal Gap Identification via Anomaly Detection
* Implementation: Run unsupervised clustering (e.g., DBSCAN or Isolation Forests) on "False Negatives" (entities that scored Tier 1 but suffered severe losses).
* Actionable Output: If the ML identifies a cluster of Tier 1 manufacturing clients experiencing losses, it flags this as a "Signal Registry Gap." It indicates that the current 50 extractors are blind to a specific operational dimension (e.g., OT/IT convergence security), prompting the engineering team to build a new extractor.

## Pillar 3: API Structure Refinement
Goal: Ensure all relevant items can be interacted with seamlessly by the new UI and ML modules.

The API will be expanded from transactional endpoints to analytical and simulation endpoints.

### 3.1 New Endpoint Architecture
Add the following routers to infrastructure/api/routes/:

* GET /api/v2/analytics/tuning-proposals
  Returns the ACOE's mathematically backed suggestions for config.yaml changes, including backtested "Before vs. After" portfolio loss ratios.

* POST /api/v2/world-model/simulate
  Allows the frontend to pass hypothetical signals or graph edges (e.g., "What if this client acquires company X?") and runs the Rust PageRank and scoring layers in memory, returning the theoretical Tier and Premium change in <100ms.

* GET /api/v2/signals/gap-analysis
  Exposes the anomaly detection results, listing clusters of unexpected losses to guide product development.

### 3.2 GraphQL Integration (Optional but Recommended)
Given the highly relational nature of the Causal World Model (Entities -> Edges -> Risks -> Pricing -> Quotes), introducing a GraphQL layer (via Strawberry in FastAPI) will allow the new frontend to seamlessly query deep relationships without over-fetching.

## Pillar 4: Frontend Build-out
Goal: Begin building the exact frontend that users will interact with.

We will transition away from the static HTML files in demo/ to a modern React + TypeScript + TailwindCSS Single Page Application (SPA).

### 4.1 Tech Stack Recommendation
* Framework: Next.js (React) or Vite.
* State Management: Zustand or Redux (for complex what-if scenario states).
* Graph Visualization: react-force-graph (WebGL accelerated) to render the Causal World Model nodes and edges.
* Styling: TailwindCSS with shadcn/ui for clean, data-dense financial interfaces.

### 4.2 Core User Interfaces

View A: The Underwriter Workbench (Daily Execution)
* Layout: Split screen.
  * Left: Submission details, final Tier, Recommended Premium, and Auto-Approve/Referral decision.
  * Right: The "Signal Cascade". A collapsible tree showing exactly how the Three-Layer Assessment (Risk, Loss, Exposure) was calculated.
  * Interaction: Underwriters can click on any flagged signal (e.g., MFA not enabled) to see the raw extractor evidence. They can input an override, which immediately triggers the telemetry capture defined in Pillar 1.

View B: The Causal World Model Explorer (Deep Risk Analysis)
* Layout: Full-screen 3D/2D force-directed graph.
  * Interaction: Focuses on a target entity node. Visually maps first, second, and third-degree connections (supply chain, shared technology, common investors).
  * Use Case: An underwriter sees that a prospective client shares an IT provider with three other companies that recently filed claims. The graph visualises this "blast radius" dynamically.

View C: Actuarial Retuning Dashboard (The ML Interface)
* Layout: Analytics dashboard.
  * Interaction: Actuaries view the ACOE tuning proposals. The UI shows two ILF/Pricing curves: the Current Config and the ML-Proposed Config.
  * Action: Actuaries can hit "Accept Proposal," which automatically updates the underlying YAML file via the Builder CLI logic, hashes it (content-addressable storage), and versions the model without requiring a developer.

# Referral & Exception Methodology

| Item | Value |
| :--- | :--- |
| Version | 1.0 |
| Date | February 2026 |
| Classification | Core Methodology |

## 1. Overview
In the Digital Signal Intelligence (DSI) framework, the traditional concept of an underwriting "referral" has been fundamentally redesigned. 

Historically, a referral initiated a price negotiation, ending with a subjective "schedule credit" or discount applied by an underwriter to win the business. In DSI, this is architecturally prohibited. The DSI Whitepaper states unequivocally: **"No subjective adjustments are permitted"**.

The core formula—$P_{final} = (B \times R) \times ILF \times D_{fac} \times Mods$—must remain mathematically pure. If subjective price adjustments are allowed, the system can no longer mathematically correlate the input signals to the eventual loss ratio, destroying the ability to train AI and refine models.

Therefore, in DSI, underwriters do not negotiate *outputs* (the premium). They audit and correct *inputs* (the signals).

## 2. The Two Paths of a Referral
When a risk is referred to an underwriter (e.g., it hits a Tier 4 "SUBSTANDARD" score, or triggers a specific direct query), the underwriter has two distinct paths:

### Path A: Factual Signal Override (Correcting the Machine)
Often, a risk is referred because the DSI inference engine pulled outdated or incorrect data from an external provider. 
* **The Process:** The underwriter reviews the Signal Ledger. If they identify a factual error (e.g., the system flagged a "Pending Lawsuit", but the underwriter has proof it was dismissed yesterday), they execute a **Signal Override**.
* **The Requirement:** They must provide the corrected fact and attach a verified rationale.
* **The Result:** The DSI engine automatically runs a new **Model Cycle**. The math engine recalculates the entire risk profile based on the new, true data. The premium adjusts organically, and the referral often clears itself.
* **Why this matters:** The original machine extraction is preserved in the database alongside the human correction. This allows us to track the exact error rates of our external data providers and improve the ingestion engine over time.

### Path B: Contextual Decision (Accepting the Machine's Math)
If the underwriter reviews the Signal Ledger and determines that the machine's data is 100% factually correct, the model's math stands. 
* **The Process:** The underwriter evaluates the context of the risk outside of the digital signals. (e.g., "The client has a poor historical safety record, but they were just acquired by a best-in-class operator.")
* **The Requirement:** The underwriter cannot change the premium. They must enter a mandatory rationale explaining their business decision, and then click **Approve** or **Decline**. 
* **The Result:** If approved, the quote is issued at the exact, elevated premium calculated by the model's penalty modifiers. 

## 3. Auditability and Model Versions
Every time a signal is overridden or a decision is made, DSI generates a new **Model Version**. 

Version 1 represents the pure, autonomous machine view. Version 2 represents the human-audited view. This ensures total transparency for capacity providers, reinsurers, and portfolio managers, permanently ending the "black box" of subjective underwriting discounts.

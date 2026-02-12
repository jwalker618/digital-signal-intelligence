# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Premium Calculation Methodology

| Item | Value |
|-|-|
|Version|1.0|
|Date|February 2026|
|Classification|Methodology|

---

## 1. Overview
The DSI Pricing Engine uses a **"Base × Modifiers"** approach, augmented by **Anchored Relativities**. This ensures that pricing scales logically across different client sizes (SME to Enterprise) and coverage choices (Limits/Deductibles).

The core philosophy is: **"Define the price of the Anchor Unit, then scale relative to it."**

---

## 2. The Core Formula

The final premium ($P_{final}$) is calculated as:

$$P_{final} = \underbrace{(B \times R)}_{\text{Base}} \times \underbrace{\frac{ILF_{req}}{ILF_{ref}}}_{\text{Limit}} \times \underbrace{D_{fac}}_{\text{Ded}} \times \underbrace{M_{risk} \times M_{loss} \times M_{exp}}_{\text{Modifiers}}$$

### Components:
1.  **Basis ($B$):** The exposure unit (Revenue, TIV) OR 1 (for Flat Rated).
2.  **Rate ($R$):** The Risk Tier Rate (e.g., 0.10%) OR Flat Premium ($1,500).
3.  **Limit Relativity ($ILF$):** Scaling for higher/lower limits.
4.  **Deductible Factor ($D$):** Credit/Load for deductible choice.
5.  **Modifiers ($M$):** DSI Signal outputs for Risk, Loss, and Exposure.

---

## 3. Calculation Methods

The engine supports two primary methods for determining the **Base ($B \times R$)**:

### Method A: PREMIUM_BASE (Fixed)
*Used for: SME, Micro-Business, Professional Indemnity*
* **Logic:** The "Basis" is effectively 1.0. The "Rate" is a flat dollar amount.
* **Example:** Tier 1 Price = $1,500.
* **Why:** For small risks, data collection (Revenue/Payroll) adds friction, and exposure variance is low.

### Method B: MULTIPLIER (Rate-Based)
*Used for: Corporate Cyber, Energy, Tech E&O*
* **Logic:** Price is a percentage of the client's size.
* **Example:** Tier 1 Rate = 0.10% (10 bps). Basis = $100M Revenue.
* **Base Price:** $100,000.
* **Why:** Essential for risks where "Size" is the primary driver of maximum probable loss.

---

## 4. Anchoring & Relativity (The Phase 5 Update)

To make Rate-Based pricing work, we must define **what coverage the rate buys**. This is the **Anchor Point**.

### The Anchor Definition
Defined in `config.yaml`:
```yaml
pricing:
  base_limit_reference: 1000000      # $1M Limit
  base_deductible_reference: 50000   # $50k Deductible
```

***Meaning:***  "The calculated Base Price purchases a $1M Limit with a $50k Deductible.

**Scaling Logic**
If the user requests a $5M Limit with a $100k Deductible:

1. **Limit Scaling:**
  * Anchor ILF ($1M) = 1.00
  * Requested ILF ($5M) = 3.50
  * Multiplier = $3.50 / 1.00 = \mathbf{3.50}$

2. **Deductible Scaling:**
  * Anchor Factor ($50k) = 1.00
  * Requested Factor ($100k) = 0.85
  * Multiplier = $\mathbf{0.85}$

Result: The premium is $3.50 \times 0.85 = \mathbf{2.975} \times$ the Base Price.

## 5. Pricing Towers (Corporate Structure)

For large risks, pricing is often constructed in Layers.
* Primary Layer: The first $X million of coverage. (Calculated using the Base Rate).
* Excess Layers: Coverage above the primary. (Calculated using ILF curves).

The DSI engine handles this natively via the ILF Curve.
* The curve represents the cumulative price of the tower.
* Price of Layer $X$ to $Y$ = Price($Y$) - Price($X$).

## 6. Modifier Application
Modifiers are applied multiplicatively to the Scaled Base Premium.

|Modifier|Source|Direction|
|-|-|-|
|Exposure Size|exposure.size|"< 1.0 (Volume Discount) or > 1.0 (Surcharge). In Rate-based pricing, this usually provides a ""Log-Linear"" discount for scale."|
|Loss Propensity|loss.bands|"0.80 - 1.40. Adjusts for frequency/severity signals (e.g., Backups, MFA)."|
|Complexity|exposure.complexity|"> 1.0. Surcharge for difficult operations (e.g., Multi-jurisdiction)."|

## 7. Summary of Logic Flow

1. **Determine Tier:** Signals $\rightarrow$ Risk Score $\rightarrow$ Tier Band $\rightarrow$ Base Rate.
2. **Calculate Base:** Base Rate $\times$ Client Revenue = Anchor Premium.
3. **Scale Coverage:** Anchor Premium $\times$ ILF Relativity $\times$ Deductible Factor = Technical Premium.
4. **Apply Modifiers:** Technical Premium $\times$ Size $\times$ Loss $\times$ Complexity = Final Technical Price.
5. **Apply Constraints:** Check Min Premium and Limit Capacity rules.

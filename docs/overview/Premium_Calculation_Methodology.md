# Digital Signal Intelligence (DSI)

## Premium Calculation Methodology

| Item | Value |
|-|-|
|Version|2.0|
|Date|February 2026|
|Classification|Methodology|
|Schema Version|v2.2|

---

## 1. Overview
The DSI Pricing Engine uses a **"Base × Modifiers"** approach, augmented by **Anchored Relativities**. This ensures that pricing scales logically across different client sizes (SME to Enterprise) and coverage choices (Limits/Deductibles).

The core philosophy is: **"Define the price of the Anchor Unit, then scale relative to it."**

---

## 2. The Core Formula

The final premium ($P_{final}$) is calculated as:

$$P_{final} = \underbrace{(B \times R)}_{\text{Base}} \times \underbrace{\frac{ILF_{req}}{ILF_{ref}}}_{\text{Limit}} \times \underbrace{D_{fac}}_{\text{Ded}} \times \underbrace{M_{risk} \times M_{loss} \times M_{exp}}_{\text{Modifiers}}$$

### Components:
1.  **Basis ($B$):** The exposure unit (Revenue, TIV, etc) OR 1 (for Flat Rated).
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

## 4. Anchoring & Relativity 

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

Result: The premium is $3.50 \times 0.85 = \mathbf{2.975}\times$ the Base Price.

### Deductible Factor Table

The `deductible_factors` table defines the pricing adjustment for each deductible option. The anchor deductible always has a factor of 1.00.

```yaml
pricing:
  base_deductible_reference: 50000  # Anchor = $50k
  deductible_factors:
    - deductible: 25000    # Lower ded = premium loading
      factor: 1.15         # +15%
    - deductible: 50000    # Anchor deductible
      factor: 1.00         # Base price
    - deductible: 100000   # Higher ded = premium credit
      factor: 0.85         # -15%
    - deductible: 250000
      factor: 0.70         # -30%
    - deductible: 500000
      factor: 0.55         # -45%
```

**Key Principle:** Lower deductibles increase premium (factor > 1.0), higher deductibles decrease premium (factor < 1.0). The anchor deductible is the reference point where factor = 1.00.

---

## 5. Pricing Towers (Corporate Structure)

For large risks, pricing is often constructed in Layers.
* Primary Layer: The first $X million of coverage. (Calculated using the Base Rate).
* Excess Layers: Coverage above the primary. (Calculated using ILF curves).

The DSI engine handles this natively via the ILF Curve.
* The curve represents the cumulative price of the tower.
* Price of Layer $X$ to $Y$ = Price($Y$) - Price($X$).

---

## 5a. Limit & Deductible Configuration

All DSI configurations use a **DECOUPLED** limit/deductible structure via `limit_configuration`. This allows clients to independently select their preferred limit and deductible from predefined valid options.

### Configuration Structure
```yaml
limit_configuration:
  type: "DECOUPLED"
  valid_limits:
    - 1000000      # $1M
    - 2000000      # $2M
    - 5000000      # $5M
    - 10000000     # $10M
  valid_deductibles:
    - 10000        # $10k
    - 25000        # $25k
    - 50000        # $50k
    - 100000       # $100k
```

### Rationale
The DECOUPLED approach provides:
1. **Flexibility:** Clients can select the exact limit/deductible combination that fits their risk tolerance and budget.
2. **Transparency:** Pricing scales predictably via ILF curves and deductible factors.
3. **Consistency:** All coverages use the same structural approach, simplifying the pricing engine.

**Note:** Legacy "bundled" (menu-style) configurations where limits and deductibles were locked together have been deprecated. The decoupled structure with anchor-based relativities provides superior flexibility and actuarial integrity.

---

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

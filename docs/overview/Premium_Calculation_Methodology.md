# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Premium Calculation Methodology

| Item | Value |
|-|-|
|Version|3.0|
|Date|March 2026|
|Classification|Methodology|
|Schema Version|v2.3|

---

## 1. Overview
The DSI Pricing Engine uses a **"Base × Modifiers"** approach, augmented by **Anchored Relativities**. This ensures that pricing scales logically across different client sizes (SME to Enterprise) and coverage choices (Limits/Deductibles).

The core philosophy is: **"Define the price of the Anchor Unit, then scale relative to it."**

### Technical vs Commercial Separation

DSI separates pricing into two distinct concerns:

1. **Technical Premium** — the actuarially-derived price in USD, computed by the pricing engine using signals, modifiers, ILF curves, and deductible factors. This is currency-neutral and entity-agnostic.
2. **Commercial Premium** — the offered price in the entity's base currency, incorporating distribution economics (commission, taxes, fronting fees), FX conversion, and underwriter discretion. This is governed by the Commercial Entity schema (see [Commercial Entity Schema](Commercial_Entity_Schema.md)).

The pricing engine computes the technical premium. The `PremiumAssembler` then transforms it into a gross and offered premium using the commercial entity's terms.

---

## 2. The Core Formula

The final technical premium ($P_{tech}$) is calculated as:

$$P_{tech} = \underbrace{(B \times R)}_{\text{Base}} \times \underbrace{\frac{ILF_{req}}{ILF_{ref}}}_{\text{Limit}} \times \underbrace{D_{fac}}_{\text{Ded}} \times \underbrace{M_{risk} \times M_{loss} \times M_{exp}}_{\text{Modifiers}}$$

### Components:
1.  **Basis ($B$):** The exposure unit (Revenue, TIV, etc) OR 1 (for Flat Rated).
2.  **Rate ($R$):** The Risk Tier Rate (e.g., 0.10%) OR Flat Premium ($1,500).
3.  **Limit Relativity ($ILF$):** Scaling for higher/lower limits.
4.  **Deductible Factor ($D$):** Credit/Load for deductible choice (see §4a).
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

## 4a. Deductible Interpolation

When a submission requests a deductible that does not exactly match a reference point in the `deductible_factors` table, the engine applies **log-linear interpolation** between the two nearest reference deductibles.

### Why Log-Linear?

Deductible factors follow a concave relationship — the marginal credit for increasing a deductible from \$50k to \$100k is larger than from \$250k to \$300k. A log-linear model captures this curvature naturally:

$$D_{fac} = D_{lo} \times \left(\frac{D_{hi}}{D_{lo}}\right)^{t}$$

where:

$$t = \frac{\ln(d / d_{lo})}{\ln(d_{hi} / d_{lo})}$$

- $d$ is the requested deductible
- $d_{lo}$, $d_{hi}$ are the bracketing reference deductibles
- $D_{lo}$, $D_{hi}$ are their corresponding factors

### Boundary Behaviour

| Condition | Behaviour |
|-|-|
| Exact match in table | Return factor directly (fast path) |
| Below lowest reference | Clamp to lowest factor (no extrapolation) |
| Above highest reference | Clamp to highest factor (no extrapolation) |
| Between two references | Log-linear interpolation |

### Example

Given references at \$50k (1.00) and \$100k (0.85), a \$75k deductible:

$$t = \frac{\ln(75000 / 50000)}{\ln(100000 / 50000)} = \frac{\ln(1.5)}{\ln(2.0)} \approx 0.585$$

$$D_{fac} = 1.00 \times (0.85 / 1.00)^{0.585} \approx 0.909$$

This replaces the previous exact-match-only lookup, allowing any deductible within the reference range to be priced smoothly.

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

DSI supports two limit/deductible configuration modes via `limit_configuration`. The `type` field determines which mode applies and how the pricing engine processes limit/deductible selection.

### Mode 1: BUNDLED (Menu Pricing)

**Use case:** SME (Small & Medium Enterprise) segments where simplified selection is preferred.

```yaml
limit_configuration:
  type: "BUNDLED"
  packages:
    - id: 1
      label: "STARTER"
      limit: 250000
      deductible: 10000
    - id: 2
      label: "STANDARD"
      limit: 500000
      deductible: 25000
    - id: 3
      label: "PREMIUM"
      limit: 1000000
      deductible: 50000
```

**Characteristics:**
- Fixed limit/deductible combinations in predefined packages
- Simpler client selection (choose a package label rather than individual values)
- Each package has a unique `id` and human-readable `label`
- Pricing engine uses the package's limit/deductible directly without ILF/deductible factor scaling

### Mode 2: DECOUPLED (Tower Pricing)

**Use case:** Corporate/General segments requiring flexible limit and deductible selection.

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

**Characteristics:**
- Independent limit and deductible selection from valid options
- Pricing scales via ILF curves (for limits) and deductible factors (with interpolation)
- Maximum flexibility for sophisticated buyers
- Requires anchor references (`base_limit_reference`, `base_deductible_reference`) in pricing section

### Engine Behaviour

The pricing engine reads the `type` field to determine behaviour:
- **BUNDLED:** Validates that selected package exists, applies package limit/deductible directly
- **DECOUPLED:** Validates limit ∈ valid_limits and deductible ∈ valid_deductibles, applies ILF and deductible factor scaling (with log-linear interpolation for non-exact deductibles)

> **Note:** `limit_configuration` defines what the coverage config offers. How those limits are *distributed* to the market (subscription lines, tower layers, fronted programs) is governed by the Commercial Entity. See [Commercial Entity Schema](Commercial_Entity_Schema.md).

---

## 6. Modifier Application
Modifiers are applied multiplicatively to the Scaled Base Premium.

|Modifier|Source|Direction|
|-|-|-|
|Exposure Size|exposure.size|"< 1.0 (Volume Discount) or > 1.0 (Surcharge). In Rate-based pricing, this usually provides a ""Log-Linear"" discount for scale."|
|Loss Propensity|loss.bands|"0.80 - 1.40. Adjusts for frequency/severity signals (e.g., Backups, MFA)."|
|Complexity|exposure.complexity|"> 1.0. Surcharge for difficult operations (e.g., Multi-jurisdiction)."|

---

## 7. Appetite Evaluation

Before pricing begins, the engine evaluates whether a submission falls within the entity's **underwriting appetite**. Appetite is entity-scoped — each commercial entity declares which coverages it writes, the maximum limits it can bind, and field-level constraints on submission data.

### How It Works

1. The `evaluate_appetite()` function receives the coverage, submission data, and the commercial entity.
2. It looks up the entity's `CoverageBinding` for that coverage line.
3. It checks:
   - **Max single limit** — does the requested limit exceed the entity's authority?
   - **Max aggregate limit** — does the aggregate exposure exceed the cap?
   - **Field constraints** — e.g., "revenue ≤ $10B", "TIV ≤ $100B"
4. If any check fails, the submission is declined with reasons.

### Example Constraint

```yaml
coverages:
  - coverage: cyber
    max_single_limit: 25_000_000
    constraints:
      - field: revenue
        operator: "<="
        value: 10_000_000_000
        reason: "Revenue exceeds MGA cyber binding authority"
```

A submission with revenue of $12B and a $30M limit request would fail on both the limit and the revenue constraint.

> **Note:** Appetite was previously defined in per-coverage YAML files. It is now entity-scoped, reflecting the reality that different entities writing the same coverage have different authorities and risk tolerances.

---

## 8. Premium Assembly Pipeline

Once the technical premium is computed (Steps 1–5 above), the `PremiumAssembler` transforms it into a commercial premium using the entity's terms. This pipeline runs as Step 14 in the pricing workflow.

### Pipeline Flow

```
Technical Premium (USD)
        │
        ▼
┌───────────────────────┐
│   FX Conversion       │  USD → Entity base currency
│   (FXConverter)       │  e.g., USD → GBP at 0.79
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Distribution         │  Apply signed line, layer allocation,
│  Adjustment           │  or lead loading factor
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Commission           │  Deduct brokerage, overrider,
│  Deductions           │  profit commission
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Taxes & Levies       │  IPT, stamp duty, regulatory levy
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Fronting Fee         │  If entity.fronting.enabled = true
│  (optional)           │  e.g., 5% fronting fee
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Minimum Premium      │  Floor enforcement
│  Check                │  (entity.minimum_gross_premium)
└───────────┬───────────┘
            │
            ▼
       Gross Premium (local currency)
            │
            ▼
┌───────────────────────┐
│  Offered Premium      │  Underwriter applies ± discretion
│  Discretion           │  within entity bounds
└───────────┬───────────┘
            │
            ▼
       Offered Premium (local currency)
```

### FX Conversion

All technical pricing is computed in USD regardless of the entity's operating currency. The `FXConverter` handles currency translation:

- **Input conversion:** Submission monetary fields (revenue, TIV) are converted *to* USD before pricing, so the technical premium is always in USD.
- **Output conversion:** The technical premium is converted *from* USD to the entity's `base_currency` for commercial assembly.
- **Audit context:** Every conversion records the rate, source, date, and which fields were converted via an `FXContext` object.

```python
# FX is I/O — all internal pricing is USD
assembler = PremiumAssembler(fx_converter)
breakdown = assembler.assemble(
    technical_premium_usd=pricing_result.final_premium,
    submission_data=submission_data,
    config=config,
    entity=commercial_entity,
)
```

### Distribution Types

The entity's distribution type determines how the technical premium is allocated:

| Type | Behaviour |
|-|-|
| **DIRECT** | 100% writer — full premium retained |
| **BUNDLED** | MGA with predefined limit/deductible packages |
| **SUBSCRIPTION** | Signed line percentage (e.g., 10% of a £50M program). Lead role applies a loading factor. |
| **TOWER** | Layer-by-layer allocation with attachment points and excess structure |
| **FRONTED** | EU/international fronting — 100% ceded to risk carrier, fronting fee applies |

### Commission Structure

Commissions are deducted from the net premium:

$$P_{net} = P_{tech\_local} \times (1 - b - o)$$

Where $b$ = brokerage rate and $o$ = overrider rate. Profit commission, if applicable, is computed post-loss-ratio against a threshold (e.g., 15% profit commission below 70% loss ratio).

### Offered Premium

The final output is the **offered premium** — the price presented to the broker or client. The underwriter may adjust the gross premium within the entity's `offered_premium_discretion` bounds (e.g., ±5%).

This discretion is the **only** subjective adjustment permitted in the entire pipeline, and it operates on the *output* of the mathematical model, not the inputs. The technical premium, modifiers, and signal-derived pricing remain mathematically pure.

---

## 9. Summary of Logic Flow

1. **Evaluate Appetite:** Entity + Coverage + Submission → fit / decline.
2. **Determine Tier:** Signals $\rightarrow$ Risk Score $\rightarrow$ Tier Band $\rightarrow$ Base Rate.
3. **Calculate Base:** Base Rate $\times$ Client Revenue = Anchor Premium.
4. **Scale Coverage:** Anchor Premium $\times$ ILF Relativity $\times$ Deductible Factor = Technical Premium.
5. **Apply Modifiers:** Technical Premium $\times$ Size $\times$ Loss $\times$ Complexity = Final Technical Price.
6. **Apply Constraints:** Check Min Premium and Limit Capacity rules.
7. **Assemble Commercial Premium:** Technical (USD) → FX → Distribution → Commission → Taxes → Gross → Offered (local currency).

```
Signals ──→ Risk Score ──→ Tier ──→ Base Rate
                                        │
Submission ──→ Revenue/TIV ─────────────┤
                                        ▼
                                  Anchor Premium
                                        │
                              ┌─────────┴─────────┐
                              │  ILF × Ded Factor  │
                              └─────────┬─────────┘
                                        ▼
                                Technical Premium (USD)
                                        │
                              ┌─────────┴─────────┐
                              │ Modifiers (R×L×E)  │
                              └─────────┬─────────┘
                                        ▼
                              Final Technical Price (USD)
                                        │
                              ┌─────────┴─────────┐
                              │ Premium Assembly   │
                              │ (FX, Commission,   │
                              │  Taxes, Fronting)  │
                              └─────────┬─────────┘
                                        ▼
                              Offered Premium (local ccy)
```

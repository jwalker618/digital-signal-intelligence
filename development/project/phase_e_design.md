# Phase E Design: Tower & Subscription Market Structure

## Context

Insurance markets beyond "ground-up" (single-layer, full participation) exist in two major forms:

1. **Tower (Excess Layers)**: Multiple stacked layers of coverage, each with an attachment point and a per-layer limit. The total program limit is the sum of all layer limits. Each layer is priced independently.

2. **Subscription (Participation)**: An insurer writes a percentage of a layer rather than 100%. Premium = participation% x full_layer_premium. ROL is unchanged (applies to the whole layer).

These structures are standard in large commercial and specialty markets. DSI must support them to price large accounts accurately.

## Key Insight: ILF Curves Are Cumulative

The existing parametric ILF curves are cumulative loss distribution functions. This means tower layer pricing derives naturally:

```
Ground-up premium at limit L:
  premium(L) = base_premium x ILF(L)

Tower layer premium (attachment A, layer limit L):
  premium(A, L) = base_premium x [ILF(A + L) - ILF(A)]
```

No new curve types are needed. Phase E **composes** existing ILF evaluations.

## Architecture

### E2: Tower Layer Schema

Add `TOWER` to `LimitConfigType` and extend `LimitConfiguration`:

```yaml
limit_configuration:
  type: TOWER
  layers:
    - id: 1
      label: Primary
      attachment: 0
      limit: 10000000
    - id: 2
      label: First Excess
      attachment: 10000000
      limit: 15000000
    - id: 3
      label: Second Excess
      attachment: 25000000
      limit: 25000000
```

Schema changes:
- New enum value: `LimitConfigType.TOWER`
- New model: `TowerLayer(StrictModel)` with `id`, `label`, `attachment: int`, `limit: int`
- `LimitConfiguration.layers: Optional[List[TowerLayer]]`
- `generate_limit_options()` becomes polymorphic: for TOWER, returns the layer structure; for DECOUPLED/BUNDLED, behaves as today

#### Bespoke Towers

Tower configs support arbitrary limit/excess bandings — there is no requirement to use standard layer structures. A config can define any combination of attachment and limit values per layer, allowing:

- Non-standard layer widths (e.g. a thin primary with wide excess layers, or vice versa)
- Gaps between layers (if the program intentionally leaves a band uninsured)
- Overlapping coverage across products within the same tower

Validation rules for bespoke towers:
- Each layer must have `attachment >= 0` and `limit > 0`
- Layers must be ordered by attachment (ascending)
- No two layers within the same product may overlap (i.e. `layer[n].attachment + layer[n].limit <= layer[n+1].attachment`)
- ILF curves must cover the full range up to `max(attachment + limit)` — the health gate validates this

### E3: Multi-Layer Pricing Engine

In `ModelPricer.scale_to_limits()`:

```python
elif limit_config.type == LimitConfigType.TOWER:
    for layer in limit_config.layers:
        ilf_top = config.get_ilf(product_type, layer.attachment + layer.limit)
        ilf_bottom = config.get_ilf(product_type, layer.attachment)
        layer_ilf = ilf_top - ilf_bottom
        layer_premium = premium * layer_ilf * ded_factor

        limit_details.append(LimitPremiumDetail(
            limit=layer.limit,
            attachment_point=layer.attachment,
            ilf_factor=layer_ilf,
            deductible_factor=ded_factor,
            premium_before_scaling=premium,
            premium_after_scaling=round(layer_premium, 2),
        ))
```

ROL validation per layer:
```python
for detail in limit_details:
    rol_result = rol_validator.validate_rol(
        premium=detail.premium_after_scaling,
        limit=detail.limit,
        attachment=detail.attachment_point or 0,
    )
```

### E4: Subscription Market — Order & Line Model

The subscription market operates at two levels:

1. **Order**: The slip/policy unit that defines the 100% terms — total limit, total premium, attachment, deductible, and the full layer structure (if tower). The order represents the risk as placed in the market.
2. **Line**: Each subscriber's participation on the order. A line captures the insurer's signed percentage, their share of premium, and their role (lead or follow).

This distinction matters because the order is the pricing unit (ROL, ILF, and premium all apply at the 100% order level) while the line is the allocation unit (what each insurer actually books).

#### Schema

```yaml
# Order-level configuration (on LimitConfiguration)
limit_configuration:
  type: SUBSCRIPTION
  total_limit: 50000000
  order_premium: 2500000    # 100% premium for the order

# Line-level (per subscriber, on the output/booking side)
subscription_line:
  minimum_line: 0.05        # 5% minimum participation
  maximum_line: 0.25        # 25% maximum participation
  signed_line: 0.15         # actual signed line (any value between min and max)
  role: LEAD                # LEAD or FOLLOW
```

Any line percentage between `minimum_line` and `maximum_line` is valid — no discrete options needed.

Schema changes:
- New enum value: `LimitConfigType.SUBSCRIPTION`
- New model: `SubscriptionOrder(StrictModel)` with `total_limit`, `order_premium`
- New model: `SubscriptionLine(StrictModel)` with `minimum_line`, `maximum_line`, `signed_line: Optional[float]`, `role: LineRole`
- New enum: `LineRole` — `LEAD`, `FOLLOW`
- `LimitConfiguration` extended with `subscription_order: Optional[SubscriptionOrder]`, `subscription_line: Optional[SubscriptionLine]`

#### Lead vs Follow Pricing Impact

Lead/follow status is captured as a DB marker on the line and affects pricing:

- **Lead**: Typically commands a higher rate. The lead insurer sets terms, handles claims, and bears administrative burden. A `lead_loading_factor` (e.g. 1.05–1.15) is applied to the lead's premium to reflect this.
- **Follow**: Takes the terms as set by the lead. No loading applied — follows at the order price.

```python
line_premium = order_premium * signed_line
if role == LineRole.LEAD:
    line_premium *= lead_loading_factor  # from config, e.g. 1.10
```

The `lead_loading_factor` is configurable per product type in the pricing config.

#### Pricing

- `order_premium` = full 100% premium derived from ILF/base pricing (same as ground-up)
- `line_premium` = `signed_line x order_premium` (adjusted for lead loading if applicable)
- ROL is always calculated at the order level (100% basis), not the line level

Subscription composes with tower: each tower layer has an order-level premium, and the insurer takes a line on one or more layers.

### E5: Output Types

New `LayerPremiumDetail` composing layer info:

```python
@dataclass
class LayerPremiumDetail:
    layer_id: int
    layer_label: str
    attachment: int
    limit: int
    order_premium: float = 0.0      # 100% premium for the layer
    signed_line: float = 1.0        # participation (1.0 = ground-up / 100%)
    role: str = "FOLLOW"            # LEAD or FOLLOW
    lead_loading: float = 1.0       # applied multiplier (1.0 for follow)
    line_premium: float = 0.0       # signed_line x order_premium x lead_loading
    rol: float = 0.0                # order_premium / limit (always at 100%)
    ilf_top: float = 0.0            # ILF(attachment + limit)
    ilf_bottom: float = 0.0         # ILF(attachment)
    layer_ilf: float = 0.0          # ilf_top - ilf_bottom
```

`DualRecommendation` extended for multi-layer:
- `structure_type: str` — "ground_up", "tower", "subscription"
- `layers: List[LayerPremiumDetail]` — populated for tower/subscription
- `signed_line: Optional[float]` — the insurer's line on the order
- `role: Optional[LineRole]` — lead or follow
- Upper/lower recommendations at both layer and program level

## Impact on Ground-Up Behavior

**None.** All changes are additive:
- `LimitConfigType.TOWER` and `SUBSCRIPTION` are new enum values
- Existing `DECOUPLED` and `BUNDLED` paths are unchanged
- `attachment_point=None` (ground-up default) remains the norm
- `participation_pct=1.0` (full participation default) is no-op
- ROL validator defaults to `attachment=0` for existing bands

## Phase E Dependencies

- **Requires Phase C (ROL Engine)**: ROL validator must support attachment-based bands
- **Requires Phase A (LimitPremiumDetail)**: attachment_point field must exist
- Both are now complete.

## Testing Strategy

1. **Unit tests for layer ILF derivation**: Verify `ILF(A+L) - ILF(A)` produces correct layer premiums
2. **Tower ROL validation**: Verify per-layer ROL is within appetite for the attachment/limit band
3. **Bespoke tower validation**: Non-standard bandings, gap detection, ILF range coverage
4. **Order/line separation**: Verify order-level pricing is independent of line allocation
5. **Line premium arithmetic**: Verify `signed_line x order_premium x lead_loading`
6. **Lead vs follow pricing**: Lead loading applied correctly; follow at par
7. **Combined tower + subscription**: Multi-layer order with partial line on selected layers
8. **Ground-up regression**: Verify all existing tests still pass unchanged
9. **Config health gate**: Tower and subscription configs pass health gate validation

## Implementation Order

E2 (tower schema) -> E3 (multi-layer pricing) -> E4 (subscription) -> E5 (output types)

E2 and E4 are schema-only changes that can be validated independently.
E3 is the core pricing logic change.
E5 is the output layer that composes E3 results.

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

### E4: Subscription Participation

Add `SUBSCRIPTION` to `LimitConfigType`:

```yaml
limit_configuration:
  type: SUBSCRIPTION
  total_limit: 50000000
  minimum_line: 0.05    # 5% minimum participation
  maximum_line: 0.25    # 25% maximum participation
  participation_options: [0.05, 0.10, 0.15, 0.20, 0.25]
```

Schema changes:
- New enum value: `LimitConfigType.SUBSCRIPTION`
- New fields on `LimitConfiguration`: `total_limit`, `minimum_line`, `maximum_line`, `participation_options`

Pricing: `our_premium = participation_pct x full_premium`. ROL unchanged.

Subscription can also compose with tower: each layer has a total premium, and the insurer participates on one or more layers at a percentage.

### E5: Output Types

New `LayerPremiumDetail` composing layer info:

```python
@dataclass
class LayerPremiumDetail:
    layer_id: int
    layer_label: str
    attachment: int
    limit: int
    participation_pct: float = 1.0
    gross_premium: float = 0.0  # 100% premium for the layer
    net_premium: float = 0.0    # participation_pct x gross_premium
    rol: float = 0.0            # gross_premium / limit
    ilf_top: float = 0.0        # ILF(attachment + limit)
    ilf_bottom: float = 0.0     # ILF(attachment)
    layer_ilf: float = 0.0      # ilf_top - ilf_bottom
```

`DualRecommendation` extended for multi-layer:
- `structure_type: str` — "ground_up", "tower", "subscription"
- `layers: List[LayerPremiumDetail]` — populated for tower/subscription
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
3. **Subscription premium scaling**: Verify `participation_pct x premium` arithmetic
4. **Combined tower + subscription**: Multi-layer with partial participation
5. **Ground-up regression**: Verify all existing tests still pass unchanged
6. **Config health gate**: Tower configs pass health gate validation

## Implementation Order

E2 (tower schema) -> E3 (multi-layer pricing) -> E4 (subscription) -> E5 (output types)

E2 and E4 are schema-only changes that can be validated independently.
E3 is the core pricing logic change.
E5 is the output layer that composes E3 results.

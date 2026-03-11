# Phase [N]: [Coverage Line] Coverage Expansion — Companion Document

## Strategic Rationale

[Why this expansion is needed. Market context, production pipeline requirements, demo credibility, regulatory alignment.]

## Architecture Summary

- **Configurations**: [N] new + [N] existing = [N] total
- **New Signal Groups**: [N]
- **New Signals**: [N] total
- **Routing Field**: `[field_name]` (optional input)
- **Pricing Method**: MULTIPLIER on [basis]
- **Spec File**: `development/project/version/4/phase_[N]_spec.yaml`

## Expansion Spec

The machine-consumable spec is the authoritative source for generation:

```bash
python -m infrastructure.builder.cli expand \
    --spec development/project/version/4/phase_[N]_spec.yaml \
    --existing-config coverages/[line]/config.yaml \
    --write
```

## Configuration Rationale

### [config_id_1]

[2-3 sentences on why this configuration exists as distinct from the general model. What underwriting reality does it capture?]

### [config_id_2]

[...]

## Key Design Decisions

1. [Decision 1 and rationale]
2. [Decision 2 and rationale]

## Pricing Philosophy

[Brief summary of pricing approach, rate differentiation logic, ILF curve rationale.]

## Signals Not Included (and Why)

[Any signals considered but excluded, with rationale. Helps future maintainers understand the boundary.]

## Post-Generation Review Checklist

- [ ] Generated config validates: `python -m infrastructure.builder.cli validate coverages/[line]/config.yaml`
- [ ] Group weights sum to ~1.0 for each dimension (risk, loss, exposure)
- [ ] Tier band rates are actuarially reasonable relative to general config
- [ ] Signal code stubs compile without import errors
- [ ] logic.md generated and reviewed
- [ ] Routing constraints tested with example submissions

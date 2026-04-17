# Golden-Entity Registry (V6/E5)

Snapshot regression fixtures for the full DSI assessment pipeline. Each YAML
file under `{coverage}/{entity_id}.yaml` captures:

- Identity: `entity_id`, `name`, optional `domain`, optional `registry_id`.
- Routing: `coverage` and (optional) `config_id` when the coverage has no
  `*_general` default.
- `minimum_viable_input` — the exact submission payload the test will feed
  into `run_workflow`.
- `expected` — the pipeline output to match (`composite_score`, `tier`,
  `decision`, `recommended_premium`).
- `tolerance` — per-fixture tolerance: `score_points` (absolute),
  `premium_bps` (basis points, 10000 = 100%), `tier_spread`
  (how many tiers the actual tier may drift from `expected.tier`).

## Target

**10 entities × every existing coverage** per the V6 plan (E5). The registry
currently ships with two entities per coverage as a scaffold; the remaining
entities are added alongside the A1-A8 coverage-maturation phases so each
new sub-config is paired with a real-world entity that exercises it.

## Adding an entity

1. Add a block under the correct coverage in `_manifest.yaml`:
   ```yaml
   coverages:
     cyber:
       - entity_id: stripe
         name: Stripe, Inc.
         config_id: cyber_financial_services   # optional if *_general exists
         domain: stripe.com
         registry_id: US-Delaware-0001745814
         minimum_viable_input:
           revenue: 14400000000
           limit: 50000000
           deductible: 500000
           product_type: standard
           industry_sector: FINANCIAL_SERVICES
           domain: stripe.com
         score_tolerance: 50          # optional override
         premium_tolerance_bps: 1000  # optional override
   ```
2. Regenerate the fixture:
   ```bash
   python tests/fixtures/golden_entities/_generator.py --coverage cyber
   ```
3. Inspect the generated YAML. Hand-tighten tolerances if the output is
   stable enough to deserve a narrower band.
4. Commit both `_manifest.yaml` and the generated fixture.

## Refreshing after an intentional pricing change

```bash
python tests/fixtures/golden_entities/_generator.py --all --refresh
```

Per the V6 plan this **requires a signed-off PR** — a reviewer must see the
rendered `logic.md` diff (via the config-diff workflow) alongside the
updated golden premium deltas and approve the change.

## Why snapshot tests?

- **Determinism for regressions.** These fixtures are deterministic given
  the current stub-extractor surface — any change in scoring, ILF, damping,
  or exposure modifier surfaces as a premium/score delta that exceeds
  `tolerance`.
- **Reality catches up.** As more production extractors land (D1, D3, D2,
  …) the inputs to these entities start reflecting real signal. The goldens
  then measure the *real* pipeline, and intentional premium shifts are
  documented changes.
- **Commercial evidence.** Paired with the Evidence Dashboard (E8), these
  fixtures are the `last_golden_check_at` timestamp per coverage that sales
  and reinsurer conversations rely on.

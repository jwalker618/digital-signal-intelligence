# DSI Seed Package (V6/C4)

Consolidates bench + v5 companion + synthetic-generator seed scripts
behind a single `python -m seed` CLI.

## Commands

| Command | What it does |
|---------|--------------|
| `python -m seed init --tenant dsi-demo --entities 1000` | Runs reset → bench → v5 → synthetic in order. |
| `python -m seed bench` | Executes the hand-curated 61-company bench seed. |
| `python -m seed v5` | Augments with V5 governance / experience artefacts. |
| `python -m seed synthetic --coverage cyber --n 100` | Generates high-volume synthetic portfolios. |
| `python -m seed reset --confirm` | Placeholder for truncation (C4-interim). |
| `python -m seed verify` | Assert headline row counts post-seed. |

## State — V6/C4-final (Q4)

Legacy root-level scripts (`seed_dsi_bench.py`, `seed_v5.py`,
`synthetic_generator.py`) have been **deleted**. The canonical home
for seed logic is this package — the CLI and modules import directly:

- `seed/bench.py` — hand-curated 61-company bench (+ optional
  synthetic fold-in).
- `seed/v5.py` — V5 governance / experience augmentation.
- `seed/synthetic.py` — high-volume synthetic portfolio.

Every module exposes a `run(**kwargs) -> int` entry point used by the
CLI dispatcher in `seed/cli.py`.

## Remaining (C4-final follow-ups)

- `seed/fixtures/` — YAML fixtures replacing hard-coded entity tables
  inside `bench.py` (refactor to be stepwise).
- `python -m seed verify` — assert a YAML-defined row-count contract
  per tenant.
- `python -m seed reset` — wire into alembic downgrade-to-base +
  ordered TRUNCATE.

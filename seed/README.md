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

## State — V6/C4-interim

This package is a **thin shim** during Q1: each submodule imports the
legacy root-level script (`seed_dsi_bench.py`, `seed_v5.py`,
`synthetic_generator.py`) and delegates to its `main()`. Legacy scripts
emit a `DeprecationWarning` on import so callers migrate to the CLI.

## C4-final (Q4)

- Legacy scripts deleted from the repo root.
- Content moved into `seed/bench.py`, `seed/v5.py`, `seed/synthetic.py`.
- `seed/fixtures/` (new) replaces hard-coded entity tables inside bench.
- `python -m seed verify` asserts a YAML-defined row-count contract.
- `python -m seed reset` wires into alembic downgrade-to-base + ordered
  TRUNCATE.

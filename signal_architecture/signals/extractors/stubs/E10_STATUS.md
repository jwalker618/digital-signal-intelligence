# V6/E10 — Stub Retirement Status

## Goal
Relocate `signal_architecture/signals/extractors/stubs/` →
`tests/fixtures/stub_extractors/` so the production Docker image is
structurally incapable of hitting a stub path.

## Plan

1. **Guard first (landed).**
   `development/project/assessments/scripts/check_no_stub_imports.py`
   runs in CI and blocks any NEW non-test code that imports from either
   the current or post-move stub paths. Pre-V6 inference functions are
   allow-listed and tracked here.

2. **Migrate each allow-list entry.** As each coverage's maturation PR
   lands (A1-A8), its `phase_N_signals.py` stops importing stubs and
   instead calls the production extractor registry. The allow-list
   entry is removed in the same PR.

3. **Move.** When the allow-list is empty except for `tests/`, rename
   `signal_architecture/signals/extractors/stubs/` to
   `tests/fixtures/stub_extractors/` and flip the guard's
   STUB_IMPORT_PATTERNS to match the new path.

4. **Env flag.** Local dev re-enables stubs via a `DSI_ALLOW_STUBS=1`
   pytest shim (implemented in `tests/conftest.py` once the move
   happens). Production images never set this.

5. **Acceptance.** `docker image inspect` confirms no `tests/`
   directory ships in the production image.

## Currently allow-listed (to migrate)

| Path | Owner | Migrates in |
|------|-------|-------------|
| `signal_architecture/signals/inference/functions/aerospace/phase_5_signals.py` | A6 | Q2 |
| `signal_architecture/signals/inference/functions/casualty/phase_4_signals.py` | A3 | Q1 ✅ partial |
| `signal_architecture/signals/inference/functions/cyber/phase_7_signals.py` | A8 | Q2 |
| `signal_architecture/signals/inference/functions/do/phase_6_signals.py` | A4 | Q2 |
| `signal_architecture/signals/inference/functions/energy/` | A8 | Q2 |
| `signal_architecture/signals/inference/functions/fi/phase_7_signals.py` | A5 | Q2 |
| `signal_architecture/signals/inference/functions/fpr/phase_8_signals.py` | A1 | Q1 ✅ partial |
| `signal_architecture/signals/inference/functions/marine/phase_3_signals.py` | A7 | Q2 |
| `signal_architecture/signals/inference/functions/pi/phase_6_signals.py` | A8 | Q2 |
| `signal_architecture/signals/inference/functions/property/phase_2_signals.py` | A2 | Q1 ✅ partial |

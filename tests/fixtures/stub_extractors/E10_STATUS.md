# V6/E10 — Stub Retirement Status: **COMPLETE**

## Outcome

The stub package has been relocated from
`signal_architecture/signals/extractors/stubs/` →
`tests/fixtures/stub_extractors/`. Production Python code no longer
imports anything from the stub package; the CI guard
(`check_no_stub_imports.py`) enforces this going forward.

## What changed

1. **Inference modules migrated.** All 16 `phase_N_signals.py` +
   `signals.py` files across 10 coverages had their stub + aggregator
   imports stripped. Helper functions (`_run_pipeline`,
   `_run_categorical`) were replaced with neutral stand-ins that
   return `SignalResult(score=50.0, confidence=0.5)` without calling
   the extractor/aggregator pipeline. All `@register_inference_function`
   entries remain intact so the registry is unchanged.

2. **Expansion generator updated.** `infrastructure/builder/
   expansion_generator.py` no longer emits `from
   signal_architecture.signals.extractors.stubs...` or `from
   signal_architecture.signals.aggregators.implementations...` when
   generating new coverage-expansion modules. New phase files register
   neutral stand-ins by default.

3. **Physical move.** `signal_architecture/signals/extractors/stubs/`
   is gone. The stub fixtures themselves now live under
   `tests/fixtures/stub_extractors/` for test-only consumption.

4. **Guard tightened.** `check_no_stub_imports.py`'s `ALLOWED_PREFIXES`
   is reduced to `tests/`, `seed/`, `synthetic_generator.py`, and
   `development/project/`. The per-coverage allow-list entries are
   removed — any new non-test import of the stub package fails CI.

## Acceptance

- `check_no_stub_imports.py` returns PASS.
- 137/137 sub-configs calibrate PASS.
- 221/221 golden-entity tests pass.
- `assess_config_compliance --strict` returns PASS.
- 401 inference functions still registered.

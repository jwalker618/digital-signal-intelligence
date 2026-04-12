# Phase B-2: Config Management

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1 (auth), A-2 (audit trail for config changes) |

---

## Overview

UI for viewing, editing, validating, and deploying coverage configurations. Replaces CLI-only config management with a governed, auditable workflow: Draft -> Validated -> Calibrated -> Deployed.

## Current State

- `coverages/` -- 10 coverage lines, 76 configs, each a YAML file following `master_config_layout.yaml` v2.3
- `infrastructure/validation/config_validator.py` -- `ModelConfigValidator` with `validate_file()` and `validate_all()`. Checks: structure, weight sums, tier coverage, score conditions.
- `layers/risk/calibration_harness.py` -- `CalibrationHarness` with `run_coverage()`. Generates fixtures, validates premium distributions, guardrail hit rates.
- `coverages/doc_generator.py` -- Regenerates config documentation
- `infrastructure/db/models.py` -- `ConfigSnapshot` stores frozen config at execution time (content-addressable via `config_hash`)
- No web-based config editing, no version management UI, no deployment workflow.

## Target State

Config browser, YAML editor with inline validation, calibration runner, diff viewer, and governed deployment flow in the admin UI.

---

## Implementation Plan

### B-2a: Config API

**New file**: `infrastructure/api/admin/config_routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/configs` | GET | List all coverages and their configs |
| `/admin/configs/{coverage}/{config}` | GET | Get config YAML content |
| `/admin/configs/{coverage}/{config}` | PUT | Update config (creates draft version) |
| `/admin/configs/{coverage}/{config}/validate` | POST | Run `ModelConfigValidator`, return results |
| `/admin/configs/{coverage}/{config}/calibrate` | POST | Run `CalibrationHarness`, return results |
| `/admin/configs/{coverage}/{config}/deploy` | POST | Promote draft to active (requires `config:deploy` permission) |
| `/admin/configs/{coverage}/{config}/rollback` | POST | Revert to previous version |
| `/admin/configs/{coverage}/{config}/history` | GET | Version history with diffs |

### B-2b: Config Versioning

**Migration**: `alembic/versions/015_config_versions.py`

| Table | Key Columns |
|-------|-------------|
| `config_versions` | `id`, `coverage`, `config_name`, `version_number`, `content` (TEXT -- YAML), `config_hash`, `status` (enum: DRAFT/VALIDATED/CALIBRATED/DEPLOYED/ROLLED_BACK), `author_id` FK, `created_at` |
| `config_deployments` | `id`, `config_version_id` FK, `deployed_by` FK, `calibration_result` (JSONB), `deployed_at`, `rolled_back_at` |

**New file**: `infrastructure/admin/config_service.py`

```python
class ConfigService:
    """Config version management: create, validate, calibrate, deploy."""

    def create_draft(self, coverage: str, config: str, content: str, author_id: str) -> ConfigVersion: ...
    def validate(self, version_id: str) -> ValidationReport: ...
    def calibrate(self, version_id: str) -> CalibrationResult: ...
    def deploy(self, version_id: str, deployer_id: str) -> None: ...
    def rollback(self, version_id: str) -> None: ...
    def diff(self, version_a: str, version_b: str) -> ConfigDiff: ...
```

### B-2c: Config Diff Engine

**New file**: `infrastructure/admin/config_diff.py`

```python
class ConfigDiffEngine:
    """Computes structured diff between two YAML config versions."""

    def diff(self, yaml_a: str, yaml_b: str) -> ConfigDiff:
        """
        Parse both YAMLs. Walk structure. Identify:
        - Weight changes (signal_id, old_weight, new_weight)
        - Signal additions/removals
        - Tier threshold changes
        - Score condition changes
        Return structured diff, not raw text diff.
        """
```

### B-2d: Frontend -- Config Management UI

**New file**: `frontend/src/app/admin/configs/page.tsx` -- Config browser: tree view of coverages -> configs. Version, last modified, status badge.

**New file**: `frontend/src/components/admin/ConfigEditor.tsx` -- YAML editor with syntax highlighting (Monaco). Live validation on keystroke (debounced).

**New file**: `frontend/src/components/admin/ValidationPanel.tsx` -- Run validator, display errors/warnings inline with line references.

**New file**: `frontend/src/components/admin/CalibrationPanel.tsx` -- Run calibration harness, display pass/fail per config, guardrail hit rate, tier distribution charts.

**New file**: `frontend/src/components/admin/ConfigDiffViewer.tsx` -- Side-by-side comparison of any two versions. Highlighted changes.

**Deployment flow in UI**: Draft -> Validate (button) -> Calibrate (button) -> Review diff against active -> Deploy (requires `config:deploy`, confirmation dialog) -> Audit trail.

---

## Constraints

1. Config edits create new versions -- never modify active config in place
2. Deployment requires `config:deploy` permission (typically ADMIN or ACTUARIAL)
3. Every config change, validation run, calibration run, and deployment is audit-logged
4. Deployed config must pass both validation and calibration before promotion

## Success Criteria

1. All 76 configs viewable and editable in the UI
2. Validator runs inline and displays results correctly
3. Calibration harness runs from UI and displays results
4. Config changes create audited versions with diffs
5. Deployment requires approval from permissioned user
6. Rollback restores previous version correctly

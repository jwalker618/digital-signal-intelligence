# Phase 18: Architecture Restructuring

## Purpose

Restructure the DSI codebase to support the **three-layer assessment model** by extracting shared signal infrastructure to the repository root and creating a dedicated `layers/` directory for assessment layer implementations.

## Status

🔲 **In Progress**

## Rationale

The current architecture has signals nested within `technical_pricing/signals/`. However, signals now feed **all three assessment layers**:

1. **Risk Layer** - existing risk scoring (Steps 5a, 9a)
2. **Exposure Shadow Layer** - Phase 17 (Steps 5b, 9b)
3. **Loss Correlation Layer** - Phase 16 (Steps 5c, 9c)

Implementing Phases 16 and 17 before restructuring would create technical debt by building new layers in the wrong location.

## Key Changes

### Directory Moves

| From | To | Notes |
|------|----|-------|
| `technical_pricing/signals/` | `signals/` | Shared signal infrastructure |
| `technical_pricing/coverages/` | `coverages/` | Coverage configurations |
| `technical_pricing/model/` | `layers/risk/` | Risk assessment layer |
| `technical_pricing/api/` | `api/` | API layer |
| `technical_pricing/analytics/` | `analytics/` | Analytics |
| `technical_pricing/orchestration/` | `orchestration/` | Multi-coverage orchestration |
| `technical_pricing/discovery/` | `discovery/` | Website discovery |
| `technical_pricing/integrations/` | `integrations/` | External integrations |
| `technical_pricing/builder/` | `builder/` | Coverage builder |
| `technical_pricing/db/` | `db/` | Database layer |
| `exposure/shadow_layer/development/` | `layers/exposure/development/` | Exposure layer specs |
| `loss/correlation_layer/development/` | `layers/loss/development/` | Loss layer specs |

### New Directory Structure

```
digital-signal-intelligence/
├── signals/                    # Shared signal infrastructure
│   ├── __init__.py
│   ├── base.py
│   ├── types.py
│   ├── extractors/
│   ├── aggregators/
│   ├── categorisers/
│   ├── inference/
│   ├── routing/
│   └── cross_walk/
│
├── layers/                     # Assessment layer implementations
│   ├── __init__.py
│   ├── risk/                   # Risk layer (from technical_pricing/model/)
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── scorer.py
│   │   ├── pricer.py
│   │   ├── workflow.py
│   │   ├── config_manager.py
│   │   ├── model_data.py
│   │   ├── query_evaluator.py
│   │   └── modifiers/
│   ├── exposure/               # Exposure shadow layer (Phase 17)
│   │   ├── __init__.py
│   │   └── development/        # Specifications (from exposure/shadow_layer/)
│   └── loss/                   # Loss correlation layer (Phase 16)
│       ├── __init__.py
│       └── development/        # Specifications (from loss/correlation_layer/)
│
├── coverages/                  # Coverage configurations
│   ├── aerospace/config.yaml
│   ├── cyber/config.yaml
│   ├── do/config.yaml
│   ├── energy/config.yaml
│   ├── fi/config.yaml
│   ├── marine/config.yaml
│   └── pi/config.yaml
│
├── api/                        # FastAPI application
├── analytics/                  # Analytics engine
├── orchestration/              # Multi-coverage orchestration
├── discovery/                  # Website discovery
├── integrations/               # External integrations
├── builder/                    # Coverage builder
├── db/                         # Database layer
│
├── development/                # Documentation (unchanged)
├── demo/                       # Demos (unchanged)
├── deploy/                     # Deployment (unchanged)
├── docs/                       # Documentation (unchanged)
└── tests/                      # Tests (consolidated)
```

## Import Changes

### Old Import Patterns → New Import Patterns

```python
# Signals
from technical_pricing.signals.base import ...
→ from signals.base import ...

from technical_pricing.signals.extractors.base import ...
→ from signals.extractors.base import ...

from technical_pricing.signals.aggregators.base import ...
→ from signals.aggregators.base import ...

# Risk Layer (formerly model)
from technical_pricing.model.scorer import ...
→ from layers.risk.scorer import ...

from technical_pricing.model.workflow import ...
→ from layers.risk.workflow import ...

from technical_pricing.model.types import ...
→ from layers.risk.types import ...

# Coverages
from technical_pricing.coverages import ...
→ from coverages import ...

# Other modules
from technical_pricing.api import ...
→ from api import ...

from technical_pricing.analytics import ...
→ from analytics import ...
```

## Implementation Tasks

| Task | Status |
|------|--------|
| Create `signals/` directory at root | 🔲 Not Started |
| Create `layers/` directory structure | 🔲 Not Started |
| Create `coverages/` directory at root | 🔲 Not Started |
| Move `technical_pricing/signals/*` to `signals/` | 🔲 Not Started |
| Move `technical_pricing/model/*` to `layers/risk/` | 🔲 Not Started |
| Move `technical_pricing/coverages/*` to `coverages/` | 🔲 Not Started |
| Move `technical_pricing/api/*` to `api/` | 🔲 Not Started |
| Move `technical_pricing/analytics/*` to `analytics/` | 🔲 Not Started |
| Move `technical_pricing/orchestration/*` to `orchestration/` | 🔲 Not Started |
| Move `technical_pricing/discovery/*` to `discovery/` | 🔲 Not Started |
| Move `technical_pricing/integrations/*` to `integrations/` | 🔲 Not Started |
| Move `technical_pricing/builder/*` to `builder/` | 🔲 Not Started |
| Move `technical_pricing/db/*` to `db/` | 🔲 Not Started |
| Move `exposure/shadow_layer/` to `layers/exposure/` | 🔲 Not Started |
| Move `loss/correlation_layer/` to `layers/loss/` | 🔲 Not Started |
| Update all imports in Python files | 🔲 Not Started |
| Update all imports in test files | 🔲 Not Started |
| Update demo scripts | 🔲 Not Started |
| Update pyproject.toml package configuration | 🔲 Not Started |
| Update setup.py | 🔲 Not Started |
| Update SKILL.md file structure documentation | 🔲 Not Started |
| Run all tests and fix failures | 🔲 Not Started |
| Remove empty `technical_pricing/` directory | 🔲 Not Started |
| Remove empty `exposure/` directory | 🔲 Not Started |
| Remove empty `loss/` directory | 🔲 Not Started |

## Backward Compatibility

To maintain backward compatibility during transition, we will:

1. **NOT create aliases** - Clean break, update all imports directly
2. **Update all files atomically** - Single commit for structure, single commit for imports
3. **Verify with tests** - All existing tests must pass after migration

## Files Requiring Import Updates

Based on the current codebase, the following files will need import updates:

### Core Modules (~50 files)
- All files in `signals/` (internal imports)
- All files in `layers/risk/` (internal imports + signal imports)
- All files in `api/`, `analytics/`, `orchestration/`, etc.

### Demo Scripts (~10 files)
- `demo/server.py`
- `demo/examples/run_*.py`

### Test Files (~20 files)
- `tests/unit/*.py`
- `tests/integration/*.py`
- `tests/api/*.py`

## Verification Steps

After restructuring:

1. Run `python -c "import signals; import layers; import coverages"`
2. Run `python -m pytest tests/ -v`
3. Run `python demo/examples/run_cyber.py`
4. Verify all imports resolve correctly

## Rollback Plan

If issues are discovered:
1. `git revert` the commits
2. Document issues found
3. Plan fixes before re-attempting

---

**This phase is a prerequisite for Phases 16 and 17.**

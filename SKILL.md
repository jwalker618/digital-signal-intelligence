-----

## name: dsi-framework
description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on DSI project code including extractors, aggregators, categorizers, inference functions, signal processing, YAML config interpretation, or any technical model development. Triggers on mentions of DSI, signal architecture, coverage configs, technical pricing, or insurance underwriting automation.

# DSI Framework Development Guide

## What is DSI?

Digital Signal Intelligence (DSI) is insurance underwriting based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

Key principles:

- All primary signals externally observable (no cooperation required)
- Machine-readable, no subjective judgment
- Network authority (PageRank-style) over self-reporting
- Absence is signal (missing expected presence)
- Signal → Score → Tier → Price (auditable flow)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YAML CONFIG                              │
│     Single source of truth for coverage model definition        │
│     (weights, modifiers, tiers, direct queries, features)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL ARCHITECTURE                          │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌────────── ┐ │
│  │EXTRACTOR │ →  │AGGREGATOR│ →  │CATEGORIZER│ →  │INFERENCE  │ │
│  │          │    │          │    │           │    │           │ │
│  │Raw data  │    │Structure/│    │Score or   │    │Orchestrate│ │
│  │from APIs │    │normalize │    │category   │    │pipeline   │ │
│  └──────────┘    └──────────┘    └───────────┘    └───────── ─┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL OUTPUT                               │
│  Composite score (0-1000) → Tier (1-5) → Premium + Modifiers    │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Status

### ✅ Phase 1: Foundation (COMPLETE)

All base infrastructure is built and tested:

|Component                       |File                           |Status    |
|--------------------------------|-------------------------------|----------|
|Core Data Types                 |`signals/types.py`             |✅ Complete|
|Abstract Base Classes           |`signals/base.py`              |✅ Complete|
|StubExtractor (with TTL caching)|`signals/extractors/base.py`   |✅ Complete|
|ProductionAggregator            |`signals/aggregators/base.py`  |✅ Complete|
|ProductionCategorizer           |`signals/categorizers/base.py` |✅ Complete|
|Inference Registry              |`signals/inference/registry.py`|✅ Complete|

### ✅ Phase 2: Reusable Categorizer Types (COMPLETE)

12 parameterized categorizer types ready for use in `signals/categorizers/types/`.

### ✅ Phase 3: Coverage Implementation (4 OF 7 COMPLETE)

|Coverage |Extractors|Aggregators|Inference|Status    |
|---------|----------|-----------|---------|----------|
|Aerospace|21        |26         |41       |✅ Complete|
|Cyber    |35        |35         |38       |✅ Complete|
|D&O      |46        |46         |47       |✅ Complete|
|Energy   |44        |44         |46       |✅ Complete|
|Common   |7         |7          |-        |✅ Complete|
|**Total**|**153**   |**158**    |**173**  |          |

### 🔲 Phase 4: Remaining Coverages (NOT STARTED)

- [ ] Financial Institutions (FI)
- [ ] Marine
- [ ] Professional Indemnity (PI)

### 🔲 Phase 5: Model Integration (NOT STARTED)

- [ ] Config loader (parse YAML, validate structure)
- [ ] Model scorer (composite scoring logic)
- [ ] Model pricer (premium calculation with modifiers)
- [ ] End-to-end pipeline testing

-----

## File Structure (STANDARDIZED)

```
technical_pricing/
├── __init__.py
├── coverages/
│   ├── aerospace/config.yaml
│   ├── cyber/config.yaml
│   ├── do/config.yaml
│   ├── energy/config.yaml
│   ├── fi/config.yaml                   🔲
│   ├── marine/config.yaml               🔲
│   └── pi/config.yaml                   🔲
├── signals/
│   ├── __init__.py
│   ├── base.py                          ✅ Base classes
│   ├── types.py                         ✅ Data structures
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base.py                      ✅ StubExtractor + utilities
│   │   └── stubs/
│   │       ├── __init__.py
│   │       ├── common.py                ✅ Cross-coverage extractors
│   │       ├── aerospace/               ✅ 3 files, 21 extractors
│   │       ├── cyber/                   ✅ 4 files, 35 extractors
│   │       ├── do/                      ✅ 3 files, 46 extractors
│   │       ├── energy/                  ✅ 3 files, 44 extractors
│   │       ├── fi/                      🔲
│   │       ├── marine/                  🔲
│   │       └── pi/                      🔲
│   ├── aggregators/
│   │   ├── __init__.py
│   │   ├── base.py                      ✅ ProductionAggregator + utilities
│   │   └── implementations/
│   │       ├── __init__.py
│   │       ├── common.py                ✅ Cross-coverage aggregators
│   │       ├── aerospace/
│   │       │   ├── __init__.py
│   │       │   └── aggregators.py       ✅ 26 aggregators
│   │       ├── cyber/
│   │       │   ├── __init__.py
│   │       │   └── aggregators.py       ✅ 35 aggregators
│   │       ├── do/
│   │       │   ├── __init__.py
│   │       │   └── aggregators.py       ✅ 46 aggregators
│   │       ├── energy/
│   │       │   ├── __init__.py
│   │       │   └── aggregators.py       ✅ 44 aggregators
│   │       ├── fi/                      🔲
│   │       ├── marine/                  🔲
│   │       └── pi/                      🔲
│   ├── categorizers/
│   │   ├── __init__.py
│   │   ├── base.py                      ✅ ProductionCategorizer + utilities
│   │   └── types/
│   │       ├── __init__.py
│   │       ├── threshold_bucket.py      ✅
│   │       ├── boolean_score.py         ✅
│   │       ├── weighted_composite.py    ✅
│   │       └── category_mapper.py       ✅
│   └── inference/
│       ├── __init__.py
│       ├── registry.py                  ✅
│       └── functions/
│           ├── __init__.py
│           ├── aerospace/
│           │   ├── __init__.py
│           │   └── signals.py           ✅ 41 functions
│           ├── cyber/
│           │   ├── __init__.py
│           │   └── signals.py           ✅ 38 functions
│           ├── do/
│           │   ├── __init__.py
│           │   └── signals.py           ✅ 47 functions
│           ├── energy/
│           │   ├── __init__.py
│           │   └── signals.py           ✅ 46 functions
│           ├── fi/                      🔲
│           ├── marine/                  🔲
│           └── pi/                      🔲
├── model/
│   ├── __init__.py                      🔲
│   ├── config_loader.py                 🔲
│   ├── scorer.py                        🔲
│   └── pricer.py                        🔲
└── tests/                               🔲
```

Legend: ✅ Complete | 🔲 Not Started

-----

## Standard Pattern for New Coverages

When adding a new coverage (e.g., FI, Marine, PI), follow this pattern:

### 1. Extractors

Create `signals/extractors/stubs/{coverage}/`:

- `__init__.py` - exports all extractors
- `{group1}.py` - extractors for signal group 1
- `{group2}.py` - extractors for signal group 2
- etc.

### 2. Aggregators

Create `signals/aggregators/implementations/{coverage}/`:

- `__init__.py` - exports all aggregators
- `aggregators.py` - ALL aggregators in single file

### 3. Inference Functions

Create `signals/inference/functions/{coverage}/`:

- `__init__.py` - imports signals module
- `signals.py` - ALL inference functions in single file

### 4. Update Imports

- Add to `signals/extractors/stubs/__init__.py`
- Add to `signals/aggregators/implementations/__init__.py`
- Add to `signals/inference/functions/__init__.py`

-----

## YAML Config Structure

**CRITICAL: The YAML config is the single source of truth. Never hardcode values that exist in config.**

```yaml
coverage:                          # Domain (e.g., aerospace, cyber, marine)
  configuration:                   # Instantiable model (e.g., aerospace_general)
    metadata:                      # Name, version, min premium, markets
    direct_queries:                # Optional boolean questions (max 5-10)
    categorical_groups:            # Groups that impact pricing (modifier or premium basis)
    categorical_features:          # Categories within each group + their modifiers
    signal_groups:                 # Groups of signals with weights (must sum to 1.0)
    signal_features:               # Individual signals within groups (weights sum to 1.0 per group)
    tier_thresholds:               # Score ranges → tiers → premiums
    pricing:                       # ILF tables, deductible credits, experience mods
    test_profiles:                 # Validation scenarios
```

-----

## Coverages

Seven coverage domains:

|Coverage              |Config File            |Signals|Key Signal Focus                                           |
|----------------------|-----------------------|-------|-----------------------------------------------------------|
|Aerospace             |`aerospace/config.yaml`|~40    |Safety record, regulatory compliance, fleet quality        |
|Cyber                 |`cyber/config.yaml`    |~35    |Technical infrastructure, security posture                 |
|D&O                   |`do/config.yaml`       |~45    |Corporate governance, regulatory filings                   |
|Energy                |`energy/config.yaml`   |~44    |Operational safety, environmental compliance               |
|Financial Institutions|`fi/config.yaml`       |TBD    |Regulatory standing, financial stability                   |
|Marine                |`marine/config.yaml`   |TBD    |Vessel tracking, classification society, port state control|
|Professional Indemnity|`pi/config.yaml`       |TBD    |Professional certifications, claims history                |

-----

## Critical Rules

1. **YAML is truth**: Never hardcode weights, thresholds, modifiers, or tier definitions
1. **Extractors are stubs**: Randomized but structurally realistic, with TTL caching
1. **Aggregators are production**: Must handle real data when extractors upgraded
1. **Categorizers are reusable**: Use the 12 parameterized types, don’t create signal-specific logic
1. **Inference functions are glue**: One per YAML `inference_utility_function`
1. **Consistent structure**: All coverages follow the same file organization pattern
1. **Scores are 0-100**: Individual signals
1. **Composite is 0-1000**: Weighted sum * 10
1. **Confidence matters**: Track data availability throughout pipeline
1. **TTL varies by source**: Set appropriate `DEFAULT_TTL_SECONDS` per extractor

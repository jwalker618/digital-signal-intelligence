# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.4.0|
|Date|March 2026|
|Classification|loss|

---

# Loss Signal Correlation Layer

This folder contains the specification and implementation for DSI Phase 16: Loss Signal Correlation Layer.

## Purpose

The Loss Signal Correlation Layer extends DSI from risk quality assessment to loss prediction by:

1. **Correlating signals with loss outcomes** - Map observable signals to historical loss frequency and severity
2. **Inferring loss propensity** - Calculate loss likelihood for new submissions
3. **Enabling cohort-based pricing** - Group similar risks for experience-based adjustments
4. **Providing continuous monitoring** - Track risk deterioration for in-force policies

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SIGNAL EXTRACTION                        │
│                    (Steps 0-4 unchanged)                    │
└──────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ RISK SCORING │ │  EXPOSURE    │ │    LOSS      │
  │              │ │  SHADOW      │ │ CORRELATION  │
  │ Steps 5-6    │ │  LAYER       │ │    LAYER     │
  │ Composite    │ │              │ │              │
  │ + Conditions │ │ Exposure Band│ │ Propensity   │
  │              │ │ + Complexity │ │ + Cohort     │
  └──────────────┘ └──────────────┘ └──────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    PRICING ENGINE                         │
  │  Risk Tier × Exposure Band × Loss Propensity → Premium   │
  └──────────────────────────────────────────────────────────┘
```

## Contents

```
loss/
└── correlation_layer/
    ├── development/
    │   └── plan.md       # Implementation plan
    └── (implementation files to be added in Phase 16)
```

## Key Concepts

### Loss Propensity Bands

| Band | Score Range | Frequency Multiplier | Severity Multiplier |
|------|-------------|---------------------|---------------------|
| Very Low | 0-20 | 0.60 | 0.70 |
| Low | 20-40 | 0.80 | 0.85 |
| Moderate | 40-60 | 1.00 | 1.00 |
| Elevated | 60-80 | 1.25 | 1.20 |
| High | 80-100 | 1.50 | 1.50 |

### Signal-Derived Cohorts

Unlike traditional industry code segmentation, DSI cohorts are defined by signal patterns:

- **High Governance** - Strong executive stability, audit quality
- **Technical Leaders** - Excellent security posture, modern infrastructure
- **Regulatory Clean** - No enforcement actions, strong compliance
- **Mixed Profile** - Combination of strengths and weaknesses

## Implementation Status

| Component | Status |
|-----------|--------|
| Specification | Complete |
| Core Types | Not Started |
| Loss Correlation Scorer | Not Started |
| Correlation Matrix Manager | Not Started |
| Monitoring Engine | Not Started |
| YAML Configuration | Not Started |

## References

- **SKILL.md** - Architecture documentation
- **layers/loss/** - Implementation

# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|exposure|

---

# Exposure Shadow Layer

This folder contains the Exposure Shadow Layer implementation - a parallel processing path that infers exposure characteristics from observable signals.

## Purpose

The Exposure Shadow Layer enables accurate exposure estimation without requiring explicit TIV (Total Insured Value) data from submissions by:

1. **Inferring exposure band** from company size signals (revenue, employees, market cap)
2. **Estimating complexity** from operational scope signals
3. **Providing exposure-based pricing adjustments** in the pricing engine

## Architecture

The Exposure Shadow Layer runs in parallel with risk scoring:

```
┌─────────────────────────────────────────────────────────────┐
│                    SIGNAL EXTRACTION                        │
└──────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ RISK SCORING │ │  EXPOSURE    │ │    LOSS      │
  │              │ │  SHADOW      │ │ CORRELATION  │
  │ Composite    │ │  LAYER       │ │    LAYER     │
  │ + Tier       │ │ Exposure Band│ │ Propensity   │
  └──────────────┘ └──────────────┘ └──────────────┘
```

## Contents

```
exposure/
└── shadow_layer/
    └── (implementation files)
```

## Exposure Bands

| Band | Revenue Range | Typical TIV | Pricing Multiplier |
|------|--------------|-------------|-------------------|
| Micro | <$10M | <$1M | 0.7 |
| Small | $10M-$100M | $1M-$10M | 0.85 |
| Medium | $100M-$1B | $10M-$100M | 1.0 |
| Large | $1B-$10B | $100M-$500M | 1.2 |
| Enterprise | >$10B | >$500M | 1.5 |

## Key Signals

| Signal | Source | Impact |
|--------|--------|--------|
| Revenue | SEC filings, D&B | Primary band indicator |
| Employee Count | LinkedIn, filings | Secondary band indicator |
| Geographic Scope | DNS, subsidiaries | Complexity factor |
| Industry | SIC/NAICS codes | Sector multiplier |

## References

- **SKILL.md** - Architecture documentation
- **technical_pricing/model/exposure.py** - Implementation

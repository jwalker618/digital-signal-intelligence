# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|demonstration|

---

# DSI Examples

Working examples demonstrating the DSI workflow for all 7 coverage types.

## Prerequisites

```bash
# From repository root
pip install -r requirements.txt
```

## Available Examples

| Script | Coverage | Description |
|--------|----------|-------------|
| `run_aerospace.py` | Aerospace | Aviation and space industry assessment |
| `run_cyber.py` | Cyber | Cybersecurity and data breach coverage |
| `run_do.py` | D&O | Directors & Officers liability |
| `run_energy.py` | Energy | Oil, gas, and renewable energy |
| `run_fi.py` | Financial Institutions | Banks, insurers, asset managers |
| `run_marine.py` | Marine | Hull, cargo, and P&I coverage |
| `run_pi.py` | Professional Indemnity | Professional services E&O |
| `run_multi.py` | Multi-Coverage | Assess entity across multiple coverages |

## Running Examples

### Single Coverage

```bash
# Run from repository root
python examples/run_cyber.py

# Or run directly
cd examples
python run_cyber.py
```

### Multi-Coverage Assessment

```bash
python examples/run_multi.py
```

This runs an entity through multiple coverage types and shows comparative results.

## Example Output

Each example produces output showing:

```
=== DSI Assessment: [Coverage] ===

Entity: [Company Name]
Domain: [Discovered Domain]

Discovery:
  - Confidence: HIGH
  - Method: dns_enumeration

Scoring:
  - Composite Score: 742/1000
  - Confidence: 85%
  - Signal Coverage: 92%

Tier Assignment:
  - Score-based Tier: 2
  - Final Tier: 2 (STANDARD_PLUS)

Decision:
  - Decision: APPROVE
  - Auto-approve: Yes

Premium Options:
  - $1M limit: $12,500
  - $5M limit: $32,000
  - $10M limit: $48,000
```

## Customizing Examples

Each example can be modified to test different scenarios:

```python
# Change entity
result = run_assessment(
    entity_id="my-company-001",
    coverage="cyber",
    entity_name="My Company Inc",
    domain_hint="mycompany.com",
    submission_data={
        "tiv": 50_000_000,
        "limit": 10_000_000,
    }
)

# Add direct query responses
result = run_assessment(
    entity_id="my-company-001",
    coverage="cyber",
    entity_name="My Company Inc",
    direct_query_responses={
        "mfa_enabled": True,
        "security_training": True,
    }
)
```

## Utility Functions

The `utils.py` module provides helper functions:

```python
from examples.utils import print_result, format_premium

# Pretty-print a workflow result
print_result(result)

# Format currency
print(format_premium(25000))  # → $25,000
```

## Notes

- Examples use **stub extractors** that return simulated data
- Results will vary between runs due to random simulation
- For production use, implement real signal extractors

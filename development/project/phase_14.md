# Phase 14: Examples & Final Validation

## Purpose
Provide complete, working examples for all coverages and validate the entire DSI framework end‑to‑end.

## Key Deliverables
- 7 full coverage examples
- Live demo application
- Deployment configurations
- Final validation of all modules

## Implementation Summary
This phase ensures that every coverage has a working example demonstrating the full workflow: discovery → extraction → scoring → pricing → decision. It also includes a demo application and deployment templates.

## Detailed Plan

Working examples for all coverages and complete repository validation.

### 14.1 Coverage Example Scripts

Create runnable examples for each coverage that:
- Demonstrate complete workflow
- Use stub extractors with realistic data
- Output full model execution details
- Serve as integration tests

```python
# examples/run_aerospace_example.py

"""
Complete Aerospace Coverage Example

Demonstrates:
- Discovery workflow
- Signal extraction (stub mode)
- Composite scoring
- Tier assignment
- Premium calculation
- Full audit trail
"""

from technical_pricing.model.workflow import run_assessment
from technical_pricing.model.types import WorkflowResult

def run_example():
    # Example aerospace entity
    result = run_assessment(
        entity_id="boeing-example",
        coverage="aerospace",
        entity_name="Boeing Company",
        domain_hint="boeing.com",
        country_hint="US",
        submission_data={
            "tiv": 500_000_000,
            "fleet_size": 450,
            "annual_departures": 125000,
            "limit_requested": 100_000_000,
        },
        direct_query_responses={
            "grounding_events": False,
            "regulatory_actions": False,
            "accident_history_3yr": False,
        }
    )

    # Output full details
    print_result_summary(result)
    print_signal_breakdown(result)
    print_pricing_breakdown(result)
    print_audit_trail(result)

    return result

def print_result_summary(result: WorkflowResult):
    print("=" * 60)
    print("DSI ASSESSMENT SUMMARY")
    print("=" * 60)
    print(f"Entity: {result.model_version.entity_id}")
    print(f"Coverage: {result.model_version.coverage}")
    print(f"")
    print(f"Discovery:")
    print(f"  Domain: {result.discovered_domain}")
    print(f"  Confidence: {result.discovery_confidence}")
    print(f"")
    print(f"Scoring:")
    print(f"  Composite Score: {result.composite_score}/1000")
    print(f"  Tier: {result.tier} ({result.tier_label})")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"")
    print(f"Decision:")
    print(f"  Decision: {result.decision.value.upper()}")
    print(f"  Auto-Approve: {result.auto_approve}")
    if result.referral_reasons:
        print(f"  Referral Reasons: {result.referral_reasons}")
    print(f"")
    print(f"Premium:")
    print(f"  Recommended: ${result.recommended_premium:,.0f}")
    print(f"  Options: {result.premium_options}")

def print_signal_breakdown(result: WorkflowResult):
    print("=" * 60)
    print("SIGNAL BREAKDOWN")
    print("=" * 60)
    for output in result.model_version.signal_outputs:
        print(f"{output.signal_name}:")
        print(f"  Raw Score: {output.raw_score:.1f}")
        print(f"  Weight: {output.weight:.2f}")
        print(f"  Weighted: {output.weighted_score:.1f}")
        print(f"  Confidence: {output.confidence:.1%}")
        if output.conditions_triggered:
            print(f"  Conditions: {output.conditions_triggered}")

if __name__ == "__main__":
    run_example()
```

### 14.2 Repository Validation Checklist

```markdown
## Pre-Production Validation Checklist

### Code Quality
- [ ] All tests passing (pytest)
- [ ] Test coverage > 80%
- [ ] No linting errors (flake8, mypy)
- [ ] Documentation complete
- [ ] No TODO/FIXME in production code

### Configuration
- [ ] All 7 coverages have valid YAML configs
- [ ] Weight sums verified (= 1.0)
- [ ] Tier thresholds complete (0-1000 coverage)
- [ ] Test profiles defined for each coverage

### Architecture
- [ ] No circular dependencies
- [ ] Clean module boundaries
- [ ] Consistent error handling
- [ ] Logging throughout

### Security
- [ ] No hardcoded credentials
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] Authentication implemented

### Performance
- [ ] Benchmark tests passing
- [ ] Response time < 5s for single quote
- [ ] Memory usage acceptable
- [ ] Database queries optimized

### Documentation
- [ ] README.md complete
- [ ] SKILL.md up to date
- [ ] API documentation (OpenAPI)
- [ ] Deployment guide
- [ ] Troubleshooting guide
```

### 14.3 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create aerospace example | `examples/run_aerospace.py` | ✅ Complete |
| Create cyber example | `examples/run_cyber.py` | ✅ Complete |
| Create do example | `examples/run_do.py` | ✅ Complete |
| Create energy example | `examples/run_energy.py` | ✅ Complete |
| Create fi example | `examples/run_fi.py` | ✅ Complete |
| Create marine example | `examples/run_marine.py` | ✅ Complete |
| Create pi example | `examples/run_pi.py` | ✅ Complete |
| Create multi-coverage example | `examples/run_multi.py` | ✅ Complete |
| Run validation checklist | - | ✅ Complete |
| Fix any identified issues | - | ✅ Complete |
| Final documentation review | `*.md` | ✅ Complete |
| Tag release | - | 🔲 Pending |


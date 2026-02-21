# Phase 1: In-Memory Pydantic Compilation

## 1. Objective
Replace all raw dictionary lookups (`config.get("pricing", {}).get("base_limit_reference")`) with strongly typed, compiled Pydantic models. This provides O(1) attribute access, IDE autocomplete, and guarantees that malformed configurations prevent the application from booting.

## 2. Implementation Framework

### Step 1: Define the Pydantic Hierarchy
Create `infrastructure/models/config_schema.py`. This must perfectly mirror `master_config_layout.yaml`.

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal

class ILFCurveFactor(BaseModel):
    limit: int
    factor: float

class ILFCurve(BaseModel):
    base_limit: int
    factors: List[ILFCurveFactor]

class PricingBlock(BaseModel):
    base_limit_reference: int
    base_deductible_reference: int
    by_product_type: Dict[str, Dict[str, Any]] # Will type this strictly later
    taxes_fees_rate: float = 0.05

    @validator('by_product_type')
    def validate_anchor_presence(cls, v, values):
        # Example: Ensure the base_limit_reference exists in every ILF curve with factor 1.0
        base_limit = values.get('base_limit_reference')
        for prod, data in v.items():
            factors = data.get('ilf_curve', {}).get('factors', [])
            anchor = next((f for f in factors if f.get('limit') == base_limit), None)
            if not anchor or anchor.get('factor') != 1.0:
                raise ValueError(f"Product {prod} ILF curve does not anchor 1.0 at {base_limit}")
        return v
```

### Step 2: The Startup Compiler
Create a bootstrap sequence that loads the YAMLs into these models using @lru_cache so it only executes once.

```python
from functools import lru_cache
import yaml

@lru_cache(maxsize=1)
def get_compiled_configs() -> Dict[str, CoverageModel]:
    with open("coverages/master_registry.yaml") as f: # Or walk directories
        raw_data = yaml.safe_load(f)
    
    # This will instantly throw a ValidationError if the YAML breaks schema
    return {k: CoverageModel(**v) for k, v in raw_data.items()}
```

### Step 3: Engine Refactor
Refactor scorer.py to use dot notation:

```python
# OLD: weight = group.get("risk", {}).get("weight", 0.0)
# NEW: weight = group.risk.weight
```

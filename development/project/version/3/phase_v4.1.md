# Phase 4.1: Metadata-Driven Routing Constraints

## Context
While Phase 4 introduces the "Race-Track" architecture to run multiple configurations in parallel, it currently lacks a sophisticated mechanism to disqualify models based on risk characteristics *before* execution.

Without this, the system is "blind" to commercial intent. It would essentially run a "Cyber SME" model (designed for <$50M revenue) against a Fortune 500 submission, wasting compute resources and potentially returning dangerous quotes if the model tries to extrapolate beyond its design limits.

## Purpose
To implement a hard-filtering logic layer within `DSIMultiplexer` that evaluates **Routing Constraints** defined in each configuration's metadata. This ensures that models only participate in the race if the submission fits their explicit risk profile (e.g., Revenue size, Limit capacity, Employee count).

## 1. Schema Definition

We augment the `metadata` block in `master_config_layout.yaml` and individual coverage configs (e.g., `cyber/config.yaml`).

### Updated Metadata Block
```yaml
metadata:
  name: "Cyber SME Automated"
  model_specificity: 2
  # ... existing fields ...

  # NEW SECTION:
  routing_constraints:
    - field: "revenue"         # The JSON key in the submission payload
      operator: "<="           # Supported: <, >, <=, >=, ==, !=
      value: 50000000          # The threshold value
      required_in_input: true  # If true, missing field = Disqualify Candidate
                               # If false, missing field = Pass (Benefit of doubt)

    - field: "limit"
      operator: "<="
      value: 5000000
      required_in_input: true
```

## 2. Configuration Examples
Scenario A: Cyber SME (Restricted Entry)
Target: Small businesses with revenue under $50M, seeking limits up to $5M.

```yaml
cyber:
  cyber_sme:
    metadata:
      routing_constraints:
        - { field: "revenue", operator: "<=", value: 50000000, required_in_input: true }
        - { field: "limit", operator: "<=", value: 5000000, required_in_input: true }
```

Scenario B: Cyber Corporate (Restricted Entry)
Target: Mid-to-Large Corps with revenue over $50M, or seeking limits > $5M.

```yaml
cyber:
  cyber_corp:
    metadata:
      routing_constraints:
        # Note: We use 'false' for required_in_input here if we want to allow 
        # the Corporate model to pick up cases where revenue is unknown (safety net),
        # or 'true' to force strict validation.
        - { field: "revenue", operator: ">", value: 50000000, required_in_input: true }
        - { field: "limit", operator: "<=", value: 100000000, required_in_input: true }
```

## 3. Implementation Logic
The DSIMultiplexer must implement a robust constraint checker that handles:
1. Missing Data: What if revenue isn't in the payload?
2. Type Safety: Comparing strings to integers safely.
3. Operator Logic: Handling standard comparisons.

Updated Component: multiplexer/broker.py
This replaces the basic _check_constraints placeholder in Phase 4.

```python
import operator

class DSIMultiplexer:
    # ... existing __init__ ...

    # Map string symbols to python operator functions
    OPS = {
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        '==': operator.eq,
        '!=': operator.ne
    }

    def _check_constraints(self, constraints: list, user_input: dict) -> bool:
        """
        Evaluates a list of routing constraints against the user input.
        Returns True if ALL constraints pass.
        Returns False if ANY constraint fails.
        """
        if not constraints:
            return True

        for rule in constraints:
            field = rule.get('field')
            op_sym = rule.get('operator')
            target_val = rule.get('value')
            is_required = rule.get('required_in_input', True)

            # 1. Handle Missing Fields
            if field not in user_input:
                if is_required:
                    # Strict fail: The model NEEDS this field to decide
                    return False
                else:
                    # Permissive pass: Field missing, but rule not strict
                    continue

            # 2. Extract Value
            actual_val = user_input[field]

            # 3. Type Safety / Conversion (Basic)
            # Ensure we don't crash comparing "500" (str) > 100 (int)
            try:
                if isinstance(target_val, (int, float)) and isinstance(actual_val, str):
                    actual_val = float(actual_val)
            except ValueError:
                # If conversion fails, we can't evaluate mathematical ops
                # Default to Fail for safety
                return False

            # 4. Evaluate Operator
            op_func = self.OPS.get(op_sym)
            if not op_func:
                # Configuration Error: Unknown operator
                # Log warning in real impl
                return False

            if not op_func(actual_val, target_val):
                return False

        return True
```        

## 4. Integration Point
This logic sits inside the identify_candidates loop defined in Phase 4.

```python
def identify_candidates(self, user_input: Dict[str, Any]) -> List[Dict]:
        candidates = []
        for cfg in self.configs:
            meta = cfg.get('metadata', {})
            
            # ... Product/Market checks ...

            # NEW: Robust Constraint Check
            constraints = meta.get('routing_constraints', [])
            if self._check_constraints(constraints, user_input):
                candidates.append(cfg)
                
        return candidates
```

## 5. Migration Tasks
1. Code: Update multiplexer/broker.py with the robust _check_constraints method and OPS dictionary.
2. Config: Update cyber/config.yaml (and others) to split monolithic definitions into segmented definitions (e.g., cyber_sme, cyber_corp) with appropriate constraints.
3. Testing: Create a unit test test_routing_constraints.py that passes various payloads (missing fields, wrong types, boundary values) to ensure the filter behaves as expected.

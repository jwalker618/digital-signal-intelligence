# Phase 4: Multi-Configuration Multiplexer

##Context
The existing process - which loads a coverage / configuration in isolation - requires augmentation. 
Ultimately, the minimum viable inputs to each configuration are likely to be very similar. But they will differ by product type, applicable markets, signal weights etc.
So, we need a mechanism that identifies all valid configurations based on a single set of minimum_viable_inputs and then executes those configurations,
making sure to reuse discovery; signals; and any other relevant items when possible, in parallel.
This would return multiple results, all of which need to be stored (to enable analysis at a later date, and operating as proxy scenarios to enable model tuning.
Each of the results would then be compared for applicability, say total % of signals successfully returned - a proxy for model confidence, and overall potential profitability.
One would be selected and this would move forwards to be bound, declined, or refered.

## Purpose
Implement a **"Signal Broker"** and **"Configuration Multiplexer"** architecture. This mechanism enables the system to dynamically discover all applicable configurations 
for a submission (e.g., *Cyber General*, *Cyber Tech*, *Cyber SME*), deduplicate their required signals, execute them once in parallel, and arbitrate the results to 
select the optimal commercial outcome.

## Key Deliverables
- **Metadata Schema Update**: Extensions for `model_specificity` and `routing_constraints`.
- **Signal Broker (`DSIMultiplexer`)**: A class to unionise signal requirements across multiple configs.
- **Result Arbiter (`ConfigArbiter`)**: Logic to rank outcomes based on validity, confidence, specificity, and margin.
- **Execution Harness**: Updated main entry point to support "Fan-Out/Fan-In" execution.

## Implementation Summary
This phase shifts the application from a "Single-Track" execution model to a "Race-Track" model. Instead of picking one configuration upfront, we pick *all valid candidates*, 
let them race using a shared pool of signal data, and algorithmically select the winner.

## Detailed Plan

### 4.1 Architecture: The Multiplexer Loop

The new architecture introduces a layer *above* the individual pricing models.

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                       DSI MULTIPLEXER ARCHITECTURE                      │
│                                                                         │
│  1. DISCOVERY                2. SIGNAL BROKER         3. FAN-OUT        │
│  ┌──────────────┐            ┌──────────────┐         ┌─────────────┐   │
│  │User Input    │            │Union of all  │         │Config A     │   │
│  │(Product/Mkt) │ ─────────> │Signal IDs    │ ──────> │Logic Engine │   │
│  └──────┬───────┘            │(Deduped)     │    ┌──> └──────┬──────┘   │
│         │                    └──────┬───────┘    │           │          │
│         │                           │            │    ┌─────────────┐   │
│  ┌──────▼───────┐            ┌──────▼───────┐    ├──> │Config B     │   │
│  │Config        │            │Parallel      │    │    │Logic Engine │   │
│  │Registry      │            │Execution     │ ───┘    └──────┬──────┘   │
│  │(Filter Metadata)          └──────────────┘                │          │
│  └──────────────┘                                            │          │
│                                                              │          │
│                                                       4. ARBITRATION    │
│                                                       ┌──────▼──────┐   │
│                                                       │ConfigArbiter│   │
│                                                       │(Select Best)│   │
│                                                       └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Schema Updates (master_config_layout.yaml)
We must update the metadata section to support arbitration logic.

metadata:
  # ... existing fields ...
  
  # NEW: Specificity Score (1-5)
  # Used by Arbiter: If two models approve, the one with higher specificity wins.
  # 1 = General/Base, 2 = Segment Specific, 3 = Niche/Bespoke
  model_specificity: 2

  # NEW: Routing Constraints
  # Hard filters to optimize candidate selection BEFORE signal execution.
  # Prevents running "SME" models for "Enterprise" clients.
  routing_constraints:
    - field: "revenue"         # Checks input JSON
      operator: "<"            # <, >, <=, >=, ==
      value: 50000000          # Threshold
      required_in_input: false # If false, passes if field is missing

### 4.3 The Signal Broker (DSIMultiplexer)
This class is responsible for identifying candidates and optimising signal retrieval.

# technical_pricing/multiplexer/broker.py

```python
from typing import List, Dict, Any
from technical_pricing.configuration import ConfigLoader
from technical_pricing.signals import SignalExecutor

class DSIMultiplexer:
    def __init__(self, config_registry: List[Dict]):
        self.configs = config_registry

    def identify_candidates(self, user_input: Dict[str, Any]) -> List[Dict]:
        """
        Scans all loaded configs. Returns those matching:
        1. Product Type
        2. Market/Locale
        3. Hard Routing Constraints (Revenue, TIV, etc.)
        """
        candidates = []
        for cfg in self.configs:
            meta = cfg.get('metadata', {})
            
            # Basic Filtering
            if user_input.get('product_type') not in meta.get('product_types', []):
                continue
            if user_input.get('market') not in meta.get('applicable_markets', []):
                continue
                
            # Constraint Checking
            if self._check_constraints(meta.get('routing_constraints', []), user_input):
                candidates.append(cfg)
                
        return candidates

    def optimize_signals(self, candidates: List[Dict]) -> Dict[str, Any]:
        """
        Extracts unique signal_ids from all candidate configs.
        Returns a dict of {signal_id: inference_utility_function} to execute.
        """
        unique_signals = {}
        for cfg in candidates:
            # Flatten signals from all candidates
            for signal in cfg.get('signal_registry', []):
                # Assumes 'id' is unique per function signature
                if signal['id'] not in unique_signals:
                    unique_signals[signal['id']] = signal['inference_utility_function']
        
        return unique_signals

    async def execute(self, user_input: Dict[str, Any]):
        # 1. Find Candidates
        candidates = self.identify_candidates(user_input)
        if not candidates:
            return {"error": "No matching configuration found"}

        # 2. Broker Signals (Dedup)
        # Returns a map of what needs to be fetched
        signal_map = self.optimize_signals(candidates)
        
        # 3. Execute Signals (Once, Parallel)
        # Assuming SignalExecutor handles the async lifting defined in Phase 15
        signal_results = await SignalExecutor.execute_batch(signal_map, user_input)
        
        # 4. Fan-Out: Inject results into each config
        quote_results = []
        for cfg in candidates:
            # The Logic Engine must be updated to accept pre-calculated signals
            quote = LogicEngine(cfg).evaluate(user_input, precomputed_signals=signal_results)
            quote_results.append(quote)
            
        return quote_results
        
    def _check_constraints(self, constraints: List[Dict], user_input: Dict) -> bool:
        """Evaluates constraints like revenue < 50000000"""
        for c in constraints:
            field = c['field']
            if field not in user_input:
                if c.get('required_in_input', False):
                    return False
                continue
            
            val = user_input[field]
            target = c['value']
            op = c['operator']
            
            if op == '<' and not (val < target): return False
            if op == '>' and not (val > target): return False
            if op == '<=' and not (val <= target): return False
            if op == '>=' and not (val >= target): return False
            if op == '==' and not (val == target): return False
            
        return True
```

### 4.4 The Arbiter (ConfigArbiter)
This component selects the "Winner" from the list of quote_results.

# technical_pricing/multiplexer/arbiter.py

```python
from typing import List, Dict

class ConfigArbiter:
    def select_best_outcome(self, results: List[Dict]) -> Dict:
        """
        Selection Hierarchy:
        1. Validity (Action != DECLINE)
        2. Signal Confidence (Data completeness)
        3. Specificity (Niche > General)
        4. Commercial (Highest Premium? Lowest? Configurable strategy)
        """
        
        # 1. Filter Declines (unless all declined)
        approved = [r for r in results if r['decision']['action'] != 'DECLINE']
        
        if not approved:
            # If all declined, return the "best" decline (e.g. most specific reason)
            # Sorting by specificity descending to give the most detailed "No"
            results.sort(key=lambda x: x['config_metadata']['model_specificity'], reverse=True)
            return results[0]
            
        # 2. Filter Low Confidence (e.g., < 70% signals found)
        # We prefer a General model with 100% data over a Niche model with 20% data
        confident = [r for r in approved if r['meta'].get('signal_completeness', 0) >= 0.7]
        
        # Fallback to approved list if no high-confidence results exist
        candidates = confident if confident else approved
        
        # 3. Sort by Specificity (High to Low) then Margin (High to Low)
        # 'pricing.final_premium' is a proxy for commercial value here
        candidates.sort(key=lambda x: (
            x['config_metadata'].get('model_specificity', 1), # Primary Sort: Specificity
            x['pricing'].get('final_premium', 0)              # Secondary Sort: Premium
        ), reverse=True)
        
        return candidates[0]

```

### 4.5 Integration into main.py
The entry point simply changes from initialising one model to initialising the Multiplexer.

# main.py (Updated)

```python
async def handle_submission(submission_payload):
    # Load all YAMLs in config/ directory
    registry = ConfigLoader.load_all() 
    
    # Initialize Multiplexer
    mux = DSIMultiplexer(registry)
    arbiter = ConfigArbiter()
    
    # Execute Race
    all_results = await mux.execute(submission_payload)
    
    # Pick Winner
    final_decision = arbiter.select_best_outcome(all_results)
    
    return final_decision

```

### 4.6 Logic Engine Updates
We must modify the LogicEngine to support Fan-In execution.

# technical_pricing/engine/logic_engine.py

```python
class LogicEngine:
    def __init__(self, config):
        self.config = config

    def evaluate(self, user_input, precomputed_signals=None):
        """
        Modified evaluate method.
        If precomputed_signals is provided, skip internal fetching.
        """
        
        # 1. Determine Signal Source
        if precomputed_signals:
            # EXTRACT only what this config needs from the master pool
            current_signals = self._map_signals(precomputed_signals)
        else:
            # Legacy/Single mode: fetch purely for this config
            current_signals = self._fetch_signals(user_input)
            
        # 2. Calculate Completeness (New Metric)
        completeness = self._calculate_completeness(current_signals)
        
        # 3. Run Standard Logic (Scoring, Tiers, etc.)
        # ... existing logic ...
        
        result = {
            # ... existing result structure ...
            "meta": {
                "signal_completeness": completeness,
                # ...
            },
            "config_metadata": self.config['metadata'] # Pass metadata for Arbiter
        }
        
        return result

    def _map_signals(self, master_pool):
        """Filters the master pool for signals used by this config"""
        mapped = {}
        for signal_def in self.config['signal_registry']:
            sig_id = signal_def['id']
            if sig_id in master_pool:
                mapped[sig_id] = master_pool[sig_id]
            else:
                mapped[sig_id] = None # Handle missing signals
        return mapped
        
    def _calculate_completeness(self, signals):
        """Returns float 0.0 - 1.0"""
        if not signals: return 0.0
        valid = sum(1 for v in signals.values() if v is not None)
        return valid / len(signals)

```

### Implementation Tasks

|Category|Task|File|Status|
|-|-|-|-|
|Schema|Update master_config_layout.yaml with model_specificity and routing_constraints|config/master_config_layout.yaml|🔲 Pending|
|Schema|Update config/cyber/config.yaml to include new metadata fields|config/cyber/config.yaml|🔲 Pending|
|Broker|Implement DSIMultiplexer class|multiplexer/broker.py|🔲 Pending|
|Broker|Implement identify_candidates filtering logic|multiplexer/broker.py|🔲 Pending|
|Broker|Implement optimize_signals deduplication logic|multiplexer/broker.py|🔲 Pending|
|Arbiter|Implement ConfigArbiter class|multiplexer/arbiter.py|🔲 Pending|
|Arbiter|Implement sorting logic (validity > confidence > specificity)|multiplexer/arbiter.py|🔲 Pending|
|Engine|Update LogicEngine.evaluate to accept precomputed_signals|engine/logic_engine.py|🔲 Pending|
|Engine|Implement _calculate_completeness method|engine/logic_engine.py|🔲 Pending|
|Testing|Unit test: test_multiplexer_candidate_selection|tests/unit/test_multiplexer.py|🔲 Pending|
|Testing|Unit test: test_arbiter_specificity_logic|tests/unit/test_multiplexer.py|🔲 Pending|
|Testing|Integration test: Full Fan-Out/Fan-In cycle|tests/integration/test_full_cycle.py|🔲 Pending|

### Integration Notes

1. **Signal "Fan-In" & Reliability**: Completeness Metric: The LogicEngine must now return a signal_completeness metric (Signals_Returned_Non_Null / Signals_Defined_In_Registry). This is critical for the Arbiter to reject "phantom" approvals where a model approves simply because it lacked data to trigger flags.
2. **Error Handling**: Global Failures: If a specific signal fails (e.g., shodan_api_down), it affects all configurations that use it.
3. **Error Handling**: Graceful Degradation: The Broker will pass null or error for that signal. Individual configurations must handle the null gracefully (via proxy_tier fallbacks already defined in config.yaml).
4. **Performance**: Parallelism: The SignalExecutor (Phase 15) handles the async fetching. The Broker merely orchestrates the request. This ensures that adding 5 more configurations adds negligible time to the overall request, as the I/O is the bottleneck and it is deduplicated.

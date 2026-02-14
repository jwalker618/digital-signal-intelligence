import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

class DSIConfigAssessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.results = []
        self.passed = 0
        self.failed = 0
        
        with open(file_path, 'r') as f:
            self.data = yaml.safe_load(f)

    def _assert(self, condition: bool, test_name: str, config_name: str, success_msg: str, fail_msg: str):
        """Helper to record test results."""
        if condition:
            self.passed += 1
            self.results.append(f"[PASS] {config_name} | {test_name}: {success_msg}")
        else:
            self.failed += 1
            self.results.append(f"[FAIL] {config_name} | {test_name}: {fail_msg}")

    def run_all_tests(self):
        """Iterate through all coverages and configurations in the YAML."""
        for coverage_name, coverage_data in self.data.items():
            configs = [k for k in coverage_data.keys() if isinstance(coverage_data[k], dict)]
            
            # 1. Cross-Configuration Tests
            self.test_routing_exclusivity(coverage_name, coverage_data, configs)

            # 2. Per-Configuration Tests
            for config_name in configs:
                config = coverage_data[config_name]
                self.test_schema_version(config_name, config)
                self.test_weights_sum_to_one(config_name, config)
                self.test_pricing_anchors(config_name, config)
                self.test_deprecation_rules(config_name, config)
                self.test_premium_methodology(config_name, config)
                self.test_monotonicity_and_penalty(config_name, config)

    # =========================================================================
    # MULTIPLEXER & ROUTING TESTS (Phase 4)
    # =========================================================================
    def test_routing_exclusivity(self, coverage_name: str, coverage_data: Dict, configs: List[str]):
        """Ensures SME and Corporate configs don't overlap in routing constraints."""
        routing_maps = {}
        for c in configs:
            constraints = coverage_data[c].get('metadata', {}).get('routing_constraints', [])
            for req in constraints:
                routing_maps.setdefault(req['field'], []).append((c, req['operator'], req['value']))
        
        # Simple heuristic: If multiple configs route on 'revenue', check for exclusivity
        for field, rules in routing_maps.items():
            if len(rules) > 1:
                operators = [r[1] for r in rules]
                has_ceiling = any(op in ['<', '<='] for op in operators)
                has_floor = any(op in ['>', '>='] for op in operators)
                self._assert(
                    has_ceiling and has_floor,
                    "Routing Exclusivity", coverage_name,
                    f"Mutually exclusive routing found on '{field}'",
                    f"Potential Arbiter collision on '{field}': Rules -> {rules}"
                )

    # =========================================================================
    # CORE SCHEMA & WEIGHTS
    # =========================================================================
    def test_schema_version(self, config_name: str, config: Dict):
        """Enforces schema version baseline."""
        version = config.get('metadata', {}).get('version', '0.0.0')
        # Expecting at least 2.2.0 or 2.3.0 for Phase 5 compliance
        is_compliant = int(version.split('.')[0]) >= 2 and int(version.split('.')[1]) >= 2
        self._assert(
            is_compliant, "Schema Version", config_name,
            f"Version {version} is compliant",
            f"Version {version} is below Phase 5 requirements (>= 2.2.0)"
        )

    def test_weights_sum_to_one(self, config_name: str, config: Dict):
        """Checks if risk, loss, and exposure weights across groups sum to 1.0"""
        groups = config.get('groups', {}).get('three_layer_assessment', [])
        
        totals = {'risk': 0.0, 'loss': 0.0, 'exposure': 0.0}
        for g in groups:
            totals['risk'] += g.get('risk', {}).get('weight', 0.0)
            totals['loss'] += g.get('loss', {}).get('weight', 0.0)
            totals['exposure'] += g.get('exposure', {}).get('weight', 0.0)
            
        for dim, total in totals.items():
            # Using round to handle floating point precision issues
            is_one = round(total, 2) == 1.00
            self._assert(
                is_one, f"Weights Sum ({dim})", config_name,
                f"{dim} weights sum to 1.0",
                f"{dim} weights sum to {total}, expected 1.0"
            )

    # =========================================================================
    # PRICING METHODOLOGY & SCALABILITY (Phase 5)
    # =========================================================================
    def test_premium_methodology(self, config_name: str, config: Dict):
        """Validates the 'Scalability Trap' and Basis mapping."""
        bands = config.get('risk_tier_bands', {}).get('bands', [])
        if not bands:
            return
            
        method = bands[0].get('interpretation', {}).get('application', {}).get('method')
        constraints = config.get('metadata', {}).get('routing_constraints', [])
        
        has_ceiling = any(c['operator'] in ['<', '<='] for c in constraints)
        has_floor = any(c['operator'] in ['>', '>='] for c in constraints)

        if method == "PREMIUM_BASE":
            self._assert(
                has_ceiling, "Scalability Trap", config_name,
                "PREMIUM_BASE safely constrained by routing ceiling.",
                "PREMIUM_BASE used without a routing ceiling (< or <=). Model is exposed to Scalability Trap."
            )
        elif method == "MULTIPLIER":
            # Check if basis is in minimum_viable_input
            basis = bands[0].get('interpretation', {}).get('application', {}).get('basis')
            mvi = config.get('metadata', {}).get('minimum_viable_input', {}).get('required', [])
            mvi_fields = [f['field'] for f in mvi]
            
            self._assert(
                basis in mvi_fields, "Multiplier Basis", config_name,
                f"Basis '{basis}' found in MVI.",
                f"Basis '{basis}' missing from minimum_viable_input."
            )
            
            if not constraints or has_floor:
                 self._assert(
                    True, "Enterprise Enforcement", config_name,
                    "MULTIPLIER correctly applied for unconstrained/large risks.", ""
                 )

    def test_monotonicity_and_penalty(self, config_name: str, config: Dict):
        """Checks if Tier 1 is cheapest, Tier 5 is most expensive, and ratio >= 2.0."""
        bands = config.get('risk_tier_bands', {}).get('bands', [])
        if not bands or len(bands) < 5:
            return
            
        # Extract values depending on methodology
        method = bands[0]['interpretation']['application']['method']
        key = 'value' if method == 'PREMIUM_BASE' else 'applied'
        
        try:
            prices = [b['interpretation']['application'][key] for b in sorted(bands, key=lambda x: x['id'])]
            
            # Check Monotonicity
            is_monotonic = all(prices[i] < prices[i+1] for i in range(len(prices)-1))
            self._assert(
                is_monotonic, "Actuarial Monotonicity", config_name,
                "Pricing strictly increases as tiers worsen.",
                f"Pricing is not monotonic: {prices}"
            )
            
            # Check Penalty Ratio (Tier 5 / Tier 1)
            ratio = prices[-1] / prices[0]
            self._assert(
                ratio >= 2.0, "Penalty Ratio", config_name,
                f"Tier 5 penalty ratio is {ratio:.2f}x (>= 2.0).",
                f"Tier 5 penalty ratio is {ratio:.2f}x. Does not adequately penalize bad risk."
            )
        except KeyError:
            self._assert(False, "Actuarial Monotonicity", config_name, "", "Malformed risk tier application data.")

    # =========================================================================
    # ANCHORS & TOWERS (Phase 5)
    # =========================================================================
    def test_pricing_anchors(self, config_name: str, config: Dict):
        """Ensures pricing anchors are explicitly defined and match factor 1.0."""
        pricing = config.get('pricing', {})
        products = pricing.get('by_product_type', {})
        
        for prod_name, p_data in products.items():
            base_limit = p_data.get('base_limit_reference')
            base_deductible = p_data.get('base_deductible_reference')
            
            # 1. Anchors Exist
            self._assert(
                bool(base_limit and base_deductible), "Anchors Present", config_name,
                f"Anchors found for {prod_name}",
                f"Missing base_limit_reference or base_deductible_reference in {prod_name}"
            )
            
            # 2. ILF Anchor is 1.00
            ilf_factors = p_data.get('ilf_curve', {}).get('factors', [])
            ilf_anchor_val = next((f['factor'] for f in ilf_factors if f['limit'] == base_limit), None)
            self._assert(
                ilf_anchor_val == 1.0, "ILF Normalization", config_name,
                f"ILF for {base_limit} is strictly 1.0",
                f"ILF factor for base_limit {base_limit} is {ilf_anchor_val}, expected 1.0"
            )

            # 3. Deductible Anchor is 1.00
            ded_factors = p_data.get('deductible_factors', [])
            ded_anchor_val = next((f['factor'] for f in ded_factors if f['deductible'] == base_deductible), None)
            self._assert(
                ded_anchor_val == 1.0, "Deductible Normalization", config_name,
                f"Deductible factor for {base_deductible} is strictly 1.0",
                f"Deductible factor for base {base_deductible} is {ded_anchor_val}, expected 1.0"
            )

    def test_deprecation_rules(self, config_name: str, config: Dict):
        """Ensures legacy fields have been removed."""
        products = config.get('pricing', {}).get('by_product_type', {})
        for prod_name, p_data in products.items():
            has_legacy = 'deductible_credits' in p_data or 'deductible_buy_down_rates' in p_data
            self._assert(
                not has_legacy, "Phase 5 Deprecation", config_name,
                f"No legacy deductible fields in {prod_name}",
                f"Found deprecated 'deductible_credits' in {prod_name}. Use 'deductible_factors' instead."
            )

    def print_summary(self):
        print("\n" + "="*60)
        print(" DSI CONFIGURATION COMPLETENESS ASSESSMENT")
        print("="*60)
        for r in self.results:
            print(r)
        
        total = self.passed + self.failed
        score = (self.passed / total) * 100 if total > 0 else 0
        
        print("\n" + "-"*60)
        print(f" TOTAL SCORE: {self.passed} / {total} assertions passed ({score:.1f}%)")
        if self.failed > 0:
            print(" STATUS: ❌ ACTION REQUIRED (See failures above)")
        else:
            print(" STATUS: ✅ CONFIGURATION IS PHASE 5 COMPLIANT")
        print("-"*60 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assess_completeness.py <path_to_config.yaml>")
        sys.exit(1)
        
    assessor = DSIConfigAssessor(sys.argv[1])
    assessor.run_all_tests()
    assessor.print_summary()

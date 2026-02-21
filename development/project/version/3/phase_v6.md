# Phase 6: Schema Consolidation & Builder Modernization

## Context

The DSI platform has evolved through several phases:
- **Phase V4**: Introduced the Multiplexer architecture with `model_specificity` and `routing_constraints`
- **Phase V4.1**: Enhanced routing constraints with type safety and comprehensive validation
- **Phase V5**: Defined Advanced Pricing Architecture (Anchors & Towers) with `base_limit_reference`, `base_deductible_reference`, and BUNDLED/DECOUPLED modes

However, these changes exist only in planning documents and schema definitions. The Coverage Builder (`infrastructure/builder/coverage_builder.py`) still generates v2.0.0 configs using the deprecated `deductible_credits` structure. The existing coverage configs require migration to the new v2.2.0 schema.

## Purpose

Implement a comprehensive modernization that:
1. **Upgrades the Coverage Builder** to generate v2.2.0 compliant configs
2. **Migrates all existing coverage configs** to the new schema
3. **Removes deprecated structures** (deductible_credits → deductible_factors)
4. **Updates documentation** to reflect current architecture

This phase operationalizes the theoretical work from V4/V5 into production-ready tooling.

## Key Deliverables

1. **Builder v2.2.0**: Updated Coverage Builder supporting V4/V5 schema features
2. **Config Migration**: All 7 coverage types migrated to v2.2.0 schema
3. **Documentation Cleanup**: LaTeX rendering fixes, deprecated reference removal
4. **Validation Updates**: Schema validators updated for new structures

## Detailed Plan

### 6.1 Coverage Builder Modernization

The Coverage Builder requires updates across multiple methods to support the v2.2.0 schema.

#### A. Metadata Updates (`_build_metadata`)

Current (v2.0.0):
```python
def _build_metadata(self, spec: CoverageSpec) -> Dict[str, Any]:
    return {
        "name": f"DSI {spec.name} Technical Pricing Model",
        "version": "2.0.0",
        "coverage_type": spec.coverage_type,
        "schema_compliant": True,
        "generated_timestamp": datetime.now().isoformat(),
        # Missing V4 fields
    }
```

Target (v2.2.0):
```python
def _build_metadata(self, spec: CoverageSpec) -> Dict[str, Any]:
    return {
        "name": f"DSI {spec.name} Technical Pricing Model",
        "version": "2.2.0",  # Updated version
        "coverage_type": spec.coverage_type,
        "schema_compliant": True,
        "generated_timestamp": datetime.now().isoformat(),
        # V4 Multiplexer Support
        "model_specificity": spec.model_specificity,  # 1-5 scale
        "routing_constraints": spec.routing_constraints,  # List of constraints
    }
```

#### B. Pricing Structure Updates (`_build_pricing`)

Current (deductible_credits):
```python
def _build_pricing(self) -> Dict[str, Any]:
    return {
        "ilf_curve": {...},
        "deductible_credits": [
            {"min_pct": 0.001, "max_pct": 0.005, "credit": 0.05},
            {"min_pct": 0.005, "max_pct": 0.010, "credit": 0.10},
            ...
        ],
        "taxes_fees_rate": 0.05,
    }
```

Target (deductible_factors + anchors):
```python
def _build_pricing(self, spec: CoverageSpec) -> Dict[str, Any]:
    return {
        # V5 Pricing Anchors
        "base_limit_reference": spec.base_limit_reference,  # e.g., 1000000
        "base_deductible_reference": spec.base_deductible_reference,  # e.g., 50000
        "ilf_curve": {...},
        # V5 Deductible Factors (replaces deductible_credits)
        "deductible_factors": self._build_deductible_factors(spec),
        "taxes_fees_rate": 0.05,
    }

def _build_deductible_factors(self, spec: CoverageSpec) -> List[Dict]:
    """Generate deductible factor table with anchor = 1.00"""
    return [
        {"deductible": 25000, "factor": 1.15},
        {"deductible": spec.base_deductible_reference, "factor": 1.00},  # Anchor
        {"deductible": 100000, "factor": 0.85},
        {"deductible": 250000, "factor": 0.70},
    ]
```

#### C. Limit Configuration Support

New method for DECOUPLED mode (Corporate/Enterprise):
```python
def _build_limit_configuration(self, spec: CoverageSpec) -> Dict[str, Any]:
    """Generate limit configuration for DECOUPLED mode"""
    if spec.pricing_mode == "BUNDLED":
        return None  # Use limit_bandings instead

    return {
        "type": "DECOUPLED",
        "valid_limits": spec.valid_limits or [1000000, 5000000, 10000000],
        "valid_deductibles": spec.valid_deductibles or [25000, 50000, 100000, 250000],
    }
```

#### D. CoverageSpec Dataclass Extension

```python
@dataclass
class CoverageSpec:
    name: str
    coverage_type: str
    industry: str
    # ... existing fields ...

    # V4 Multiplexer fields
    model_specificity: int = 1  # 1=General, 2=Segment, 3=Niche, 4=Bespoke, 5=Custom
    routing_constraints: List[Dict[str, Any]] = field(default_factory=list)

    # V5 Pricing Anchor fields
    base_limit_reference: int = 1000000
    base_deductible_reference: int = 50000
    pricing_mode: str = "BUNDLED"  # BUNDLED or DECOUPLED
    valid_limits: Optional[List[int]] = None
    valid_deductibles: Optional[List[int]] = None
```

### 6.2 Config Migration Strategy

All existing coverage configs must be migrated from v2.0/v2.1 to v2.2.0.

#### Migration Checklist per Coverage

| Coverage | Status | V4 Fields | V5 Pricing | deductible_factors |
|----------|--------|-----------|------------|-------------------|
| aerospace | Pending | Add | Add | Convert |
| cyber | Pending | Add | Add | Convert |
| do | Pending | Add | Add | Convert |
| energy | Pending | Add | Add | Convert |
| fi | Pending | Add | Add | Convert |
| marine | Pending | Add | Add | Convert |
| pi | Pending | Add | Add | Convert |

#### Migration Script Approach

The modernized builder should include a migration utility:

```python
class ConfigMigrator:
    def migrate_to_v2_2(self, config_path: str) -> None:
        """Migrate a v2.0/v2.1 config to v2.2.0"""
        config = self._load_config(config_path)

        # 1. Add V4 metadata if missing
        if 'model_specificity' not in config['metadata']:
            config['metadata']['model_specificity'] = 1
            config['metadata']['routing_constraints'] = []

        # 2. Add V5 pricing anchors
        if 'base_limit_reference' not in config['pricing']:
            config['pricing']['base_limit_reference'] = self._infer_limit_anchor(config)
            config['pricing']['base_deductible_reference'] = self._infer_ded_anchor(config)

        # 3. Convert deductible_credits to deductible_factors
        if 'deductible_credits' in config['pricing']:
            config['pricing']['deductible_factors'] = self._convert_credits_to_factors(
                config['pricing'].pop('deductible_credits'),
                config['pricing']['base_deductible_reference']
            )

        # 4. Update version
        config['metadata']['version'] = '2.2.0'

        self._save_config(config_path, config)

    def _convert_credits_to_factors(self, credits: List[Dict], anchor_ded: int) -> List[Dict]:
        """Convert percentage-based credits to fixed deductible factors"""
        # Logic to map credit percentages to fixed deductibles
        ...
```

### 6.3 Documentation Updates

#### Premium_Calculation_Methodology.md Fixes

1. **LaTeX Rendering**: Fix inline math delimiters
   - Change: `$P_{base}$` → `$P_{base}$` (ensure proper escaping)
   - Change: `$$formula$$` → proper block math syntax

2. **Deprecated References**: Remove all `deductible_credits` mentions
   - Replace with `deductible_factors` structure
   - Update formulas to use factor multiplication instead of credit subtraction

3. **New Sections**: Add documentation for:
   - Pricing Anchors (base_limit_reference, base_deductible_reference)
   - ILF Relativity calculation
   - BUNDLED vs DECOUPLED modes

### 6.4 Validation Updates

Schema validators must be updated to:
1. Require `deductible_factors` (error if `deductible_credits` present)
2. Validate anchor constraints:
   - `base_limit_reference` must exist in `ilf_curve` keys
   - `base_deductible_reference` must have `factor: 1.00` in `deductible_factors`
3. Validate `model_specificity` is 1-5
4. Validate `routing_constraints` structure and operators

## Implementation Tasks

| Priority | Category | Task | File | Status |
|----------|----------|------|------|--------|
| 1 | Builder | Update CoverageSpec dataclass with V4/V5 fields | coverage_builder.py | Pending |
| 1 | Builder | Update _build_metadata() for v2.2.0 | coverage_builder.py | Pending |
| 1 | Builder | Update _build_pricing() with anchors + factors | coverage_builder.py | Pending |
| 1 | Builder | Add _build_deductible_factors() method | coverage_builder.py | Pending |
| 1 | Builder | Add _build_limit_configuration() for DECOUPLED | coverage_builder.py | Pending |
| 2 | Migration | Create ConfigMigrator class | coverage_builder.py | Pending |
| 2 | Migration | Implement credits_to_factors conversion | coverage_builder.py | Pending |
| 3 | Migration | Migrate aerospace config | coverages/aerospace/config.yaml | Pending |
| 3 | Migration | Migrate cyber config | coverages/cyber/config.yaml | Pending |
| 3 | Migration | Migrate do config | coverages/do/config.yaml | Pending |
| 3 | Migration | Migrate energy config | coverages/energy/config.yaml | Pending |
| 3 | Migration | Migrate fi config | coverages/fi/config.yaml | Pending |
| 3 | Migration | Migrate marine config | coverages/marine/config.yaml | Pending |
| 3 | Migration | Migrate pi config | coverages/pi/config.yaml | Pending |
| 4 | Docs | Fix LaTeX rendering in Premium_Calculation_Methodology.md | docs/overview/ | Pending |
| 4 | Docs | Remove deductible_credits references | docs/overview/ | Pending |
| 5 | Validation | Update schema validators for v2.2.0 | validators/schema.py | Pending |
| 5 | Testing | Unit tests for builder V4/V5 methods | tests/ | Pending |
| 5 | Testing | Migration tests | tests/ | Pending |

## Success Criteria

1. **Builder Generates v2.2.0**: All generated configs include V4/V5 fields
2. **No Deprecated Structures**: Zero references to `deductible_credits` in configs or docs
3. **Anchor Validation**: All configs have valid pricing anchors with proper constraints
4. **Migration Complete**: All 7 coverages migrated and passing validation
5. **Tests Pass**: All existing tests pass, new tests cover V4/V5 features
6. **Documentation Accurate**: LaTeX renders correctly, reflects current architecture

## Dependencies

- Phase V4.1 (Complete): Routing constraints with type safety
- Phase V5 (Design Complete): Pricing Anchors & Towers architecture
- Phase V3-3 (Optional): LLM Builder integration (can be done post-V6)

## Risk Mitigation

1. **Breaking Changes**: The `deductible_credits` → `deductible_factors` migration is breaking. All downstream consumers must be updated simultaneously.
2. **Data Integrity**: Conversion logic must preserve the economic intent of the original credits. Include validation that computes equivalent credit values for spot-checking.
3. **Rollback Plan**: Maintain v2.1.0 tagged configs until V6 is fully validated in staging.

## Post-V6 Considerations

- Phase V3-3 (LLM Builder): Once V6 is complete, LLM integration can enhance the builder for smarter signal selection
- Simulation Engine (V3-5): Test pricing scenarios with new anchor architecture
- Production Rollout: Staged deployment starting with lowest-volume coverages

# Phase 13: LLM Coverage Builder

## Purpose
Enable automated generation, validation, and refinement of coverage models using LLM‑assisted tooling. This dramatically accelerates the creation of new coverages and ensures consistency across YAML configurations.

## Key Deliverables
- Coverage builder module
- YAML validator
- Signal library integration
- Automated generation of coverage definitions

## Implementation Summary
This phase introduces an LLM‑driven builder that constructs coverage models from natural‑language specifications. It ensures that new coverages follow the same structure, naming conventions, and signal architecture as the existing seven.

## Detailed Plan

Automated coverage creation via LLM with validation and integration.

### 13.1 The Coverage Building Problem

Creating a new coverage requires:
- Industry domain expertise
- Understanding of signal types
- Configuration of 40+ signals
- Proper weighting
- Tier threshold calibration
- Test profile creation

**Solution**: LLM-assisted workflow that guides coverage creation with validation.

### 13.2 LLM Builder Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM COVERAGE BUILDER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      INPUTS                              │   │
│  │                                                          │   │
│  │  Required:                                               │   │
│  │  • Coverage name (e.g., "Renewable Energy")              │   │
│  │  • Industry description                                  │   │
│  │  • Target market (region, company size)                  │   │
│  │  • Risk characteristics                                  │   │
│  │                                                          │   │
│  │  Optional:                                               │   │
│  │  • Example companies                                     │   │
│  │  • Known risk factors                                    │   │
│  │  • Existing similar coverage to extend                   │   │
│  │  • Historical loss data                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   GENERATION STEPS                       │   │
│  │                                                          │   │
│  │  1. Analyze industry and identify signal categories      │   │
│  │  2. Select appropriate signal groups from library        │   │
│  │  3. Configure signal weights based on industry           │   │
│  │  4. Define tier thresholds                               │   │
│  │  5. Create direct queries                                │   │
│  │  6. Generate test profiles                               │   │
│  │  7. Validate configuration                               │   │
│  │  8. Generate documentation                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   VALIDATION                             │   │
│  │                                                          │   │
│  │  • Schema validation                                     │   │
│  │  • Weight sum verification (= 1.0)                       │   │
│  │  • Tier coverage verification                            │   │
│  │  • Test profile execution                                │   │
│  │  • Signal availability check                             │   │
│  │  • Human review prompts                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   OUTPUTS                                │   │
│  │                                                          │   │
│  │  • config.yaml (complete coverage configuration)         │   │
│  │  • Extractors stubs (for new signals)                    │   │
│  │  • Aggregators (for new signals)                         │   │
│  │  • Inference functions (for new signals)                 │   │
│  │  • Test cases                                            │   │
│  │  • Documentation                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 13.3 Builder Workflow

```python
class CoverageBuilder:
    """
    LLM-assisted coverage building.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        signal_library: SignalLibrary,
        validator: ConfigValidator
    ):
        pass

    async def create_coverage(
        self,
        spec: CoverageSpec
    ) -> CoverageBuildResult:
        """
        Main entry point for coverage creation.

        Steps:
        1. Analyze industry requirements
        2. Select and configure signals
        3. Generate configuration
        4. Validate and test
        5. Generate code stubs
        """
        pass

    async def analyze_industry(
        self,
        description: str,
        examples: List[str] = None
    ) -> IndustryAnalysis:
        """
        LLM analyzes industry to identify:
        - Key risk factors
        - Relevant signal categories
        - Industry-specific considerations
        """
        pass

    async def select_signals(
        self,
        analysis: IndustryAnalysis
    ) -> List[SignalSelection]:
        """
        Select signals from library based on analysis.

        Returns ranked list of signals with:
        - Relevance score
        - Suggested weight
        - Customization notes
        """
        pass

    async def generate_config(
        self,
        selections: List[SignalSelection],
        tier_strategy: str = "standard"
    ) -> CoverageConfig:
        """Generate complete YAML configuration"""
        pass

    async def validate_config(
        self,
        config: CoverageConfig
    ) -> ValidationResult:
        """
        Validate configuration:
        - Schema compliance
        - Weight verification
        - Signal availability
        - Test execution
        """
        pass

    async def generate_stubs(
        self,
        config: CoverageConfig,
        new_signals: List[str]
    ) -> GeneratedCode:
        """
        Generate code stubs for new signals:
        - Extractors
        - Aggregators
        - Inference functions
        """
        pass

@dataclass
class CoverageSpec:
    """Input specification for new coverage"""
    name: str
    description: str
    industry: str
    target_market: str  # "US mid-market", "Global enterprise", etc.
    risk_factors: List[str]
    example_companies: List[str] = None
    base_coverage: str = None  # Extend from existing
    notes: str = None

@dataclass
class CoverageBuildResult:
    """Output from coverage building"""
    success: bool
    config_yaml: str
    generated_files: Dict[str, str]  # path -> content
    validation_results: ValidationResult
    warnings: List[str]
    human_review_required: List[str]
```

### 13.4 Signal Library

```python
class SignalLibrary:
    """
    Reusable signal components for coverage building.
    """

    # Standard signal groups available
    SIGNAL_GROUPS = {
        "technical_infrastructure": [
            "security_headers",
            "tls_configuration",
            "email_authentication",
            "dns_security",
            # ...
        ],
        "corporate_footprint": [
            "website_quality",
            "security_disclosure",
            "leadership_visibility",
            # ...
        ],
        "network_authority": [
            "customer_quality",
            "partner_ecosystem",
            "certification_status",
            # ...
        ],
        # ... more groups
    }

    def get_signals_for_industry(
        self,
        industry: str
    ) -> List[SignalRecommendation]:
        """Get recommended signals for industry"""
        pass

    def get_signal_template(
        self,
        signal_id: str
    ) -> SignalTemplate:
        """Get template for signal implementation"""
        pass
```

### 13.5 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create CoverageBuilder | `builder/coverage_builder.py` | ✅ Complete |
| Create ConfigValidator | `builder/validator.py` | ✅ Complete |
| Add builder tests | `tests/unit/test_builder.py` | ✅ Complete |
| Create SignalLibrary | `builder/signal_library.py` | 🔲 Optional |
| Create CodeGenerator | `builder/code_generator.py` | 🔲 Optional |
| Implement LLM prompts | `builder/prompts/` | 🔲 Optional |
| Create builder CLI | `builder/cli.py` | 🔲 Optional |
| Create documentation | `docs/coverage_building.md` | 🔲 Optional |


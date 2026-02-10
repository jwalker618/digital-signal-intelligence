# Phase 7: Traditional Pricing Integration

## Purpose
Integrate traditional actuarial modifiers into the pricing engine, enabling hybrid DSI + actuarial pricing.

## Key Deliverables
- Loss history modifier
- Exposure modifier
- External rating modifier
- Modifier sequencing logic

## Implementation Summary
This phase introduces actuarial adjustments applied after base premium generation. These modifiers operate independently of signal scoring and are fully configurable via YAML.

## Detailed Plan

This phase integrates traditional actuarial data sources as **OPTIONAL** modifiers applied after base premium generation. These complement DSI signals with historical and exposure-based factors when data is available.

### 7.1 The Integration Problem

DSI provides forward-looking risk assessment through digital signals, but traditional pricing can optionally include:
- **Loss History**: Past claims experience (when available)
- **Exposure Data**: Revenue, payroll, TIV, fleet size, etc. (when available)
- **Actuarial Models**: Experience rating, credibility weighting
- **External Ratings**: Credit scores, financial strength (when integrated)

**Key Design Principles**:
1. **All inputs are OPTIONAL** - DSI works without traditional data
2. **Graceful degradation** - Skip modifiers when data unavailable
3. **Streamlined mode** - Quick exposure scoring for STP (Straight-Through Processing)
4. **Full mode** - Detailed analysis when data is rich

**Solution**: Create optional modifier interfaces that can be plugged in after Step 10 (Base Premium) and before Step 11 (Modifier Application). Modifiers that lack data simply return factor=1.0 (no impact).

### 7.2 Traditional Modifier Architecture

```
┌────────────────────────────────────────────────────────────── ───┐
│                 TRADITIONAL PRICING MODIFIERS                    │
├─────────────────────────────────────────────────────────────── ──┤
│                                                                  │
│  Applied after base premium (Step 10), before modifiers (Step 11)│
│                                                                  │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐  │
│  │LOSS HISTORY      │   │EXPOSURE          │   │EXTERNAL      │  │
│  │MODIFIER          │   │MODIFIER          │   │RATING        │  │
│  │                  │   │                  │   │MODIFIER      │  │
│  │• Claims count    │   │• TIV ratio       │   │• Credit score│  │
│  │• Loss ratio      │   │• Revenue growth  │   │• AM Best     │  │
│  │• Large losses    │   │• Employee count  │   │• S&P rating  │  │
│  │• Trend analysis  │   │• Fleet age       │   │              │  │
│  └──────────────────┘   └──────────────────┘   └──────────────┘  │
│           │                     │                     │          │
│           └─────────────────────┼─────────────────────┘          │
│                                 ▼                                │
│                    COMBINED TRADITIONAL MODIFIER                 │
│                                 │                                │
│                                 ▼                                │
│              Step 11: Apply with DSI modifiers                   │
│                                                                  │
└──────────────────────────────────────────────────────────────── ─┘
```

### 7.3 Data Structures

```python
@dataclass
class LossHistoryInput:
    """Loss history data for experience rating"""
    policy_years: List[PolicyYear]  # 3-5 years of history
    claims: List[Claim]
    large_loss_threshold: float
    credibility_factor: float  # 0-1 based on exposure volume

@dataclass
class PolicyYear:
    year: int
    premium: float
    incurred_losses: float
    paid_losses: float
    outstanding_reserves: float
    claim_count: int

@dataclass
class Claim:
    claim_id: str
    occurrence_date: date
    incurred_amount: float
    paid_amount: float
    status: str  # open, closed, reopened
    cause_code: str
    is_large_loss: bool

@dataclass
class ExposureInput:
    """
    Exposure metrics for rating - ALL FIELDS OPTIONAL

    Two modes:
    - Streamlined (STP): Only needs revenue OR tiv for quick factor
    - Full: Uses all available data for detailed analysis
    """
    # Core exposure (any ONE enables streamlined mode)
    tiv: Optional[float] = None
    revenue: Optional[float] = None

    # Additional metrics (for full mode)
    employee_count: Optional[int] = None
    payroll: Optional[float] = None
    fleet_size: Optional[int] = None
    fleet_average_age: Optional[float] = None
    locations_count: Optional[int] = None

    # Coverage-specific (optional)
    cyber_endpoints: Optional[int] = None
    vessels_count: Optional[int] = None
    aircraft_count: Optional[int] = None

    @property
    def has_minimal_data(self) -> bool:
        """Check if enough data for streamlined exposure factor"""
        return self.tiv is not None or self.revenue is not None

    @property
    def mode(self) -> str:
        """Determine analysis mode based on available data"""
        if not self.has_minimal_data:
            return "none"  # Skip exposure modifier
        full_fields = [self.employee_count, self.payroll, self.fleet_size]
        if sum(1 for f in full_fields if f is not None) >= 2:
            return "full"
        return "streamlined"  # STP mode

@dataclass
class TraditionalModifierResult:
    """Output from traditional modifier calculation"""
    modifier_type: str  # 'loss_history', 'exposure', 'external_rating'
    factor: float  # Multiplicative factor (1.0 = no change)
    confidence: float  # Data quality/credibility
    components: Dict[str, float]  # Breakdown
    notes: List[str]
    data_sources: List[str]
```

### 7.4 Modifier Interfaces

```python
class TraditionalModifier(ABC):
    """Base class for traditional pricing modifiers"""

    @abstractmethod
    def calculate(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Dict[str, Any],
        context: InferenceContext
    ) -> TraditionalModifierResult:
        """Calculate the modifier factor"""
        pass

    @property
    @abstractmethod
    def modifier_type(self) -> str:
        """Type identifier for this modifier"""
        pass

class LossHistoryModifier(TraditionalModifier):
    """
    Experience rating based on loss history - OPTIONAL input.

    Methods:
    - Pure loss ratio method
    - Frequency/severity method
    - Credibility-weighted method

    When no loss history is provided, returns factor=1.0 (no impact).
    """

    def calculate(self, entity_id: str, ...) -> TraditionalModifierResult:
        # Check if loss data is available
        loss_data = self._get_loss_data(entity_id, submission_data)
        if not loss_data:
            # No loss history - return neutral (no impact)
            return TraditionalModifierResult(
                modifier_type="loss_history",
                factor=1.0,
                confidence=0.0,
                components={},
                notes=["No loss history available - modifier skipped"],
                data_sources=[]
            )

        # Process available loss data
        loss_ratio = self._calculate_loss_ratio(loss_data)
        expected_loss_ratio = self._get_expected_loss_ratio(coverage)
        premium_volume = loss_data.total_premium

        # Experience modification factor with credibility weighting
        credibility = min(1.0, premium_volume / self.full_credibility_premium)
        emf = (credibility * loss_ratio + (1 - credibility) * expected_loss_ratio) / expected_loss_ratio

        # Apply cap and floor
        emf = max(self.floor_factor, min(self.cap_factor, emf))

        return TraditionalModifierResult(
            modifier_type="loss_history",
            factor=emf,
            confidence=credibility,
            components={
                "loss_ratio": loss_ratio,
                "expected_loss_ratio": expected_loss_ratio,
                "credibility": credibility,
                "raw_emf": emf,
            },
            notes=[f"Experience mod based on {len(loss_data.policy_years)} years of history"],
            data_sources=["claims_system", "submission"]
        )

class ExposureModifier(TraditionalModifier):
    """
    Exposure-based adjustments with streamlined STP mode.

    Two modes:
    1. STREAMLINED (STP - Straight-Through Processing):
       - Only needs revenue OR tiv
       - Uses simplified size curve lookup
       - Returns quick factor for automatic processing

    2. FULL (when rich data available):
       - Analyzes multiple exposure metrics
       - Considers growth trends
       - Evaluates concentration factors
    """

    def calculate(self, entity_id: str, ...) -> TraditionalModifierResult:
        exposure = ExposureInput.from_submission(submission_data)

        if not exposure.has_minimal_data:
            # No exposure data - return neutral (no impact)
            return TraditionalModifierResult(
                modifier_type="exposure",
                factor=1.0,
                confidence=0.0,
                components={},
                notes=["No exposure data available - modifier skipped"],
                data_sources=[]
            )

        if exposure.mode == "streamlined":
            # STP mode: Quick factor from size curve
            factor = self._streamlined_factor(exposure)
            return TraditionalModifierResult(
                modifier_type="exposure",
                factor=factor,
                confidence=0.7,  # Lower confidence for simplified analysis
                components={"size_factor": factor},
                notes=["Streamlined exposure analysis (STP mode)"],
                data_sources=["submission"]
            )
        else:
            # Full mode: Detailed analysis
            return self._full_analysis(exposure)

class ExternalRatingModifier(TraditionalModifier):
    """
    External rating adjustments.

    Sources:
    - Credit ratings (D&B, Experian)
    - Financial strength (AM Best, S&P)
    - ESG scores
    """
    pass
```

### 7.5 Integration with Workflow

```python
class WorkflowEngine:
    def __init__(
        self,
        # ... existing
        traditional_modifiers: List[TraditionalModifier] = None
    ):
        self.traditional_modifiers = traditional_modifiers or []

    def run_workflow(self, ...):
        # Steps 1-10: Existing workflow

        # NEW: Step 10.5 - Traditional Modifiers
        traditional_results = []
        for modifier in self.traditional_modifiers:
            result = modifier.calculate(
                entity_id=entity_id,
                coverage=coverage,
                submission_data=submission_data,
                context=context
            )
            traditional_results.append(result)

        # Step 11: Apply all modifiers (DSI + Traditional)
        all_modifiers = query_modifiers + [
            {"name": r.modifier_type, "factor": r.factor}
            for r in traditional_results
        ]
```

### 7.6 Configuration

```yaml
traditional_modifiers:
  loss_history:
    enabled: true
    full_credibility_premium: 500000
    years_required: 3
    large_loss_threshold: 100000
    cap_factor: 1.50  # Max loading
    floor_factor: 0.75  # Max credit

  exposure:
    enabled: true
    size_curve: "iso_curve_2"
    growth_threshold: 0.20  # >20% growth triggers review

  external_rating:
    enabled: false  # Enable when integration ready
    sources:
      - type: credit_rating
        provider: dun_bradstreet
      - type: financial_strength
        provider: am_best
```

### 7.7 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create TraditionalModifier base class | `model/modifiers/base.py` | ✅ Complete |
| Implement LossHistoryModifier | `model/modifiers/loss_history.py` | ✅ Complete |
| Implement ExposureModifier | `model/modifiers/exposure.py` | ✅ Complete |
| Implement ExternalRatingModifier | `model/modifiers/external_rating.py` | ✅ Complete |
| Add modifier types | `model/types.py` | ✅ Complete |
| Integrate into workflow | `model/workflow.py` | ✅ Complete |
| Add YAML configuration schema | `coverages/*/config.yaml` | ✅ Complete |
| Create unit tests | `tests/unit/test_traditional_modifiers.py` | ✅ Complete |


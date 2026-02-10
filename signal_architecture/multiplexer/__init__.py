"""
DSI Multi-Configuration Multiplexer (Phase V4)

Enables "Race-Track" execution where multiple configurations are evaluated
simultaneously using shared signal data, with algorithmic selection of
the optimal outcome.

Components:
- DSIMultiplexer: Signal broker that identifies candidates, deduplicates
  signals, executes once, and fans out results to each configuration
- ConfigArbiter: Selects winner based on validity → confidence →
  specificity → commercial value
- Types: Data structures for candidates, signal pools, and results

Example usage:
    from signal_architecture.multiplexer import (
        DSIMultiplexer,
        ConfigArbiter,
        MultiplexerConfig,
    )

    # Create multiplexer with custom config
    config = MultiplexerConfig(min_signal_completeness=0.7)
    multiplexer = DSIMultiplexer(config=config)
    arbiter = ConfigArbiter(config=config)

    # Execute race
    result = await multiplexer.execute(
        coverage_id="cyber",
        user_input={"client_name": "Example Corp", "product_type": "cyber_liability"},
    )

    # Select winner
    result = arbiter.arbitrate(result)
    print(f"Selected: {result.selected_config_id}")
"""

from .types import (
    # Enums
    ConstraintOperator,
    # Core types
    RoutingConstraint,
    ConfigCandidate,
    SignalPool,
    CandidateResult,
    MultiplexerResult,
    MultiplexerConfig,
)

from .broker import DSIMultiplexer

from .arbiter import ConfigArbiter, create_arbiter

from .integration import (
    MultiplexedWorkflow,
    create_multiplexed_workflow_factory,
    run_multiplexed_assessment,
)


__all__ = [
    # Enums
    "ConstraintOperator",
    # Core types
    "RoutingConstraint",
    "ConfigCandidate",
    "SignalPool",
    "CandidateResult",
    "MultiplexerResult",
    "MultiplexerConfig",
    # Broker
    "DSIMultiplexer",
    # Arbiter
    "ConfigArbiter",
    "create_arbiter",
    # Integration
    "MultiplexedWorkflow",
    "create_multiplexed_workflow_factory",
    "run_multiplexed_assessment",
]

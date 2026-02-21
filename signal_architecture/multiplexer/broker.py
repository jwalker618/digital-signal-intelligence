"""
DSI Signal Broker / Multiplexer (Phase V4 + V4.1 + Cycle 3)

Implements the "Race-Track" model for multi-configuration evaluation.
Identifies candidates, deduplicates signals, executes once, fans out results.

Phase V4.1 adds robust routing constraint evaluation with type safety.
Cycle 3 adds robust ExtractionError logging for signal failures.
"""

import asyncio
import logging
import operator
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import yaml

from .types import (
    ConfigCandidate,
    ConstraintOperator,
    ExtractionError,
    ExtractionErrorType,
    MultiplexerConfig,
    MultiplexerResult,
    CandidateResult,
    RoutingConstraint,
    SignalPool,
)


logger = logging.getLogger("dsi.multiplexer")


# Operator mapping for constraint evaluation (Phase V4.1)
CONSTRAINT_OPS = {
    ConstraintOperator.LT: operator.lt,
    ConstraintOperator.GT: operator.gt,
    ConstraintOperator.LTE: operator.le,
    ConstraintOperator.GTE: operator.ge,
    ConstraintOperator.EQ: operator.eq,
    ConstraintOperator.NEQ: operator.ne,
}


class DSIMultiplexer:
    """
    Signal Broker that enables multi-configuration racing.

    Flow:
    1. Load all configs for a coverage
    2. Filter by routing constraints
    3. Union and deduplicate signals
    4. Execute signals once (parallel)
    5. Fan-out results to each candidate
    6. Return all results for arbitration
    """

    def __init__(
        self,
        config_loader: Optional[Callable[[str], List[Dict]]] = None,
        signal_executor: Optional[Callable[[Dict, Dict], Any]] = None,
        logic_engine_factory: Optional[Callable[[Dict], Any]] = None,
        config: Optional[MultiplexerConfig] = None,
    ):
        """
        Initialize DSIMultiplexer.

        Args:
            config_loader: Function to load configs for a coverage
            signal_executor: Function to execute signals
            logic_engine_factory: Factory to create logic engines
            config: Multiplexer configuration
        """
        self.config_loader = config_loader or self._default_config_loader
        self.signal_executor = signal_executor
        self.logic_engine_factory = logic_engine_factory
        self.config = config or MultiplexerConfig()

        # Cache loaded configs
        self._config_cache: Dict[str, List[Dict]] = {}

    def load_configs_for_coverage(self, coverage_id: str) -> List[Dict]:
        """
        Load all configuration variants for a coverage.

        Args:
            coverage_id: Coverage identifier (e.g., "cyber")

        Returns:
            List of configuration dictionaries
        """
        if coverage_id in self._config_cache:
            return self._config_cache[coverage_id]

        configs = self.config_loader(coverage_id)
        self._config_cache[coverage_id] = configs
        return configs

    def identify_candidates(
        self,
        coverage_id: str,
        user_input: Dict[str, Any],
    ) -> List[ConfigCandidate]:
        """
        Identify all candidate configurations matching the input.

        Filters by:
        1. Product type match
        2. Market match
        3. Routing constraints

        Args:
            coverage_id: Coverage identifier
            user_input: Submission input data

        Returns:
            List of ConfigCandidate objects that passed filtering
        """
        configs = self.load_configs_for_coverage(coverage_id)
        candidates: List[ConfigCandidate] = []

        for config_dict in configs:
            for config_id, config in config_dict.items():
                if config_id == coverage_id:
                    # Skip the coverage-level key
                    continue

                metadata = config.get("metadata", {})

                # Check product type
                product_types = metadata.get("product_types", [])
                user_product = user_input.get("product_type")
                if user_product and user_product not in product_types:
                    logger.debug(
                        f"Config {config_id} excluded: product_type {user_product} "
                        f"not in {product_types}"
                    )
                    continue

                # Check market
                markets = metadata.get("applicable_markets", [])
                user_market = user_input.get("market")
                if user_market and markets and user_market not in markets:
                    logger.debug(
                        f"Config {config_id} excluded: market {user_market} "
                        f"not in {markets}"
                    )
                    continue

                # Parse routing constraints
                constraints = self._parse_constraints(
                    metadata.get("routing_constraints", [])
                )

                # Check routing constraints
                if not self._check_constraints(constraints, user_input):
                    logger.debug(
                        f"Config {config_id} excluded: routing constraints failed"
                    )
                    continue

                # Build candidate
                candidate = ConfigCandidate(
                    coverage_id=coverage_id,
                    config_id=config_id,
                    config=config,
                    model_specificity=metadata.get("model_specificity", 1),
                    routing_constraints=constraints,
                )

                candidates.append(candidate)
                logger.debug(
                    f"Config {config_id} included as candidate "
                    f"(specificity={candidate.model_specificity})"
                )

        # Limit candidates
        if len(candidates) > self.config.max_candidates:
            logger.warning(
                f"Too many candidates ({len(candidates)}), "
                f"limiting to {self.config.max_candidates}"
            )
            # Sort by specificity descending, take top N
            candidates.sort(key=lambda c: c.model_specificity, reverse=True)
            candidates = candidates[: self.config.max_candidates]

        return candidates

    def optimize_signals(
        self,
        candidates: List[ConfigCandidate],
    ) -> Dict[str, str]:
        """
        Extract unique signal IDs from all candidates.

        Deduplicates signals that appear in multiple configs.

        Args:
            candidates: List of candidate configurations

        Returns:
            Dict of {signal_id: inference_utility_function}
        """
        unique_signals: Dict[str, str] = {}

        for candidate in candidates:
            registry = candidate.config.get("signal_registry", [])
            for signal in registry:
                signal_id = signal.get("id")
                function_name = signal.get("inference_utility_function")

                if signal_id and function_name:
                    if signal_id not in unique_signals:
                        unique_signals[signal_id] = function_name
                    else:
                        # Verify same function (should be consistent)
                        if unique_signals[signal_id] != function_name:
                            logger.warning(
                                f"Signal {signal_id} has inconsistent functions: "
                                f"{unique_signals[signal_id]} vs {function_name}"
                            )

        logger.info(
            f"Optimized signals: {len(unique_signals)} unique from "
            f"{sum(len(c.signal_ids) for c in candidates)} total references"
        )

        return unique_signals

    async def execute_signals(
        self,
        signal_map: Dict[str, str],
        user_input: Dict[str, Any],
        entity_id: str = "",
    ) -> SignalPool:
        """
        Execute all signals in parallel.

        Cycle 3 Enhancement: Robust error logging with ExtractionError classification.
        All failures are logged with exact reasons (Timeout, Rate Limit, Parsing Error)
        before passing None to the scoring engine.

        Args:
            signal_map: {signal_id: function_name}
            user_input: Submission input data
            entity_id: Entity identifier for audit logging

        Returns:
            SignalPool with results
        """
        pool = SignalPool()

        if not self.signal_executor:
            logger.warning("No signal executor configured, returning empty pool")
            return pool

        import time
        start = time.time()

        entity_id = entity_id or user_input.get("client_name", "unknown")

        for signal_id, function_name in signal_map.items():
            try:
                result = await self._execute_single_signal(
                    signal_id, function_name, user_input
                )
                pool.signals[signal_id] = result

            except ExtractionError as e:
                # Cycle 3: Structured error with full context
                self._log_extraction_error(e)
                pool.errors[signal_id] = str(e)

            except Exception as e:
                # Cycle 3: Convert raw exceptions to structured ExtractionError
                extraction_error = ExtractionError.from_exception(
                    signal_id=signal_id,
                    exc=e,
                    entity_id=entity_id,
                    source=function_name,
                )
                self._log_extraction_error(extraction_error)
                pool.errors[signal_id] = str(extraction_error)

        pool.execution_time_ms = (time.time() - start) * 1000

        logger.info(
            f"Executed {len(pool.signals)} signals in {pool.execution_time_ms:.1f}ms "
            f"({len(pool.errors)} errors)"
        )

        return pool

    def _log_extraction_error(self, error: ExtractionError) -> None:
        """
        Log extraction error to audit system.

        Cycle 3 Requirement: Log exact failure reasons before passing None
        to the scoring engine for adaptive absence handling.
        """
        # Log to standard logger with appropriate level
        log_level = logging.WARNING
        if error.error_type in (ExtractionErrorType.AUTH_ERROR, ExtractionErrorType.UNKNOWN):
            log_level = logging.ERROR

        logger.log(
            log_level,
            f"Signal extraction failed: {error.signal_id} | "
            f"Type: {error.error_type.value} | "
            f"Source: {error.source} | "
            f"Entity: {error.entity_id} | "
            f"Message: {error.message}"
        )

        # Prepare audit log entry
        audit_entry = error.to_audit_dict()

        # In production, this would write to the audit_logs table
        # For now, we log it in structured format
        logger.debug(f"Audit log entry: {audit_entry}")

    async def evaluate_candidate(
        self,
        candidate: ConfigCandidate,
        signal_pool: SignalPool,
        user_input: Dict[str, Any],
    ) -> CandidateResult:
        """
        Evaluate a single candidate using precomputed signals.

        Args:
            candidate: Configuration to evaluate
            signal_pool: Shared signal results
            user_input: Submission input data

        Returns:
            CandidateResult with scoring and completeness
        """
        # Map signals for this config
        mapped_signals = self._map_signals(candidate, signal_pool)

        # Calculate completeness
        signals_defined = len(candidate.signal_ids)
        signals_returned = sum(
            1 for sid in candidate.signal_ids
            if signal_pool.has_result(sid)
        )
        completeness = signals_returned / signals_defined if signals_defined > 0 else 0.0

        # Run logic engine with precomputed signals
        if self.logic_engine_factory:
            engine = self.logic_engine_factory(candidate.config)
            result = engine.evaluate(user_input, precomputed_signals=mapped_signals)

            return CandidateResult(
                coverage_id=candidate.coverage_id,
                config_id=candidate.config_id,
                model_specificity=candidate.model_specificity,
                composite_score=result.get("composite_score", 0),
                tier=result.get("tier", 3),
                tier_label=result.get("tier_label", "STANDARD"),
                decision=result.get("decision", {}).get("action", "REFER"),
                referral_reasons=result.get("referral_reasons", []),
                recommended_premium=result.get("pricing", {}).get("final_premium", 0),
                signal_completeness=completeness,
                signals_returned=signals_returned,
                signals_defined=signals_defined,
                full_result=result,
            )
        else:
            # Fallback: return placeholder result
            return CandidateResult(
                coverage_id=candidate.coverage_id,
                config_id=candidate.config_id,
                model_specificity=candidate.model_specificity,
                composite_score=0,
                tier=3,
                tier_label="STANDARD",
                decision="REFER",
                referral_reasons=["No logic engine configured"],
                recommended_premium=0,
                signal_completeness=completeness,
                signals_returned=signals_returned,
                signals_defined=signals_defined,
            )

    async def execute(
        self,
        coverage_id: str,
        user_input: Dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> MultiplexerResult:
        """
        Execute the full multiplexer flow.

        Args:
            coverage_id: Coverage identifier (e.g., "cyber")
            user_input: Submission input data
            entity_id: Optional entity identifier

        Returns:
            MultiplexerResult with all candidate results
        """
        entity_id = entity_id or user_input.get("client_name", "unknown")

        # 1. Identify candidates
        candidates = self.identify_candidates(coverage_id, user_input)

        if not candidates:
            logger.warning(f"No matching configurations for {coverage_id}")
            return MultiplexerResult(
                entity_id=entity_id,
                coverage_id=coverage_id,
                candidates_evaluated=0,
                candidate_results=[],
                selection_reason="No matching configurations found",
            )

        logger.info(f"Found {len(candidates)} candidate configurations")

        # 2. Optimize signals (deduplicate)
        signal_map = self.optimize_signals(candidates)

        # 3. Execute signals (with entity_id for Cycle 3 audit logging)
        signal_pool = await self.execute_signals(signal_map, user_input, entity_id)

        # 4. Fan-out: Evaluate each candidate
        candidate_results: List[CandidateResult] = []

        if self.config.enable_parallel_execution:
            tasks = [
                self.evaluate_candidate(c, signal_pool, user_input)
                for c in candidates
            ]
            candidate_results = await asyncio.gather(*tasks)
        else:
            for candidate in candidates:
                result = await self.evaluate_candidate(
                    candidate, signal_pool, user_input
                )
                candidate_results.append(result)

        # Build result (arbitration happens separately)
        return MultiplexerResult(
            entity_id=entity_id,
            coverage_id=coverage_id,
            candidates_evaluated=len(candidates),
            candidate_results=list(candidate_results),
            unique_signals_executed=len(signal_map),
            total_execution_time_ms=signal_pool.execution_time_ms,
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _parse_constraints(
        self,
        constraints_raw: List[Dict],
    ) -> List[RoutingConstraint]:
        """Parse routing constraints from config."""
        constraints = []
        for c in constraints_raw:
            try:
                operator = ConstraintOperator(c.get("operator", "=="))
                constraints.append(RoutingConstraint(
                    field=c.get("field", ""),
                    operator=operator,
                    value=c.get("value"),
                    required_in_input=c.get("required_in_input", False),
                ))
            except ValueError as e:
                logger.warning(f"Invalid constraint operator: {e}")
        return constraints

    def _check_constraints(
        self,
        constraints: List[RoutingConstraint],
        user_input: Dict[str, Any],
    ) -> bool:
        """
        Evaluate all routing constraints against input (Phase V4.1 enhanced).

        Handles:
        - Missing fields (based on required_in_input flag)
        - Type coercion (string to numeric conversion)
        - All comparison operators via operator module

        Returns True if ALL constraints pass, False if ANY fails.
        """
        if not constraints:
            return True

        for c in constraints:
            # 1. Handle Missing Fields
            if c.field not in user_input:
                if c.required_in_input:
                    # Strict fail: The model NEEDS this field to decide
                    logger.debug(
                        f"Constraint failed: required field '{c.field}' missing"
                    )
                    return False
                else:
                    # Permissive pass: Field missing, but rule not strict
                    continue

            # 2. Extract Values
            actual_val = user_input[c.field]
            target_val = c.value

            # 3. Type Safety / Conversion
            # Ensure we don't crash comparing "500" (str) > 100 (int)
            try:
                if isinstance(target_val, (int, float)) and isinstance(actual_val, str):
                    actual_val = float(actual_val)
                elif isinstance(actual_val, (int, float)) and isinstance(target_val, str):
                    target_val = float(target_val)
            except (ValueError, TypeError) as e:
                # If conversion fails, we can't evaluate mathematical ops
                # Default to Fail for safety
                logger.warning(
                    f"Constraint type conversion failed for field '{c.field}': {e}"
                )
                return False

            # 4. Evaluate Operator
            op_func = CONSTRAINT_OPS.get(c.operator)
            if not op_func:
                # Configuration Error: Unknown operator
                logger.warning(f"Unknown constraint operator: {c.operator}")
                return False

            if not op_func(actual_val, target_val):
                logger.debug(
                    f"Constraint failed: {c.field} ({actual_val}) "
                    f"{c.operator.value} {target_val}"
                )
                return False

        return True

    def _map_signals(
        self,
        candidate: ConfigCandidate,
        pool: SignalPool,
    ) -> Dict[str, Any]:
        """Map signal pool results to this candidate's requirements."""
        mapped = {}
        for signal_id in candidate.signal_ids:
            mapped[signal_id] = pool.get(signal_id)
        return mapped

    async def _execute_single_signal(
        self,
        signal_id: str,
        function_name: str,
        user_input: Dict[str, Any],
    ) -> Any:
        """Execute a single signal."""
        if self.signal_executor:
            return await self.signal_executor({
                "signal_id": signal_id,
                "function_name": function_name,
            }, user_input)
        return None

    def _default_config_loader(self, coverage_id: str) -> List[Dict]:
        """Default config loader - loads from coverages/{coverage_id}/config.yaml."""
        config_path = Path(f"coverages/{coverage_id}/config.yaml")
        if not config_path.exists():
            logger.error(f"Config not found: {config_path}")
            return []

        with open(config_path) as f:
            raw = yaml.safe_load(f)

        # Extract all configs under the coverage
        if coverage_id in raw:
            coverage_section = raw[coverage_id]
            # Return as list of single-config dicts for iteration
            return [{config_id: config} for config_id, config in coverage_section.items()]

        return []

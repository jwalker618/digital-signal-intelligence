"""
DSI Multi-Coverage Orchestrator (Phase 10)

Coordinates pricing across multiple coverages and locales
from a single submission with shared signal caching.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .types import (
    MultiCoverageRequest,
    MultiCoverageResult,
    ExecutionPlan,
    PlannedRun,
    CoverageResult,
    ExecutionStatus,
    LocaleDetectionMode,
    OrchestrationConfig,
    SharedSignalCache,
    PackageRecommendation,
)


logger = logging.getLogger("dsi.orchestration")


class MultiCoverageOrchestrator:
    """
    Orchestrates multi-coverage and multi-locale pricing.

    Capabilities:
    - Price multiple lines (FI, PI, D&O, Cyber) for same client
    - Test multiple locales to find best fit
    - Auto-detect locale from discovery
    - Shared signal cache for cost optimization
    - Package discount calculation
    """

    def __init__(
        self,
        workflow_factory: Optional[Callable] = None,
        locale_detector: Optional[Any] = None,
        config: Optional[OrchestrationConfig] = None,
        max_workers: int = 4,
    ):
        """
        Initialize MultiCoverageOrchestrator.

        Args:
            workflow_factory: Callable that creates workflow instances
            locale_detector: LocaleDetector instance for auto-detection
            config: Orchestration configuration
            max_workers: Maximum parallel workers
        """
        self.workflow_factory = workflow_factory
        self.locale_detector = locale_detector
        self.config = config or OrchestrationConfig.default()
        self.max_workers = min(max_workers, self.config.max_parallel_runs)

        # Active caches
        self._active_caches: Dict[str, SharedSignalCache] = {}

    def create_plan(
        self,
        request: MultiCoverageRequest,
        discovery_result: Optional[Any] = None,
    ) -> ExecutionPlan:
        """
        Create an execution plan for the request.

        Args:
            request: Multi-coverage request
            discovery_result: Optional discovery result for locale detection

        Returns:
            ExecutionPlan with all planned runs
        """
        runs: List[PlannedRun] = []
        shared_signals: List[str] = []

        # Determine coverages
        coverages = self._determine_coverages(request, discovery_result)

        # Determine locales
        locales = self._determine_locales(request, discovery_result)

        # Create runs for each coverage/locale combination
        for coverage in coverages:
            for locale in locales:
                configuration = f"{coverage}_{locale.lower()}"

                # Estimate cost
                estimated_signals = self._estimate_signals(coverage, locale)
                estimated_cost = estimated_signals * 1.0  # 1 cost unit per signal

                runs.append(PlannedRun(
                    coverage=coverage,
                    locale=locale,
                    configuration=configuration,
                    estimated_signals=estimated_signals,
                    estimated_cost=estimated_cost,
                    priority=self._get_coverage_priority(coverage),
                ))

        # Identify shared signals
        shared_signals = self._identify_shared_signals(coverages)

        # Calculate totals
        total_cost = sum(r.estimated_cost for r in runs)

        # Adjust for cache sharing
        if request.share_cache and len(shared_signals) > 0:
            cache_savings = len(shared_signals) * (len(runs) - 1) * 0.5
            total_cost = max(total_cost - cache_savings, sum(r.estimated_signals for r in runs) * 0.3)

        # Estimate duration (parallel vs sequential)
        if request.parallel:
            max_duration = max((r.estimated_signals * 0.5 for r in runs), default=0)
            estimated_duration = max_duration + 2.0  # overhead
        else:
            estimated_duration = sum(r.estimated_signals * 0.5 for r in runs)

        # Check if approval needed
        requires_approval = total_cost > request.require_approval_above

        return ExecutionPlan(
            runs=runs,
            estimated_cost_units=int(total_cost),
            estimated_duration_seconds=estimated_duration,
            shared_signals=shared_signals,
            requires_approval=requires_approval,
            plan_id=str(uuid.uuid4()),
        )

    def execute(
        self,
        request: MultiCoverageRequest,
        plan: Optional[ExecutionPlan] = None,
        discovery_result: Optional[Any] = None,
    ) -> MultiCoverageResult:
        """
        Execute multi-coverage pricing.

        Args:
            request: Multi-coverage request
            plan: Optional pre-created plan (will create if not provided)
            discovery_result: Optional discovery result

        Returns:
            MultiCoverageResult with all coverage results
        """
        # Create plan if not provided
        if plan is None:
            plan = self.create_plan(request, discovery_result)

        # Check approval
        if plan.requires_approval and not plan.approved:
            logger.warning(
                f"Plan {plan.plan_id} requires approval but not approved. "
                f"Estimated cost: {plan.estimated_cost_units}"
            )
            # Auto-approve if under max_cost_units
            if request.max_cost_units and plan.estimated_cost_units <= request.max_cost_units:
                plan.approved = True
                plan.approved_by = "auto"

        # Initialize shared cache
        cache_key = f"{request.entity_name}_{request.request_id or uuid.uuid4()}"
        shared_cache = SharedSignalCache(
            entity_id=request.entity_name,
            ttl_seconds=self.config.signal_cache_ttl,
        )
        self._active_caches[cache_key] = shared_cache

        try:
            # Execute runs
            if request.parallel and len(plan.runs) > 1:
                results = self._execute_parallel(request, plan, shared_cache)
            else:
                results = self._execute_sequential(request, plan, shared_cache)

            # Aggregate results
            return self._aggregate_results(request, plan, results, shared_cache, discovery_result)

        finally:
            # Cleanup cache
            if cache_key in self._active_caches:
                del self._active_caches[cache_key]

    def _execute_parallel(
        self,
        request: MultiCoverageRequest,
        plan: ExecutionPlan,
        shared_cache: SharedSignalCache,
    ) -> Dict[str, CoverageResult]:
        """Execute runs in parallel."""
        results: Dict[str, CoverageResult] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all runs
            futures = {}
            for run in plan.runs:
                future = executor.submit(
                    self._execute_single_run,
                    request,
                    run,
                    shared_cache,
                )
                futures[future] = run

            # Collect results
            for future in as_completed(futures):
                run = futures[future]
                try:
                    result = future.result()
                    results[run.run_id] = result

                    # Check fail_fast
                    if request.fail_fast and not result.success:
                        logger.warning(f"Fail fast triggered by {run.run_id}")
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                except Exception as e:
                    logger.error(f"Run {run.run_id} failed with exception: {e}")
                    results[run.run_id] = CoverageResult(
                        coverage=run.coverage,
                        locale=run.locale,
                        configuration=run.configuration,
                        status=ExecutionStatus.FAILED,
                        error=str(e),
                    )

        return results

    def _execute_sequential(
        self,
        request: MultiCoverageRequest,
        plan: ExecutionPlan,
        shared_cache: SharedSignalCache,
    ) -> Dict[str, CoverageResult]:
        """Execute runs sequentially."""
        results: Dict[str, CoverageResult] = {}

        # Sort by priority
        sorted_runs = sorted(plan.runs, key=lambda r: r.priority, reverse=True)

        for run in sorted_runs:
            try:
                result = self._execute_single_run(request, run, shared_cache)
                results[run.run_id] = result

                # Check fail_fast
                if request.fail_fast and not result.success:
                    logger.warning(f"Fail fast triggered by {run.run_id}")
                    break

            except Exception as e:
                logger.error(f"Run {run.run_id} failed with exception: {e}")
                results[run.run_id] = CoverageResult(
                    coverage=run.coverage,
                    locale=run.locale,
                    configuration=run.configuration,
                    status=ExecutionStatus.FAILED,
                    error=str(e),
                )

                if request.fail_fast:
                    break

        return results

    def _execute_single_run(
        self,
        request: MultiCoverageRequest,
        run: PlannedRun,
        shared_cache: SharedSignalCache,
    ) -> CoverageResult:
        """Execute a single coverage/locale run."""
        run.status = ExecutionStatus.RUNNING
        started_at = datetime.utcnow()

        result = CoverageResult(
            coverage=run.coverage,
            locale=run.locale,
            configuration=run.configuration,
            status=ExecutionStatus.RUNNING,
            started_at=started_at,
        )

        try:
            # Create workflow if factory available
            if self.workflow_factory:
                workflow = self.workflow_factory(
                    coverage=run.coverage,
                    locale=run.locale,
                    shared_cache=shared_cache if request.share_cache else None,
                )

                # Execute workflow
                workflow_result = workflow.run(
                    entity_name=request.entity_name,
                    domain=request.domain_hint,
                    submission_data=request.submission_data,
                )

                result.workflow_result = workflow_result
                result.signals_executed = getattr(workflow_result, 'signals_executed', 0)
                result.signals_from_cache = getattr(workflow_result, 'signals_from_cache', 0)
                result.cost_units = result.signals_executed * 1.0

            else:
                # No workflow factory - create placeholder result
                logger.debug(f"No workflow factory, simulating run for {run.run_id}")
                result.signals_executed = run.estimated_signals
                result.cost_units = run.estimated_cost

            result.status = ExecutionStatus.COMPLETED

        except Exception as e:
            logger.error(f"Error executing {run.run_id}: {e}")
            result.status = ExecutionStatus.FAILED
            result.error = str(e)

        finally:
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - started_at
            ).total_seconds()
            run.status = result.status

        return result

    def _aggregate_results(
        self,
        request: MultiCoverageRequest,
        plan: ExecutionPlan,
        results: Dict[str, CoverageResult],
        shared_cache: SharedSignalCache,
        discovery_result: Optional[Any] = None,
    ) -> MultiCoverageResult:
        """Aggregate all run results into final result."""
        # Initialize result
        multi_result = MultiCoverageResult(
            entity_name=request.entity_name,
            result_id=str(uuid.uuid4()),
        )

        # Add discovery info
        if discovery_result:
            multi_result.discovered_domain = getattr(discovery_result, 'domain', None)
            multi_result.detected_locale = getattr(discovery_result, 'locale', None)

        # Copy results
        multi_result.coverage_results = results

        # Count successes/failures
        multi_result.total_runs = len(results)
        multi_result.successful_runs = sum(
            1 for r in results.values() if r.success
        )
        multi_result.failed_runs = sum(
            1 for r in results.values() if r.status == ExecutionStatus.FAILED
        )

        # Aggregate metrics
        multi_result.total_cost_units = sum(r.cost_units for r in results.values())
        multi_result.total_duration_seconds = max(
            (r.duration_seconds for r in results.values()),
            default=0.0,
        )
        multi_result.cache_hit_rate = shared_cache.hit_rate

        # Find best locale per coverage
        multi_result.best_locale_per_coverage = self._find_best_locales(results)

        # Extract premiums
        multi_result.individual_premiums = self._extract_premiums(results)

        # Calculate package discounts
        successful_coverages = [
            r.coverage for r in results.values()
            if r.success and r.workflow_result
        ]
        package_info = self._calculate_package_discount(
            successful_coverages,
            multi_result.individual_premiums,
        )

        multi_result.package_discount = package_info["discount_rate"]
        multi_result.combined_premium = package_info["combined_premium"]
        multi_result.total_savings = package_info["savings"]
        multi_result.recommended_package = package_info.get("package", [])
        multi_result.package_recommendations = package_info.get("recommendations", [])

        return multi_result

    def _determine_coverages(
        self,
        request: MultiCoverageRequest,
        discovery_result: Optional[Any],
    ) -> List[str]:
        """Determine which coverages to run."""
        if request.coverages:
            return request.coverages

        # Auto-detect based on rules
        coverages = list(self.config.default_coverages)

        if request.coverage_rules:
            # Apply custom rules
            for rule in self.config.coverage_detection_rules:
                if self._evaluate_rule(rule.condition, request, discovery_result):
                    if rule.coverage not in coverages:
                        coverages.append(rule.coverage)

        return coverages

    def _determine_locales(
        self,
        request: MultiCoverageRequest,
        discovery_result: Optional[Any],
    ) -> List[str]:
        """Determine which locales to test."""
        if request.locales:
            return request.locales

        if request.locale_detection_mode == LocaleDetectionMode.EXPLICIT:
            return self.config.fallback_locales

        if request.locale_detection_mode == LocaleDetectionMode.ALL:
            return self.config.fallback_locales

        # Discovery mode
        if self.locale_detector and discovery_result:
            detected = self.locale_detector.detect_locale(discovery_result)
            if detected:
                return [detected]

        return self.config.fallback_locales

    def _identify_shared_signals(self, coverages: List[str]) -> List[str]:
        """Identify signals that can be shared across coverages."""
        # Common entity-level signals
        shared = [
            "company_profile",
            "financial_health",
            "regulatory_status",
            "news_sentiment",
            "leadership_stability",
        ]
        return shared

    def _estimate_signals(self, coverage: str, locale: str) -> int:
        """Estimate number of signals for a coverage/locale."""
        # Base signal counts by coverage
        base_counts = {
            "fi": 25,
            "cyber": 20,
            "do": 18,
            "pi": 15,
            "marine": 22,
        }
        return base_counts.get(coverage, 20)

    def _get_coverage_priority(self, coverage: str) -> int:
        """Get priority for coverage ordering."""
        priorities = {
            "fi": 100,
            "cyber": 90,
            "do": 80,
            "pi": 70,
        }
        return priorities.get(coverage, 50)

    def _evaluate_rule(
        self,
        condition: str,
        request: MultiCoverageRequest,
        discovery_result: Optional[Any],
    ) -> bool:
        """Evaluate a coverage detection rule."""
        # Simple rule evaluation
        try:
            context = {
                "submission_data": request.submission_data,
                "discovery": discovery_result,
            }

            # Handle common conditions
            if "sic_code in" in condition:
                sic = request.submission_data.get("sic_code", "")
                return sic in condition

            if "is_public_company" in condition:
                return request.submission_data.get("is_public_company", False)

            return False

        except Exception as e:
            logger.warning(f"Rule evaluation failed: {e}")
            return False

    def _find_best_locales(
        self,
        results: Dict[str, CoverageResult],
    ) -> Dict[str, str]:
        """Find best locale for each coverage."""
        best: Dict[str, str] = {}
        coverage_results: Dict[str, List[CoverageResult]] = {}

        # Group by coverage
        for result in results.values():
            if result.coverage not in coverage_results:
                coverage_results[result.coverage] = []
            coverage_results[result.coverage].append(result)

        # Find best for each
        for coverage, locale_results in coverage_results.items():
            successful = [r for r in locale_results if r.success]
            if successful:
                # Use first successful (or could rank by score)
                best[coverage] = successful[0].locale

        return best

    def _extract_premiums(
        self,
        results: Dict[str, CoverageResult],
    ) -> Dict[str, float]:
        """Extract premiums from results."""
        premiums: Dict[str, float] = {}

        for result in results.values():
            if result.success and result.workflow_result:
                premium = getattr(result.workflow_result, 'final_premium', 0)
                if premium > 0:
                    premiums[result.coverage] = premium

        return premiums

    def _calculate_package_discount(
        self,
        coverages: List[str],
        premiums: Dict[str, float],
    ) -> Dict[str, Any]:
        """Calculate applicable package discounts."""
        if not coverages or not premiums:
            return {
                "discount_rate": 0.0,
                "combined_premium": sum(premiums.values()),
                "savings": 0.0,
                "package": [],
                "recommendations": [],
            }

        # Find best applicable discount
        best_discount = None
        for discount in self.config.package_discounts:
            if discount.applies_to(coverages):
                if best_discount is None or discount.discount_rate > best_discount.discount_rate:
                    best_discount = discount

        total_premium = sum(premiums.values())

        if best_discount:
            savings = total_premium * best_discount.discount_rate
            combined = total_premium - savings

            recommendation = PackageRecommendation(
                coverages=best_discount.coverages,
                combined_premium=combined,
                discount_applied=savings,
                discount_rate=best_discount.discount_rate,
                savings=savings,
                reason=f"Bundling {', '.join(best_discount.coverages)} qualifies for {best_discount.discount_rate:.0%} discount",
            )

            return {
                "discount_rate": best_discount.discount_rate,
                "combined_premium": combined,
                "savings": savings,
                "package": best_discount.coverages,
                "recommendations": [recommendation],
            }

        return {
            "discount_rate": 0.0,
            "combined_premium": total_premium,
            "savings": 0.0,
            "package": coverages,
            "recommendations": [],
        }

    def approve_plan(self, plan: ExecutionPlan, approved_by: str) -> ExecutionPlan:
        """Approve an execution plan."""
        plan.approved = True
        plan.approved_by = approved_by
        return plan

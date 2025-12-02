"""
Entity-to-Assessment Generator
================================

Single-input pricing: provide just an Entity Identifier, get comprehensive
assessments across all coverage types with standard limit bandings.

This reduces the minimum viable interaction from 4 data points to 1:
  OLD: entity_id, coverage_type, limit, deductible
  NEW: entity_id

All other parameters are derived from:
- Configurable limit bandings (coverage_limit_bands.yaml)
- DSI signal extraction (automated)
- Model defaults

Usage:
  python entity_to_assessment.py "Microsoft Corporation"
  python entity_to_assessment.py --entity-id "msft-001" --name "Microsoft Corporation"
  python entity_to_assessment.py "Apple Inc" --coverage-types cyber,fi --output json

Author: John Walker
Version: 1.0.0
"""

import argparse
import json
import yaml
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow.dsi_workflow import (
    DSIWorkflow,
    WorkflowRequest,
    WorkflowResponse,
    create_workflow,
    initialize_models,
)
from workflow.dsi_persistence import QuoteStatus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("entity_to_assessment")


# =============================================================================
# CONFIGURATION LOADING
# =============================================================================

@dataclass
class LimitBand:
    """Represents a single limit band."""
    limit: float
    label: str
    standard_deductible: Optional[float] = None


@dataclass
class CoverageConfig:
    """Configuration for a coverage type."""
    enabled: bool
    currency: str
    bands: List[LimitBand]
    name: Optional[str] = None


class LimitBandingConfig:
    """Loads and manages limit banding configuration."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to file in same directory as this script
            config_path = Path(__file__).parent / "coverage_limit_bands.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.defaults = self.config.get("defaults", {})

    def _load_config(self) -> Dict:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_coverage_config(self, coverage_type: str) -> Optional[CoverageConfig]:
        """Get configuration for a coverage type."""
        config = self.config.get(coverage_type)

        if not config or not config.get("enabled", False):
            return None

        bands = [
            LimitBand(
                limit=b["limit"],
                label=b["label"],
                standard_deductible=b.get("standard_deductible")
            )
            for b in config.get("bands", [])
        ]

        return CoverageConfig(
            enabled=config.get("enabled", True),
            currency=config.get("currency", "USD"),
            name=config.get("name"),
            bands=bands,
        )

    def get_enabled_coverages(self) -> List[str]:
        """Get list of enabled coverage types."""
        enabled = []
        for key, value in self.config.items():
            if key not in ["defaults", "custom_bands"] and isinstance(value, dict):
                if value.get("enabled", False):
                    enabled.append(key)
        return enabled


# =============================================================================
# ASSESSMENT GENERATOR
# =============================================================================

@dataclass
class AssessmentResult:
    """Result for a single coverage/limit combination."""
    entity_id: str
    entity_name: str
    coverage_type: str
    coverage_name: str
    limit: float
    limit_label: str
    currency: str
    deductible: Optional[float]

    # Assessment
    composite_score: float
    tier: int
    tier_label: str
    confidence: float
    signal_coverage: float

    # Pricing
    gross_premium: Optional[float]
    net_premium: Optional[float]
    rate_per_million: Optional[float]
    tier_modifier: Optional[float]

    # Decision
    decision_path: str
    status: str
    decision_reasons: List[str]

    # Flags
    green_flag_count: int
    red_flag_count: int
    amber_flag_count: int

    # Metadata
    quote_id: str
    model_version: str
    signal_count: int
    processing_time_ms: float
    cache_hit_rate: float
    created_at: str
    expires_at: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_summary(self) -> Dict:
        """Convert to summary format (less verbose)."""
        return {
            "coverage": self.coverage_type,
            "limit": f"${self.limit:,.0f}",
            "limit_label": self.limit_label,
            "deductible": f"${self.deductible:,.0f}" if self.deductible else "N/A",
            "score": f"{self.composite_score}/1000",
            "tier": self.tier_label,
            "premium": f"${self.gross_premium:,.2f}" if self.gross_premium else "N/A",
            "decision": self.decision_path,
            "status": self.status,
            "flags": {
                "green": self.green_flag_count,
                "amber": self.amber_flag_count,
                "red": self.red_flag_count,
            }
        }


class EntityAssessmentGenerator:
    """
    Generates comprehensive assessments for an entity across all coverages.
    """

    def __init__(self,
                 config_path: Optional[str] = None,
                 storage_type: str = "memory",
                 storage_config: Optional[Dict] = None):
        """
        Initialize generator.

        Args:
            config_path: Path to limit banding config (uses default if None)
            storage_type: "memory", "redis", or "postgres"
            storage_config: Configuration for storage backend
        """
        self.banding_config = LimitBandingConfig(config_path)
        self.workflow = create_workflow(storage_type, storage_config)

        # Initialize models
        initialize_models(self.workflow)

        logger.info("Entity Assessment Generator initialized")
        logger.info(f"Enabled coverages: {', '.join(self.banding_config.get_enabled_coverages())}")

    def generate_for_entity(self,
                            entity_name: str,
                            entity_id: Optional[str] = None,
                            coverage_types: Optional[List[str]] = None,
                            effective_date: Optional[datetime] = None,
                            term_months: int = 12,
                            market: str = "us") -> List[AssessmentResult]:
        """
        Generate assessments for all enabled coverages and limit bands.

        Args:
            entity_name: Company name (required)
            entity_id: Optional entity ID (generated from name if not provided)
            coverage_types: Specific coverage types (all enabled if None)
            effective_date: Policy effective date (30 days from now if None)
            term_months: Policy term in months (default 12)
            market: Market code (default "us")

        Returns:
            List of AssessmentResult objects
        """
        # Generate entity_id from name if not provided
        if entity_id is None:
            entity_id = self._generate_entity_id(entity_name)

        # Use all enabled coverages if not specified
        if coverage_types is None:
            coverage_types = self.banding_config.get_enabled_coverages()

        # Default effective date
        if effective_date is None:
            effective_date = datetime.utcnow() + timedelta(days=30)

        results = []

        logger.info(f"\n{'='*70}")
        logger.info(f"GENERATING ASSESSMENTS FOR: {entity_name}")
        logger.info(f"Entity ID: {entity_id}")
        logger.info(f"Coverage Types: {', '.join(coverage_types)}")
        logger.info(f"{'='*70}\n")

        for coverage_type in coverage_types:
            coverage_config = self.banding_config.get_coverage_config(coverage_type)

            if not coverage_config:
                logger.warning(f"Coverage {coverage_type} not enabled or not found")
                continue

            coverage_name = coverage_config.name or coverage_type.upper()

            logger.info(f"\n--- {coverage_name} ---")

            for band in coverage_config.bands:
                logger.info(f"Processing {band.label} (${band.limit:,.0f})...")

                # Create workflow request
                request = WorkflowRequest(
                    entity_id=entity_id,
                    entity_name=entity_name,
                    coverage_type=coverage_type,
                    limit=band.limit,
                    currency=coverage_config.currency,
                    effective_date=effective_date,
                    term_months=term_months,
                    deductible=band.standard_deductible,
                    market=market,
                    submission_channel="entity_assessment_generator",
                    direct_inquiry={
                        "pending_claims": False,
                        "pending_regulatory": False,
                        "coverage_declined": False,
                        "material_change": False,
                        "ownership_change": False,
                    },
                )

                try:
                    # Process through workflow
                    response = self.workflow.process(request)

                    # Convert to AssessmentResult
                    result = self._response_to_result(
                        response,
                        entity_name,
                        coverage_type,
                        coverage_name,
                        band,
                        coverage_config.currency,
                    )

                    results.append(result)

                    logger.info(
                        f"  ✓ Score: {result.composite_score}/1000 | "
                        f"Tier: {result.tier_label} | "
                        f"Premium: ${result.gross_premium:,.2f} | "
                        f"Path: {result.decision_path}"
                    )

                except Exception as e:
                    logger.error(f"  ✗ Error processing {band.label}: {e}")
                    continue

        logger.info(f"\n{'='*70}")
        logger.info(f"ASSESSMENT COMPLETE: {len(results)} quotes generated")
        logger.info(f"{'='*70}\n")

        return results

    def _generate_entity_id(self, entity_name: str) -> str:
        """Generate a consistent entity ID from entity name."""
        # Simple slug generation
        import re
        slug = re.sub(r'[^a-z0-9]+', '-', entity_name.lower()).strip('-')
        # Add timestamp suffix for uniqueness
        suffix = datetime.utcnow().strftime('%Y%m%d')
        return f"{slug}-{suffix}"

    def _response_to_result(self,
                            response: WorkflowResponse,
                            entity_name: str,
                            coverage_type: str,
                            coverage_name: str,
                            band: LimitBand,
                            currency: str) -> AssessmentResult:
        """Convert WorkflowResponse to AssessmentResult."""
        quote = response.quote

        return AssessmentResult(
            entity_id=quote.entity_id,
            entity_name=entity_name,
            coverage_type=coverage_type,
            coverage_name=coverage_name,
            limit=band.limit,
            limit_label=band.label,
            currency=currency,
            deductible=band.standard_deductible,
            composite_score=quote.composite_score,
            tier=quote.tier,
            tier_label=quote.tier_label,
            confidence=quote.confidence,
            signal_coverage=quote.signal_coverage,
            gross_premium=quote.gross_premium,
            net_premium=quote.net_premium,
            rate_per_million=quote.rate_per_million,
            tier_modifier=quote.tier_modifier,
            decision_path=quote.decision_path,
            status=quote.status.value,
            decision_reasons=quote.decision_reasons,
            green_flag_count=len(quote.green_flags),
            red_flag_count=len(quote.red_flags),
            amber_flag_count=len(quote.amber_flags),
            quote_id=quote.quote_id,
            model_version=response.model_version,
            signal_count=response.signal_count,
            processing_time_ms=response.processing_time_ms,
            cache_hit_rate=response.cache_stats.get("hit_rate", 0),
            created_at=quote.created_at.isoformat(),
            expires_at=quote.expires_at.isoformat(),
        )

    def export_results(self,
                       results: List[AssessmentResult],
                       output_format: str = "json",
                       output_file: Optional[str] = None) -> str:
        """
        Export results to file or return as string.

        Args:
            results: List of assessment results
            output_format: "json", "summary", or "csv"
            output_file: Optional file path to write to

        Returns:
            Formatted string output
        """
        if output_format == "json":
            data = {
                "entity": results[0].entity_name if results else "",
                "entity_id": results[0].entity_id if results else "",
                "generated_at": datetime.utcnow().isoformat(),
                "total_assessments": len(results),
                "assessments": [r.to_dict() for r in results],
            }
            output = json.dumps(data, indent=2)

        elif output_format == "summary":
            data = {
                "entity": results[0].entity_name if results else "",
                "entity_id": results[0].entity_id if results else "",
                "generated_at": datetime.utcnow().isoformat(),
                "total_assessments": len(results),
                "assessments": [r.to_summary() for r in results],
            }
            output = json.dumps(data, indent=2)

        elif output_format == "csv":
            import csv
            from io import StringIO

            buffer = StringIO()
            if results:
                writer = csv.DictWriter(buffer, fieldnames=results[0].to_dict().keys())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.to_dict())

            output = buffer.getvalue()

        else:
            raise ValueError(f"Unknown output format: {output_format}")

        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            logger.info(f"Results exported to: {output_file}")

        return output


# =============================================================================
# COMMAND-LINE INTERFACE
# =============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive DSI assessments from just an entity identifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate assessments for all coverages
  python entity_to_assessment.py "Microsoft Corporation"

  # Specific coverages only
  python entity_to_assessment.py "Apple Inc" --coverage-types cyber,fi,do

  # With custom entity ID and output
  python entity_to_assessment.py "Tesla" --entity-id tsla-001 --output results.json

  # Summary format
  python entity_to_assessment.py "Amazon" --format summary --output summary.json

  # CSV export
  python entity_to_assessment.py "Google" --format csv --output assessments.csv
        """
    )

    parser.add_argument(
        "entity_name",
        help="Company/entity name to assess"
    )

    parser.add_argument(
        "--entity-id",
        help="Optional entity ID (generated from name if not provided)"
    )

    parser.add_argument(
        "--coverage-types",
        help="Comma-separated list of coverage types (e.g., 'cyber,fi,do'). Defaults to all enabled."
    )

    parser.add_argument(
        "--config",
        help="Path to limit banding config YAML file (uses default if not specified)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "summary", "csv"],
        default="summary",
        help="Output format (default: summary)"
    )

    parser.add_argument(
        "--output",
        help="Output file path (prints to stdout if not specified)"
    )

    parser.add_argument(
        "--market",
        default="us",
        help="Market code (default: us)"
    )

    parser.add_argument(
        "--term-months",
        type=int,
        default=12,
        help="Policy term in months (default: 12)"
    )

    parser.add_argument(
        "--storage",
        choices=["memory", "redis", "postgres"],
        default="memory",
        help="Storage backend (default: memory)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse coverage types
    coverage_types = None
    if args.coverage_types:
        coverage_types = [c.strip() for c in args.coverage_types.split(",")]

    try:
        # Initialize generator
        generator = EntityAssessmentGenerator(
            config_path=args.config,
            storage_type=args.storage,
        )

        # Generate assessments
        results = generator.generate_for_entity(
            entity_name=args.entity_name,
            entity_id=args.entity_id,
            coverage_types=coverage_types,
            term_months=args.term_months,
            market=args.market,
        )

        # Export results
        output = generator.export_results(
            results,
            output_format=args.format,
            output_file=args.output,
        )

        # Print to stdout if no output file
        if not args.output:
            print(output)

        # Summary statistics
        if results:
            print(f"\n{'='*70}")
            print(f"SUMMARY STATISTICS")
            print(f"{'='*70}")
            print(f"Entity: {results[0].entity_name}")
            print(f"Total Assessments: {len(results)}")
            print(f"Average Score: {sum(r.composite_score for r in results) / len(results):.0f}/1000")
            print(f"Total Premium: ${sum(r.gross_premium or 0 for r in results):,.2f}")

            # Breakdown by decision path
            straight_through = sum(1 for r in results if r.decision_path == "straight_through")
            referred = sum(1 for r in results if r.decision_path == "referred")
            declined = sum(1 for r in results if r.decision_path == "declined")

            print(f"\nDecision Breakdown:")
            print(f"  Straight Through: {straight_through} ({straight_through/len(results)*100:.0f}%)")
            print(f"  Referred: {referred} ({referred/len(results)*100:.0f}%)")
            print(f"  Declined: {declined} ({declined/len(results)*100:.0f}%)")
            print(f"{'='*70}\n")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()

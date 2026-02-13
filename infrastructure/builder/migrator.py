"""
DSI Config Migrator (Phase V6)

Migrates existing coverage configurations from v2.0/v2.1 to v2.2 schema.

Key migrations:
- Add V5 pricing anchors (base_limit_reference, base_deductible_reference)
- Convert deductible_credits (percentage-based) to deductible_factors (fixed amounts)
- Ensure V4 multiplexer fields are present (model_specificity, routing_constraints)
- Update version to 2.2.0

Usage:
    from infrastructure.builder.migrator import ConfigMigrator

    migrator = ConfigMigrator()
    migrator.migrate_file("coverages/cyber/config.yaml")
    # or
    migrator.migrate_all_coverages()
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger("dsi.migrator")


class ConfigMigrator:
    """
    Migrates coverage configurations to v2.2 schema.

    Handles the conversion from percentage-based deductible_credits
    to fixed-amount deductible_factors with anchor-based pricing.
    """

    # Standard deductible amounts for conversion
    STANDARD_DEDUCTIBLES = [10000, 25000, 50000, 100000, 250000, 500000, 1000000]

    # Default anchor values
    DEFAULT_BASE_LIMIT = 1000000
    DEFAULT_BASE_DEDUCTIBLE = 50000

    def __init__(self, coverages_dir: str = "coverages", dry_run: bool = False):
        """
        Initialize migrator.

        Args:
            coverages_dir: Root directory containing coverage configs
            dry_run: If True, don't write changes, just report what would change
        """
        self.coverages_dir = Path(coverages_dir)
        self.dry_run = dry_run
        self.migration_log: List[str] = []

    def migrate_all_coverages(self) -> Dict[str, bool]:
        """
        Migrate all coverage configs in the coverages directory.

        Returns:
            Dict mapping coverage name to success status
        """
        results = {}

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir():
                continue

            config_path = coverage_dir / "config.yaml"
            if config_path.exists():
                try:
                    success = self.migrate_file(str(config_path))
                    results[coverage_dir.name] = success
                except Exception as e:
                    logger.error(f"Failed to migrate {coverage_dir.name}: {e}")
                    results[coverage_dir.name] = False

        return results

    def migrate_file(self, config_path: str) -> bool:
        """
        Migrate a single config file to v2.2 schema.

        Args:
            config_path: Path to the config.yaml file

        Returns:
            True if migration successful
        """
        logger.info(f"Migrating {config_path}")
        self.migration_log.append(f"\n=== Migrating {config_path} ===")

        # Read the file content as text to preserve structure
        with open(config_path, 'r') as f:
            content = f.read()

        # Parse YAML
        config = yaml.safe_load(content)
        if not config:
            logger.warning(f"Empty or invalid config: {config_path}")
            return False

        # Track if changes were made
        changes_made = False

        # Get coverage root key (e.g., "cyber", "do", "marine")
        coverage_key = list(config.keys())[0]
        coverage_config = config[coverage_key]

        # Migrate each configuration within the coverage
        for config_name, inner_config in coverage_config.items():
            if not isinstance(inner_config, dict):
                continue

            # Migrate pricing section
            if 'pricing' in inner_config:
                pricing_changed = self._migrate_pricing_section(
                    inner_config['pricing'],
                    config_name
                )
                changes_made = changes_made or pricing_changed

            # Ensure V4 metadata fields exist
            if 'metadata' in inner_config:
                metadata_changed = self._ensure_v4_metadata(
                    inner_config['metadata'],
                    config_name
                )
                changes_made = changes_made or metadata_changed

        if changes_made and not self.dry_run:
            # Write back with preserved formatting as much as possible
            self._write_config(config_path, config)
            self.migration_log.append(f"  [SAVED] Changes written to {config_path}")
        elif changes_made:
            self.migration_log.append(f"  [DRY RUN] Would save changes to {config_path}")
        else:
            self.migration_log.append(f"  [NO CHANGES] {config_path} already up to date")

        return True

    def _migrate_pricing_section(self, pricing: Dict[str, Any], config_name: str) -> bool:
        """
        Migrate pricing section to v2.2 schema.

        Handles both flat pricing and by_product_type nested pricing.
        """
        changes_made = False

        # Check if pricing uses by_product_type structure
        if 'by_product_type' in pricing:
            for product_type, product_pricing in pricing['by_product_type'].items():
                if isinstance(product_pricing, dict):
                    changed = self._migrate_single_pricing(
                        product_pricing,
                        f"{config_name}.{product_type}"
                    )
                    changes_made = changes_made or changed
        else:
            # Flat pricing structure
            changed = self._migrate_single_pricing(pricing, config_name)
            changes_made = changes_made or changed

        return changes_made

    def _migrate_single_pricing(self, pricing: Dict[str, Any], context: str) -> bool:
        """Migrate a single pricing block."""
        changes_made = False

        # Add pricing anchors if missing
        if 'base_limit_reference' not in pricing:
            # Infer from ILF curve if possible
            base_limit = self._infer_base_limit(pricing)
            pricing['base_limit_reference'] = base_limit
            self.migration_log.append(f"  [ADD] {context}: base_limit_reference = {base_limit}")
            changes_made = True

        if 'base_deductible_reference' not in pricing:
            # Use default or infer from deductible structure
            base_ded = self._infer_base_deductible(pricing)
            pricing['base_deductible_reference'] = base_ded
            self.migration_log.append(f"  [ADD] {context}: base_deductible_reference = {base_ded}")
            changes_made = True

        # Convert deductible_credits to deductible_factors
        if 'deductible_credits' in pricing and 'deductible_factors' not in pricing:
            credits = pricing['deductible_credits']
            base_ded = pricing.get('base_deductible_reference', self.DEFAULT_BASE_DEDUCTIBLE)

            factors = self._convert_credits_to_factors(credits, base_ded)
            pricing['deductible_factors'] = factors

            # Remove old structure
            del pricing['deductible_credits']

            self.migration_log.append(f"  [CONVERT] {context}: deductible_credits -> deductible_factors")
            self.migration_log.append(f"            Factors: {factors}")
            changes_made = True

        return changes_made

    def _ensure_v4_metadata(self, metadata: Dict[str, Any], config_name: str) -> bool:
        """Ensure V4 multiplexer fields exist in metadata."""
        changes_made = False

        if 'model_specificity' not in metadata:
            # Default to 1 (General) - can be manually adjusted
            metadata['model_specificity'] = 1
            self.migration_log.append(f"  [ADD] {config_name}: model_specificity = 1")
            changes_made = True

        if 'routing_constraints' not in metadata:
            metadata['routing_constraints'] = []
            self.migration_log.append(f"  [ADD] {config_name}: routing_constraints = []")
            changes_made = True

        # Update version if needed
        current_version = metadata.get('version', '1.0.0')
        if not current_version.startswith('2.2') and not current_version.startswith('2.3'):
            # Don't downgrade if already at 2.3+
            if self._version_compare(current_version, '2.2.0') < 0:
                metadata['version'] = '2.2.0'
                self.migration_log.append(f"  [UPDATE] {config_name}: version {current_version} -> 2.2.0")
                changes_made = True

        return changes_made

    def _infer_base_limit(self, pricing: Dict[str, Any]) -> int:
        """Infer base limit reference from ILF curve."""
        ilf_curve = pricing.get('ilf_curve', {})

        # Check for explicit base_limit in curve
        if 'base_limit' in ilf_curve:
            return ilf_curve['base_limit']

        # Find the factor = 1.00 entry
        factors = ilf_curve.get('factors', [])
        for entry in factors:
            if entry.get('factor') == 1.0 or entry.get('factor') == 1.00:
                return entry.get('limit', self.DEFAULT_BASE_LIMIT)

        return self.DEFAULT_BASE_LIMIT

    def _infer_base_deductible(self, pricing: Dict[str, Any]) -> int:
        """Infer base deductible reference from existing structure."""
        # Check if there's a deductible_factors already with factor 1.00
        factors = pricing.get('deductible_factors', [])
        for entry in factors:
            if entry.get('factor') == 1.0 or entry.get('factor') == 1.00:
                return entry.get('deductible', self.DEFAULT_BASE_DEDUCTIBLE)

        # For percentage-based credits, use standard anchor
        return self.DEFAULT_BASE_DEDUCTIBLE

    def _convert_credits_to_factors(
        self,
        credits: List[Dict[str, Any]],
        base_deductible: int
    ) -> List[Dict[str, Any]]:
        """
        Convert percentage-based deductible credits to fixed deductible factors.

        The old system used: credit based on deductible as % of TIV
        The new system uses: factor based on fixed deductible amounts

        Conversion approach:
        - Map percentage bands to standard deductible amounts
        - Convert credit (subtraction) to factor (multiplication)
        - Ensure anchor deductible has factor 1.00
        """
        # Build factor table with standard deductibles
        factors = []

        # Start with lower deductibles (premium loading)
        lower_deds = [d for d in self.STANDARD_DEDUCTIBLES if d < base_deductible]
        for ded in sorted(lower_deds, reverse=True):
            ratio = base_deductible / ded
            # Lower deductible = higher premium, factor > 1.0
            # Use inverse relationship: half the deductible = ~15% loading
            factor = 1.0 + (ratio - 1) * 0.15
            factors.append({
                "deductible": ded,
                "factor": round(min(factor, 1.50), 2)  # Cap at 50% loading
            })

        # Add anchor
        factors.append({
            "deductible": base_deductible,
            "factor": 1.00
        })

        # Higher deductibles (premium credit)
        higher_deds = [d for d in self.STANDARD_DEDUCTIBLES if d > base_deductible]

        # Map credits from old structure if available
        credit_map = self._build_credit_map(credits)

        for ded in sorted(higher_deds):
            ratio = ded / base_deductible
            # Use credit map if available, otherwise estimate
            if ratio <= 2:
                factor = 1.0 - credit_map.get('low', 0.10)
            elif ratio <= 5:
                factor = 1.0 - credit_map.get('medium', 0.20)
            else:
                factor = 1.0 - credit_map.get('high', 0.30)

            factors.append({
                "deductible": ded,
                "factor": round(max(factor, 0.40), 2)  # Floor at 60% credit
            })

        # Sort by deductible
        factors.sort(key=lambda x: x['deductible'])

        return factors

    def _build_credit_map(self, credits: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract credit values from percentage-based structure."""
        credit_map = {'low': 0.10, 'medium': 0.20, 'high': 0.30}

        if not credits:
            return credit_map

        # Map credit bands to approximate tiers
        for i, credit_def in enumerate(credits):
            credit_val = credit_def.get('credit', 0)
            if i == 0:
                credit_map['low'] = credit_val
            elif i == 1:
                credit_map['medium'] = credit_val
            else:
                credit_map['high'] = max(credit_map['high'], credit_val)

        return credit_map

    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare version strings. Returns -1, 0, or 1."""
        def parse(v):
            return [int(x) for x in re.findall(r'\d+', v)]

        p1, p2 = parse(v1), parse(v2)

        for a, b in zip(p1, p2):
            if a < b:
                return -1
            if a > b:
                return 1

        return len(p1) - len(p2)

    def _write_config(self, config_path: str, config: Dict[str, Any]) -> None:
        """Write config back to file with proper YAML formatting."""
        # Custom representer to handle flow style for simple lists
        def represent_list(dumper, data):
            # Use flow style for simple dicts in lists (like factors)
            if all(isinstance(item, dict) and len(item) <= 3 for item in data):
                if all(
                    all(isinstance(v, (int, float, str, bool, type(None))) for v in item.values())
                    for item in data
                ):
                    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
            return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)

        # Read original file to preserve header comments
        with open(config_path, 'r') as f:
            original_content = f.read()

        # Extract header comments (lines starting with #)
        header_lines = []
        for line in original_content.split('\n'):
            if line.startswith('#') or line.strip() == '':
                header_lines.append(line)
            else:
                break

        header = '\n'.join(header_lines)
        if header and not header.endswith('\n'):
            header += '\n\n'

        # Dump YAML
        yaml_content = yaml.dump(
            config,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120
        )

        # Write with header
        with open(config_path, 'w') as f:
            f.write(header)
            f.write(yaml_content)

    def get_migration_report(self) -> str:
        """Get a report of all migration actions."""
        return '\n'.join(self.migration_log)


def migrate_coverage_configs(dry_run: bool = False) -> None:
    """
    CLI entry point for migrating all coverage configs.

    Args:
        dry_run: If True, report changes without writing
    """
    migrator = ConfigMigrator(dry_run=dry_run)
    results = migrator.migrate_all_coverages()

    print("\n" + "=" * 60)
    print("MIGRATION REPORT")
    print("=" * 60)
    print(migrator.get_migration_report())
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for coverage, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {coverage}: {status}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\nTotal: {passed}/{total} coverages migrated successfully")


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    migrate_coverage_configs(dry_run=dry_run)

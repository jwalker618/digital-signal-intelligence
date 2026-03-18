"""
DSI Configuration Compiler (Version 4 - Phase 1)

Compiles YAML configurations into strongly-typed Pydantic models at startup.
Uses @lru_cache for singleton behavior - configs are loaded once and cached.

Usage:
    from infrastructure.models.compiler import get_compiled_configs, get_config

    # Get all compiled configs (cached)
    configs = get_compiled_configs()

    # Get specific config with dot notation
    config = get_config("cyber", "cyber_general")
    base_limit = config.pricing.base_limit_reference
    tier = config.get_tier_for_score(750.0)
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional
import logging

import yaml
from pydantic import ValidationError

from .config_schema import Coverage, CoverageConfig


logger = logging.getLogger("dsi.compiler")


class ConfigCompilationError(Exception):
    """Raised when configuration fails to compile."""
    def __init__(self, coverage: str, config: str, errors: str):
        self.coverage = coverage
        self.config = config
        self.errors = errors
        super().__init__(f"Failed to compile {coverage}/{config}: {errors}")


class ConfigNotFoundError(Exception):
    """Raised when requested configuration is not found."""
    pass


# =============================================================================
# COMPILED CONFIG CACHE
# =============================================================================

@lru_cache(maxsize=1)
def get_compiled_configs(
    coverages_dir: Optional[str] = None
) -> Dict[str, Coverage]:
    """
    Load and compile all coverage configurations into Pydantic models.

    This function is cached - it executes only once per process lifetime.
    All configurations are validated at startup. If any config fails validation,
    the application will not boot (fail-fast behavior).

    Args:
        coverages_dir: Path to coverages directory. If None, auto-discovers.

    Returns:
        Dict mapping coverage_id to Coverage model

    Raises:
        ConfigCompilationError: If any configuration fails validation
    """
    if coverages_dir is None:
        # Auto-discover coverages directory
        possible_paths = [
            Path(__file__).parent.parent.parent / "coverages",
            Path(__file__).parent.parent / "coverages",
            Path("coverages"),
        ]
        for p in possible_paths:
            if p.exists() and p.is_dir():
                coverages_dir = str(p)
                break

    if coverages_dir is None:
        logger.warning("No coverages directory found, returning empty config")
        return {}

    coverages_path = Path(coverages_dir)
    compiled: Dict[str, Coverage] = {}

    logger.info(f"Compiling configs from {coverages_path}")

    for coverage_path in coverages_path.iterdir():
        if not coverage_path.is_dir():
            continue

        config_file = coverage_path / "config.yaml"
        if not config_file.exists():
            continue

        coverage_id = coverage_path.name

        try:
            with open(config_file) as f:
                raw_data = yaml.safe_load(f)

            if not isinstance(raw_data, dict):
                logger.warning(f"Invalid structure in {config_file}, skipping")
                continue

            # Try directory name first, then fall back to the first (only) key
            if coverage_id in raw_data:
                coverage_data = raw_data[coverage_id]
            elif len(raw_data) == 1:
                actual_key = next(iter(raw_data))
                logger.info(
                    f"Using key '{actual_key}' for coverage dir '{coverage_id}'"
                )
                coverage_data = raw_data[actual_key]
            else:
                logger.warning(f"No matching key in {config_file}, skipping")
                continue
            configurations = {}

            for config_id, config_data in coverage_data.items():
                if not isinstance(config_data, dict):
                    continue

                # Skip if this looks like a metadata key, not a config
                if "metadata" not in config_data and "signal_registry" not in config_data:
                    continue

                try:
                    compiled_config = CoverageConfig(
                        coverage_id=coverage_id,
                        config_id=config_id,
                        **config_data,
                    )
                    configurations[config_id] = compiled_config
                    logger.info(f"Compiled: {coverage_id}/{config_id}")
                except (ValidationError, ValueError) as e:
                    # Log validation errors and skip this config
                    if isinstance(e, ValidationError):
                        error_messages = []
                        for err in e.errors():
                            loc = " -> ".join(str(x) for x in err["loc"])
                            error_messages.append(f"{loc}: {err['msg']}")
                        detail = "; ".join(error_messages)
                    else:
                        detail = str(e)
                    logger.warning(
                        f"Skipping {coverage_id}/{config_id}: {detail}"
                    )
                    continue

            if configurations:
                compiled[coverage_id] = Coverage(
                    coverage_id=coverage_id,
                    configurations=configurations
                )

        except ConfigCompilationError:
            raise  # Re-raise compilation errors
        except Exception as e:
            logger.error(f"Failed to load {config_file}: {e}")
            raise ConfigCompilationError(coverage_id, "unknown", str(e))

    logger.info(f"Compilation complete: {len(compiled)} coverages loaded")
    return compiled


def clear_config_cache():
    """Clear the compiled config cache. Useful for testing."""
    get_compiled_configs.cache_clear()


# =============================================================================
# CONFIG ACCESS HELPERS
# =============================================================================

def get_coverage(coverage_id: str) -> Coverage:
    """
    Get a compiled Coverage by ID.

    Args:
        coverage_id: Coverage identifier (e.g., "cyber")

    Returns:
        Compiled Coverage model

    Raises:
        ConfigNotFoundError: If coverage not found
    """
    configs = get_compiled_configs()
    if coverage_id not in configs:
        raise ConfigNotFoundError(f"Coverage '{coverage_id}' not found")
    return configs[coverage_id]


def get_config(
    coverage_id: str,
    config_id: Optional[str] = None
) -> CoverageConfig:
    """
    Get a compiled CoverageConfig.

    Args:
        coverage_id: Coverage identifier (e.g., "cyber")
        config_id: Configuration identifier (e.g., "cyber_general").
                   If None, defaults to {coverage_id}_general.

    Returns:
        Compiled CoverageConfig model with O(1) attribute access

    Raises:
        ConfigNotFoundError: If coverage or config not found

    Example:
        config = get_config("cyber", "cyber_general")

        # O(1) attribute access (no dict lookups)
        base_limit = config.pricing.base_limit_reference
        min_premium = config.metadata.min_premium

        # Type-safe methods
        tier = config.get_tier_for_score(750.0)
        ilf = config.get_ilf("standard", 5_000_000)
    """
    coverage = get_coverage(coverage_id)

    if config_id is None:
        config_id = f"{coverage_id}_general"

    if config_id not in coverage.configurations:
        available = list(coverage.configurations.keys())
        raise ConfigNotFoundError(
            f"Configuration '{config_id}' not found in coverage '{coverage_id}'. "
            f"Available: {available}"
        )

    return coverage.configurations[config_id]


def list_coverages() -> list[str]:
    """List all available coverage IDs."""
    return list(get_compiled_configs().keys())


def list_configurations(coverage_id: str) -> list[str]:
    """List all configuration IDs for a coverage."""
    coverage = get_coverage(coverage_id)
    return list(coverage.configurations.keys())


# =============================================================================
# STARTUP VALIDATION
# =============================================================================

def validate_all_configs() -> Dict[str, list[str]]:
    """
    Validate all configurations and return any warnings.

    This is called implicitly by get_compiled_configs(), but can be
    called explicitly for health checks or CI/CD pipelines.

    Returns:
        Dict mapping coverage/config to list of warnings

    Raises:
        ConfigCompilationError: If any config fails validation
    """
    configs = get_compiled_configs()
    warnings: Dict[str, list[str]] = {}

    for coverage_id, coverage in configs.items():
        for config_id, config in coverage.configurations.items():
            key = f"{coverage_id}/{config_id}"
            config_warnings = []

            # Check signal registry completeness
            if len(config.signal_registry) == 0:
                config_warnings.append("Empty signal_registry")

            # Check group weight sums
            risk_weight = sum(
                g.risk.weight if g.risk else 0.0
                for g in config.groups.three_layer_assessment
            )
            if risk_weight > 0 and not (0.99 <= risk_weight <= 1.01):
                config_warnings.append(
                    f"Risk group weights sum to {risk_weight:.2f}, expected 1.0"
                )

            # Check for DECLINE tier
            has_decline = any(
                band.interpretation.action.value == "DECLINE"
                for band in config.risk_tier_bands.bands
            )
            if not has_decline:
                config_warnings.append("No DECLINE tier defined")

            # Check product type coverage
            for pt in config.metadata.product_types:
                if pt not in config.pricing.by_product_type:
                    config_warnings.append(
                        f"Product type '{pt}' missing from pricing.by_product_type"
                    )

            if config_warnings:
                warnings[key] = config_warnings

    return warnings


# =============================================================================
# MIGRATION HELPER
# =============================================================================

def migrate_dict_config(raw_config: dict) -> CoverageConfig:
    """
    Migrate a raw dictionary config to compiled Pydantic model.

    Useful for gradually migrating code that uses raw dict configs.

    Args:
        raw_config: Raw configuration dictionary (inner config, not full YAML)

    Returns:
        Compiled CoverageConfig

    Raises:
        ValidationError: If config doesn't match schema
    """
    return CoverageConfig(**raw_config)

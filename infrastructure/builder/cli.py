"""
DSI Coverage Builder CLI

Command-line interface for building new coverage configurations.

Usage:
    python -m infrastructure.builder.cli --name "Cyber Japan" \
        --industry technology --market jp \
        --description "Cyber liability for Japanese market" \
        --strategy conservative

    python -m infrastructure.builder.cli --name "Casualty" \
        --industry manufacturing --market us \
        --description "General casualty coverage"

    python -m infrastructure.builder.cli --validate coverages/cyber/config.yaml
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .coverage_builder import CoverageBuilder
from .types import CoverageSpec
from .validator import ConfigValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dsi-builder",
        description="DSI Coverage Builder - Generate v2.0 compliant coverage configurations",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- build command ---
    build_cmd = subparsers.add_parser("build", help="Build a new coverage configuration")
    build_cmd.add_argument("--name", required=True, help="Coverage name (e.g. 'Cyber Japan')")
    build_cmd.add_argument("--industry", required=True, help="Target industry")
    build_cmd.add_argument("--description", required=True, help="Coverage description")
    build_cmd.add_argument("--market", default="us", help="Target market (default: us)")
    build_cmd.add_argument("--strategy", default="standard",
                           choices=["standard", "conservative", "aggressive"],
                           help="Tier strategy")
    build_cmd.add_argument("--min-signals", type=int, default=15, help="Min signal count")
    build_cmd.add_argument("--max-signals", type=int, default=40, help="Max signal count")
    build_cmd.add_argument("--output-dir", default="coverages", help="Output directory")
    build_cmd.add_argument("--write", action="store_true", help="Write config to file")
    build_cmd.add_argument("--json", action="store_true", dest="json_output",
                           help="Output result as JSON")

    # --- validate command ---
    validate_cmd = subparsers.add_parser("validate", help="Validate an existing config")
    validate_cmd.add_argument("file", help="YAML config file to validate")
    validate_cmd.add_argument("--json", action="store_true", dest="json_output",
                              help="Output result as JSON")

    # --- expand command ---
    expand_cmd = subparsers.add_parser("expand", help="Expand coverage from an expansion spec")
    expand_cmd.add_argument("--spec", required=True, help="Path to expansion spec YAML")
    expand_cmd.add_argument("--existing-config", default=None,
                            help="Path to existing config.yaml to merge into")
    expand_cmd.add_argument("--output-dir", default=".", help="Output directory root")
    expand_cmd.add_argument("--write", action="store_true", help="Write generated files to disk")
    expand_cmd.add_argument("--dry-run", action="store_true",
                            help="Show what would be generated without writing")
    expand_cmd.add_argument("--json", action="store_true", dest="json_output",
                            help="Output result as JSON")

    # --- list command ---
    subparsers.add_parser("list-industries", help="List available industry profiles")
    subparsers.add_parser("list-signals", help="List available signal groups")

    return parser


async def cmd_build(args) -> int:
    """Build a new coverage."""
    spec = CoverageSpec(
        name=args.name,
        description=args.description,
        industry=args.industry,
        target_market=args.market,
        applicable_markets=[args.market.lower()],
        tier_strategy=args.strategy,
        min_signals=args.min_signals,
        max_signals=args.max_signals,
    )

    builder = CoverageBuilder(output_dir=args.output_dir)

    def on_progress(p):
        if not args.json_output:
            print(f"  [{p.progress:.0%}] {p.message}")

    builder.on_progress(on_progress)

    if not args.json_output:
        print(f"Building coverage: {spec.name}")
        print(f"  Industry: {spec.industry}")
        print(f"  Market: {spec.applicable_markets}")
        print(f"  Strategy: {spec.tier_strategy}")
        print()

    result = await builder.create_coverage(spec)

    if args.json_output:
        output = {
            "success": result.success,
            "coverage_name": result.coverage_name,
            "config_path": result.config_path,
            "warnings": result.warnings,
            "human_review_required": result.human_review_required,
            "validation_errors": result.validation_results.error_count if result.validation_results else 0,
            "validation_warnings": result.validation_results.warning_count if result.validation_results else 0,
            "build_duration_seconds": round(result.build_duration_seconds, 3),
            "generated_files": list(result.generated_files.keys()),
        }
        print(json.dumps(output, indent=2))
    else:
        print()
        if result.success:
            print(f"BUILD SUCCESSFUL: {result.coverage_name}")
        else:
            print(f"BUILD FAILED: {result.coverage_name}")

        if result.validation_results:
            vr = result.validation_results
            print(f"  Validation: {'PASS' if vr.valid else 'FAIL'} "
                  f"({vr.error_count} errors, {vr.warning_count} warnings)")

        if result.warnings:
            print(f"  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

        if result.human_review_required:
            print(f"  Human review required:")
            for r in result.human_review_required:
                print(f"    - {r}")

        print(f"  Duration: {result.build_duration_seconds:.3f}s")
        print(f"  Config path: {result.config_path}")

        if args.write and result.config_yaml:
            output_path = Path(result.config_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.config_yaml)
            print(f"  Written to: {output_path}")

            for path, content in result.generated_files.items():
                file_path = Path(path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                print(f"  Generated: {file_path}")
        elif result.config_yaml and not args.write:
            print()
            print("--- Generated Config (use --write to save) ---")
            print(result.config_yaml[:2000])
            if len(result.config_yaml) > 2000:
                print(f"... ({len(result.config_yaml)} bytes total)")

    return 0 if result.success else 1


def cmd_validate(args) -> int:
    """Validate an existing config."""
    validator = ConfigValidator()
    result = validator.validate_file(args.file)

    if args.json_output:
        output = {
            "valid": result.valid,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "issues": [
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                    "path": i.path,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Validating: {args.file}")
        print(f"  Result: {'VALID' if result.valid else 'INVALID'}")
        print(f"  Errors: {result.error_count}")
        print(f"  Warnings: {result.warning_count}")

        if result.issues:
            print()
            for issue in result.issues:
                severity = issue.severity.value.upper()
                print(f"  [{severity}] {issue.category}: {issue.message}")
                if issue.path:
                    print(f"           at: {issue.path}")
                if issue.suggestion:
                    print(f"           fix: {issue.suggestion}")

    return 0 if result.valid else 1


def cmd_expand(args) -> int:
    """Expand coverage from an expansion spec."""
    from .expansion_generator import CoverageExpansionGenerator, load_expansion_spec

    spec_path = args.spec
    if not Path(spec_path).exists():
        print(f"Error: spec file not found: {spec_path}")
        return 1

    spec = load_expansion_spec(spec_path)

    if not args.json_output:
        print(f"Coverage Expansion: {spec.description}")
        print(f"  Coverage line: {spec.coverage_line}")
        print(f"  Phase: {spec.phase}")
        print(f"  Configurations: {len(spec.configurations)}")
        print(f"  New signal groups: {len(spec.new_signal_groups)}")
        new_signals = sum(len(g.signals) for g in spec.new_signal_groups)
        print(f"  New signals: {new_signals}")
        print()

    generator = CoverageExpansionGenerator(
        spec=spec,
        existing_config_path=args.existing_config,
        output_dir=args.output_dir,
    )

    result = generator.generate(write=args.write, dry_run=args.dry_run)

    if args.json_output:
        output = {
            "success": result.success,
            "stats": result.stats,
            "validation_errors": result.validation_errors,
            "validation_warnings": result.validation_warnings,
            "generated_files": list(result.generated_files.keys()),
        }
        print(json.dumps(output, indent=2))
    else:
        if result.validation_errors:
            print("VALIDATION ERRORS:")
            for err in result.validation_errors:
                print(f"  - {err}")
            return 1

        print(f"GENERATION {'(dry run) ' if args.dry_run else ''}COMPLETE")
        print(f"  Configurations: {result.stats.get('configurations_generated', 0)}")
        print(f"  Config YAML lines: {result.stats.get('config_yaml_lines', 0)}")
        print(f"  Code files: {result.stats.get('code_files_generated', 0)}")
        print(f"  Total code lines: {result.stats.get('total_code_lines', 0)}")

        if result.generated_files:
            print(f"\n  Generated files:")
            for path in result.generated_files:
                lines = len(result.generated_files[path].splitlines())
                print(f"    {path} ({lines} lines)")

        if args.write and not args.dry_run:
            print(f"\n  Files written to: {args.output_dir}")
        elif not args.write:
            print(f"\n  Use --write to save files to disk")

        if not args.dry_run and not args.write:
            # Show preview of config YAML
            preview = result.config_yaml[:1500]
            print(f"\n--- Config YAML Preview ---")
            print(preview)
            if len(result.config_yaml) > 1500:
                print(f"... ({len(result.config_yaml)} chars total)")

    return 0 if result.success else 1


def cmd_list_industries() -> int:
    """List available industry profiles."""
    from .signal_library import SignalLibrary
    lib = SignalLibrary()

    print("Available Industry Profiles:")
    print()
    for name, profile in lib.INDUSTRY_PROFILES.items():
        print(f"  {name}")
        print(f"    Primary groups: {', '.join(profile.primary_groups)}")
        print(f"    Secondary groups: {', '.join(profile.secondary_groups)}")
        print(f"    Risk focus: {', '.join(profile.risk_focus)}")
        print()

    return 0


def cmd_list_signals() -> int:
    """List available signal groups."""
    from .signal_library import SignalLibrary
    lib = SignalLibrary()

    print("Available Signal Groups:")
    print()
    for gid, group in lib.SIGNAL_GROUPS.items():
        print(f"  {gid} ({group.name})")
        print(f"    Weight: {group.default_weight}")
        print(f"    Signals: {', '.join(group.signals)}")
        print(f"    Industries: {', '.join(group.applicable_industries)}")
        print()

    return 0


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "build":
        return asyncio.run(cmd_build(args))
    elif args.command == "expand":
        return cmd_expand(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "list-industries":
        return cmd_list_industries()
    elif args.command == "list-signals":
        return cmd_list_signals()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Golden-entity fixture generator (V6/E5).

Populates ``tests/fixtures/golden_entities/{coverage}/{entity_id}.yaml`` by
running the full assessment pipeline against a list of real public entities
and snapshotting the outputs.

Usage:
    python tests/fixtures/golden_entities/_generator.py --coverage cyber
    python tests/fixtures/golden_entities/_generator.py --all
    python tests/fixtures/golden_entities/_generator.py --all --refresh

The source of truth for which entities belong to which coverage is
``tests/fixtures/golden_entities/_manifest.yaml``. Adding new entries to the
manifest and re-running the generator creates new fixtures. Passing
``--refresh`` re-snapshots existing fixtures (use when an intentional
pricing change landed and the goldens legitimately need to move — requires
a signed-off PR per the V6 plan).
"""
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.fixtures.golden_entities._schema import (  # noqa: E402
    FIXTURE_ROOT,
    GoldenEntity,
    GoldenExpectation,
    GoldenTolerance,
    dump,
)

MANIFEST_PATH = FIXTURE_ROOT / "_manifest.yaml"


def _silence_logging() -> None:
    warnings.filterwarnings("ignore")
    logging.getLogger().setLevel(logging.ERROR)
    for name in list(logging.Logger.manager.loggerDict):
        logging.getLogger(name).setLevel(logging.ERROR)


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, List[Dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"manifest not found at {path}")
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("coverages", {})


def _assess(entity: Dict[str, Any]):
    """Run the assessment pipeline against a manifest entity."""
    from infrastructure.models.compiler import get_config
    from layers.risk.workflow import get_workflow_engine

    config = None
    if entity.get("config_id"):
        config = get_config(entity["coverage"], entity["config_id"])

    engine = get_workflow_engine()
    return engine.run_workflow(
        entity_id=entity["entity_id"],
        coverage=entity["coverage"],
        entity_name=entity["name"],
        submission_data=dict(entity.get("minimum_viable_input", {})),
        config=config,
        skip_discovery=True,
        skip_input_validation=True,
    )


def build_fixture(entity: Dict[str, Any]) -> GoldenEntity:
    result = _assess(entity)
    decision = result.decision
    decision_value = decision.value if hasattr(decision, "value") else str(decision)
    return GoldenEntity(
        entity_id=entity["entity_id"],
        name=entity["name"],
        coverage=entity["coverage"],
        config_id=entity.get("config_id"),
        domain=entity.get("domain"),
        registry_id=entity.get("registry_id"),
        minimum_viable_input=dict(entity.get("minimum_viable_input", {})),
        expected=GoldenExpectation(
            composite_score=round(float(result.composite_score), 3),
            tier=int(result.tier),
            decision=decision_value,
            recommended_premium=round(float(result.recommended_premium), 2),
        ),
        tolerance=GoldenTolerance(
            score_points=float(entity.get("score_tolerance", 50.0)),
            premium_bps=float(entity.get("premium_tolerance_bps", 1000.0)),
            tier_spread=int(entity.get("tier_spread", 0)),
        ),
        notes=entity.get("notes"),
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="golden-entity-generator")
    parser.add_argument("--coverage", help="Limit to a single coverage")
    parser.add_argument("--all", action="store_true", help="Process every coverage in the manifest")
    parser.add_argument("--refresh", action="store_true",
                        help="Overwrite fixtures that already exist")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH), help="Manifest YAML path")
    parser.add_argument("--output-root", default=str(FIXTURE_ROOT),
                        help="Root directory for written fixtures")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-entity output")
    args = parser.parse_args(argv)

    if not args.all and not args.coverage:
        print("error: specify --all or --coverage NAME", file=sys.stderr)
        return 2

    _silence_logging()
    coverages = load_manifest(Path(args.manifest))
    if args.coverage:
        coverages = {args.coverage: coverages.get(args.coverage, [])}
        if not coverages[args.coverage]:
            print(f"error: no entities in manifest for coverage '{args.coverage}'", file=sys.stderr)
            return 2

    out_root = Path(args.output_root)
    written = 0
    skipped = 0
    for coverage, entities in coverages.items():
        for raw in entities:
            entity = {**raw, "coverage": coverage}
            out_path = out_root / coverage / f"{entity['entity_id']}.yaml"
            if out_path.exists() and not args.refresh:
                skipped += 1
                if not args.quiet:
                    print(f"SKIP  {out_path.relative_to(REPO_ROOT)} (exists — pass --refresh to overwrite)")
                continue
            fixture = build_fixture(entity)
            dump(fixture, out_path)
            written += 1
            if not args.quiet:
                print(
                    f"WROTE {out_path.relative_to(REPO_ROOT)}  "
                    f"score={fixture.expected.composite_score} "
                    f"tier={fixture.expected.tier} "
                    f"decision={fixture.expected.decision} "
                    f"premium=${fixture.expected.recommended_premium:,.0f}"
                )

    print(f"\n{written} fixture(s) written, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

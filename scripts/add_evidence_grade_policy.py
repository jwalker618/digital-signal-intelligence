"""V7 Phase 4 — inject the default evidence_grade_policy block into every
coverage config. Idempotent: re-running on an already-injected config is a
no-op (block presence detected by top-level key under each config_id).

Operates on coverages/*/config.yaml (NOT overlays — they're patch documents
that inherit policy from the base config).

Usage:
    python scripts/add_evidence_grade_policy.py            # all configs
    python scripts/add_evidence_grade_policy.py --check    # dry-run; exit 1 if any config_id needs the block

Layout:
    Each base config is shaped
        coverage_id:
          config_id_a: {body_a}
          config_id_b: {body_b}
    The block is injected at the {body_*} level alongside metadata/
    direct_queries/etc.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

COVERAGES_DIR = Path("coverages")
DEFAULT_POLICY_YAML = """\
evidence_grade_policy:
  enabled: true
  expected_grades:
    grades: {}
  composite_referral:
    enabled: true
    rules:
      - condition: distribution_share_below_grade
        floor: observed
        share: 0.5
        note: "Only {actual_share:.0%} of weight is at OBSERVED or above (target 50%)"
"""


def _build_default_policy(yaml_obj: YAML) -> object:
    """Parse the default policy YAML and return the policy mapping."""
    parsed = yaml_obj.load(DEFAULT_POLICY_YAML)
    return parsed["evidence_grade_policy"]


def _process_config_file(path: Path, *, check: bool) -> tuple[int, int]:
    """Inject policy into every config_id under every coverage in this file.

    Returns (configs_total, configs_needing_injection).
    """
    yaml_obj = YAML()
    yaml_obj.preserve_quotes = True
    yaml_obj.indent(mapping=2, sequence=4, offset=2)
    yaml_obj.width = 200  # keep notes on one line

    data = yaml_obj.load(path)
    if not isinstance(data, dict):
        return (0, 0)

    total = 0
    needs = 0
    modified = False
    for coverage_id, configs in data.items():
        if not isinstance(configs, dict):
            continue
        for config_id, body in configs.items():
            if not isinstance(body, dict):
                continue
            total += 1
            if "evidence_grade_policy" in body:
                continue
            needs += 1
            if check:
                continue
            body["evidence_grade_policy"] = _build_default_policy(yaml_obj)
            modified = True

    if modified and not check:
        with path.open("w", encoding="utf-8") as f:
            yaml_obj.dump(data, f)

    return (total, needs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="dry-run; exit 1 if any config needs the block")
    args = parser.parse_args()

    target_files = sorted(
        p for p in COVERAGES_DIR.rglob("*.yaml")
        if p.name != "master_config_layout.yaml"
        and "overlays" not in p.parts
    )
    if not target_files:
        print("no config files found")
        return 1

    total = 0
    missing = 0
    touched_files: list[Path] = []
    for p in target_files:
        n_total, n_missing = _process_config_file(p, check=args.check)
        total += n_total
        missing += n_missing
        if n_missing:
            touched_files.append(p)

    if args.check:
        if missing:
            print(f"{missing}/{total} config(s) missing evidence_grade_policy")
            for p in touched_files:
                print(f"  {p}")
            return 1
        print(f"all {total} config(s) carry evidence_grade_policy")
        return 0

    print(f"injected evidence_grade_policy into {missing}/{total} config(s)")
    for p in touched_files:
        print(f"  modified {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

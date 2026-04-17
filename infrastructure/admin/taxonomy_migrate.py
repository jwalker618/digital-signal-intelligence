"""V6/E9 — one-shot taxonomy migration script.

Walks every `coverages/*/config.yaml`, builds a mapping of
non-canonical `three_layer_assessment.id` values to canonical ones,
and writes the required in-place edits back to each config.

The mapping is tenant-safe (no weights, guardrails, or signal IDs
change — only the category membership `id` is rewritten). Signals
that cannot be mapped are emitted as a referral list for human
reclassification.

Usage::

    python infrastructure/admin/taxonomy_migrate.py --dry-run
    python infrastructure/admin/taxonomy_migrate.py --write

Default mapping is deliberately conservative: anything touching
operational metrics → technical_infrastructure; anything regulatory
or litigation-facing → public_record; anything board / corporate-
governance → corporate_footprint; anything derived-over-time →
behavioural. Unmapped IDs end up in the referral list.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from signal_architecture.signals.taxonomy import CANONICAL_IDS  # noqa: E402


DEFAULT_MAPPING: Dict[str, str] = {
    # Operational / technical
    "operational_quality": "technical_infrastructure",
    "operational_risk": "technical_infrastructure",
    "operational_telemetry": "technical_infrastructure",
    "cyber_security": "technical_infrastructure",
    "ot_ics_security": "technical_infrastructure",
    "security_posture": "technical_infrastructure",
    "technical_security": "technical_infrastructure",
    "health_data_security": "technical_infrastructure",
    "professional_data_security": "technical_infrastructure",
    "platform_user_security": "technical_infrastructure",
    "retail_operations_security": "technical_infrastructure",
    "manufacturing_operations_security": "technical_infrastructure",
    "product_supply_chain_security": "technical_infrastructure",
    "public_sector_cyber_posture": "technical_infrastructure",
    "financial_system_security": "technical_infrastructure",
    "fleet_profile": "technical_infrastructure",
    "fleet_age_band": "technical_infrastructure",
    "fleet_quality": "technical_infrastructure",
    "fleet_category": "technical_infrastructure",
    "fleet_size": "technical_infrastructure",
    "unmanned_systems": "technical_infrastructure",
    "cargo_quality": "technical_infrastructure",
    "valuation_quality": "technical_infrastructure",
    "delivery_quality": "technical_infrastructure",
    "fire_protection": "technical_infrastructure",
    "construction_quality": "technical_infrastructure",
    "engineering_quality": "technical_infrastructure",
    "design_quality": "technical_infrastructure",
    "advisory_quality": "technical_infrastructure",
    "audit_quality": "technical_infrastructure",
    "practice_quality": "technical_infrastructure",
    "environmental_assessment_quality": "technical_infrastructure",
    # Regulatory / public record
    "regulatory_compliance": "public_record",
    "regulatory_framework": "public_record",
    "regulatory_standing": "public_record",
    "sanctions_compliance": "public_record",
    "litigation": "public_record",
    "litigation_history": "public_record",
    "safety_compliance": "public_record",
    "safety_record": "public_record",
    "safety_performance": "public_record",
    "workplace_safety": "public_record",
    "environmental_compliance": "public_record",
    "environmental": "public_record",
    "environmental_liability": "public_record",
    "port_state_compliance": "public_record",
    "flag_state_quality": "public_record",
    "iosa_status": "public_record",
    "public_company_governance": "public_record",
    "case_portfolio": "public_record",
    # Corporate footprint / governance
    "corporate_governance": "corporate_footprint",
    "governance": "corporate_footprint",
    "executive": "corporate_footprint",
    "partner_practice_mix": "corporate_footprint",
    "asset_portfolio": "corporate_footprint",
    # Behavioural / derived
    "trading_pattern": "behavioural",
    "firm_stability": "behavioural",
    "financial_condition": "behavioural",
    "financial_stability": "behavioural",
    "financial": "structured_data",
    # Exposure / surface area
    "business_interruption": "structured_data",
    "cat_exposure": "structured_data",
    "umbrella_exposure": "structured_data",
    "occupancy_risk": "structured_data",
    "gl_class_risk": "structured_data",
    "auto_fleet_risk": "structured_data",
    "premises_operations": "structured_data",
    "transaction_event_risk": "structured_data",
    "fintech_risk": "structured_data",
    "banking_risk": "structured_data",
    "trade_credit_risk": "structured_data",
    "surety_risk": "structured_data",
    "political_risk": "public_record",
    "kidnap_ransom_risk": "public_record",
    "tanker_risk": "technical_infrastructure",
    "offshore_marine": "technical_infrastructure",
    "deepwater_operations": "technical_infrastructure",
    "space_risk": "technical_infrastructure",
    "mro_risk": "technical_infrastructure",
    "rotary_wing_risk": "technical_infrastructure",
    "route_risk": "technical_infrastructure",
    # Already canonical — no-ops
    "corporate_footprint": "corporate_footprint",
    "technical_infrastructure": "technical_infrastructure",
    "network_authority": "network_authority",
    "public_record": "public_record",
    "structured_data": "structured_data",
    "behavioural": "behavioural",
    "direct_inquiry": "direct_inquiry",
    "footprint": "corporate_footprint",
}


def _apply(path: Path, mapping: Dict[str, str]) -> Tuple[int, List[str]]:
    """Return (count_changes, unmapped_ids) after mutating the file in memory."""
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        return 0, []
    changes = 0
    unmapped: List[str] = []
    for cov_key, sub_configs in data.items():
        if not isinstance(sub_configs, dict):
            continue
        for sub_key, cfg in sub_configs.items():
            if not isinstance(cfg, dict):
                continue
            tla = (cfg.get("groups") or {}).get("three_layer_assessment")
            if not isinstance(tla, list):
                continue
            for entry in tla:
                if not isinstance(entry, dict):
                    continue
                cur = entry.get("id")
                if not cur or cur in CANONICAL_IDS:
                    continue
                new = mapping.get(cur)
                if new is None:
                    unmapped.append(f"{cov_key}/{sub_key}: '{cur}'")
                    continue
                entry["id"] = new
                changes += 1
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=120))
    return changes, unmapped


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="taxonomy_migrate")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--write", action="store_true")
    p.add_argument("--coverages-root", default=str(REPO_ROOT / "coverages"))
    args = p.parse_args(argv)

    if not args.dry_run and not args.write:
        print("error: pass --dry-run or --write", file=sys.stderr)
        return 2

    root = Path(args.coverages_root)
    total = 0
    all_unmapped: List[str] = []
    for cfg_path in sorted(root.glob("*/config.yaml")):
        changes, unmapped = (0, [])
        original = cfg_path.read_text()
        if args.write:
            changes, unmapped = _apply(cfg_path, DEFAULT_MAPPING)
        else:
            # dry-run: copy in memory, restore
            tmp = cfg_path.with_suffix(".yaml.tmp")
            tmp.write_text(original)
            changes, unmapped = _apply(tmp, DEFAULT_MAPPING)
            tmp.unlink(missing_ok=True)
        total += changes
        all_unmapped.extend(unmapped)
        print(f"{'CHG' if changes else '--- '} {cfg_path.relative_to(REPO_ROOT)} "
              f"changes={changes} unmapped={len(unmapped)}")

    print(f"\nTotal category renames: {total}")
    if all_unmapped:
        print("\nUNMAPPED (referral required):")
        for u in all_unmapped:
            print(f"  - {u}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
DSI Example Utilities (Phase 14)

Shared utilities for example scripts.
"""

from typing import Optional
from layers.risk.types import WorkflowResult


def print_header(title: str) -> None:
    """Print section header."""
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_result_summary(result: WorkflowResult) -> None:
    """Print workflow result summary."""
    print_header("DSI ASSESSMENT SUMMARY")

    if result.model_version:
        print(f"Entity: {result.model_version.entity_id}")
        print(f"Coverage: {result.model_version.coverage}")
        print(f"Configuration: {result.model_version.configuration}")

    print()
    print("Discovery:")
    if result.discovered_domain:
        print(f"  Domain: {result.discovered_domain}")
        print(f"  Confidence: {result.discovery_confidence}")
        if result.discovery_warnings:
            print(f"  Warnings: {result.discovery_warnings}")
    else:
        print("  (skipped)")

    print()
    print("Scoring:")
    print(f"  Composite Score: {result.composite_score:.0f}/1000")
    print(f"  Tier: {result.tier} ({result.tier_label})")
    print(f"  Confidence: {result.confidence:.1%}")

    print()
    print("Decision:")
    print(f"  Decision: {result.decision.value.upper()}")
    print(f"  Auto-Approve: {result.auto_approve}")
    if result.referral_reasons:
        print(f"  Referral Reasons:")
        for reason in result.referral_reasons:
            print(f"    - {reason}")

    print()
    print("Premium:")
    print(f"  Recommended: ${result.recommended_premium:,.0f}")
    if result.premium_options:
        print("  Options by Limit:")
        for limit, premium in sorted(result.premium_options.items(), key=lambda x: float(x[0])):
            print(f"    ${float(limit):,.0f}: ${premium:,.0f}")


def print_signal_breakdown(result: WorkflowResult) -> None:
    """Print signal breakdown."""
    print_header("SIGNAL BREAKDOWN")

    if not result.model_version or not result.model_version.signal_outputs:
        print("No signal outputs available")
        return

    # Group by signal group
    groups: dict = {}
    for output in result.model_version.signal_outputs:
        if output.group_id not in groups:
            groups[output.group_id] = []
        groups[output.group_id].append(output)

    for group_id, outputs in groups.items():
        group_score = result.model_version.group_scores.get(group_id, 0)
        print(f"\n{group_id.upper()} (Group Score: {group_score:.1f})")
        print("-" * 40)

        for output in outputs:
            print(f"  {output.signal_name}:")
            print(f"    Raw Score: {output.raw_score:.1f}")
            print(f"    Weight: {output.weight:.3f}")
            print(f"    Weighted: {output.weighted_score:.1f}")
            print(f"    Confidence: {output.confidence:.1%}")
            if output.conditions_triggered:
                print(f"    Conditions: {output.conditions_triggered}")


def print_pricing_breakdown(result: WorkflowResult) -> None:
    """Print pricing breakdown."""
    print_header("PRICING BREAKDOWN")

    if not result.model_version:
        print("No model version available")
        return

    mv = result.model_version

    print(f"Score-Based Tier: {mv.score_based_tier}")
    print(f"Final Tier: {mv.final_tier} ({mv.tier_label})")

    if mv.tier_overrides:
        print(f"Tier Overrides: {mv.tier_overrides}")

    print()
    print(f"Base Premium: ${mv.base_premium:,.0f}")
    print(f"Method: {mv.base_premium_method}")

    if mv.modifiers_applied:
        print("\nModifiers Applied:")
        for mod in mv.modifiers_applied:
            print(f"  {mod.name}:")
            print(f"    Factor: {mod.factor:.3f}")
            print(f"    Before: ${mod.premium_before:,.0f}")
            print(f"    After: ${mod.premium_after:,.0f}")

    print(f"\nPremium After Modifiers: ${mv.premium_after_modifiers:,.0f}")
    print(f"Final Premium: ${mv.final_premium:,.0f}")


def print_audit_trail(result: WorkflowResult) -> None:
    """Print audit trail."""
    print_header("AUDIT TRAIL")

    if not result.model_version:
        print("No model version available")
        return

    mv = result.model_version

    print(f"Version ID: {mv.version_id}")
    print(f"Model ID: {mv.model_id}")
    print(f"Version Number: {mv.version_number}")
    print(f"Version Type: {mv.version_type}")
    print(f"Created At: {mv.created_at}")
    print(f"Created By: {mv.created_by}")

    print("\nConfig Reference:")
    print(f"  Hash: {mv.config_hash[:16]}...")
    print(f"  Coverage: {mv.coverage}")
    print(f"  Configuration: {mv.configuration}")

    if mv.notes:
        print("\nNotes:")
        for note in mv.notes:
            print(f"  - {note}")

    print("\nConditions Triggered:")
    if mv.signal_conditions:
        print("  Signal Conditions:")
        for cond in mv.signal_conditions:
            print(f"    - {cond.source_name}: {cond.note}")

    if mv.query_conditions:
        print("  Query Conditions:")
        for cond in mv.query_conditions:
            print(f"    - {cond.source_name}: {cond.note}")

    if not mv.signal_conditions and not mv.query_conditions:
        print("  (none)")


def print_full_report(result: WorkflowResult) -> None:
    """Print complete assessment report."""
    print_result_summary(result)
    print()
    print_signal_breakdown(result)
    print()
    print_pricing_breakdown(result)
    print()
    print_audit_trail(result)

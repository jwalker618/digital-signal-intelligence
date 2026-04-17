"""
DSI V6 Config Compliance Assessor
=================================

Enforces structural compliance checks on every coverage `config.yaml`
before it is allowed into production. Invoked by the V6 Config Health
Gate CI job — PRs that fail any compliance check are blocked from merge.

Checks performed (per config.yaml under ``coverages/``):

1. YAML parses without error.
2. v2.0 structural validation via ``infrastructure.builder.validator.ConfigValidator``
   (nested ``coverage_id -> config_name -> {sections}`` layout, required
   sections, score_conditions action constraints, weight sums, band coverage).
3. Required top-level pricing blocks present (``pricing``, ``limit_configuration``,
   ``guardrails``) on every sub-config.
4. Every sub-config has a ``three_layer_assessment`` group with at least one
   member.
5. (Soft) canonical-category audit. E9 will harden this to a hard failure
   once the taxonomy unification migration lands.

Exit codes
----------
0 — every config is compliant (no errors)
1 — one or more configs produced validation errors
2 — usage / runtime error

Baseline
--------
Pre-V6 coverages carry known debt (PI has sub-configs missing ``guardrails`` —
addressed by A8). To let the gate start enforcing today without blocking on
pre-existing issues, a baseline JSON file records known-permitted findings.
Each finding is keyed by ``(file, scope, category, message)``.

The gate fails only when a *new* finding appears that is not in the baseline.
Use ``--update-baseline`` to refresh the baseline after an intentional change.

Usage
-----
    python development/project/assessments/scripts/assess_config_compliance.py
    python development/project/assessments/scripts/assess_config_compliance.py \
        --report compliance-report.json --json
    python development/project/assessments/scripts/assess_config_compliance.py \
        --update-baseline

Flags
-----
--coverages-root DIR   Root containing ``*/config.yaml`` (default: ``coverages``)
--report PATH          Write a JSON report to PATH
--json                 Emit summary as JSON to stdout instead of text
--strict               Treat warnings as errors (default: errors only)
--config PATH          Check a single config file instead of walking the tree
--baseline PATH        Use this baseline file (default: V6 default location)
--no-baseline          Ignore any baseline file (flag every finding)
--update-baseline      Write the current findings to the baseline file
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repo root is on sys.path when run as a bare script from CI.
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from infrastructure.builder.validator import ConfigValidator  # noqa: E402


# Canonical 7 categories enforced by E9. Sourced from the central taxonomy
# module so there is a single source of truth.
try:
    from signal_architecture.signals.taxonomy import CANONICAL_IDS as CANONICAL_CATEGORIES
except ImportError:  # fallback so the script runs pre-taxonomy-import
    CANONICAL_CATEGORIES = {
        "network_authority",
        "technical_infrastructure",
        "corporate_footprint",
        "behavioural",
        "public_record",
        "structured_data",
        "direct_inquiry",
    }

REQUIRED_TOP_SECTIONS = (
    "metadata",
    "signal_registry",
    "groups",
    "risk_tier_bands",
    "loss_tier_bands",
    "exposure",
    "pricing",
    "limit_configuration",
    "guardrails",
)

DEFAULT_BASELINE_PATH = (
    REPO_ROOT
    / "development"
    / "project"
    / "version"
    / "6"
    / "config_compliance_baseline.json"
)


@dataclass
class Finding:
    severity: str            # "error" | "warning"
    category: str            # "structure" | "canonical_category" | "schema" | ...
    path: str                # file path
    message: str
    scope: Optional[str] = None   # e.g. "cyber/cyber_general"
    baselined: bool = False       # true if this finding is in the baseline

    def key(self) -> str:
        """Stable identity used for baseline matching."""
        return f"{self.path}||{self.scope or ''}||{self.category}||{self.message}"


@dataclass
class ConfigReport:
    file: str
    coverage_id: str
    sub_configs: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def unbaselined_error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error" and not f.baselined)

    @property
    def unbaselined_warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning" and not f.baselined)

    @property
    def passed(self) -> bool:
        return self.unbaselined_error_count == 0


@dataclass
class Report:
    configs: List[ConfigReport] = field(default_factory=list)

    @property
    def total_error_count(self) -> int:
        return sum(c.error_count for c in self.configs)

    @property
    def total_warning_count(self) -> int:
        return sum(c.warning_count for c in self.configs)

    @property
    def total_unbaselined_errors(self) -> int:
        return sum(c.unbaselined_error_count for c in self.configs)

    @property
    def total_unbaselined_warnings(self) -> int:
        return sum(c.unbaselined_warning_count for c in self.configs)

    @property
    def passed(self) -> bool:
        return self.total_unbaselined_errors == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total_configs": len(self.configs),
            "failed_configs": sum(1 for c in self.configs if not c.passed),
            "total_errors": self.total_error_count,
            "total_warnings": self.total_warning_count,
            "unbaselined_errors": self.total_unbaselined_errors,
            "unbaselined_warnings": self.total_unbaselined_warnings,
            "configs": [
                {
                    "file": c.file,
                    "coverage_id": c.coverage_id,
                    "sub_configs": c.sub_configs,
                    "passed": c.passed,
                    "error_count": c.error_count,
                    "warning_count": c.warning_count,
                    "unbaselined_error_count": c.unbaselined_error_count,
                    "findings": [asdict(f) for f in c.findings],
                }
                for c in self.configs
            ],
        }


def _inner_config(raw: Any) -> Optional[Dict[str, Dict[str, Any]]]:
    """Return the v2.0 ``coverage_id -> {sub_config_id: {...}}`` mapping."""
    if not isinstance(raw, dict) or len(raw) != 1:
        return None
    sub = next(iter(raw.values()))
    if not isinstance(sub, dict):
        return None
    return sub


def _assess_sub_config(
    sub_id: str,
    sub: Dict[str, Any],
    scope: str,
    path: str,
) -> List[Finding]:
    findings: List[Finding] = []

    # Required top-level sections
    for section in REQUIRED_TOP_SECTIONS:
        if section not in sub:
            findings.append(Finding(
                severity="error",
                category="structure",
                path=path,
                scope=scope,
                message=f"missing required section '{section}'",
            ))

    # three_layer_assessment presence
    groups = sub.get("groups")
    if isinstance(groups, dict):
        tla = groups.get("three_layer_assessment")
        if not isinstance(tla, list) or not tla:
            findings.append(Finding(
                severity="error",
                category="structure",
                path=path,
                scope=scope,
                message="'groups.three_layer_assessment' is missing or empty",
            ))
        else:
            for entry in tla:
                if not isinstance(entry, dict):
                    continue
                cat_id = entry.get("id")
                if not cat_id:
                    findings.append(Finding(
                        severity="error",
                        category="structure",
                        path=path,
                        scope=scope,
                        message="three_layer_assessment entry missing 'id'",
                    ))
                    continue
                if cat_id not in CANONICAL_CATEGORIES:
                    findings.append(Finding(
                        severity="warning",
                        category="canonical_category",
                        path=path,
                        scope=scope,
                        message=(
                            f"three_layer_assessment id '{cat_id}' is not in the "
                            "canonical V6 category list "
                            f"({sorted(CANONICAL_CATEGORIES)}); E9 will harden this "
                            "check to an error."
                        ),
                    ))

    return findings


def _normalise_path(path: Path) -> str:
    """Return a path relative to the repo root if possible, else posix-absolute."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def assess_file(path: Path) -> ConfigReport:
    file_str = _normalise_path(path)
    rep = ConfigReport(file=file_str, coverage_id=path.parent.name)

    try:
        raw = yaml.safe_load(path.read_text())
    except Exception as e:
        rep.findings.append(Finding(
            severity="error",
            category="syntax",
            path=file_str,
            message=f"failed to parse YAML: {e}",
        ))
        return rep

    inner = _inner_config(raw)
    if inner is None:
        rep.findings.append(Finding(
            severity="error",
            category="structure",
            path=file_str,
            message=(
                "expected v2.0 layout 'coverage_id -> sub_config -> {sections}'"
            ),
        ))
        return rep

    rep.sub_configs = sorted(inner.keys())

    # Run the shared structural validator (covers weight sums, band coverage, etc.)
    validator = ConfigValidator()
    vr = validator.validate_yaml(path.read_text())
    for issue in vr.issues:
        severity = issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity)
        sev = "error" if severity.lower() == "error" else "warning"
        rep.findings.append(Finding(
            severity=sev,
            category=f"schema.{issue.category}",
            path=file_str,
            message=issue.message,
            scope=issue.path or rep.coverage_id,
        ))

    # Per-sub-config V6 checks
    for sub_id, sub in inner.items():
        if not isinstance(sub, dict):
            rep.findings.append(Finding(
                severity="error",
                category="structure",
                path=file_str,
                scope=f"{rep.coverage_id}/{sub_id}",
                message="sub-config must be a mapping",
            ))
            continue
        rep.findings.extend(
            _assess_sub_config(sub_id, sub, f"{rep.coverage_id}/{sub_id}", file_str)
        )

    return rep


def discover_configs(root: Path) -> List[Path]:
    return sorted(root.glob("*/config.yaml"))


def format_text(report: Report, strict: bool) -> str:
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("V6 CONFIG COMPLIANCE GATE")
    lines.append("=" * 70)
    lines.append("")
    lines.append(
        f"Configs checked: {len(report.configs)}  "
        f"|  Errors: {report.total_error_count} "
        f"(new: {report.total_unbaselined_errors})  "
        f"|  Warnings: {report.total_warning_count} "
        f"(new: {report.total_unbaselined_warnings})"
    )
    lines.append("")
    lines.append(
        f"{'Coverage':<18s} {'Sub-cfgs':>8s} {'Err(new)':>10s} {'Warn(new)':>11s}  Status"
    )
    lines.append("-" * 70)
    for c in report.configs:
        status = "PASS" if c.passed and (not strict or c.unbaselined_warning_count == 0) else "FAIL"
        lines.append(
            f"{c.coverage_id:<18s} {len(c.sub_configs):>8d} "
            f"{c.error_count:>4d}({c.unbaselined_error_count:>3d}) "
            f"{c.warning_count:>5d}({c.unbaselined_warning_count:>3d})  {status}"
        )

    new_findings = [
        (c, f)
        for c in report.configs
        for f in c.findings
        if not f.baselined
    ]
    if new_findings:
        lines.append("")
        lines.append("NEW FINDINGS (not in baseline):")
        current_file = None
        for c, f in new_findings:
            if c.file != current_file:
                current_file = c.file
                lines.append("")
                lines.append(f"  {c.file}")
            scope = f" [{f.scope}]" if f.scope else ""
            lines.append(f"    [{f.severity.upper():<7s}] {f.category}{scope}: {f.message}")
    else:
        lines.append("")
        lines.append("No new findings vs baseline.")

    lines.append("")
    verdict = (
        "PASS"
        if report.passed and (not strict or report.total_unbaselined_warnings == 0)
        else "FAIL"
    )
    lines.append(f"Gate verdict: {verdict}")
    return "\n".join(lines)


def load_baseline(path: Path) -> set:
    """Load a baseline file and return a set of finding keys."""
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"warning: baseline {path} is not valid JSON ({e}); ignoring", file=sys.stderr)
        return set()
    keys = set()
    for entry in data.get("findings", []):
        keys.add(
            "{}||{}||{}||{}".format(
                entry.get("path", ""),
                entry.get("scope") or "",
                entry.get("category", ""),
                entry.get("message", ""),
            )
        )
    return keys


def write_baseline(path: Path, report: Report) -> None:
    """Write every current finding to the baseline (used by --update-baseline)."""
    findings = []
    for c in report.configs:
        for f in c.findings:
            findings.append({
                "path": f.path,
                "scope": f.scope,
                "category": f.category,
                "severity": f.severity,
                "message": f.message,
            })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "_comment": (
            "V6 config-compliance baseline. Pre-V6 known debt lives here so the "
            "health gate can start enforcing without blocking on pre-existing "
            "issues. Entries are cleared as maturation phases (A1-A8) land."
        ),
        "findings": findings,
    }, indent=2) + "\n")


def apply_baseline(report: Report, baseline_keys: set) -> None:
    """Mark every finding whose key is in ``baseline_keys`` as baselined."""
    for c in report.configs:
        for f in c.findings:
            if f.key() in baseline_keys:
                f.baselined = True


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="assess_config_compliance",
        description="V6 Config Compliance Gate — validates every coverage config.yaml.",
    )
    parser.add_argument("--coverages-root", default="coverages",
                        help="Directory containing '<coverage>/config.yaml' (default: coverages)")
    parser.add_argument("--config", help="Assess a single config file instead of walking the tree")
    parser.add_argument("--report", help="Write a JSON report to this path")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Emit the summary as JSON on stdout (default: human-readable)")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as failures")
    parser.add_argument("--baseline",
                        help=f"Baseline file (default: {DEFAULT_BASELINE_PATH})")
    parser.add_argument("--no-baseline", action="store_true",
                        help="Ignore any baseline file and flag every finding")
    parser.add_argument("--update-baseline", action="store_true",
                        help="Write current findings to the baseline file and exit 0")
    args = parser.parse_args(argv)

    if args.config:
        files = [Path(args.config)]
    else:
        root = Path(args.coverages_root)
        if not root.is_dir():
            print(f"error: coverages root does not exist: {root}", file=sys.stderr)
            return 2
        files = discover_configs(root)
        if not files:
            print(f"error: no coverage configs found under {root}", file=sys.stderr)
            return 2

    report = Report()
    for f in files:
        report.configs.append(assess_file(f))

    baseline_path = Path(args.baseline) if args.baseline else DEFAULT_BASELINE_PATH

    if args.update_baseline:
        write_baseline(baseline_path, report)
        print(f"Baseline written to {baseline_path} "
              f"({report.total_error_count} errors, {report.total_warning_count} warnings)")
        return 0

    if not args.no_baseline:
        baseline_keys = load_baseline(baseline_path)
        apply_baseline(report, baseline_keys)

    if args.report:
        Path(args.report).write_text(json.dumps(report.to_dict(), indent=2))

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_text(report, args.strict))

    if not report.passed:
        return 1
    if args.strict and report.total_unbaselined_warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

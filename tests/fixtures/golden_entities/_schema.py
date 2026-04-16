"""Schema + loader for V6 golden-entity fixtures.

Each fixture lives at ``tests/fixtures/golden_entities/{coverage}/{entity_id}.yaml``
and snapshots the expected output of ``run_assessment`` for a single real
public entity. The regression test in
``tests/integration/test_golden_entities.py`` re-runs the pipeline on every
PR and asserts the output falls within the stored tolerance.

See the README in this directory for authoring rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


FIXTURE_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class GoldenExpectation:
    composite_score: float
    tier: int
    decision: str
    recommended_premium: float


@dataclass(frozen=True)
class GoldenTolerance:
    score_points: float = 50.0       # absolute composite-score delta allowed
    premium_bps: float = 1000.0      # premium delta in basis points (10_000 = 100%)
    tier_spread: int = 0             # how many tiers the actual tier may differ


@dataclass(frozen=True)
class GoldenEntity:
    entity_id: str
    name: str
    coverage: str
    minimum_viable_input: Dict[str, Any]
    expected: GoldenExpectation
    tolerance: GoldenTolerance
    config_id: Optional[str] = None
    domain: Optional[str] = None
    registry_id: Optional[str] = None
    notes: Optional[str] = None
    source_path: Optional[Path] = None


REQUIRED_TOP_KEYS = {
    "entity_id", "name", "coverage",
    "minimum_viable_input", "expected", "tolerance",
}
REQUIRED_EXPECTED_KEYS = {"composite_score", "tier", "decision", "recommended_premium"}


class GoldenEntityError(Exception):
    pass


def _validate(path: Path, raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise GoldenEntityError(f"{path}: fixture root must be a mapping")
    missing = REQUIRED_TOP_KEYS - set(raw)
    if missing:
        raise GoldenEntityError(f"{path}: missing required keys: {sorted(missing)}")
    exp = raw.get("expected") or {}
    if not isinstance(exp, dict):
        raise GoldenEntityError(f"{path}: 'expected' must be a mapping")
    missing_exp = REQUIRED_EXPECTED_KEYS - set(exp)
    if missing_exp:
        raise GoldenEntityError(
            f"{path}: 'expected' missing keys: {sorted(missing_exp)}"
        )
    return raw


def load(path: Path) -> GoldenEntity:
    raw = yaml.safe_load(path.read_text())
    data = _validate(path, raw)
    exp = data["expected"]
    tol = data.get("tolerance") or {}
    return GoldenEntity(
        entity_id=str(data["entity_id"]),
        name=str(data["name"]),
        coverage=str(data["coverage"]),
        config_id=data.get("config_id"),
        domain=data.get("domain"),
        registry_id=data.get("registry_id"),
        notes=data.get("notes"),
        minimum_viable_input=dict(data["minimum_viable_input"]),
        expected=GoldenExpectation(
            composite_score=float(exp["composite_score"]),
            tier=int(exp["tier"]),
            decision=str(exp["decision"]),
            recommended_premium=float(exp["recommended_premium"]),
        ),
        tolerance=GoldenTolerance(
            score_points=float(tol.get("score_points", 50.0)),
            premium_bps=float(tol.get("premium_bps", 1000.0)),
            tier_spread=int(tol.get("tier_spread", 0)),
        ),
        source_path=path,
    )


def discover(root: Path = FIXTURE_ROOT) -> List[GoldenEntity]:
    """Return every ``*.yaml`` fixture under ``root/<coverage>/``."""
    fixtures: List[GoldenEntity] = []
    for path in sorted(root.glob("*/*.yaml")):
        if path.name.startswith("_"):
            continue
        fixtures.append(load(path))
    return fixtures


def dump(entity: GoldenEntity, path: Optional[Path] = None) -> str:
    """Serialize ``entity`` back to YAML (used by the generator)."""
    payload = {
        "entity_id": entity.entity_id,
        "name": entity.name,
        "coverage": entity.coverage,
    }
    if entity.config_id:
        payload["config_id"] = entity.config_id
    if entity.domain:
        payload["domain"] = entity.domain
    if entity.registry_id:
        payload["registry_id"] = entity.registry_id
    payload.update({
        "minimum_viable_input": entity.minimum_viable_input,
        "expected": {
            "composite_score": entity.expected.composite_score,
            "tier": entity.expected.tier,
            "decision": entity.expected.decision,
            "recommended_premium": entity.expected.recommended_premium,
        },
        "tolerance": {
            "score_points": entity.tolerance.score_points,
            "premium_bps": entity.tolerance.premium_bps,
            "tier_spread": entity.tolerance.tier_spread,
        },
    })
    if entity.notes:
        payload["notes"] = entity.notes
    body = yaml.safe_dump(payload, sort_keys=False, width=88)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    return body

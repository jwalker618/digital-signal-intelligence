"""
C-3: ProposalDeployer

Applies an APPROVED RecalibrationProposal via the B-2 ConfigService
pipeline. Steps:

1. Load the approved proposal row.
2. Generate a modified config YAML (apply weight_changes +
   tier_threshold_changes on top of the currently-deployed config).
3. Create a DRAFT via ConfigService.create_draft.
4. Validate via ConfigService.validate.
5. Calibrate via ConfigService.calibrate (must pass).
6. Deploy via ConfigService.deploy.
7. Mark the proposal DEPLOYED + record the config_version_id.

Failure at any stage leaves the proposal APPROVED (not DEPLOYED); the
governance UI can retry after fixing the root cause. The entire chain
from proposal -> config version -> deployment is traceable in the
audit log (caller records an audit event before/after invoking this).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.admin import ConfigService

logger = logging.getLogger("dsi.recalibration.deployer")


@dataclass
class DeploymentResult:
    """Summary of a proposal deployment."""
    proposal_id: str
    config_version_id: str
    coverage: str
    config_name: str
    deployed_at: datetime
    calibration_passed: bool


class DeploymentError(Exception):
    """Raised when a proposal deployment fails. Message is safe to surface to the UI."""


class ProposalDeployer:
    """Deploys approved recalibration proposals via the B-2 pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def deploy(self, proposal_id: str, deployer_id: Optional[str] = None) -> DeploymentResult:
        """Deploy an APPROVED proposal.

        Raises DeploymentError on any failure. The proposal remains APPROVED
        (not mutated) unless the deployment succeeds end-to-end.
        """
        proposal = self._load_proposal(proposal_id)
        if proposal["status"] != "APPROVED":
            raise DeploymentError(
                f"Proposal {proposal_id} is {proposal['status']} -- must be APPROVED"
            )

        coverage = proposal["coverage"]
        config_name = proposal["config_name"]

        # Build the new YAML by applying changes to the currently-deployed config
        current_yaml = self.config_service.get_active_deployment_content(coverage, config_name)
        if not current_yaml:
            raise DeploymentError(
                f"No active config found for {coverage}/{config_name} to apply proposal on top of"
            )

        proposed_yaml = self._apply_proposal_to_yaml(
            current_yaml,
            weight_changes=proposal["weight_changes"],
            tier_threshold_changes=proposal["tier_threshold_changes"],
        )

        # Create draft
        try:
            draft = self.config_service.create_draft(
                coverage=coverage,
                config_name=config_name,
                content=proposed_yaml,
                author_id=deployer_id,
                notes=f"Auto-generated from recalibration proposal {proposal_id}",
            )
        except ValueError as exc:
            raise DeploymentError(f"Failed to create draft: {exc}")

        # Validate
        validation = self.config_service.validate(draft.id)
        if not validation.get("valid"):
            raise DeploymentError(
                f"Validation failed on draft {draft.id}: "
                f"{len(validation.get('issues', []))} issue(s). Review and try again."
            )

        # Calibrate
        calibration = self.config_service.calibrate(draft.id)
        if not calibration.get("success", True):
            raise DeploymentError(
                f"Calibration failed on draft {draft.id}: {calibration.get('error', 'unknown')}"
            )

        # Deploy
        try:
            deploy_result = self.config_service.deploy(draft.id, deployed_by=deployer_id)
        except ValueError as exc:
            raise DeploymentError(f"Deploy failed: {exc}")

        # Mark proposal DEPLOYED + link to config version
        now = datetime.now(timezone.utc)
        self.db.execute(
            text(
                """
                UPDATE recalibration_proposals
                SET status = 'DEPLOYED',
                    deployed_config_version_id = :version_id,
                    deployed_at = :now,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": proposal_id, "version_id": draft.id, "now": now},
        )

        return DeploymentResult(
            proposal_id=proposal_id,
            config_version_id=draft.id,
            coverage=coverage,
            config_name=config_name,
            deployed_at=now,
            calibration_passed=True,
        )

    def simulate(self, proposal_id: str) -> dict:
        """Return the proposed YAML + a quick validation summary, without
        persisting anything. Used by the 'what-if' button in C-3 UI."""
        proposal = self._load_proposal(proposal_id)
        coverage = proposal["coverage"]
        config_name = proposal["config_name"]

        current_yaml = self.config_service.get_active_deployment_content(coverage, config_name)
        if not current_yaml:
            return {
                "proposal_id": proposal_id,
                "error": "No active config to simulate against",
            }

        proposed_yaml = self._apply_proposal_to_yaml(
            current_yaml,
            weight_changes=proposal["weight_changes"],
            tier_threshold_changes=proposal["tier_threshold_changes"],
        )

        return {
            "proposal_id": proposal_id,
            "coverage": coverage,
            "config_name": config_name,
            "current_yaml_length": len(current_yaml),
            "proposed_yaml_length": len(proposed_yaml),
            "proposed_yaml_preview": proposed_yaml[:4000],
            "impact_assessment": proposal["impact_assessment"],
        }

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_proposal(self, proposal_id: str) -> dict:
        row = self.db.execute(
            text(
                """
                SELECT id::text, tenant_id::text, coverage, config_name,
                       status, weight_changes, tier_threshold_changes,
                       impact_assessment, signal_report_cards, statistical_evidence
                FROM recalibration_proposals
                WHERE id = :id
                """
            ),
            {"id": proposal_id},
        ).mappings().first()
        if row is None:
            raise DeploymentError(f"Proposal {proposal_id} not found")
        return dict(row)

    # ------------------------------------------------------------------
    # YAML mutation
    # ------------------------------------------------------------------

    def _apply_proposal_to_yaml(
        self,
        current_yaml: str,
        weight_changes: list[dict],
        tier_threshold_changes: list[dict],
    ) -> str:
        """Apply weight + tier changes to the current YAML and return new YAML.

        Weight changes target signal_registry.{signal_id}. Tier changes
        target risk_tier_bands.bands[{id}].interpretation.bands.{min|max}.

        The YAML structure is preserved; we mutate the parsed dict and
        re-serialise with sort_keys=False so formatting stays close to
        the original.
        """
        parsed = yaml.safe_load(current_yaml) or {}
        cfg = _ensure_path(parsed, ["coverage", "configuration"])

        # Apply weight changes
        registry = cfg.get("signal_registry") or {}
        for change in weight_changes or []:
            sig_id = change.get("signal_id")
            new_weight = change.get("proposed_weight")
            if sig_id is None or new_weight is None:
                continue
            _apply_signal_weight(registry, sig_id, new_weight)
        cfg["signal_registry"] = registry

        # Apply tier threshold changes
        tier_section = cfg.get("risk_tier_bands")
        if tier_section is not None and tier_threshold_changes:
            _apply_tier_changes(tier_section, tier_threshold_changes)

        return yaml.safe_dump(parsed, sort_keys=False, default_flow_style=False)


# =============================================================================
# YAML mutation helpers
# =============================================================================


def _ensure_path(d: dict, path: list[str]) -> dict:
    cur = d
    for key in path:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    return cur


def _apply_signal_weight(registry: Any, signal_id: str, new_weight: float) -> None:
    """Handles both dict-form (signal_registry[signal_id]) and list-form
    registries (list of {id: ..., weight: ...} dicts)."""
    if isinstance(registry, dict) and signal_id in registry:
        entry = registry[signal_id]
        if isinstance(entry, dict):
            _set_weight_in_signal(entry, new_weight)
        return
    if isinstance(registry, list):
        for entry in registry:
            if isinstance(entry, dict) and (entry.get("id") == signal_id or entry.get("signal_id") == signal_id):
                _set_weight_in_signal(entry, new_weight)
                return


def _set_weight_in_signal(entry: dict, new_weight: float) -> None:
    """Prefer flat `weight` field; fall back to three_layer_assessment.risk_weight."""
    if "weight" in entry:
        entry["weight"] = new_weight
        return
    tla = entry.get("three_layer_assessment") or entry.get("three_layer")
    if isinstance(tla, dict):
        if "risk_weight" in tla or "weight" in tla:
            if "risk_weight" in tla:
                tla["risk_weight"] = new_weight
            else:
                tla["weight"] = new_weight
            return
    # No existing weight field -- default to flat `weight`
    entry["weight"] = new_weight


def _apply_tier_changes(tier_section: Any, changes: list[dict]) -> None:
    """Apply tier-boundary shifts to either the bands list or top-level list."""
    bands = tier_section.get("bands") if isinstance(tier_section, dict) else tier_section
    if not isinstance(bands, list):
        return

    for change in changes:
        band_id = change.get("band_id")
        boundary = change.get("boundary")
        new_value = change.get("proposed_value")
        if band_id is None or boundary not in ("min", "max") or new_value is None:
            continue
        for band in bands:
            if not isinstance(band, dict) or band.get("id") != band_id:
                continue
            interp = band.get("interpretation")
            if isinstance(interp, dict) and isinstance(interp.get("bands"), dict):
                interp["bands"][boundary] = new_value

"""
B-2b: ConfigService

Orchestrates the config change lifecycle:

    file + PUT body -> DRAFT -> validate() -> VALIDATED
                              \-> calibrate() -> CALIBRATED
                                               \-> deploy() -> DEPLOYED
                                                             \-> rollback() restores previous DEPLOYED

Non-destructive: changes NEVER modify the on-disk YAML directly. The
deployed version is the authoritative "active" config, stored in DB.
At deploy time we write the YAML to disk so the pricer/scorer (which
reads from files) picks up the new version.

Validation and calibration results are stored on the version row so the
governance UI can display them without re-running.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("dsi.admin.config_service")


# Where YAML configs live on disk. The ConfigService reads from here
# when there is no DRAFT/DEPLOYED row yet, and writes here when a
# version is DEPLOYED.
COVERAGES_DIR = Path(__file__).resolve().parents[2] / "coverages"


@dataclass
class ConfigVersionRow:
    """In-memory representation of a config_versions row."""

    id: str
    coverage: str
    config_name: str
    version_number: int
    content: str
    config_hash: str
    status: str
    validation_report: Optional[dict]
    calibration_report: Optional[dict]
    notes: Optional[str]
    author_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConfigService:
    """Lifecycle service for versioned coverage configs."""

    def __init__(self, db: Session, coverages_dir: Optional[Path] = None):
        self.db = db
        self.coverages_dir = coverages_dir or COVERAGES_DIR

    # ==================================================================
    # Listing / retrieval
    # ==================================================================

    def list_configs(self) -> list[dict]:
        """List every (coverage, config_name) pair with its active version.

        Uses on-disk YAML as the source of truth for the set of configs,
        joins with any DB versions to show status + version_number.
        """
        on_disk = self._discover_on_disk_configs()

        latest_by_key: dict[tuple[str, str], ConfigVersionRow] = {}
        rows = self.db.execute(
            text(
                """
                SELECT DISTINCT ON (coverage, config_name)
                    id, coverage, config_name, version_number, content,
                    config_hash, status, validation_report, calibration_report,
                    notes, author_id::text AS author_id, created_at, updated_at
                FROM config_versions
                ORDER BY coverage, config_name, version_number DESC
                """
            )
        ).mappings().all()
        for row in rows:
            latest_by_key[(row["coverage"], row["config_name"])] = self._row_to_dataclass(row)

        result: list[dict] = []
        seen: set[tuple[str, str]] = set()

        for coverage, config_name, disk_path in on_disk:
            seen.add((coverage, config_name))
            active = latest_by_key.get((coverage, config_name))
            result.append({
                "coverage": coverage,
                "config_name": config_name,
                "status": active.status if active else "DISK_ONLY",
                "version_number": active.version_number if active else 0,
                "updated_at": (active.updated_at if active else None),
                "file_path": str(disk_path),
            })

        # Include DB-only configs (none should exist unless config deleted from disk)
        for (coverage, config_name), active in latest_by_key.items():
            if (coverage, config_name) in seen:
                continue
            result.append({
                "coverage": coverage,
                "config_name": config_name,
                "status": active.status,
                "version_number": active.version_number,
                "updated_at": active.updated_at,
                "file_path": None,
            })

        return sorted(result, key=lambda r: (r["coverage"], r["config_name"]))

    def get_latest_version(
        self, coverage: str, config_name: str
    ) -> Optional[ConfigVersionRow]:
        row = self.db.execute(
            text(
                """
                SELECT id, coverage, config_name, version_number, content,
                       config_hash, status, validation_report, calibration_report,
                       notes, author_id::text AS author_id, created_at, updated_at
                FROM config_versions
                WHERE coverage = :cov AND config_name = :cfg
                ORDER BY version_number DESC
                LIMIT 1
                """
            ),
            {"cov": coverage, "cfg": config_name},
        ).mappings().first()
        return self._row_to_dataclass(row) if row else None

    def get_version(self, version_id: str) -> Optional[ConfigVersionRow]:
        row = self.db.execute(
            text(
                """
                SELECT id, coverage, config_name, version_number, content,
                       config_hash, status, validation_report, calibration_report,
                       notes, author_id::text AS author_id, created_at, updated_at
                FROM config_versions WHERE id = :id
                """
            ),
            {"id": version_id},
        ).mappings().first()
        return self._row_to_dataclass(row) if row else None

    def get_active_deployment_content(
        self, coverage: str, config_name: str
    ) -> str:
        """Return the content of the most recently DEPLOYED version, or fall
        back to the on-disk YAML if no deployment exists yet."""
        row = self.db.execute(
            text(
                """
                SELECT content FROM config_versions
                WHERE coverage = :cov AND config_name = :cfg AND status = 'DEPLOYED'
                ORDER BY version_number DESC LIMIT 1
                """
            ),
            {"cov": coverage, "cfg": config_name},
        ).scalar_one_or_none()
        if row is not None:
            return row

        disk_path = self._disk_path(coverage, config_name)
        if disk_path.exists():
            return disk_path.read_text()
        return ""

    def list_history(
        self, coverage: str, config_name: str, limit: int = 50
    ) -> list[ConfigVersionRow]:
        rows = self.db.execute(
            text(
                """
                SELECT id, coverage, config_name, version_number, content,
                       config_hash, status, validation_report, calibration_report,
                       notes, author_id::text AS author_id, created_at, updated_at
                FROM config_versions
                WHERE coverage = :cov AND config_name = :cfg
                ORDER BY version_number DESC LIMIT :limit
                """
            ),
            {"cov": coverage, "cfg": config_name, "limit": limit},
        ).mappings().all()
        return [self._row_to_dataclass(r) for r in rows]

    # ==================================================================
    # Lifecycle
    # ==================================================================

    def create_draft(
        self,
        coverage: str,
        config_name: str,
        content: str,
        author_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ConfigVersionRow:
        """Create a new DRAFT version with the given YAML content."""
        # Validate YAML syntax up-front (cheap + gives clear error)
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}")

        version_number = self._next_version_number(coverage, config_name)
        config_hash = hashlib.sha256(content.encode()).hexdigest()

        # Generate id in Python rather than relying on the column's server
        # default. The model declares `default=uuid.uuid4` (Python-side), so
        # if the table was created via Base.metadata.create_all instead of
        # the alembic migration (which sets server_default=gen_random_uuid()),
        # an INSERT that omits `id` leaves it NULL and violates NOT NULL.
        new_id = str(uuid.uuid4())

        self.db.execute(
            text(
                """
                INSERT INTO config_versions (
                    id, coverage, config_name, version_number, content, config_hash,
                    status, notes, author_id
                ) VALUES (
                    :id, :coverage, :config_name, :version_number, :content, :hash,
                    'DRAFT', :notes, :author_id
                )
                """
            ),
            {
                "id": new_id,
                "coverage": coverage,
                "config_name": config_name,
                "version_number": version_number,
                "content": content,
                "hash": config_hash,
                "notes": notes,
                "author_id": author_id,
            },
        )
        logger.info(
            "ConfigService: DRAFT created coverage=%s config=%s v%d (hash=%s)",
            coverage, config_name, version_number, config_hash[:12],
        )
        return self.get_version(new_id)

    def validate(self, version_id: str) -> dict:
        """Run ModelConfigValidator against the version's content.

        Writes the content to a temp file, validates, stores the report,
        and (if valid) bumps status DRAFT -> VALIDATED.
        """
        version = self.get_version(version_id)
        if version is None:
            raise ValueError(f"Version {version_id} not found")

        import tempfile
        from infrastructure.validation.config_validator import ModelConfigValidator

        report: dict
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
                f.write(version.content)
                tmp_path = Path(f.name)
            validator = ModelConfigValidator()
            validation_report = validator.validate_file(tmp_path)
            report = {
                "coverage": validation_report.coverage,
                "valid": validation_report.valid,
                "issues": [
                    {
                        "severity": issue.severity,
                        "category": issue.category,
                        "message": issue.message,
                        "location": issue.location,
                    }
                    for issue in validation_report.issues
                ],
            }
        finally:
            try:
                tmp_path.unlink()
            except Exception:
                pass

        new_status = "VALIDATED" if report["valid"] else version.status
        self.db.execute(
            text(
                """
                UPDATE config_versions
                SET validation_report = CAST(:report AS jsonb),
                    status = :status,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "report": json.dumps(report, default=str),
                "status": new_status,
                "now": datetime.now(timezone.utc),
                "id": version_id,
            },
        )

        logger.info(
            "ConfigService: validated %s -> valid=%s issues=%d",
            version_id, report["valid"], len(report["issues"]),
        )
        return report

    def calibrate(self, version_id: str) -> dict:
        """Run the calibration harness against this version's content.

        The harness expects configs on disk, so we write to a temporary
        coverages directory and run it against that.
        """
        version = self.get_version(version_id)
        if version is None:
            raise ValueError(f"Version {version_id} not found")

        # Use the existing calibration harness -- requires on-disk YAML.
        # We write to a real temporary tree so the compiler can resolve
        # references to master_config_layout etc.
        import shutil
        import tempfile
        from layers.risk.calibration_harness import CalibrationHarness

        calibration_report: dict
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir) / "coverages"
            shutil.copytree(self.coverages_dir, tmp_root)
            target = tmp_root / version.coverage / f"{version.config_name}.yaml"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(version.content)

            try:
                harness = CalibrationHarness(coverages_dir=tmp_root)
                result = harness.run_coverage(version.coverage)
                # result may be a ConfigCalibrationResult or a CalibrationReport
                calibration_report = _serialise_calibration_result(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Calibration failed for %s", version_id)
                calibration_report = {
                    "success": False,
                    "error": str(exc),
                }

        new_status = (
            "CALIBRATED"
            if calibration_report.get("success", True)
            and version.status in ("VALIDATED", "DRAFT")
            else version.status
        )
        self.db.execute(
            text(
                """
                UPDATE config_versions
                SET calibration_report = CAST(:report AS jsonb),
                    status = :status,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "report": json.dumps(calibration_report, default=str),
                "status": new_status,
                "now": datetime.now(timezone.utc),
                "id": version_id,
            },
        )
        return calibration_report

    def deploy(
        self, version_id: str, deployed_by: Optional[str] = None
    ) -> dict:
        """Promote a CALIBRATED (or VALIDATED) version to DEPLOYED.

        Writes the YAML to disk + records a config_deployments audit row.
        """
        version = self.get_version(version_id)
        if version is None:
            raise ValueError(f"Version {version_id} not found")

        if version.status not in ("CALIBRATED", "VALIDATED", "DEPLOYED"):
            raise ValueError(
                f"Version {version_id} is {version.status}, cannot deploy "
                "(must be CALIBRATED or VALIDATED first)"
            )

        disk_path = self._disk_path(version.coverage, version.config_name)
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        disk_path.write_text(version.content)

        self.db.execute(
            text(
                """
                UPDATE config_versions
                SET status = 'DEPLOYED', updated_at = :now
                WHERE id = :id
                """
            ),
            {"now": datetime.now(timezone.utc), "id": version_id},
        )
        self.db.execute(
            text(
                """
                INSERT INTO config_deployments (
                    id, config_version_id, deployed_by, deployed_at, calibration_result
                ) VALUES (
                    :id, :version_id, :deployed_by, :now, CAST(:calibration AS jsonb)
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "version_id": version_id,
                "deployed_by": deployed_by,
                "now": datetime.now(timezone.utc),
                "calibration": json.dumps(version.calibration_report or {}, default=str),
            },
        )
        logger.info(
            "ConfigService: DEPLOYED %s -> %s (%s/%s v%d)",
            version_id, disk_path, version.coverage, version.config_name, version.version_number,
        )
        return {
            "version_id": version_id,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "file_path": str(disk_path),
        }

    def rollback(
        self,
        coverage: str,
        config_name: str,
        rolled_back_by: Optional[str] = None,
    ) -> dict:
        """Revert to the previous DEPLOYED version.

        Finds the two most-recent DEPLOYED rows for this (coverage, config_name):
        - Current DEPLOYED -> mark ROLLED_BACK + timestamp.
        - Previous DEPLOYED -> re-deploy (write YAML to disk + new
          config_deployments row).
        """
        rows = self.db.execute(
            text(
                """
                SELECT id::text, version_number, content, status, updated_at
                FROM config_versions
                WHERE coverage = :cov AND config_name = :cfg
                  AND status IN ('DEPLOYED', 'ROLLED_BACK')
                ORDER BY version_number DESC LIMIT 5
                """
            ),
            {"cov": coverage, "cfg": config_name},
        ).mappings().all()

        current = next((r for r in rows if r["status"] == "DEPLOYED"), None)
        previous = next(
            (r for r in rows if r["status"] in ("DEPLOYED", "ROLLED_BACK") and r["id"] != (current["id"] if current else None)),
            None,
        )
        if current is None or previous is None:
            raise ValueError("No previous deployment to roll back to")

        # Mark current as ROLLED_BACK
        self.db.execute(
            text(
                """
                UPDATE config_versions
                SET status = 'ROLLED_BACK', updated_at = :now
                WHERE id = :id
                """
            ),
            {"now": datetime.now(timezone.utc), "id": current["id"]},
        )
        # Mark the latest deployment row as rolled back
        self.db.execute(
            text(
                """
                UPDATE config_deployments
                SET rolled_back_at = :now, rolled_back_by = :by
                WHERE config_version_id = :id AND rolled_back_at IS NULL
                """
            ),
            {"now": datetime.now(timezone.utc), "by": rolled_back_by, "id": current["id"]},
        )

        # Re-deploy the previous version
        self.db.execute(
            text(
                """
                UPDATE config_versions SET status = 'DEPLOYED', updated_at = :now
                WHERE id = :id
                """
            ),
            {"now": datetime.now(timezone.utc), "id": previous["id"]},
        )
        disk_path = self._disk_path(coverage, config_name)
        disk_path.write_text(previous["content"])
        self.db.execute(
            text(
                """
                INSERT INTO config_deployments (id, config_version_id, deployed_by, deployed_at)
                VALUES (:deployment_id, :id, :by, :now)
                """
            ),
            {
                "deployment_id": str(uuid.uuid4()),
                "id": previous["id"],
                "by": rolled_back_by,
                "now": datetime.now(timezone.utc),
            },
        )

        logger.info(
            "ConfigService: ROLLED BACK %s/%s from v%d to v%d",
            coverage, config_name, current["version_number"], previous["version_number"],
        )
        return {
            "rolled_back_version_id": current["id"],
            "restored_version_id": previous["id"],
            "rolled_back_at": datetime.now(timezone.utc).isoformat(),
        }

    # ==================================================================
    # Helpers
    # ==================================================================

    def _next_version_number(self, coverage: str, config_name: str) -> int:
        row = self.db.execute(
            text(
                """
                SELECT MAX(version_number) FROM config_versions
                WHERE coverage = :cov AND config_name = :cfg
                """
            ),
            {"cov": coverage, "cfg": config_name},
        ).scalar()
        return int(row or 0) + 1

    def _discover_on_disk_configs(self) -> list[tuple[str, str, Path]]:
        """Return (coverage, config_name, path) for every YAML on disk."""
        if not self.coverages_dir.exists():
            return []
        results: list[tuple[str, str, Path]] = []
        for coverage_dir in sorted(self.coverages_dir.iterdir()):
            if not coverage_dir.is_dir():
                continue
            for yaml_file in sorted(coverage_dir.glob("*.yaml")):
                if yaml_file.name in ("master_config_layout.yaml",):
                    continue
                if yaml_file.name == "config.yaml":
                    # Multi-coverage master file or canonical config
                    results.append((coverage_dir.name, "config", yaml_file))
                else:
                    config_name = yaml_file.stem
                    results.append((coverage_dir.name, config_name, yaml_file))
        return results

    def _disk_path(self, coverage: str, config_name: str) -> Path:
        if config_name == "config":
            return self.coverages_dir / coverage / "config.yaml"
        return self.coverages_dir / coverage / f"{config_name}.yaml"

    def _row_to_dataclass(self, row) -> ConfigVersionRow:
        return ConfigVersionRow(
            id=str(row["id"]),
            coverage=row["coverage"],
            config_name=row["config_name"],
            version_number=row["version_number"],
            content=row["content"],
            config_hash=row["config_hash"],
            status=row["status"],
            validation_report=row["validation_report"],
            calibration_report=row["calibration_report"],
            notes=row["notes"],
            author_id=row.get("author_id") if hasattr(row, "get") else row["author_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def _serialise_calibration_result(result) -> dict:
    """Convert the calibration harness's dataclass output into a JSON-safe dict."""
    if hasattr(result, "__dict__"):
        d: dict = {}
        for k, v in result.__dict__.items():
            if k.startswith("_"):
                continue
            try:
                json.dumps(v, default=str)
                d[k] = v
            except TypeError:
                d[k] = str(v)
        return d
    return {"result": str(result)}

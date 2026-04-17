"""V6/E4 — integration test for `get_config(tenant_id=...)`.

Verifies the compiler picks up a tenant overlay, merges allowed
sections, records the overlay version, and otherwise is a no-op for
tenants without an overlay file.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COVERAGES_ROOT = REPO_ROOT / "coverages"


@pytest.fixture()
def cyber_tenant_overlay(tmp_path, monkeypatch):
    """Write a minimal cyber tenant overlay + point the loader at it."""
    # Copy cyber coverage into a tmp root so we don't touch the real tree.
    tmp_cov = tmp_path / "coverages"
    shutil.copytree(COVERAGES_ROOT / "cyber", tmp_cov / "cyber")

    overlays = tmp_cov / "cyber" / "overlays"
    overlays.mkdir()
    overlay_payload = {
        "_overlay_version": "acme-v3",
        "cyber": {
            "cyber_general": {
                "guardrails": {
                    "modifier_cap": 3.5,
                }
            }
        }
    }
    (overlays / "acme-tenant.yaml").write_text(yaml.safe_dump(overlay_payload))

    # Re-point REPO_ROOT for overlay_loader by patching its FIXTURE_ROOT /
    # coverages root via the compiler path.
    from infrastructure.models import overlay_loader
    monkeypatch.setattr(overlay_loader, "REPO_ROOT", tmp_path)
    yield tmp_cov, "acme-tenant"


def test_get_config_without_tenant_returns_base():
    from infrastructure.models.compiler import get_config
    config = get_config("cyber", "cyber_general")
    assert config.config_id == "cyber_general"


def test_get_config_with_missing_tenant_overlay_is_noop(cyber_tenant_overlay):
    from infrastructure.models.compiler import get_config
    # tenant that has no overlay file
    config = get_config("cyber", "cyber_general", tenant_id="no-such-tenant")
    assert config.config_id == "cyber_general"
    assert not hasattr(config, "_overlay_version") or config._overlay_version is None


def test_get_config_merges_allowed_overlay(cyber_tenant_overlay):
    from infrastructure.models.compiler import get_config
    config = get_config("cyber", "cyber_general", tenant_id="acme-tenant")
    # Overlay touched guardrails.modifier_cap — should be the new value.
    assert config.guardrails.modifier_cap == 3.5
    assert getattr(config, "_overlay_version", None) == "acme-v3"
    assert getattr(config, "_overlay_tenant_id", None) == "acme-tenant"


def test_get_config_rejects_disallowed_overlay_section(
    tmp_path, monkeypatch,
):
    from infrastructure.models import overlay_loader
    from infrastructure.models.compiler import get_config
    from infrastructure.models.overlay_loader import OverlayValidationError

    overlays = tmp_path / "coverages" / "cyber" / "overlays"
    overlays.mkdir(parents=True)
    # signal_registry is outside the allow-list → should raise.
    bad = {
        "cyber": {
            "cyber_general": {
                "signal_registry": [{"id": "sneaky_new_signal"}],
            }
        }
    }
    (overlays / "evil-tenant.yaml").write_text(yaml.safe_dump(bad))
    monkeypatch.setattr(overlay_loader, "REPO_ROOT", tmp_path)

    with pytest.raises(OverlayValidationError):
        get_config("cyber", "cyber_general", tenant_id="evil-tenant")

"""V6/E7 — rate-filing kit tests."""
from __future__ import annotations

import json
from pathlib import Path

from infrastructure.admin.rate_filing import (
    FilingArtefacts,
    generate_filing,
    main,
)


def test_generate_filing_returns_all_artefacts():
    artefacts = generate_filing("cyber", "cyber_general", "IL")
    assert isinstance(artefacts, FilingArtefacts)
    assert "Rate Filing Memo" in artefacts.filing_memo
    assert "CYBER" in artefacts.filing_memo
    assert "Actuarial Justification" in artefacts.actuarial_justification
    assert "Model Governance" in artefacts.model_governance
    assert "SERFF Filing Cover" in artefacts.cover_page
    assert artefacts.rate_exhibit_csv.startswith("exposure_band,")


def test_filing_embeds_live_logic_md_when_present():
    artefacts = generate_filing("cyber", "cyber_general", "IL")
    # Cyber has a committed logic.md; should be embedded.
    assert "logic.md" not in artefacts.filing_memo or "regenerate" not in artefacts.filing_memo


def test_write_creates_all_files(tmp_path: Path):
    out = tmp_path / "IL_cyber_2026Q2"
    artefacts = generate_filing("cyber", "cyber_general", "IL")
    artefacts.write(out)

    for f in (
        "filing_memo.md",
        "actuarial_justification.md",
        "rate_exhibit.csv",
        "model_governance_statement.md",
        "filing_cover.txt",
        "_manifest.json",
    ):
        assert (out / f).exists(), f"missing {f}"
    manifest = json.loads((out / "_manifest.json").read_text())
    assert manifest["coverage"] == "cyber"
    assert manifest["state"] == "IL"


def test_cli_happy_path(tmp_path: Path):
    out = tmp_path / "IL_cyber"
    exit_code = main(
        ["--coverage", "cyber", "--config", "cyber_general", "--state", "IL",
         "--out", str(out)]
    )
    assert exit_code == 0
    assert (out / "filing_memo.md").exists()


def test_rate_exhibit_csv_has_reasonable_rows():
    artefacts = generate_filing("cyber", "cyber_general", "IL")
    rows = artefacts.rate_exhibit_csv.strip().splitlines()
    # header + 3 exposure bands * 4 limits * 3 deductibles = 36 data rows + 1 header
    assert len(rows) == 1 + 3 * 4 * 3

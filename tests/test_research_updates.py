from __future__ import annotations

import json
from pathlib import Path

from knowledge_runtime.research_updates import (
    ResearchUpdateManager,
)


def write_json(
    path: Path,
    data,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_update_manager_replaces_data_without_code_change(
    tmp_path: Path,
) -> None:
    project_root = tmp_path

    target = (
        project_root
        / "knowledge-base"
        / "emissions"
        / "emission_factors.json"
    )

    write_json(
        target,
        {
            "coal": {
                "emission_factor": 96.10,
                "unit": "tCO2/TJ"
            }
        },
    )

    package = (
        project_root
        / "incoming_update"
    )

    write_json(
        package / "metadata.json",
        {
            "category": "emission_factors",
            "dataset_version": "2026.09",
            "source_ids": [
                "SRC_NEW_EMISSION_FACTORS"
            ],
            "source_date": "2026-09-01",
            "accessed": "2026-09-05",
            "status": "verified",
            "confidence": 0.95,
            "notes": (
                "Verified updated emission "
                "factor dataset."
            ),
        },
    )

    write_json(
        package / "payload.json",
        {
            "coal": {
                "emission_factor": 95.50,
                "unit": "tCO2/TJ"
            },
            "biomass": {
                "emission_factor": 99.0,
                "unit": "tCO2/TJ"
            },
        },
    )

    manager = ResearchUpdateManager(
        project_root
    )

    result = manager.activate_package(
        package
    )

    assert result.status == "activated"

    updated = json.loads(
        target.read_text(
            encoding="utf-8"
        )
    )

    assert (
        updated["coal"]["emission_factor"]
        == 95.50
    )

    assert (
        updated["biomass"]["emission_factor"]
        == 99.0
    )

    registry = manager.get_registry()

    assert (
        registry["datasets"]
        ["emission_factors"]
        ["dataset_version"]
        == "2026.09"
    )

    assert (
        registry["datasets"]
        ["emission_factors"]
        ["source_ids"]
        == ["SRC_NEW_EMISSION_FACTORS"]
    )

    backups = (
        project_root
        / "knowledge-base"
        / "backups"
        / "emission_factors"
    )

    assert backups.exists()

    assert any(
        backups.iterdir()
    )


def test_update_manager_rejects_invalid_confidence(
    tmp_path: Path,
) -> None:
    project_root = tmp_path

    package = (
        project_root
        / "invalid_update"
    )

    write_json(
        package / "metadata.json",
        {
            "category": "tariffs",
            "dataset_version": "2026.09",
            "source_ids": [
                "SRC_TEST"
            ],
            "source_date": "2026-09-01",
            "status": "verified",
            "confidence": 4.0
        },
    )

    write_json(
        package / "payload.json",
        {
            "records": []
        },
    )

    manager = ResearchUpdateManager(
        project_root
    )

    try:
        manager.validate_package(
            package
        )

        assert False, (
            "Expected invalid confidence "
            "to be rejected."
        )

    except ValueError as exc:
        assert (
            "confidence" in str(exc).lower()
        )
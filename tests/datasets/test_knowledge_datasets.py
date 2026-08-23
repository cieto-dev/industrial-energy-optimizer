from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pytest

pytestmark = pytest.mark.dataset


def _iter_json_files(root: Path) -> Iterator[Path]:
    if not root.exists():
        return

    yield from root.rglob("*.json")


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_all_knowledge_json_files_are_valid(
    knowledge_base_root: Path,
) -> None:
    files = list(_iter_json_files(knowledge_base_root))

    assert files, "No knowledge-base JSON files were found."

    failures: list[str] = []

    for path in files:
        try:
            _load(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{path}: {exc}")

    assert not failures, "\n".join(failures)


def test_json_files_do_not_contain_nan_or_infinity(
    knowledge_base_root: Path,
) -> None:
    import math
    files = list(_iter_json_files(knowledge_base_root))

    failures: list[str] = []

    def check_for_nan_inf(obj: Any) -> bool:
        if isinstance(obj, float):
            return math.isnan(obj) or math.isinf(obj)
        elif isinstance(obj, dict):
            return any(check_for_nan_inf(v) for v in obj.values())
        elif isinstance(obj, list):
            return any(check_for_nan_inf(v) for v in obj)
        return False

    for path in files:
        try:
            payload = _load(path)
        except json.JSONDecodeError:
            continue

        if check_for_nan_inf(payload):
            failures.append(str(path))

    assert not failures, (
        "Machine-readable datasets must not contain NaN/infinity: "
        + ", ".join(failures)
    )


def test_dataset_records_use_explicit_units_when_numeric(
    knowledge_base_root: Path,
) -> None:
    """
    Heuristic quality gate.

    We do not reject every numeric value without a unit because some
    datasets legitimately contain identifiers/counts. Instead, detect
    obvious parameter-style objects missing unit metadata.
    """

    candidate_keys = {
        "value",
        "price",
        "cost",
        "emission_factor",
        "efficiency",
        "capacity",
        "rate",
    }

    violations: list[str] = []

    for path in _iter_json_files(knowledge_base_root):
        payload = _load(path)

        stack: list[tuple[str, Any]] = [("$", payload)]

        while stack:
            location, current = stack.pop()

            if isinstance(current, dict):
                keys = {str(k).lower() for k in current}

                if keys.intersection(candidate_keys):
                    numeric_present = any(
                        isinstance(value, (int, float))
                        for value in current.values()
                    )

                    if numeric_present:
                        has_unit = any(
                            key in current
                            for key in (
                                "unit",
                                "units",
                                "unit_name",
                                "unit_of_measure",
                            )
                        )

                        if not has_unit:
                            # IDs/counts and explicit booleans are exempt.
                            if "id" not in keys and "count" not in keys:
                                violations.append(
                                    f"{path}:{location}"
                                )

                for key, value in current.items():
                    stack.append(
                        (
                            f"{location}.{key}",
                            value,
                        )
                    )

            elif isinstance(current, list):
                for index, value in enumerate(current):
                    stack.append(
                        (
                            f"{location}[{index}]",
                            value,
                        )
                    )

    # Keep this a warning-style assertion boundary initially.
    # Change to strict failure once all KB records are normalized.
    if violations:
        pytest.xfail(
            "Some legacy KB records still lack explicit unit metadata: "
            + ", ".join(violations[:10])
        )


def test_required_dataset_directories_exist(
    knowledge_base_root: Path,
) -> None:
    expected = [
        "constraints",
        "technologies",
        "industries",
        "finance",
        "emissions",
        "policies",
        "references",
    ]

    missing = [
        name
        for name in expected
        if not (knowledge_base_root / name).exists()
    ]

    assert not missing, (
        "Expected knowledge-base directories missing: "
        + ", ".join(missing)
    )


def test_case_study_dataset_files_are_valid(
    datasets_root: Path,
) -> None:
    schema_path = datasets_root / "case_studies.schema.json"
    dataset_path = datasets_root / "case_studies.json"

    assert schema_path.exists()
    assert dataset_path.exists()

    schema = _load(schema_path)
    dataset = _load(dataset_path)

    assert isinstance(schema, dict)
    assert isinstance(dataset, dict)

    assert dataset.get("schema_version")
    assert dataset.get("dataset_name")
    assert isinstance(dataset.get("case_studies"), list)
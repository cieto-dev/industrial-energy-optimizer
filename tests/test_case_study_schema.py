from __future__ import annotations

import json
import importlib
from pathlib import Path

import pytest

try:
    jsonschema = importlib.import_module("jsonschema")
except ImportError:  # pragma: no cover
    jsonschema = None


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "datasets" / "case_studies.schema.json"
DATASET_PATH = ROOT / "datasets" / "case_studies.json"


@pytest.mark.skipif(
    jsonschema is None,
    reason="jsonschema package is not installed",
)
def test_case_study_dataset_registry_is_valid():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    assert isinstance(dataset, dict)
    assert dataset["schema_version"] == "1.0.0"
    assert dataset["dataset_name"] == "industrial_case_studies"
    assert isinstance(dataset["case_studies"], list)

    for case in dataset["case_studies"]:
        jsonschema.validate(instance=case, schema=schema)


def test_schema_file_exists():
    assert SCHEMA_PATH.exists()
    assert SCHEMA_PATH.stat().st_size > 0


def test_dataset_file_exists():
    assert DATASET_PATH.exists()
    assert DATASET_PATH.stat().st_size > 0


def test_dataset_is_json():
    content = DATASET_PATH.read_text(encoding="utf-8")
    parsed = json.loads(content)

    assert isinstance(parsed, dict)


def test_registry_starts_empty_for_task_1():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    assert dataset["case_studies"] == []
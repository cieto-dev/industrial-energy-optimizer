from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_runtime.cache import KnowledgeCache
from knowledge_runtime.errors import (
    KnowledgeDataError,
    KnowledgeItemNotFoundError,
    KnowledgeReferenceError,
)
from knowledge_runtime.loader import KnowledgeLoader
from knowledge_runtime.repository import KnowledgeRepository


def test_loader_caches_parsed_json(tmp_path: Path) -> None:
    knowledge_base = tmp_path / "knowledge-base"
    knowledge_base.mkdir()

    file_path = knowledge_base / "sample.json"
    file_path.write_text(
        json.dumps({"value": 10}),
        encoding="utf-8",
    )

    loader = KnowledgeLoader(
        project_root=tmp_path,
        cache=KnowledgeCache(),
    )

    first = loader.load_knowledge_json("sample.json")

    file_path.write_text(
        json.dumps({"value": 20}),
        encoding="utf-8",
    )

    second = loader.load_knowledge_json("sample.json")

    assert first["value"] == 10
    assert second["value"] == 10


def test_loader_returns_defensive_copy(tmp_path: Path) -> None:
    knowledge_base = tmp_path / "knowledge-base"
    knowledge_base.mkdir()

    file_path = knowledge_base / "sample.json"
    file_path.write_text(
        json.dumps(
            {
                "nested": {
                    "value": 10,
                }
            }
        ),
        encoding="utf-8",
    )

    loader = KnowledgeLoader(project_root=tmp_path)

    first = loader.load_knowledge_json("sample.json")
    first["nested"]["value"] = 999

    second = loader.load_knowledge_json("sample.json")

    assert second["nested"]["value"] == 10


def test_missing_file_raises_standard_error(tmp_path: Path) -> None:
    loader = KnowledgeLoader(project_root=tmp_path)

    with pytest.raises(KnowledgeDataError) as exc_info:
        loader.load_knowledge_json("../outside.json")

    assert "path escapes" in str(exc_info.value)


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    knowledge_base = tmp_path / "knowledge-base"
    knowledge_base.mkdir()

    loader = KnowledgeLoader(project_root=tmp_path)

    with pytest.raises(Exception) as exc_info:
        loader.load_knowledge_json("missing.json")

    assert "Knowledge-base file not found" in str(exc_info.value)


def test_invalid_json_raises_data_error(tmp_path: Path) -> None:
    knowledge_base = tmp_path / "knowledge-base"
    knowledge_base.mkdir()

    file_path = knowledge_base / "broken.json"
    file_path.write_text(
        "{broken",
        encoding="utf-8",
    )

    loader = KnowledgeLoader(project_root=tmp_path)

    with pytest.raises(KnowledgeDataError):
        loader.load_knowledge_json("broken.json")


def test_source_resolution() -> None:
    repo = KnowledgeRepository()

    source = repo.get_source("SRC001")

    assert source["source_id"] == "SRC001"
    assert source["title"]
    assert source["organization"]
    assert source["year"] == 2006
    assert "url" in source


def test_unknown_source_raises() -> None:
    repo = KnowledgeRepository()

    with pytest.raises(KnowledgeReferenceError):
        repo.get_source("SOURCE_DOES_NOT_EXIST")


def test_unknown_emission_factor_raises() -> None:
    repo = KnowledgeRepository()

    with pytest.raises(KnowledgeItemNotFoundError):
        repo.get_emission_factor("does_not_exist")


def test_emission_factor_access() -> None:
    repo = KnowledgeRepository()

    coal = repo.get_emission_factor("coal")

    assert coal["emission_factor"] == pytest.approx(96.10)
    assert coal["unit"] == "tCO2/TJ"
    assert coal["ncv"] == pytest.approx(19.63)
    assert coal["ncv_unit"] == "TJ/kt"
    assert coal["input_unit"] == "kg/day"
    assert coal["source_id"] == "SRC003"
    assert coal["ncv_source_id"] == "SRC004"

    assert "evidence" in coal
    assert isinstance(coal["evidence"], list)
    assert coal["evidence"]


def test_biogas_emission_factor_access() -> None:
    repo = KnowledgeRepository()

    biogas = repo.get_emission_factor("biogas")

    assert biogas["emission_factor"] == pytest.approx(54.6)
    assert biogas["ncv"] == pytest.approx(19.88)
    assert biogas["ncv_unit"] == "MJ/m3"
    assert biogas["input_unit"] == "m3/day"
    assert biogas["source_id"] == "SRC001"
    assert biogas["ncv_source_id"] == "SRC002"

    assert "evidence" in biogas
    assert isinstance(biogas["evidence"], list)
    assert biogas["evidence"]


def test_all_emission_factors_accessible() -> None:
    repo = KnowledgeRepository()

    factors = repo.get_emission_factor()

    assert isinstance(factors, dict)
    assert factors

    expected_fuels = {
        "coal",
        "diesel",
        "lpg",
        "natural_gas",
        "biomass",
        "biogas",
        "furnace_oil",
    }

    assert expected_fuels.issubset(factors.keys())

    for fuel, record in factors.items():
        assert isinstance(record, dict)
        assert "emission_factor" in record
        assert "unit" in record
        assert "evidence" in record
        assert isinstance(record["evidence"], list)


def test_tariff_repository_access() -> None:
    repo = KnowledgeRepository()

    records = repo.get_tariff(state_id="HR")

    assert isinstance(records, list)
    assert records

    for record in records:
        assert "tariff_id" in record
        assert "state_id" in record
        assert record["state_id"] == "HR"
        assert "evidence" in record
        assert isinstance(record["evidence"], list)


def test_tariff_exact_lookup() -> None:
    repo = KnowledgeRepository()

    tariff = repo.get_tariff(
        "HR_HR_UHBVN_DHBVN_001"
    )

    assert isinstance(tariff, dict)
    assert tariff["tariff_id"] == "HR_HR_UHBVN_DHBVN_001"
    assert tariff["state_id"] == "HR"
    assert tariff["state"] == "Haryana"
    assert tariff["discom"] == "UHBVN/DHBVN"


def test_tariff_discom_filter() -> None:
    repo = KnowledgeRepository()

    records = repo.get_tariff(
        discom_id="HR_UHBVN_DHBVN"
    )

    assert isinstance(records, list)
    assert records

    for record in records:
        assert record["discom_id"] == "HR_UHBVN_DHBVN"


def test_tariff_consumer_category_filter() -> None:
    repo = KnowledgeRepository()

    records = repo.get_tariff(
        state_id="HR",
        consumer_category="HT Supply / Industrial",
    )

    assert isinstance(records, list)
    assert records

    for record in records:
        assert record["state_id"] == "HR"
        assert record["consumer_category"] == "HT Supply / Industrial"


def test_technology_repository_access() -> None:
    repo = KnowledgeRepository()

    records = repo.get_technology()

    assert isinstance(records, list)
    assert records

    for record in records:
        assert isinstance(record, dict)
        assert "evidence" in record
        assert isinstance(record["evidence"], list)


def test_specific_technology_lookup() -> None:
    repo = KnowledgeRepository()

    technology = repo.get_technology("biomass")

    assert isinstance(technology, dict)
    assert "evidence" in technology
    assert isinstance(technology["evidence"], list)


def test_industry_repository_access() -> None:
    repo = KnowledgeRepository()

    records = repo.get_industry()

    assert isinstance(records, list)
    assert records

    for record in records:
        assert isinstance(record, dict)
        assert "evidence" in record
        assert isinstance(record["evidence"], list)


def test_biomass_dataset_access() -> None:
    repo = KnowledgeRepository()

    records = repo.get_biomass()

    assert isinstance(records, list)
    assert records

    first = records[0]

    assert "state" in first
    assert "district" in first
    assert "biomass_type" in first
    assert "annual_availability_tons" in first
    assert "calorific_value_mj_kg" in first
    assert "cost_rs_per_ton" in first
    assert "latitude" in first
    assert "longitude" in first
    assert "evidence" in first
    assert isinstance(first["evidence"], list)


def test_biomass_records_have_expected_numeric_fields() -> None:
    repo = KnowledgeRepository()

    records = repo.get_biomass()

    for record in records[:20]:
        assert isinstance(record["annual_availability_tons"], (int, float))
        assert isinstance(record["moisture_percent"], (int, float))
        assert isinstance(record["calorific_value_mj_kg"], (int, float))
        assert isinstance(record["cost_rs_per_ton"], (int, float))
        assert isinstance(record["latitude"], (int, float))
        assert isinstance(record["longitude"], (int, float))


def test_cache_clear() -> None:
    repo = KnowledgeRepository()

    first = repo.get_emission_factor("coal")

    repo.clear_cache()

    second = repo.get_emission_factor("coal")

    assert first["emission_factor"] == second["emission_factor"]
    assert first["ncv"] == second["ncv"]
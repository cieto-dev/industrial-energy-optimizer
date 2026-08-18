"""
Unit tests for technology constraint filtering.

Tests the Biogas technology filter against the project-level
technology rules in knowledge-base/constraints/technology_rules.json.
"""

import pytest

from decision_engine.technology.technology_filter import filter_biogas


def test_biogas_allowed_for_valid_textile_factory():
    """Biogas should be feasible for a valid textile + coal case."""

    result = filter_biogas(
        fuel="coal",
        industry="textile",
        biogas_supply=True,
        gas_cleaning=True,
        gas_storage=True,
    )

    assert result["technology"] == "biogas"
    assert result["feasible"] is True


@pytest.mark.parametrize(
    "fuel",
    [
        "electricity",
        "solar",
        "furnace_gas",
    ],
)
def test_biogas_rejects_unsupported_fuel(fuel):
    """Biogas should be rejected when it cannot replace the existing fuel."""

    result = filter_biogas(
        fuel=fuel,
        industry="textile",
        biogas_supply=True,
        gas_cleaning=True,
        gas_storage=True,
    )

    assert result["technology"] == "biogas"
    assert result["feasible"] is False
    assert "not configured to replace" in result["reason"]


def test_biogas_rejects_unsupported_industry():
    """Biogas should be rejected for an industry outside the KB rules."""

    result = filter_biogas(
        fuel="coal",
        industry="steel_making",
        biogas_supply=True,
        gas_cleaning=True,
        gas_storage=True,
    )

    assert result["technology"] == "biogas"
    assert result["feasible"] is False
    assert "not in the project eligibility rules" in result["reason"]


def test_biogas_rejects_without_supply():
    """Biogas requires a reliable biogas supply."""

    result = filter_biogas(
        fuel="coal",
        industry="textile",
        biogas_supply=False,
        gas_cleaning=True,
        gas_storage=True,
    )

    assert result["technology"] == "biogas"
    assert result["feasible"] is False
    assert result["reason"] == "Reliable biogas supply is required"


def test_biogas_rejects_without_gas_cleaning():
    """Biogas requires gas-cleaning infrastructure."""

    result = filter_biogas(
        fuel="coal",
        industry="textile",
        biogas_supply=True,
        gas_cleaning=False,
        gas_storage=True,
    )

    assert result["technology"] == "biogas"
    assert result["feasible"] is False
    assert result["reason"] == "Gas cleaning is required"


def test_biogas_rejects_without_gas_storage():
    """Biogas requires gas-storage infrastructure."""

    result = filter_biogas(
        fuel="coal",
        industry="textile",
        biogas_supply=True,
        gas_cleaning=True,
        gas_storage=False,
    )

    assert result["technology"] == "biogas"
    assert result["feasible"] is False
    assert result["reason"] == "Gas storage is required"


def test_biogas_input_is_case_insensitive():
    """Fuel and industry matching should tolerate case and whitespace."""

    result = filter_biogas(
        fuel="  COAL ",
        industry="  TEXTILE ",
        biogas_supply=True,
        gas_cleaning=True,
        gas_storage=True,
    )

    assert result["feasible"] is True
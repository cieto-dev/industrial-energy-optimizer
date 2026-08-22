"""
Unit 2.4 Tests
==============

Tests for the Industry Constraint Engine.

Run using:

    pytest tests/test_industry_constraint_engine.py
"""

import pytest

from decision_engine.technology.industry_constraint_engine import (
    IndustryConstraintEngine,
)


@pytest.fixture
def engine():
    return IndustryConstraintEngine()


# ---------------------------------------------------------
# Preferred Technologies
# ---------------------------------------------------------

def test_textile_heat_pump_preferred(engine):

    result = engine.evaluate(
        industry="textile",
        technology="heat_pump",
    )

    assert result["allowed"] is True
    assert result["classification"] == "preferred"


def test_food_heat_pump_preferred(engine):

    result = engine.evaluate(
        industry="food_processing",
        technology="heat_pump",
    )

    assert result["classification"] == "preferred"


# ---------------------------------------------------------
# Acceptable Technologies
# ---------------------------------------------------------

def test_food_thermal_storage_acceptable(engine):

    result = engine.evaluate(
        industry="food_processing",
        technology="thermal_storage",
    )

    assert result["allowed"] is True
    assert result["classification"] == "acceptable"


# ---------------------------------------------------------
# Mandatory Exclusions
# ---------------------------------------------------------

def test_steel_heat_pump_excluded(engine):

    result = engine.evaluate(
        industry="steel",
        technology="heat_pump",
    )

    assert result["allowed"] is False
    assert result["classification"] == "excluded"


def test_cement_heat_pump_excluded(engine):

    result = engine.evaluate(
        industry="cement",
        technology="heat_pump",
    )

    assert result["allowed"] is False
    assert result["classification"] == "excluded"


# ---------------------------------------------------------
# Unknown Technology
# ---------------------------------------------------------

def test_unknown_technology(engine):

    result = engine.evaluate(
        industry="steel",
        technology="future_magic_boiler",
    )

    assert result["allowed"] is True
    assert result["classification"] == "not_preferred"


# ---------------------------------------------------------
# Unknown Industry
# ---------------------------------------------------------

def test_unknown_industry(engine):

    result = engine.evaluate(
        industry="glass",
        technology="heat_pump",
    )

    assert result["allowed"] is True
    assert result["classification"] == "acceptable"


# ---------------------------------------------------------
# Cluster Recommendations
# ---------------------------------------------------------

def test_cluster_recommendations(engine):

    result = engine.evaluate(
        industry="textile",
        technology="heat_pump",
    )

    assert isinstance(
        result["cluster_recommendations"],
        list,
    )

    assert "steam_network" in result["cluster_recommendations"]


# ---------------------------------------------------------
# Operational Constraints
# ---------------------------------------------------------

def test_operational_constraints(engine):

    result = engine.evaluate(
        industry="pharma",
        technology="electric_boiler",
    )

    assert isinstance(
        result["operational_constraints"],
        list,
    )

    assert len(result["operational_constraints"]) > 0


# ---------------------------------------------------------
# Bulk Evaluation
# ---------------------------------------------------------

def test_evaluate_many(engine):

    technologies = [
        "heat_pump",
        "electric_boiler",
        "hydrogen",
    ]

    results = engine.evaluate_many(
        industry="textile",
        technologies=technologies,
    )

    assert len(results) == 3

    assert results[0]["technology"] == "heat_pump"

    assert results[1]["technology"] == "electric_boiler"

    assert results[2]["technology"] == "hydrogen"


# ---------------------------------------------------------
# Returned Structure
# ---------------------------------------------------------

def test_output_keys(engine):

    result = engine.evaluate(
        industry="textile",
        technology="heat_pump",
    )

    required_keys = {
        "allowed",
        "classification",
        "reasons",
        "operational_constraints",
        "cluster_recommendations",
    }

    assert required_keys.issubset(result.keys())
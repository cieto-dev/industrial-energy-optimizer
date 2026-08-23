
from __future__ import annotations

import pytest

from decision_engine.validation.research_validator import (
    ResearchValidationFramework,
)


class FakeEvidenceResolver:
    """
    Minimal resolver used to test the validation framework without touching
    the real knowledge-base filesystem.
    """

    def __init__(self, sources: dict[str, dict]):
        self.sources = sources

    def get_source(self, source_id: str) -> dict:
        if source_id not in self.sources:
            raise KeyError(source_id)

        return self.sources[source_id]


def valid_recommendation() -> dict:
    return {
        "factory_id": "fac-001",
        "factory_name": "Demo Textile",
        "industry": "textile",
        "state": "Tamil Nadu",
        "recommended_scenario_id": "scenario-1",
        "recommended_technology_sequence": [
            "waste_heat_recovery",
            "biomass",
        ],
        "capex_total_inr": 10_000_000,
        "annual_opex_inr": 800_000,
        "payback_range_years": [2.2, 4.1],
        "co2_reduction_pct": 58.0,
        "fossil_fuel_reduction_pct": 72.0,
        "composite_score": 0.84,
        "objective_scores": {
            "cost": 0.81,
            "emissions": 0.90,
            "risk": 0.77,
        },
        "recommended_is_cheapest": False,
    }


def valid_evidence() -> list[dict]:
    return [
        {
            "parameter_name": "capex_total_inr",
            "source_id": "SRC001",
        },
        {
            "parameter_name": "annual_opex_inr",
            "source_id": "SRC002",
        },
        {
            "parameter_name": "payback_range_years",
            "source_id": "SRC003",
        },
        {
            "parameter_name": "co2_reduction_pct",
            "source_id": "SRC004",
        },
        {
            "parameter_name": "fossil_fuel_reduction_pct",
            "source_id": "SRC005",
        },
        {
            "parameter_name": "recommended_technology_sequence",
            "source_id": "SRC006",
        },
    ]


def build_validator() -> ResearchValidationFramework:
    resolver = FakeEvidenceResolver(
        {
            "SRC001": {
                "title": "CAPEX source",
                "organization": "Primary Source",
                "year": 2026,
                "url": "https://example.com/1",
            },
            "SRC002": {
                "title": "OPEX source",
                "organization": "Primary Source",
                "year": 2026,
                "url": "https://example.com/2",
            },
            "SRC003": {
                "title": "Payback source",
                "organization": "Primary Source",
                "year": 2026,
                "url": "https://example.com/3",
            },
            "SRC004": {
                "title": "CO2 source",
                "organization": "Primary Source",
                "year": 2026,
                "url": "https://example.com/4",
            },
            "SRC005": {
                "title": "Fossil source",
                "organization": "Primary Source",
                "year": 2026,
                "url": "https://example.com/5",
            },
            "SRC006": {
                "title": "Technology source",
                "organization": "Primary Source",
                "year": 2026,
                "url": "https://example.com/6",
            },
        }
    )

    return ResearchValidationFramework(
        evidence_resolver=resolver,
    )


def test_valid_recommendation_passes():
    validator = build_validator()

    result = validator.validate_recommendation(
        valid_recommendation(),
        evidence_records=valid_evidence(),
        all_scenarios=[
            {"scenario_id": "scenario-1"},
            {"scenario_id": "scenario-2"},
        ],
    )

    assert result.valid is True
    assert result.recommendation_supported is True
    assert result.confidence_pct >= 70
    assert result.evidence_summary.source_count >= 5


def test_missing_citation_is_detected():
    validator = build_validator()

    evidence = [
        record
        for record in valid_evidence()
        if record["parameter_name"] != "capex_total_inr"
    ]

    result = validator.validate_recommendation(
        valid_recommendation(),
        evidence_records=evidence,
        all_scenarios=[{"scenario_id": "scenario-1"}],
    )

    assert result.valid is False
    assert "capex_total_inr" in (
        result.evidence_summary.missing_citations
    )


def test_broken_reference_is_detected():
    validator = build_validator()

    evidence = valid_evidence()
    evidence[0] = {
        "parameter_name": "capex_total_inr",
        "source_id": "SRC_DOES_NOT_EXIST",
    }

    result = validator.validate_recommendation(
        valid_recommendation(),
        evidence_records=evidence,
        all_scenarios=[{"scenario_id": "scenario-1"}],
    )

    assert result.valid is False
    assert any(
        issue.code == "BROKEN_REFERENCE"
        for issue in result.errors
    )


def test_invalid_dataset_is_detected():
    validator = build_validator()

    result = validator.validate_recommendation(
        valid_recommendation(),
        evidence_records=valid_evidence(),
        all_scenarios=[{"scenario_id": "scenario-1"}],
        dataset_records=[
            {},
            {"source_id": 123},
        ],
    )

    assert result.valid is False
    assert len(result.evidence_summary.invalid_datasets) >= 1


def test_unsupported_recommendation_is_detected():
    validator = build_validator()

    result = validator.validate_recommendation(
        valid_recommendation(),
        evidence_records=valid_evidence(),
        all_scenarios=[
            {"scenario_id": "scenario-2"},
        ],
    )

    assert result.valid is False
    assert any(
        issue.code == "UNSUPPORTED_RECOMMENDATION"
        for issue in result.errors
    )


def test_invalid_numeric_range_is_detected():
    validator = build_validator()

    recommendation = valid_recommendation()
    recommendation["co2_reduction_pct"] = 135.0

    result = validator.validate_recommendation(
        recommendation,
        evidence_records=valid_evidence(),
        all_scenarios=[{"scenario_id": "scenario-1"}],
    )

    assert result.valid is False
    assert any(
        issue.code == "INVALID_PARAMETER_VALUE"
        for issue in result.errors
    )


def test_payback_range_order_is_validated():
    validator = build_validator()

    recommendation = valid_recommendation()
    recommendation["payback_range_years"] = [5.0, 2.0]

    result = validator.validate_recommendation(
        recommendation,
        evidence_records=valid_evidence(),
        all_scenarios=[{"scenario_id": "scenario-1"}],
    )

    assert result.valid is False
    assert any(
        issue.code == "INVALID_PARAMETER_VALUE"
        for issue in result.errors
    )


def test_evidence_strength_is_not_fake_high():
    validator = build_validator()

    result = validator.validate_recommendation(
        valid_recommendation(),
        evidence_records=[
            {
                "parameter_name": "capex_total_inr",
                "source_id": "SRC001",
            }
        ],
        all_scenarios=[{"scenario_id": "scenario-1"}],
    )

    assert result.evidence_summary.evidence_strength != "Strong"
    assert result.evidence_summary.research_quality != "High"


@pytest.mark.parametrize(
    "confidence,expected",
    [
        (95.0, "Strong"),
        (86.0, "Strong"),
        (75.0, "Moderate"),
        (50.0, "Weak"),
    ],
)
def test_evidence_label_thresholds(confidence, expected):
    result = ResearchValidationFramework._evidence_strength(
        confidence_pct=confidence,
        source_count=5,
        blocking_errors=0,
    )

    assert result == expected

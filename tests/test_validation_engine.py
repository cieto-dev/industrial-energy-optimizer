from __future__ import annotations

import math

import pytest

from decision_engine.validation.validation_engine import (
    AssumptionRecord,
    ParameterCandidate,
    UnitValidationError,
    ValidationEngine,
    ValidationEngineError,
    run_self_test,
)


@pytest.fixture()
def engine() -> ValidationEngine:
    return ValidationEngine()


def test_kwh_to_mj(engine: ValidationEngine) -> None:
    result = engine.validate_energy_conversion(
        value=1.0,
        from_unit="kWh",
        to_unit="MJ",
        expected_value=3.6,
    )

    assert result.passed is True
    assert math.isclose(
        result.metrics["converted_value"],
        3.6,
        rel_tol=1e-9,
    )


def test_gj_to_mj(engine: ValidationEngine) -> None:
    result = engine.validate_energy_conversion(
        value=1.0,
        from_unit="GJ",
        to_unit="MJ",
        expected_value=1000.0,
    )

    assert result.passed is True


def test_incompatible_units_are_rejected(
    engine: ValidationEngine,
) -> None:
    with pytest.raises(UnitValidationError):
        engine.units.convert(
            100,
            "kWh",
            "kg",
        )


def test_efficiency_decimal_is_normalized(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_efficiency(
        parameter="boiler_efficiency",
        efficiency=0.80,
    )

    assert result.passed is True
    assert result.metrics["normalized_efficiency_pct"] == pytest.approx(
        80.0
    )


def test_efficiency_above_100_fails(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_efficiency(
        parameter="boiler_efficiency",
        efficiency=101,
    )

    assert result.passed is False


def test_energy_balance_closes(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_energy_balance(
        input_energy_mj=1000,
        useful_energy_mj=800,
        loss_components_mj={
            "boiler_loss": 100,
            "distribution_loss": 50,
            "process_loss": 50,
        },
    )

    assert result.passed is True
    assert result.metrics["residual_mj"] == pytest.approx(0.0)


def test_energy_balance_failure_is_detected(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_energy_balance(
        input_energy_mj=1000,
        useful_energy_mj=800,
        loss_components_mj={
            "loss": 100,
        },
    )

    assert result.passed is False
    assert any(
        issue.code == "ENERGY_BALANCE_FAILED"
        for issue in result.issues
    )


def test_grid_emissions(
    engine: ValidationEngine,
) -> None:
    result = engine.calculate_grid_emissions(
        electricity_kwh=1000,
        grid_factor_kgco2e_per_kwh=0.7117,
    )

    assert result["emissions_kgco2e"] == pytest.approx(
        711.7
    )

    assert result["emissions_tco2e"] == pytest.approx(
        0.7117
    )


def test_payback(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_payback(
        capex_inr=900_000,
        annual_savings_inr=300_000,
    )

    assert result.passed is True
    assert result.metrics["simple_payback_years"] == pytest.approx(
        3.0
    )


def test_low_confidence_parameter_is_flagged(
    engine: ValidationEngine,
) -> None:
    assumption = AssumptionRecord(
        parameter="example_tariff",
        value=8.2,
        unit="kWh",
        source_id=None,
        source_type="secondary",
        status="estimated",
        confidence="low",
    )

    result = engine.validate_assumption(
        assumption
    )

    assert result.passed is True

    assert any(
        issue.code == "VERIFICATION_REQUIRED"
        for issue in result.issues
    )


def test_high_confidence_requires_source(
    engine: ValidationEngine,
) -> None:
    with pytest.raises(
        Exception
    ):
        AssumptionRecord(
            parameter="grid_factor",
            value=0.7117,
            unit="kgCO2e",
            source_id=None,
            source_type="government",
            status="current",
            confidence="high",
        )


def test_conflicting_values_are_not_averaged(
    engine: ValidationEngine,
) -> None:
    conflicts = engine.detect_conflicts(
        [
            ParameterCandidate(
                parameter="tariff",
                value=8.0,
                unit="kWh",
                source_id="SRC_A",
                source_type="secondary",
                confidence="medium",
            ),
            ParameterCandidate(
                parameter="tariff",
                value=10.0,
                unit="kWh",
                source_id="SRC_B",
                source_type="secondary",
                confidence="medium",
            ),
        ]
    )

    assert len(conflicts) == 1

    assert conflicts[0].is_blocking is True

    # Ensure no averaging occurs.
    candidate_values = [
        item["value"]
        for item in conflicts[0].candidates
    ]

    assert candidate_values == [8.0, 10.0]


def test_temperature_calibration(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_temperature_range(
        required_temperature_c=600,
        minimum_supported_c=0,
        maximum_supported_c=1600,
    )

    assert result.passed is True
    assert result.metrics["temperature_feasible"] is True


def test_temperature_infeasible(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_temperature_range(
        required_temperature_c=1800,
        minimum_supported_c=0,
        maximum_supported_c=1600,
    )

    assert result.passed is False


def test_tariff_low_confidence_warning(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_tariff(
        energy_charge_inr_per_kwh=9.5,
        demand_charge_inr_per_unit_month=450,
        fixed_charge_inr_per_month=0,
        electricity_duty_pct=5,
        status="estimated",
        confidence="low",
    )

    assert result.passed is True

    warning_codes = {
        item.code
        for item in result.issues
        if item.severity == "warning"
    }

    assert "NON_CURRENT_TARIFF" in warning_codes
    assert "LOW_TARIFF_CONFIDENCE" in warning_codes


def test_assumption_set_reports_conflict(
    engine: ValidationEngine,
) -> None:
    assumptions = [
        AssumptionRecord(
            parameter="fuel_price",
            value=8.0,
            unit="kWh",
            source_id="SRC_A",
            source_type="government",
            status="current",
            confidence="high",
        ),
        AssumptionRecord(
            parameter="fuel_price",
            value=10.0,
            unit="kWh",
            source_id="SRC_B",
            source_type="government",
            status="current",
            confidence="high",
        ),
    ]

    report = engine.validate_assumption_set(
        assumptions
    )

    assert report.passed is False
    assert len(report.conflict_results) == 1


def test_production_gate_rejects_failed_report(
    engine: ValidationEngine,
) -> None:
    result = engine.validate_energy_balance(
        input_energy_mj=1000,
        useful_energy_mj=900,
        loss_components_mj={
            "loss": 1,
        },
    )

    assert result.passed is False

    report = engine.validate_assumption_set([])

    report.absorb(result)

    with pytest.raises(
        ValidationEngineError
    ):
        engine.require_production_safe(
            report=report
        )


def test_self_test() -> None:
    result = run_self_test()

    assert result["passed"] is True
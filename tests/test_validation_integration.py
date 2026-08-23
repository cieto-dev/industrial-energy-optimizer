from __future__ import annotations

from decision_engine.validation.validation_engine import ValidationEngine


def test_repository_grid_factor_is_dimensionally_valid() -> None:
    engine = ValidationEngine()

    result = engine.validate_unit(
        name="grid_emission_factor",
        value=0.7117,
        unit="kgCO2e",
        expected_unit="kgCO2e",
        minimum=0.0,
    )

    assert result.passed is True


def test_energy_balance_validation_contract() -> None:
    engine = ValidationEngine()

    result = engine.validate_energy_balance(
        input_energy_mj=10_000.0,
        useful_energy_mj=6_840.0,
        loss_components_mj={
            "boiler_loss": 2_000.0,
            "distribution_loss": 700.0,
            "process_loss": 460.0
        }
    )

    assert result.passed is True


def test_biogenic_emissions_are_not_silently_reclassified() -> None:
    engine = ValidationEngine()

    result = engine.validate_emission_factor(
        parameter="biomass_emission_factor",
        emission_factor=100.0,
        emission_factor_unit="tCO2",
        category="biogenic_combustion"
    )

    assert any(
        issue.code == "BIOGENIC_ACCOUNTING_BOUNDARY"
        for issue in result.issues
    )
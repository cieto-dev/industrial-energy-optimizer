"""
reliability_engine.py — Monte Carlo reliability and sensitivity analysis.

Task 3.4
--------
Instead of returning one deterministic payback value, quantify how payback
changes under uncertainty in:

- fuel price
- electricity tariff
- biomass procurement/logistics cost
- efficiency
- carbon price

The engine provides:

1. P10 / P50 / P90 Monte Carlo payback
2. OAT tornado swings
3. Best / Expected / Worst deterministic scenarios
4. Audit metadata for every uncertain variable

Important
---------
Carbon price is NOT treated as a universal Indian carbon tax.
It is a scenario / contractual / verified-market input and remains zero by
default unless the caller explicitly supplies an applicable value.

Efficiency
----------
Efficiency is represented as a relative multiplier:

    1.00 = base-case efficiency
    0.90 = 10% worse efficiency
    1.10 = 10% better efficiency

Higher efficiency reduces variable energy expenditure.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from decision_engine.economics.payback import calculate_payback
from decision_engine.reliability.confidence import (
    ConfidenceProfile,
    build_standard_confidence_profile,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_PERTURBATION_CONFIG_PATH = (
    _PROJECT_ROOT
    / "knowledge-base"
    / "finance"
    / "perturbation_config.json"
)


@dataclass
class BaseCaseInputs:
    """
    Base-case economic inputs required for uncertainty analysis.
    """

    capex_min: float
    capex_max: float

    baseline_annual_opex: float

    proposed_fuel_cost: float
    proposed_electricity_cost: float
    proposed_maintenance_cost: float
    proposed_labour_cost: float
    proposed_other_cost: float

    baseline_fuel_cost: float
    baseline_electricity_cost: float

    # Technology/application context.
    solar_fraction: float = 0.0
    biomass_fraction: float = 0.0

    # Carbon accounting inputs.
    baseline_co2_tco2e: float = 0.0
    proposed_co2_tco2e: float = 0.0

    # Carbon-market applicability.
    obligated_entity: bool = False
    eligible_credit_generation: bool = False

    technology_id: str = "unknown"
    scenario_id: str = "unknown"


@dataclass
class ReliabilitySweepResult:
    payback_p10: float
    payback_p50: float
    payback_p90: float
    spread_ratio: float

    raw_distribution: List[float]

    oat_swings: Dict[str, float]

    metadata: Dict

    n_iterations: int
    gate_passed: bool


@dataclass
class SensitivityScenario:
    label: str
    factors: Dict[str, float]

    payback_years: Optional[float]
    annual_savings_inr: Optional[float]

    annual_carbon_cost_inr: float
    annual_carbon_value_inr: float

    viable: bool


@dataclass
class BestExpectedWorstResult:
    best_case: SensitivityScenario
    expected_case: SensitivityScenario
    worst_case: SensitivityScenario

    payback_range_years: tuple[
        Optional[float],
        Optional[float],
    ]

    dominant_factor: Optional[str]

    tornado: Dict[str, float]

    notes: List[str]


def _load_perturbation_config(
    config_path: Optional[Path] = None,
) -> Dict:
    path = config_path or _DEFAULT_PERTURBATION_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Perturbation config not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _triangular_sample(
    low: float,
    base: float,
    high: float,
) -> float:
    return random.triangular(
        low,
        high,
        base,
    )


def _apply_widening(
    low: float,
    base: float,
    high: float,
    widening_factor: float,
) -> tuple[float, float]:
    new_low = base - (
        base - low
    ) * widening_factor

    new_high = base + (
        high - base
    ) * widening_factor

    new_low = max(
        0.01,
        new_low,
    )

    new_high = min(
        5.0,
        new_high,
    )

    return (
        new_low,
        new_high,
    )


def _calculate_carbon_adjustment(
    base_case: BaseCaseInputs,
    carbon_price: float,
) -> tuple[float, float]:
    """
    Return:

        carbon_cost,
        carbon_value

    Compliance cost is only applied when the factory is explicitly marked as
    an obligated entity.

    Credit value is only applied when eligible_credit_generation=True.

    No carbon value is inferred merely from CO2 reduction.
    """

    if carbon_price < 0:
        raise ValueError(
            "carbon_price cannot be negative."
        )

    baseline = max(
        0.0,
        base_case.baseline_co2_tco2e,
    )

    proposed = max(
        0.0,
        base_case.proposed_co2_tco2e,
    )

    shortfall = max(
        0.0,
        proposed - baseline,
    )

    reduction = max(
        0.0,
        baseline - proposed,
    )

    carbon_cost = 0.0
    carbon_value = 0.0

    if base_case.obligated_entity:
        carbon_cost = (
            shortfall
            * carbon_price
        )

    if base_case.eligible_credit_generation:
        carbon_value = (
            reduction
            * carbon_price
        )

    return (
        carbon_cost,
        carbon_value,
    )


def _compute_perturbed_payback(
    base_case: BaseCaseInputs,
    factors: Dict[str, float],
) -> Optional[float]:

    fuel_price = factors.get(
        "fuel_price",
        1.0,
    )

    production_volume = factors.get(
        "production_volume",
        1.0,
    )

    solar_capacity_factor = factors.get(
        "solar_capacity_factor",
        1.0,
    )

    electricity_tariff = factors.get(
        "electricity_tariff",
        1.0,
    )

    biomass_cost = factors.get(
        "biomass_cost",
        factors.get(
            "biomass_logistics_cost",
            1.0,
        ),
    )

    capex_overrun = factors.get(
        "capex_overrun",
        1.0,
    )

    efficiency = factors.get(
        "efficiency",
        1.0,
    )

    carbon_price = factors.get(
        "carbon_price",
        0.0,
    )

    if efficiency <= 0:
        raise ValueError(
            "Efficiency multiplier must be > 0."
        )

    # --------------------------------------------------------------
    # CAPEX
    # --------------------------------------------------------------

    perturbed_capex_min = (
        base_case.capex_min
        * capex_overrun
    )

    perturbed_capex_max = (
        base_case.capex_max
        * capex_overrun
    )

    # --------------------------------------------------------------
    # Proposed fuel
    # --------------------------------------------------------------

    biomass_share = max(
        0.0,
        min(
            1.0,
            base_case.biomass_fraction,
        ),
    )

    non_biomass_share = (
        1.0
        - biomass_share
    )

    proposed_fuel = (
        base_case.proposed_fuel_cost
        * fuel_price
        * (
            non_biomass_share
            + (
                biomass_share
                * biomass_cost
            )
        )
    )

    # --------------------------------------------------------------
    # Proposed electricity
    # --------------------------------------------------------------

    proposed_electricity = (
        base_case.proposed_electricity_cost
        * electricity_tariff
    )

    # Solar under-performance:
    # when solar capacity factor falls below 1.0, additional electricity
    # is purchased to compensate for the lost solar contribution.
    solar_shortfall = 0.0

    if base_case.solar_fraction > 0.0:

        solar_shortfall = (
            base_case.solar_fraction
            * max(
                0.0,
                1.0 - solar_capacity_factor,
            )
        )

    solar_deficit_cost = (
        base_case.baseline_electricity_cost
        * solar_shortfall
        * electricity_tariff
    )

    proposed_electricity += (
        solar_deficit_cost
    )

    # --------------------------------------------------------------
    # Efficiency sensitivity
    # --------------------------------------------------------------

    efficiency_factor = (
        1.0
        / efficiency
    )

    proposed_fuel *= (
        efficiency_factor
    )

    proposed_electricity *= (
        efficiency_factor
    )

    # --------------------------------------------------------------
    # Proposed annual OPEX
    # --------------------------------------------------------------

    proposed_annual_opex = (
        proposed_fuel
        + proposed_electricity
        + base_case.proposed_maintenance_cost
        + base_case.proposed_labour_cost
        + base_case.proposed_other_cost
    )

    proposed_annual_opex *= (
        production_volume
    )

    # --------------------------------------------------------------
    # Baseline OPEX
    # --------------------------------------------------------------

    baseline_fuel = (
        base_case.baseline_fuel_cost
        * fuel_price
        * production_volume
    )

    baseline_electricity = (
        base_case.baseline_electricity_cost
        * electricity_tariff
        * production_volume
    )

    baseline_non_energy = (
        base_case.baseline_annual_opex
        - base_case.baseline_fuel_cost
        - base_case.baseline_electricity_cost
    )

    baseline_non_energy *= (
        production_volume
    )

    perturbed_baseline_opex = (
        baseline_fuel
        + baseline_electricity
        + baseline_non_energy
    )

    # --------------------------------------------------------------
    # Carbon economics
    # --------------------------------------------------------------

    carbon_cost, carbon_value = (
        _calculate_carbon_adjustment(
            base_case=base_case,
            carbon_price=carbon_price,
        )
    )

    carbon_cost *= (
        production_volume
    )

    carbon_value *= (
        production_volume
    )

    # --------------------------------------------------------------
    # Annual savings
    # --------------------------------------------------------------

    annual_savings = (
        perturbed_baseline_opex
        - proposed_annual_opex
        - carbon_cost
        + carbon_value
    )

    if annual_savings <= 0:
        return None

    result = calculate_payback(
        capex_min=perturbed_capex_min,
        capex_max=perturbed_capex_max,
        annual_savings=annual_savings,
    )

    return result[
        "payback_min_years"
    ]


def _percentile(
    sorted_values: List[float],
    pct: float,
) -> float:

    if not sorted_values:
        raise ValueError(
            "Cannot compute percentile of empty list."
        )

    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (
        pct
        / 100.0
    ) * (
        len(sorted_values) - 1
    )

    lower = int(rank)
    upper = lower + 1

    if upper >= len(sorted_values):
        return sorted_values[-1]

    fraction = (
        rank
        - lower
    )

    return (
        sorted_values[lower]
        * (1.0 - fraction)
        + sorted_values[upper]
        * fraction
    )


def _one_at_a_time_swings(
    base_case: BaseCaseInputs,
    variables: Dict,
    widened_params: Dict[str, Dict],
) -> Dict[str, float]:

    swings: Dict[str, float] = {}

    base_factors = {
        variable_id: (
            0.0
            if variable_id
            == "carbon_price"
            else 1.0
        )
        for variable_id in variables
    }

    for variable_id, params in (
        widened_params.items()
    ):

        high_factors = {
            **base_factors,
            variable_id: params["high"],
        }

        low_factors = {
            **base_factors,
            variable_id: params["low"],
        }

        high_payback = (
            _compute_perturbed_payback(
                base_case,
                high_factors,
            )
        )

        low_payback = (
            _compute_perturbed_payback(
                base_case,
                low_factors,
            )
        )

        if (
            high_payback is None
            or low_payback is None
        ):
            swings[variable_id] = 0.0
        else:
            swings[variable_id] = (
                high_payback
                - low_payback
            )

    return swings


def run_reliability_sweep(
    base_case: BaseCaseInputs,
    confidence_profile: Optional[
        ConfidenceProfile
    ] = None,
    n_iterations: int = 5000,
    config_path: Optional[Path] = None,
    random_seed: Optional[int] = None,
) -> ReliabilitySweepResult:

    if n_iterations < 100:
        raise ValueError(
            "n_iterations must be >= 100."
        )

    if random_seed is not None:
        random.seed(
            random_seed
        )

    config = (
        _load_perturbation_config(
            config_path
        )
    )

    variables_config = (
        config.get(
            "variables",
            {},
        )
    )

    threshold = (
        config
        .get(
            "threshold",
            {},
        )
        .get(
            "minimum_spread_ratio",
            0.15,
        )
    )

    if confidence_profile is None:
        confidence_profile = (
            build_standard_confidence_profile(
                solar_applicable=(
                    base_case.solar_fraction > 0
                ),
                biomass_applicable=(
                    base_case.biomass_fraction > 0
                ),
            )
        )

    widened_params: Dict[
        str,
        Dict,
    ] = {}

    sourcing_audit: Dict[
        str,
        Dict,
    ] = {}

    for var_id, var_cfg in (
        variables_config.items()
    ):

        low = var_cfg["low"]
        base = var_cfg["base"]
        high = var_cfg["high"]

        widening_factor = (
            confidence_profile
            .widening_factor_for(
                var_id
            )
        )

        new_low, new_high = (
            _apply_widening(
                low=low,
                base=base,
                high=high,
                widening_factor=widening_factor,
            )
        )

        widened_params[var_id] = {
            "low": new_low,
            "base": base,
            "high": new_high,
            "original_low": low,
            "original_high": high,
            "widening_factor": widening_factor,
        }

        sourcing_audit[var_id] = {
            "source_status": var_cfg.get(
                "source_status",
                "unknown",
            ),
            "source_notes": var_cfg.get(
                "source_notes",
                "",
            ),
            "confidence_score": (
                confidence_profile
                .final_score_for(
                    var_id
                )
            ),
            "widening_factor": widening_factor,
            "effective_low": new_low,
            "effective_high": new_high,
        }

    oat_swings = (
        _one_at_a_time_swings(
            base_case=base_case,
            variables=variables_config,
            widened_params=widened_params,
        )
    )

    paybacks: List[float] = []

    non_viable_count = 0

    for _ in range(
        n_iterations
    ):

        factors = {}

        for var_id, params in (
            widened_params.items()
        ):

            sampled = (
                _triangular_sample(
                    low=params["low"],
                    base=params["base"],
                    high=params["high"],
                )
            )

            factors[var_id] = sampled

        pb = (
            _compute_perturbed_payback(
                base_case,
                factors,
            )
        )

        if pb is None or pb <= 0:
            non_viable_count += 1
        else:
            paybacks.append(
                pb
            )

    non_viable_rate = (
        non_viable_count
        / n_iterations
    )

    if non_viable_rate > 0.90:
        raise RuntimeError(
            "More than 90% of uncertainty "
            "samples produced non-viable savings. "
            "Check the base case and scenario economics."
        )

    if len(paybacks) < 10:
        raise RuntimeError(
            "Too few viable payback samples."
        )

    paybacks.sort()

    p10 = _percentile(
        paybacks,
        10,
    )

    p50 = _percentile(
        paybacks,
        50,
    )

    p90 = _percentile(
        paybacks,
        90,
    )

    spread_ratio = (
        (
            p90
            - p10
        )
        / p50
        if p50 > 0
        else 0.0
    )

    gate_passed = (
        spread_ratio
        >= threshold
    )

    unsourced_variables = [
        variable_id
        for variable_id, audit
        in sourcing_audit.items()
        if audit["source_status"]
        == "unsourced_assumption"
    ]

    return ReliabilitySweepResult(
        payback_p10=round(
            p10,
            4,
        ),
        payback_p50=round(
            p50,
            4,
        ),
        payback_p90=round(
            p90,
            4,
        ),
        spread_ratio=round(
            spread_ratio,
            4,
        ),
        raw_distribution=paybacks,
        oat_swings=oat_swings,
        n_iterations=n_iterations,
        gate_passed=gate_passed,
        metadata={
            "technology_id": base_case.technology_id,
            "scenario_id": base_case.scenario_id,
            "n_viable_samples": len(
                paybacks
            ),
            "non_viable_rate": round(
                non_viable_rate,
                4,
            ),
            "gate_threshold": threshold,
            "gate_passed": gate_passed,
            "spread_ratio": round(
                spread_ratio,
                4,
            ),
            "variables": sourcing_audit,
            "confidence_profile": (
                confidence_profile.to_metadata()
            ),
            "oat_swings": oat_swings,
            "unsourced_variables": (
                unsourced_variables
            ),
        },
    )


def run_best_expected_worst(
    base_case: BaseCaseInputs,
    *,
    best_factors: Dict[str, float],
    expected_factors: Dict[str, float],
    worst_factors: Dict[str, float],
) -> BestExpectedWorstResult:

    scenarios = []

    for label, factors in (
        (
            "Best case",
            best_factors,
        ),
        (
            "Expected",
            expected_factors,
        ),
        (
            "Worst case",
            worst_factors,
        ),
    ):

        payback = (
            _compute_perturbed_payback(
                base_case,
                factors,
            )
        )

        carbon_price = factors.get(
            "carbon_price",
            0.0,
        )

        carbon_cost, carbon_value = (
            _calculate_carbon_adjustment(
                base_case,
                carbon_price,
            )
        )

        scenario = (
            SensitivityScenario(
                label=label,
                factors=factors,
                payback_years=(
                    None
                    if payback is None
                    else round(
                        payback,
                        4,
                    )
                ),
                annual_savings_inr=None,
                annual_carbon_cost_inr=round(
                    carbon_cost,
                    2,
                ),
                annual_carbon_value_inr=round(
                    carbon_value,
                    2,
                ),
                viable=(
                    payback
                    is not None
                ),
            )
        )

        scenarios.append(
            scenario
        )

    best_case = scenarios[0]
    expected_case = scenarios[1]
    worst_case = scenarios[2]

    valid_paybacks = [
        scenario.payback_years
        for scenario in scenarios
        if scenario.payback_years
        is not None
    ]

    if valid_paybacks:
        low = min(
            valid_paybacks
        )
        high = max(
            valid_paybacks
        )
    else:
        low = None
        high = None

    tornado: Dict[
        str,
        float,
    ] = {}

    variable_names = sorted(
        set(best_factors)
        | set(expected_factors)
        | set(worst_factors)
    )

    for variable in variable_names:

        scenario_values = [
            factors.get(
                variable,
                1.0,
            )
            for factors in (
                best_factors,
                expected_factors,
                worst_factors,
            )
        ]

        # Convert factor excursion into a normalized indicator.
        # Payback sensitivity itself is separately represented by the MC/OAT
        # tornado and should be preferred for detailed rankings.
        tornado[variable] = round(
            max(scenario_values)
            - min(scenario_values),
            4,
        )

    dominant_factor = (
        max(
            tornado,
            key=tornado.get,
        )
        if tornado
        else None
    )

    return BestExpectedWorstResult(
        best_case=best_case,
        expected_case=expected_case,
        worst_case=worst_case,
        payback_range_years=(
            low,
            high,
        ),
        dominant_factor=dominant_factor,
        tornado=tornado,
        notes=[
            "Best / Expected / Worst are planning scenarios, not probabilities.",
            "P10/P50/P90 come from the Monte Carlo reliability sweep.",
            "Carbon price is a scenario input unless a verified applicable market price is supplied.",
            "Efficiency is represented as a relative multiplier around the base-case technology efficiency.",
        ],
    )
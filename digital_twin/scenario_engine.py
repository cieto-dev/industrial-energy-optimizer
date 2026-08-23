"""
Scenario Playground / Digital Twin economic scenario engine.

Task 3.7
--------
Allow the user to change:

- biomass price
- electricity tariff
- subsidy
- budget
- carbon price

and immediately recompute pathway economics and recommendation ranking.

This is an economic/decision digital twin for the MVP.
It is deliberately separate from the future IoT/telemetry digital twin.

The engine does NOT create new technical feasibility.
It adjusts the economics of already-generated feasible pathways and
passes them through the existing MCDA optimizer.

Design principles
-----------------
1. Never overwrite baseline assumptions.
2. Never bypass technical feasibility.
3. Never invent technical properties.
4. Keep scenario provenance explicit.
5. Re-run only the decision/economic layers after scenario changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from decision_engine.optimizer.mcda import ScenarioMetrics
from decision_engine.optimizer.optimization_engine import optimize


# ---------------------------------------------------------------------------
# Scenario contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioInputs:
    """
    User-controlled scenario variables.

    Units
    -----
    biomass_price_inr_per_kg:
        Delivered biomass fuel price in INR/kg.

    electricity_tariff_inr_per_kwh:
        Electricity tariff in INR/kWh.

    subsidy_pct:
        Direct subsidy applied to eligible CAPEX, represented as
        percentage in [0, 100].

    budget_inr:
        Maximum allowed gross CAPEX before subsidy.

    carbon_price_inr_per_tco2:
        Carbon price in INR per tonne CO2.
    """

    biomass_price_inr_per_kg: float
    electricity_tariff_inr_per_kwh: float
    subsidy_pct: float
    budget_inr: float
    carbon_price_inr_per_tco2: float

    def __post_init__(self) -> None:
        values = {
            "biomass_price_inr_per_kg": self.biomass_price_inr_per_kg,
            "electricity_tariff_inr_per_kwh": self.electricity_tariff_inr_per_kwh,
            "subsidy_pct": self.subsidy_pct,
            "budget_inr": self.budget_inr,
            "carbon_price_inr_per_tco2": self.carbon_price_inr_per_tco2,
        }

        for name, value in values.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric.")

            if value < 0:
                raise ValueError(f"{name} cannot be negative.")

        if self.subsidy_pct > 100:
            raise ValueError("subsidy_pct cannot exceed 100.")


@dataclass(frozen=True)
class PathwayScenarioBasis:
    """
    Economic/impact basis for one technically feasible pathway.

    These values are expected to come from existing technical + finance
    engines. This module does not fabricate technical data.

    Optional fields allow gradual integration with the current engine.
    """

    scenario_id: str
    technology_sequence: Sequence[str]

    # Existing baseline economics
    base_capex_inr: float
    base_annual_opex_inr: float

    # Optional decomposition for dynamic scenario pricing.
    base_biomass_kg_year: float = 0.0
    base_electricity_kwh_year: float = 0.0

    # Baseline CO2 for the scenario.
    annual_co2_tonnes: float = 0.0

    # Baseline feasibility state.
    feasible: bool = True

    # Existing MCDA fields.
    technical_score: Optional[float] = None
    financial_score: Optional[float] = None
    resource_score: Optional[float] = None
    policy_score: Optional[float] = None
    risk_score_value: Optional[float] = None
    technology_maturity: Optional[float] = None
    implementation_complexity: Optional[float] = None
    supply_reliability: Optional[float] = None
    electricity_dependence: Optional[float] = None
    biomass_dependence: Optional[float] = None
    carbon_reduction: Optional[float] = None
    confidence_score: Optional[float] = None

    spread_ratio: Optional[float] = None
    risk_tier: Optional[str] = None
    reliability_score_pct: Optional[float] = None

    # Preserve arbitrary upstream metadata.
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty.")

        if self.base_capex_inr < 0:
            raise ValueError("base_capex_inr cannot be negative.")

        if self.base_annual_opex_inr < 0:
            raise ValueError("base_annual_opex_inr cannot be negative.")

        if self.base_biomass_kg_year < 0:
            raise ValueError("base_biomass_kg_year cannot be negative.")

        if self.base_electricity_kwh_year < 0:
            raise ValueError("base_electricity_kwh_year cannot be negative.")

        if self.annual_co2_tonnes < 0:
            raise ValueError("annual_co2_tonnes cannot be negative.")


@dataclass(frozen=True)
class ScenarioEvaluation:
    scenario_id: str
    technology_sequence: List[str]

    gross_capex_inr: float
    subsidy_inr: float
    net_capex_inr: float

    annual_energy_cost_inr: float
    annual_carbon_cost_inr: float
    annual_total_cost_inr: float

    budget_inr: float
    within_budget: bool

    biomass_price_inr_per_kg: float
    electricity_tariff_inr_per_kwh: float
    subsidy_pct: float
    carbon_price_inr_per_tco2: float

    feasible: bool
    effective_feasible: bool

    carbon_cost_impact_inr_year: float
    price_sensitivity: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_metrics(self) -> ScenarioMetrics:
        """
        Convert scenario evaluation into the existing optimizer contract.

        Cost is passed as annual_total_cost_inr-adjusted OPEX, while CAPEX
        is passed net of subsidy.

        The optimizer can therefore re-score the scenario without knowing
        how the user changed the scenario inputs.
        """

        # We encode scenario economics into the existing fields.
        #
        # The annual cost becomes the primary OPEX signal.
        # Net CAPEX captures budget/subsidy impact.
        #
        # The rest of the technical fields remain untouched.
        metadata = dict(self.metadata)

        return ScenarioMetrics(
            scenario_id=self.scenario_id,
            technology_sequence=list(self.technology_sequence),

            capex_inr=self.net_capex_inr,
            annual_opex_inr=self.annual_total_cost_inr,
            pathway_co2_tonnes_year=self.metadata.get(
                "annual_co2_tonnes",
                0.0,
            ),

            co2_reduction_pct=self.metadata.get(
                "co2_reduction_pct",
                0.0,
            ),

            spread_ratio=self.metadata.get(
                "spread_ratio",
            ),

            risk_tier=self.metadata.get(
                "risk_tier",
            ),

            reliability_score_pct=self.metadata.get(
                "reliability_score_pct",
            ),

            technical_score=self.metadata.get(
                "technical_score",
            ),

            financial_score=self.metadata.get(
                "financial_score",
            ),

            resource_score=self.metadata.get(
                "resource_score",
            ),

            policy_score=self.metadata.get(
                "policy_score",
            ),

            risk_score_value=self.metadata.get(
                "risk_score_value",
            ),

            technology_maturity=self.metadata.get(
                "technology_maturity",
            ),

            implementation_complexity=self.metadata.get(
                "implementation_complexity",
            ),

            supply_reliability=self.metadata.get(
                "supply_reliability",
            ),

            electricity_dependence=self.metadata.get(
                "electricity_dependence",
            ),

            biomass_dependence=self.metadata.get(
                "biomass_dependence",
            ),

            carbon_reduction=self.metadata.get(
                "carbon_reduction",
            ),

            confidence_score=self.metadata.get(
                "confidence_score",
            ),

            financial={
                "gross_capex_inr": self.gross_capex_inr,
                "subsidy_inr": self.subsidy_inr,
                "net_capex_inr": self.net_capex_inr,
                "annual_energy_cost_inr": self.annual_energy_cost_inr,
                "annual_carbon_cost_inr": self.annual_carbon_cost_inr,
                "annual_total_cost_inr": self.annual_total_cost_inr,
            },

            emission={
                "annual_co2_tonnes": self.metadata.get(
                    "annual_co2_tonnes",
                    0.0,
                ),
                "carbon_price_inr_per_tco2": (
                    self.carbon_price_inr_per_tco2
                ),
                "annual_carbon_cost_inr": (
                    self.annual_carbon_cost_inr
                ),
            },

            risk_score={
                "within_budget": self.within_budget,
                "effective_feasible": self.effective_feasible,
            },

            extra={
                **metadata,
                "scenario_playground": True,
                "gross_capex_inr": self.gross_capex_inr,
                "subsidy_inr": self.subsidy_inr,
                "net_capex_inr": self.net_capex_inr,
                "annual_energy_cost_inr": self.annual_energy_cost_inr,
                "annual_carbon_cost_inr": self.annual_carbon_cost_inr,
                "annual_total_cost_inr": self.annual_total_cost_inr,
                "within_budget": self.within_budget,
            },
        )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


BIOMASS_TECHNOLOGY_TOKENS = {
    "biomass",
    "biomass_boiler",
    "biomass_boil",
    "biomass_fired",
    "biomass_heating",
    "biomass_heat",
    "biomass_steam",
    "pellet_boiler",
    "briquette_boiler",
    "multifuel_boiler",
}


ELECTRIC_TECHNOLOGY_TOKENS = {
    "electricity",
    "electrification",
    "electric_boiler",
    "heat_pump",
    "thermal_battery",
    "electric_resistance",
    "electric_resistance_equipment",
    "induction",
    "induction_furnace",
    "resistance_furnace",
    "electric_arc_furnace",
    "eaf",
    "plasma",
    "microwave",
    "radio_frequency",
    "rf_heater",
    "infrared",
    "electric_heat",
}


def _normalise_token(value: Any) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _technology_is_biomass(
    technologies: Iterable[str],
) -> bool:
    for technology in technologies:
        token = _normalise_token(technology)

        if token in BIOMASS_TECHNOLOGY_TOKENS:
            return True

        if "biomass" in token:
            return True

    return False


def _technology_is_electric(
    technologies: Iterable[str],
) -> bool:
    for technology in technologies:
        token = _normalise_token(technology)

        if token in ELECTRIC_TECHNOLOGY_TOKENS:
            return True

        if any(
            word in token
            for word in (
                "electric",
                "electrification",
                "heat_pump",
                "induction",
                "resistance_furnace",
                "thermal_battery",
                "plasma",
            )
        ):
            return True

    return False


def _subsidy_amount(
    gross_capex_inr: float,
    subsidy_pct: float,
) -> float:
    return gross_capex_inr * (subsidy_pct / 100.0)


def _dynamic_energy_cost(
    pathway: PathwayScenarioBasis,
    scenario: ScenarioInputs,
) -> float:
    """
    Estimate annual energy-cost contribution under the scenario.

    Only the cost-bearing dimensions supplied by the upstream pathway
    are recalculated.

    Biomass pathway:
        biomass_qty × biomass price

    Electric pathway:
        electricity_qty × electricity tariff

    Other technologies:
        preserve their baseline annual OPEX, because this layer must
        not invent a fuel quantity that upstream engineering did not supply.
    """

    technologies = pathway.technology_sequence

    is_biomass = _technology_is_biomass(technologies)
    is_electric = _technology_is_electric(technologies)

    dynamic_cost = 0.0

    if is_biomass and pathway.base_biomass_kg_year > 0:
        dynamic_cost += (
            pathway.base_biomass_kg_year
            * scenario.biomass_price_inr_per_kg
        )

    if is_electric and pathway.base_electricity_kwh_year > 0:
        dynamic_cost += (
            pathway.base_electricity_kwh_year
            * scenario.electricity_tariff_inr_per_kwh
        )

    # If no dynamic quantity is available, preserve existing annual OPEX.
    if dynamic_cost <= 0:
        return pathway.base_annual_opex_inr

    # Preserve non-energy OPEX by subtracting known baseline energy-cost
    # components when available.
    baseline_dynamic_cost = 0.0

    if is_biomass and pathway.base_biomass_kg_year > 0:
        # There is no baseline price stored inside PathwayScenarioBasis.
        # Therefore this engine intentionally treats the upstream
        # base_annual_opex as the residual baseline and uses the new
        # scenario energy cost as the principal signal.
        baseline_dynamic_cost = 0.0

    if is_electric and pathway.base_electricity_kwh_year > 0:
        baseline_dynamic_cost = 0.0

    residual_opex = max(
        0.0,
        pathway.base_annual_opex_inr - baseline_dynamic_cost,
    )

    return residual_opex + dynamic_cost


def _carbon_cost(
    annual_co2_tonnes: float,
    carbon_price_inr_per_tco2: float,
) -> float:
    return (
        annual_co2_tonnes
        * carbon_price_inr_per_tco2
    )


def _evaluate_pathway(
    pathway: PathwayScenarioBasis,
    scenario: ScenarioInputs,
) -> ScenarioEvaluation:
    gross_capex = pathway.base_capex_inr

    subsidy = _subsidy_amount(
        gross_capex_inr=gross_capex,
        subsidy_pct=scenario.subsidy_pct,
    )

    net_capex = max(
        0.0,
        gross_capex - subsidy,
    )

    energy_cost = _dynamic_energy_cost(
        pathway=pathway,
        scenario=scenario,
    )

    annual_carbon_cost = _carbon_cost(
        annual_co2_tonnes=pathway.annual_co2_tonnes,
        carbon_price_inr_per_tco2=scenario.carbon_price_inr_per_tco2,
    )

    total_annual_cost = (
        energy_cost
        + annual_carbon_cost
    )

    within_budget = (
        net_capex <= scenario.budget_inr
    )

    effective_feasible = (
        pathway.feasible
        and within_budget
    )

    is_biomass = _technology_is_biomass(
        pathway.technology_sequence,
    )

    is_electric = _technology_is_electric(
        pathway.technology_sequence,
    )

    metadata = {
        **pathway.extra,
        "annual_co2_tonnes": pathway.annual_co2_tonnes,
        "technical_score": pathway.technical_score,
        "financial_score": pathway.financial_score,
        "resource_score": pathway.resource_score,
        "policy_score": pathway.policy_score,
        "risk_score_value": pathway.risk_score_value,
        "technology_maturity": pathway.technology_maturity,
        "implementation_complexity": pathway.implementation_complexity,
        "supply_reliability": pathway.supply_reliability,
        "electricity_dependence": pathway.electricity_dependence,
        "biomass_dependence": pathway.biomass_dependence,
        "carbon_reduction": pathway.carbon_reduction,
        "confidence_score": pathway.confidence_score,
        "spread_ratio": pathway.spread_ratio,
        "risk_tier": pathway.risk_tier,
        "reliability_score_pct": pathway.reliability_score_pct,
        "co2_reduction_pct": pathway.extra.get(
            "co2_reduction_pct",
            0.0,
        ),
        "is_biomass": is_biomass,
        "is_electric": is_electric,
    }

    return ScenarioEvaluation(
        scenario_id=pathway.scenario_id,
        technology_sequence=list(
            pathway.technology_sequence,
        ),

        gross_capex_inr=gross_capex,
        subsidy_inr=subsidy,
        net_capex_inr=net_capex,

        annual_energy_cost_inr=energy_cost,
        annual_carbon_cost_inr=annual_carbon_cost,
        annual_total_cost_inr=total_annual_cost,

        budget_inr=scenario.budget_inr,
        within_budget=within_budget,

        biomass_price_inr_per_kg=(
            scenario.biomass_price_inr_per_kg
        ),

        electricity_tariff_inr_per_kwh=(
            scenario.electricity_tariff_inr_per_kwh
        ),

        subsidy_pct=scenario.subsidy_pct,

        carbon_price_inr_per_tco2=(
            scenario.carbon_price_inr_per_tco2
        ),

        feasible=pathway.feasible,
        effective_feasible=effective_feasible,

        carbon_cost_impact_inr_year=annual_carbon_cost,

        price_sensitivity={
            "biomass_exposed": is_biomass,
            "electricity_exposed": is_electric,
            "annual_biomass_qty_kg": (
                pathway.base_biomass_kg_year
            ),
            "annual_electricity_qty_kwh": (
                pathway.base_electricity_kwh_year
            ),
        },

        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------


class ScenarioPlaygroundEngine:
    """
    Recalculate and re-rank existing pathways for user-defined scenarios.

    The engine is stateless by design.

    That means the frontend can safely make many requests such as:

      tariff 8 -> 9 -> 10
      subsidy 10% -> 20% -> 30%
      carbon price 0 -> 5000 -> 10000

    without mutating the original optimization result.
    """

    def evaluate(
        self,
        pathways: Sequence[PathwayScenarioBasis],
        scenario: ScenarioInputs,
    ) -> List[ScenarioEvaluation]:
        return [
            _evaluate_pathway(
                pathway=pathway,
                scenario=scenario,
            )
            for pathway in pathways
        ]

    def rank(
        self,
        pathways: Sequence[PathwayScenarioBasis],
        scenario: ScenarioInputs,
        weights: Optional[Mapping[str, float]] = None,
    ) -> Dict[str, Any]:
        evaluations = self.evaluate(
            pathways=pathways,
            scenario=scenario,
        )

        feasible = [
            evaluation
            for evaluation in evaluations
            if evaluation.effective_feasible
        ]

        if len(feasible) < 2:
            return {
                "status": "no_valid_ranking",
                "scenario_inputs": {
                    "biomass_price_inr_per_kg":
                        scenario.biomass_price_inr_per_kg,
                    "electricity_tariff_inr_per_kwh":
                        scenario.electricity_tariff_inr_per_kwh,
                    "subsidy_pct":
                        scenario.subsidy_pct,
                    "budget_inr":
                        scenario.budget_inr,
                    "carbon_price_inr_per_tco2":
                        scenario.carbon_price_inr_per_tco2,
                },
                "evaluations": [
                    self._evaluation_to_dict(item)
                    for item in evaluations
                ],
                "message": (
                    "At least two technically feasible and "
                    "budget-feasible pathways are required "
                    "for ranking."
                ),
            }

        metrics = [
            evaluation.to_metrics()
            for evaluation in feasible
        ]

        optimization_result = optimize(
            candidates=metrics,
            weights=weights,
        )

        recommended_id = (
            optimization_result.recommended_scenario_id
        )

        recommended = next(
            item
            for item in evaluations
            if item.scenario_id == recommended_id
        )

        return {
            "status": "success",

            "scenario_inputs": {
                "biomass_price_inr_per_kg":
                    scenario.biomass_price_inr_per_kg,

                "electricity_tariff_inr_per_kwh":
                    scenario.electricity_tariff_inr_per_kwh,

                "subsidy_pct":
                    scenario.subsidy_pct,

                "budget_inr":
                    scenario.budget_inr,

                "carbon_price_inr_per_tco2":
                    scenario.carbon_price_inr_per_tco2,
            },

            "recommendation": {
                "scenario_id":
                    recommended.scenario_id,

                "technology_sequence":
                    recommended.technology_sequence,

                "net_capex_inr":
                    recommended.net_capex_inr,

                "annual_total_cost_inr":
                    recommended.annual_total_cost_inr,

                "annual_energy_cost_inr":
                    recommended.annual_energy_cost_inr,

                "annual_carbon_cost_inr":
                    recommended.annual_carbon_cost_inr,

                "within_budget":
                    recommended.within_budget,
            },

            "optimizer": optimization_result.to_dict(),

            "evaluations": [
                self._evaluation_to_dict(item)
                for item in evaluations
            ],

            "changes_that_matter": self._change_summary(
                evaluations,
                recommended_id,
            ),
        }

    def _evaluation_to_dict(
        self,
        evaluation: ScenarioEvaluation,
    ) -> Dict[str, Any]:
        return {
            "scenario_id": evaluation.scenario_id,
            "technology_sequence": evaluation.technology_sequence,
            "gross_capex_inr": evaluation.gross_capex_inr,
            "subsidy_inr": evaluation.subsidy_inr,
            "net_capex_inr": evaluation.net_capex_inr,
            "annual_energy_cost_inr": evaluation.annual_energy_cost_inr,
            "annual_carbon_cost_inr": evaluation.annual_carbon_cost_inr,
            "annual_total_cost_inr": evaluation.annual_total_cost_inr,
            "budget_inr": evaluation.budget_inr,
            "within_budget": evaluation.within_budget,
            "feasible": evaluation.feasible,
            "effective_feasible": evaluation.effective_feasible,
            "biomass_price_inr_per_kg": (
                evaluation.biomass_price_inr_per_kg
            ),
            "electricity_tariff_inr_per_kwh": (
                evaluation.electricity_tariff_inr_per_kwh
            ),
            "subsidy_pct": evaluation.subsidy_pct,
            "carbon_price_inr_per_tco2": (
                evaluation.carbon_price_inr_per_tco2
            ),
            "price_sensitivity": evaluation.price_sensitivity,
            "metadata": evaluation.metadata,
        }

    def _change_summary(
        self,
        evaluations: Sequence[ScenarioEvaluation],
        recommended_id: str,
    ) -> Dict[str, Any]:
        """
        Provide dashboard-friendly signals explaining why scenario changes
        may have moved the ranking.
        """

        recommended = next(
            item
            for item in evaluations
            if item.scenario_id == recommended_id
        )

        signals: List[str] = []

        if recommended.price_sensitivity.get(
            "biomass_exposed"
        ):
            signals.append(
                "Recommendation economics are sensitive to biomass price."
            )

        if recommended.price_sensitivity.get(
            "electricity_exposed"
        ):
            signals.append(
                "Recommendation economics are sensitive to electricity tariff."
            )

        if recommended.subsidy_pct > 0:
            signals.append(
                "Subsidy reduces the upfront capital burden of this pathway."
            )

        if recommended.annual_carbon_cost_inr > 0:
            signals.append(
                "Carbon price increases the operating burden of higher-emission pathways."
            )

        if not signals:
            signals.append(
                "The current recommendation is comparatively insensitive "
                "to the selected economic scenario variables."
            )

        return {
            "recommended_pathway": recommended_id,
            "signals": signals,
        }


__all__ = [
    "ScenarioInputs",
    "PathwayScenarioBasis",
    "ScenarioEvaluation",
    "ScenarioPlaygroundEngine",
]
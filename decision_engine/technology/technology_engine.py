"""
Technology Engine
=================

Engineering-layer calculations for industrial heat technologies.

Current supported technology engines:
    - Biogas
    - Biomass boiler

Design goals:
    - Preserve the existing biogas behaviour.
    - Add biomass support without requiring pipeline/optimizer changes.
    - Keep calculations deterministic and explainable.
    - Read technology/emission assumptions from the repository knowledge base.
    - Return pathway-compatible dictionaries that downstream modules can consume.

This module is intentionally rule-based. It does not perform optimization or ranking.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

EMISSION_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "emissions"
    / "emission_factors.json"
)

TECHNOLOGY_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)

FUEL_RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "fuel.json"
)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON knowledge-base file.

    Raises:
        FileNotFoundError:
            If the expected knowledge-base file does not exist.

        ValueError:
            If the file cannot be decoded as JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge-base file not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in knowledge-base file: {file_path}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object in knowledge-base file: {file_path}"
        )

    return data


def _normalise_text(value: Any) -> str:
    """Return a normalized lower-case string."""
    return str(value).strip().lower()


def _validate_positive(value: float, field_name: str) -> None:
    """Validate that a numeric input is strictly positive."""
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")


def _validate_efficiency(efficiency: float) -> None:
    """Validate an efficiency expressed as a decimal fraction."""
    if not 0 < efficiency <= 1:
        raise ValueError("Efficiency must be between 0 and 1.")


def _first_numeric(
    mapping: Mapping[str, Any],
    keys: Iterable[str],
    default: Optional[float] = None,
) -> Optional[float]:
    """
    Return the first numeric value found among the supplied keys.

    This helper lets the engine tolerate minor schema differences in the
    knowledge base without changing the public output contract.
    """
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, (int, float)):
            return float(value)

    return default


def _find_emission_factor(
    factors: Mapping[str, Any],
    technology_or_fuel: str,
) -> Optional[float]:
    """
    Resolve an emission factor from the emission-factor knowledge base.

    The repository may store factors under slightly different field names,
    therefore several common patterns are supported.

    Returns:
        A numeric factor if one can be resolved, otherwise None.
    """
    key = _normalise_text(technology_or_fuel)

    direct = factors.get(key)
    if isinstance(direct, (int, float)):
        return float(direct)

    if isinstance(direct, Mapping):
        factor = _first_numeric(
            direct,
            (
                "emission_factor",
                "factor",
                "co2_factor",
                "kg_co2_per_unit",
                "kg_co2_per_mj",
                "kg_co2_per_kwh",
            ),
        )
        if factor is not None:
            return factor

    # Some repositories use a nested "fuels" structure.
    for container_name in ("fuels", "emission_factors", "factors"):
        container = factors.get(container_name)
        if not isinstance(container, Mapping):
            continue

        candidate = container.get(key)
        if isinstance(candidate, (int, float)):
            return float(candidate)

        if isinstance(candidate, Mapping):
            factor = _first_numeric(
                candidate,
                (
                    "emission_factor",
                    "factor",
                    "co2_factor",
                    "kg_co2_per_unit",
                    "kg_co2_per_mj",
                    "kg_co2_per_kwh",
                ),
            )
            if factor is not None:
                return factor

    return None


# ---------------------------------------------------------------------------
# Existing Biogas functionality
# ---------------------------------------------------------------------------

def load_emission_factors() -> Dict[str, Any]:
    """Load the repository emission-factor knowledge base."""
    return load_json(EMISSION_FILE)


def calculate_biogas(
    heat_demand_kwh_day: float,
    efficiency: float = 0.80,
) -> Dict[str, Any]:
    """
    Calculate biogas consumption required for a given daily useful heat demand.

    Args:
        heat_demand_kwh_day:
            Useful process heat demand in kWh/day.

        efficiency:
            Boiler/system efficiency as a decimal.
            Example: 0.80 = 80%.

    Returns:
        Dictionary containing the calculated biogas requirement.

    Notes:
        This preserves the original engine's calculation method and output
        fields so existing biogas callers remain compatible.
    """
    _validate_positive(heat_demand_kwh_day, "Heat demand")
    _validate_efficiency(efficiency)

    factors = load_emission_factors()

    biogas = factors.get("biogas")
    if not isinstance(biogas, Mapping):
        raise KeyError(
            "Emission-factor knowledge base does not contain a valid "
            "'biogas' entry."
        )

    ncv_mj_m3 = _first_numeric(
        biogas,
        (
            "ncv",
            "ncv_mj_m3",
            "net_calorific_value_mj_m3",
        ),
    )

    if ncv_mj_m3 is None or ncv_mj_m3 <= 0:
        raise ValueError(
            "Biogas NCV is missing or invalid in emission_factors.json."
        )

    # Convert useful heat from kWh/day to MJ/day.
    heat_demand_mj_day = heat_demand_kwh_day * 3.6

    # Required fuel energy.
    fuel_energy_mj_day = heat_demand_mj_day / efficiency

    # Biogas volume required.
    biogas_m3_day = fuel_energy_mj_day / ncv_mj_m3

    return {
        "technology": "biogas",
        "heat_demand_kwh_day": heat_demand_kwh_day,
        "heat_demand_mj_day": round(heat_demand_mj_day, 2),
        "efficiency": efficiency,
        "efficiency_percent": round(efficiency * 100, 2),
        "biogas_ncv_mj_m3": ncv_mj_m3,
        "biogas_required_m3_day": round(biogas_m3_day, 2),
        "feasible": True,
    }


# ---------------------------------------------------------------------------
# Biomass Engine
# ---------------------------------------------------------------------------

class BiomassEngine:
    """
    Engineering calculator for biomass-fired industrial heat.

    The engine models biomass primarily as a thermal/steam replacement
    pathway. It intentionally stops at engineering quantities and does not
    rank biomass against other technologies.

    Supported concepts:
        - useful heat demand
        - process temperature feasibility
        - boiler efficiency
        - biomass NCV
        - daily biomass fuel requirement
        - annual biomass requirement
        - optional delivered biomass cost
        - optional CO2 estimate
        - biomass availability checks
        - technical feasibility / rejection reasons

    The uploaded MNRE/GIZ biomass report emphasizes:
        - biomass for green heat and steam,
        - agricultural residues/pellets/briquettes,
        - supply-chain reliability,
        - multi-fuel capability,
        - application across several MSME sectors.

    Those ideas are represented here as engineering/constraint fields, not
    as an optimization score.
    """

    TECHNOLOGY_NAME = "biomass_boiler"

    # Default engineering assumptions are conservative fallbacks. The caller
    # can override them with explicit values, and repository knowledge-base
    # values are used whenever the schema provides them.
    DEFAULT_EFFICIENCY = 0.80
    DEFAULT_NCV_MJ_KG = 15.0
    DEFAULT_MAX_TEMPERATURE_C = 1000.0

    def __init__(
        self,
        technology_rules_file: Path = TECHNOLOGY_RULES_FILE,
        emission_file: Path = EMISSION_FILE,
    ) -> None:
        self.technology_rules_file = technology_rules_file
        self.emission_file = emission_file

        self.technology_rules = load_json(self.technology_rules_file)
        self.emission_factors = load_json(self.emission_file)

    # ------------------------------------------------------------------
    # Knowledge-base access
    # ------------------------------------------------------------------

    def get_rules(self) -> Dict[str, Any]:
        """Return biomass boiler rules from the knowledge base."""
        rules = self.technology_rules.get(self.TECHNOLOGY_NAME, {})

        if not isinstance(rules, Mapping):
            raise ValueError(
                f"Invalid rules for technology '{self.TECHNOLOGY_NAME}'."
            )

        return dict(rules)

    def get_biomass_defaults(self) -> Dict[str, float]:
        """
        Resolve biomass engineering defaults.

        The repository currently stores the biomass eligibility structure in
        technology_rules.json rather than a dedicated biomass-properties JSON.
        Therefore the engine checks emission_factors.json for an explicit
        biomass NCV first, then falls back to a documented engineering default.
        """
        biomass_factor = self.emission_factors.get("biomass", {})

        if isinstance(biomass_factor, Mapping):
            ncv = _first_numeric(
                biomass_factor,
                (
                    "ncv_mj_kg",
                    "ncv",
                    "net_calorific_value_mj_kg",
                    "calorific_value_mj_kg",
                ),
            )
            max_temperature = _first_numeric(
                biomass_factor,
                (
                    "maximum_process_temperature_c",
                    "max_temperature_c",
                    "temperature_limit_c",
                ),
            )
            efficiency = _first_numeric(
                biomass_factor,
                (
                    "efficiency",
                    "default_efficiency",
                    "boiler_efficiency",
                ),
            )
        else:
            ncv = None
            max_temperature = None
            efficiency = None

        rules = self.get_rules()

        if max_temperature is None:
            max_temperature = _first_numeric(
                rules,
                (
                    "maximum_process_temperature_c",
                    "max_temperature_c",
                ),
            )

        return {
            "efficiency": (
                efficiency
                if efficiency is not None and 0 < efficiency <= 1
                else self.DEFAULT_EFFICIENCY
            ),
            "ncv_mj_kg": (
                ncv
                if ncv is not None and ncv > 0
                else self.DEFAULT_NCV_MJ_KG
            ),
            "maximum_process_temperature_c": (
                max_temperature
                if max_temperature is not None and max_temperature > 0
                else self.DEFAULT_MAX_TEMPERATURE_C
            ),
        }

    # ------------------------------------------------------------------
    # Applicability / feasibility
    # ------------------------------------------------------------------

    def can_replace_fuel(self, fuel: str) -> bool:
        """
        Check whether biomass is allowed to replace the supplied fuel.

        Uses the repository technology_rules.json definition rather than
        hard-coding the replacement list.
        """
        normalized_fuel = _normalise_text(fuel)
        rules = self.get_rules()

        replaces_fuels = rules.get("replaces_fuels", [])
        if not isinstance(replaces_fuels, list):
            return False

        normalized_replacements = {
            _normalise_text(item) for item in replaces_fuels
        }

        return normalized_fuel in normalized_replacements

    def is_industry_allowed(self, industry: Optional[str]) -> bool:
        """
        Check whether the industry is allowed by technology_rules.json.

        If no industry is supplied, the check is intentionally skipped.
        """
        if industry is None:
            return True

        normalized_industry = _normalise_text(industry)
        rules = self.get_rules()

        allowed_industries = rules.get("allowed_industries", [])
        if not isinstance(allowed_industries, list):
            return True

        normalized_industries = {
            _normalise_text(item) for item in allowed_industries
        }

        return normalized_industry in normalized_industries

    def check_feasibility(
        self,
        heat_demand_kwh_day: float,
        process_temperature_c: float,
        industry: Optional[str] = None,
        current_fuel: Optional[str] = None,
        biomass_available: bool = True,
        biomass_supply_reliable: bool = True,
        required_biomass_kg_day: Optional[float] = None,
        available_biomass_kg_day: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate technical biomass feasibility.

        Returns:
            {
                "feasible": bool,
                "reasons": [...],
                "checks": {...}
            }
        """
        _validate_positive(heat_demand_kwh_day, "Heat demand")

        if process_temperature_c < 0:
            raise ValueError(
                "Process temperature cannot be negative."
            )

        defaults = self.get_biomass_defaults()

        reasons = []
        checks: Dict[str, Any] = {}

        temperature_ok = (
            process_temperature_c
            <= defaults["maximum_process_temperature_c"]
        )
        checks["temperature_ok"] = temperature_ok

        if not temperature_ok:
            reasons.append(
                "Required process temperature exceeds the biomass boiler "
                "temperature capability."
            )

        industry_ok = self.is_industry_allowed(industry)
        checks["industry_ok"] = industry_ok

        if industry is not None and not industry_ok:
            reasons.append(
                f"Industry '{industry}' is not listed as an allowed "
                "biomass-boiler industry in the technology rules."
            )

        fuel_ok = True
        if current_fuel is not None:
            fuel_ok = self.can_replace_fuel(current_fuel)

        checks["fuel_replacement_ok"] = fuel_ok

        if current_fuel is not None and not fuel_ok:
            reasons.append(
                f"Biomass boiler is not configured to replace current "
                f"fuel '{current_fuel}'."
            )

        checks["biomass_available"] = bool(biomass_available)

        if not biomass_available:
            reasons.append(
                "Biomass supply is not available for the proposed site."
            )

        checks["biomass_supply_reliable"] = bool(
            biomass_supply_reliable
        )

        if not biomass_supply_reliable:
            reasons.append(
                "Biomass supply is not sufficiently reliable for the "
                "required operating profile."
            )

        quantity_ok = True

        if (
            required_biomass_kg_day is not None
            and available_biomass_kg_day is not None
        ):
            quantity_ok = (
                available_biomass_kg_day >= required_biomass_kg_day
            )

            if not quantity_ok:
                reasons.append(
                    "Available biomass quantity is lower than the "
                    "calculated daily requirement."
                )

        checks["biomass_quantity_ok"] = quantity_ok

        return {
            "feasible": len(reasons) == 0,
            "reasons": reasons,
            "checks": checks,
        }

    # ------------------------------------------------------------------
    # Engineering calculations
    # ------------------------------------------------------------------

    def calculate_biomass_requirement(
        self,
        heat_demand_kwh_day: float,
        efficiency: Optional[float] = None,
        ncv_mj_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate biomass required to provide useful heat.

        Formula:
            useful_heat_MJ_day = heat_demand_kWh_day × 3.6

            fuel_energy_MJ_day =
                useful_heat_MJ_day / efficiency

            biomass_kg_day =
                fuel_energy_MJ_day / NCV_MJ_per_kg
        """
        _validate_positive(heat_demand_kwh_day, "Heat demand")

        defaults = self.get_biomass_defaults()

        resolved_efficiency = (
            efficiency
            if efficiency is not None
            else defaults["efficiency"]
        )

        resolved_ncv = (
            ncv_mj_kg
            if ncv_mj_kg is not None
            else defaults["ncv_mj_kg"]
        )

        _validate_efficiency(resolved_efficiency)
        _validate_positive(resolved_ncv, "Biomass NCV")

        heat_demand_mj_day = heat_demand_kwh_day * 3.6
        fuel_energy_mj_day = heat_demand_mj_day / resolved_efficiency
        biomass_kg_day = fuel_energy_mj_day / resolved_ncv
        biomass_tonnes_day = biomass_kg_day / 1000.0
        biomass_tonnes_year = biomass_tonnes_day * 365.0

        return {
            "heat_demand_kwh_day": round(
                heat_demand_kwh_day,
                2,
            ),
            "heat_demand_mj_day": round(
                heat_demand_mj_day,
                2,
            ),
            "efficiency": round(
                resolved_efficiency,
                4,
            ),
            "efficiency_percent": round(
                resolved_efficiency * 100,
                2,
            ),
            "biomass_ncv_mj_kg": round(
                resolved_ncv,
                4,
            ),
            "required_fuel_energy_mj_day": round(
                fuel_energy_mj_day,
                2,
            ),
            "biomass_required_kg_day": round(
                biomass_kg_day,
                2,
            ),
            "biomass_required_tonnes_day": round(
                biomass_tonnes_day,
                4,
            ),
            "biomass_required_tonnes_year": round(
                biomass_tonnes_year,
                2,
            ),
        }

    def calculate_cost(
        self,
        biomass_kg_day: float,
        biomass_price_inr_per_kg: Optional[float] = None,
        operating_days_per_year: float = 365,
    ) -> Dict[str, Any]:
        """
        Calculate annual biomass fuel cost when a delivered price is supplied.

        The delivered-cost concept is important for biomass because logistics
        and supply-chain factors materially affect economics.

        If no price is provided, the returned cost fields are None rather than
        inventing a repository value.
        """
        _validate_positive(biomass_kg_day, "Biomass requirement")
        _validate_positive(operating_days_per_year, "Operating days")

        if biomass_price_inr_per_kg is None:
            return {
                "biomass_price_inr_per_kg": None,
                "annual_biomass_cost_inr": None,
                "cost_available": False,
            }

        _validate_positive(
            biomass_price_inr_per_kg,
            "Biomass price",
        )

        annual_biomass_kg = (
            biomass_kg_day * operating_days_per_year
        )

        annual_cost = (
            annual_biomass_kg
            * biomass_price_inr_per_kg
        )

        return {
            "biomass_price_inr_per_kg": round(
                biomass_price_inr_per_kg,
                4,
            ),
            "annual_biomass_cost_inr": round(
                annual_cost,
                2,
            ),
            "cost_available": True,
        }

    def calculate_co2(
        self,
        biomass_kg_day: float,
        operating_days_per_year: float = 365,
        biomass_emission_factor_kg_co2_per_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate an annual direct CO2 estimate when an explicit emission
        factor is supplied or available in the knowledge base.

        Important:
            Biomass lifecycle accounting is more nuanced than simply applying
            a combustion factor. This method therefore does NOT invent a
            carbon-neutral factor. It only calculates a value when an explicit
            factor is available.
        """
        _validate_positive(biomass_kg_day, "Biomass requirement")
        _validate_positive(operating_days_per_year, "Operating days")

        factor = biomass_emission_factor_kg_co2_per_kg

        if factor is None:
            factor = _find_emission_factor(
                self.emission_factors,
                "biomass",
            )

        if factor is None:
            return {
                "biomass_emission_factor_kg_co2_per_kg": None,
                "annual_biomass_co2_kg": None,
                "annual_biomass_co2_tonnes": None,
                "co2_available": False,
            }

        if factor < 0:
            raise ValueError(
                "Biomass emission factor cannot be negative."
            )

        annual_biomass_kg = (
            biomass_kg_day * operating_days_per_year
        )

        annual_co2_kg = annual_biomass_kg * factor
        annual_co2_tonnes = annual_co2_kg / 1000.0

        return {
            "biomass_emission_factor_kg_co2_per_kg": round(
                factor,
                6,
            ),
            "annual_biomass_co2_kg": round(
                annual_co2_kg,
                2,
            ),
            "annual_biomass_co2_tonnes": round(
                annual_co2_tonnes,
                4,
            ),
            "co2_available": True,
        }

    # ------------------------------------------------------------------
    # Public technology calculation
    # ------------------------------------------------------------------

    def calculate(
        self,
        heat_demand_kwh_day: float,
        process_temperature_c: float,
        industry: Optional[str] = None,
        current_fuel: Optional[str] = None,
        efficiency: Optional[float] = None,
        biomass_ncv_mj_kg: Optional[float] = None,
        biomass_available: bool = True,
        biomass_supply_reliable: bool = True,
        available_biomass_kg_day: Optional[float] = None,
        biomass_price_inr_per_kg: Optional[float] = None,
        operating_days_per_year: float = 365,
        biomass_emission_factor_kg_co2_per_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Perform the complete biomass technical evaluation.

        This is the primary public BiomassEngine API.

        Returns a stable dictionary containing:
            - technology identity
            - technical assumptions
            - calculated biomass use
            - optional economics
            - optional emissions
            - feasibility
            - explainable reasons/checks
        """
        _validate_positive(heat_demand_kwh_day, "Heat demand")

        defaults = self.get_biomass_defaults()

        resolved_efficiency = (
            efficiency
            if efficiency is not None
            else defaults["efficiency"]
        )

        resolved_ncv = (
            biomass_ncv_mj_kg
            if biomass_ncv_mj_kg is not None
            else defaults["ncv_mj_kg"]
        )

        engineering = self.calculate_biomass_requirement(
            heat_demand_kwh_day=heat_demand_kwh_day,
            efficiency=resolved_efficiency,
            ncv_mj_kg=resolved_ncv,
        )

        feasibility = self.check_feasibility(
            heat_demand_kwh_day=heat_demand_kwh_day,
            process_temperature_c=process_temperature_c,
            industry=industry,
            current_fuel=current_fuel,
            biomass_available=biomass_available,
            biomass_supply_reliable=biomass_supply_reliable,
            required_biomass_kg_day=engineering[
                "biomass_required_kg_day"
            ],
            available_biomass_kg_day=available_biomass_kg_day,
        )

        cost = self.calculate_cost(
            biomass_kg_day=engineering[
                "biomass_required_kg_day"
            ],
            biomass_price_inr_per_kg=biomass_price_inr_per_kg,
            operating_days_per_year=operating_days_per_year,
        )

        emissions = self.calculate_co2(
            biomass_kg_day=engineering[
                "biomass_required_kg_day"
            ],
            operating_days_per_year=operating_days_per_year,
            biomass_emission_factor_kg_co2_per_kg=(
                biomass_emission_factor_kg_co2_per_kg
            ),
        )

        rules = self.get_rules()

        result: Dict[str, Any] = {
            "technology": self.TECHNOLOGY_NAME,
            "technology_type": "biomass_thermal",
            "process_temperature_c": round(
                process_temperature_c,
                2,
            ),
            "industry": industry,
            "current_fuel": current_fuel,
            "efficiency": engineering["efficiency"],
            "efficiency_percent": engineering[
                "efficiency_percent"
            ],
            "biomass_ncv_mj_kg": engineering[
                "biomass_ncv_mj_kg"
            ],
            "biomass_required_kg_day": engineering[
                "biomass_required_kg_day"
            ],
            "biomass_required_tonnes_day": engineering[
                "biomass_required_tonnes_day"
            ],
            "biomass_required_tonnes_year": engineering[
                "biomass_required_tonnes_year"
            ],
            "required_fuel_energy_mj_day": engineering[
                "required_fuel_energy_mj_day"
            ],
            "annual_biomass_cost_inr": cost[
                "annual_biomass_cost_inr"
            ],
            "biomass_price_inr_per_kg": cost[
                "biomass_price_inr_per_kg"
            ],
            "annual_biomass_co2_kg": emissions[
                "annual_biomass_co2_kg"
            ],
            "annual_biomass_co2_tonnes": emissions[
                "annual_biomass_co2_tonnes"
            ],
            "feasible": feasibility["feasible"],
            "feasibility_checks": feasibility["checks"],
            "rejection_reasons": feasibility["reasons"],
            "temperature_capability_c": defaults[
                "maximum_process_temperature_c"
            ],
            "requires_biomass_supply": rules.get(
                "requires_biomass_supply",
                True,
            ),
            "continuous_operation_required": rules.get(
                "continuous_operation_required",
                False,
            ),
            "retrofit_supported": rules.get(
                "retrofit_supported",
                False,
            ),
            "compatible_with": list(
                rules.get("compatible_with", [])
            ),
            "evidence_flags": [
                "biomass_supply_reliability_is_a_technical_constraint",
                "delivered_biomass_cost_should_include_logistics",
                "emission_result_requires_explicit_factor",
            ],
        }

        # Add a compact provenance payload so downstream modules can explain
        # where the technical assumptions came from.
        result["knowledge_base"] = {
            "technology_rules_file": str(
                self.technology_rules_file.relative_to(BASE_DIR)
            ),
            "emission_factors_file": str(
                self.emission_file.relative_to(BASE_DIR)
            ),
        }

        return result


# ---------------------------------------------------------------------------
# Backward-compatible convenience API
# ---------------------------------------------------------------------------

def calculate_biomass(
    heat_demand_kwh_day: float,
    process_temperature_c: float = 250.0,
    industry: Optional[str] = None,
    current_fuel: Optional[str] = None,
    efficiency: Optional[float] = None,
    biomass_ncv_mj_kg: Optional[float] = None,
    biomass_available: bool = True,
    biomass_supply_reliable: bool = True,
    available_biomass_kg_day: Optional[float] = None,
    biomass_price_inr_per_kg: Optional[float] = None,
    operating_days_per_year: float = 365,
) -> Dict[str, Any]:
    """
    Convenience wrapper around BiomassEngine.

    This is useful for simple callers and tests that prefer a function API.
    """
    engine = BiomassEngine()

    return engine.calculate(
        heat_demand_kwh_day=heat_demand_kwh_day,
        process_temperature_c=process_temperature_c,
        industry=industry,
        current_fuel=current_fuel,
        efficiency=efficiency,
        biomass_ncv_mj_kg=biomass_ncv_mj_kg,
        biomass_available=biomass_available,
        biomass_supply_reliable=biomass_supply_reliable,
        available_biomass_kg_day=available_biomass_kg_day,
        biomass_price_inr_per_kg=biomass_price_inr_per_kg,
        operating_days_per_year=operating_days_per_year,
    )


# ---------------------------------------------------------------------------
# Combined technology helper
# ---------------------------------------------------------------------------

def calculate_technology(
    technology: str,
    heat_demand_kwh_day: float,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generic dispatcher for supported technology calculations.

    Supported:
        - biogas
        - biomass
        - biomass_boiler
    """
    normalized = _normalise_text(technology)

    if normalized == "biogas":
        return calculate_biogas(
            heat_demand_kwh_day=heat_demand_kwh_day,
            efficiency=kwargs.get("efficiency", 0.80),
        )

    if normalized in {
        "biomass",
        "biomass_boiler",
    }:
        return calculate_biomass(
            heat_demand_kwh_day=heat_demand_kwh_day,
            process_temperature_c=kwargs.get(
                "process_temperature_c",
                250.0,
            ),
            industry=kwargs.get("industry"),
            current_fuel=kwargs.get("current_fuel"),
            efficiency=kwargs.get("efficiency"),
            biomass_ncv_mj_kg=kwargs.get(
                "biomass_ncv_mj_kg"
            ),
            biomass_available=kwargs.get(
                "biomass_available",
                True,
            ),
            biomass_supply_reliable=kwargs.get(
                "biomass_supply_reliable",
                True,
            ),
            available_biomass_kg_day=kwargs.get(
                "available_biomass_kg_day"
            ),
            biomass_price_inr_per_kg=kwargs.get(
                "biomass_price_inr_per_kg"
            ),
            operating_days_per_year=kwargs.get(
                "operating_days_per_year",
                365,
            ),
        )

    raise ValueError(
        f"Unsupported technology: {technology}"
    )


# ---------------------------------------------------------------------------
# Simple manual test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Technology Engine")
    print("=================")

    print("\nBiogas example")
    biogas_result = calculate_biogas(
        heat_demand_kwh_day=10000,
        efficiency=0.80,
    )

    for key, value in biogas_result.items():
        print(f"{key}: {value}")

    print("\nBiomass example")
    biomass_result = calculate_biomass(
        heat_demand_kwh_day=10000,
        process_temperature_c=250,
        industry="textile",
        current_fuel="coal",
        biomass_available=True,
        biomass_supply_reliable=True,
        biomass_price_inr_per_kg=8.0,
    )

    for key, value in biomass_result.items():
        print(f"{key}: {value}")
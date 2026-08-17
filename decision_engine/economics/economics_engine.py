from dataclasses import dataclass, asdict

from .capex import (
    calculate_capex,
    get_technology_data
)

from .opex import (
    calculate_annual_opex,
    calculate_annual_savings
)

from .payback import calculate_payback

from .roi import calculate_roi


@dataclass
class FinancialModel:
    """
    Complete financial result for one technology scenario.
    """

    technology_id: str

    capex_min: float | None
    capex_max: float | None
    capex_estimate: float | None

    baseline_annual_opex: float
    proposed_annual_opex: float

    annual_savings: float

    payback_min_years: float | None
    payback_max_years: float | None

    roi_min_percent: float | None
    roi_max_percent: float | None

    lifetime_years: float | None

    financially_viable: bool

    def to_dict(self):
        return asdict(self)


def get_lifetime(technology_id):
    """
    Read technology lifetime from technology_costs.json.
    """

    technology = get_technology_data(
        technology_id
    )

    parameters = technology.get(
        "parameters",
        {}
    )

    lifetime = parameters.get(
        "lifetime"
    )

    if not lifetime:
        return None

    value = lifetime.get(
        "value"
    )

    if value is None:
        return None

    return float(value)


def calculate_economics(
    technology_id,
    baseline_annual_opex,
    proposed_opex,
    capacity=None,
    usd_to_inr=None
):
    """
    Calculate complete financial model
    for one technology scenario.
    """

    # ==================================================
    # 1. CAPEX
    # ==================================================

    capex = calculate_capex(
        technology_id=technology_id,
        capacity=capacity,
        usd_to_inr=usd_to_inr
    )

    # ==================================================
    # 2. PROPOSED OPEX
    # ==================================================

    proposed_opex_result = (
        calculate_annual_opex(
            fuel_cost=proposed_opex.get(
                "fuel_cost", 0
            ),
            electricity_cost=proposed_opex.get(
                "electricity_cost", 0
            ),
            maintenance_cost=proposed_opex.get(
                "maintenance_cost", 0
            ),
            labour_cost=proposed_opex.get(
                "labour_cost", 0
            ),
            other_cost=proposed_opex.get(
                "other_cost", 0
            )
        )
    )

    proposed_annual_opex = (
        proposed_opex_result[
            "annual_opex"
        ]
    )

    # ==================================================
    # 3. ANNUAL SAVINGS
    # ==================================================

    annual_savings = (
        calculate_annual_savings(
            baseline_annual_opex=(
                baseline_annual_opex
            ),
            proposed_annual_opex=(
                proposed_annual_opex
            )
        )
    )

    # ==================================================
    # 4. LIFETIME
    # ==================================================

    lifetime_years = get_lifetime(
        technology_id
    )

    # ==================================================
    # 5. PAYBACK
    # ==================================================

    payback = calculate_payback(
        capex_min=capex["capex_min"],
        capex_max=capex["capex_max"],
        annual_savings=annual_savings
    )

    # ==================================================
    # 6. ROI
    # ==================================================

    roi = calculate_roi(
        capex_min=capex["capex_min"],
        capex_max=capex["capex_max"],
        annual_savings=annual_savings,
        lifetime_years=lifetime_years
    )

    # ==================================================
    # 7. FINANCIAL VIABILITY
    # ==================================================

    financially_viable = False

    if (
        annual_savings > 0
        and payback["payback_min_years"] is not None
        and lifetime_years is not None
    ):

        financially_viable = (
            payback["payback_min_years"]
            <= lifetime_years
        )

    # ==================================================
    # 8. FINAL FINANCIAL MODEL
    # ==================================================

    return FinancialModel(

        technology_id=technology_id,

        capex_min=capex["capex_min"],
        capex_max=capex["capex_max"],
        capex_estimate=capex["capex_estimate"],

        baseline_annual_opex=(
            baseline_annual_opex
        ),

        proposed_annual_opex=(
            proposed_annual_opex
        ),

        annual_savings=annual_savings,

        payback_min_years=(
            payback["payback_min_years"]
        ),

        payback_max_years=(
            payback["payback_max_years"]
        ),

        roi_min_percent=(
            roi["roi_min_percent"]
        ),

        roi_max_percent=(
            roi["roi_max_percent"]
        ),

        lifetime_years=lifetime_years,

        financially_viable=(
            financially_viable
        )
    )
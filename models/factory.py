from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SpecialCategory(BaseModel):
    women_owned: bool = False
    sc_st_owned: bool = False
    pwd_owned: bool = False
    agniveer_owned: bool = False
    transgender_owned: bool = False
    north_east_region: bool = False
    jammu_kashmir: bool = False
    ladakh: bool = False
    aspirational_district: bool = False
    identified_credit_deficient_district: bool = False


class Quantity(BaseModel):
    value: float = Field(ge=0)
    unit: str


class Factory(BaseModel):
    """
    Factory / MSME Profile / Digital Twin baseline.

    The current-state baseline is immutable once computed.
    Pathways are evaluated against this baseline rather than
    mutating it.
    """

    factory_id: str
    name: str

    # Location / industry
    industry: str
    state: str
    district: str

    # Production and energy baseline
    production_per_day: Quantity
    operating_hours_per_day: float = Field(gt=0)
    operating_days_per_year: int = Field(default=300, ge=1, le=366)
    current_fuel: str
    fuel_consumption: Quantity
    electricity_consumption_kwh_day: float = Field(ge=0)
    required_process_temperature_c: float = Field(ge=0)

    # Site / financial constraints
    roof_area_sqm: float = Field(ge=0)
    available_land_sqm: float | None = Field(default=None, ge=0)
    budget_inr: float = Field(ge=0)
    grid_reliability_pct: float = Field(ge=0, le=100)

    # MSME identity
    msme_classification: Literal["micro", "small", "medium"]
    udyam_registered: bool
    udyam_number: str | None = None

    # Module 4a — policy / eligibility
    annual_turnover_inr: float = Field(ge=0)
    plant_and_machinery_or_equipment_investment_inr: float = Field(ge=0)

    project_type: Literal[
        "energy_efficiency",
        "electrification",
        "renewable_energy",
        "alternative_fuel",
        "biomass",
        "waste_heat_recovery",
        "energy_storage",
        "waste_management",
        "circular_economy",
        "clean_transport",
        "pollution_control",
        "green_infrastructure",
        "other",
    ]

    project_cost_inr: float = Field(ge=0)
    loan_amount_inr: float | None = Field(default=None, ge=0)

    existing_or_new_project: Literal["existing", "new"]

    brownfield_or_greenfield: (
        Literal["brownfield", "greenfield", "not_applicable"] | None
    ) = None

    cluster_name: str | None = None
    cluster_is_adeetie_identified: bool | None = None
    annual_energy_savings_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    special_category: SpecialCategory | None = None


# Backward-compatible alias
FactoryProfile = Factory
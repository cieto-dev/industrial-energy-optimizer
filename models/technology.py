"""
Technology Domain Model.

Represents an industrial energy-transition technology and the technical,
economic, environmental, and deployment information required by the
decision engine.

Maps to docs/DOMAIN_MODEL.md §3.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Technology(BaseModel):
    """
    Industrial energy-transition technology.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    technology_id: str = Field(
        ...,
        description="Canonical unique technology identifier.",
    )

    input_energy_form: str = Field(
        ...,
        description="Energy or fuel input required by the technology.",
    )

    output_energy_form: str = Field(
        ...,
        description="Useful energy form delivered by the technology.",
    )

    suitable_industries: list[str] = Field(
        ...,
        description="Industry IDs for which the technology is applicable.",
    )

    temperature_range_c: tuple[float, float] = Field(
        ...,
        description="Technology useful output-temperature range [min_C, max_C].",
    )

    capex_inr_range: tuple[float, float] = Field(
        ...,
        description="Expected capital-expenditure range [minimum_INR, maximum_INR].",
    )

    opex_inr_per_unit: float = Field(
        ...,
        ge=0,
        description="Operating expenditure per applicable output unit.",
    )

    efficiency_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Technology conversion efficiency percentage.",
    )

    capacity_range: tuple[float, float] = Field(
        ...,
        description="Supported technology capacity range [minimum, maximum].",
    )

    capacity_unit: str = Field(
        ...,
        description="Unit for capacity_range, e.g. kW, MW, kWth, MWth.",
    )

    lifetime_years: float = Field(
        ...,
        gt=0,
        description="Expected useful operating lifetime in years.",
    )

    emission_factor: float = Field(
        ...,
        ge=0,
        description="Technology emission factor in the applicable unit.",
    )

    local_availability_dependent: bool = Field(
        ...,
        description="Whether feasibility depends on local technology/fuel availability.",
    )

    constraints: list[str] = Field(
        ...,
        description="Technical, operational, site, or deployment constraints.",
    )

    source_citation: str = Field(
        ...,
        description="Source supporting the technology data.",
    )

    @model_validator(mode="after")
    def validate_ranges(self) -> "Technology":
        min_temperature, max_temperature = self.temperature_range_c

        if min_temperature < 0:
            raise ValueError(
                "temperature_range_c cannot contain a negative value."
            )

        if min_temperature > max_temperature:
            raise ValueError(
                "temperature_range_c minimum cannot exceed maximum."
            )

        min_capex, max_capex = self.capex_inr_range

        if min_capex < 0 or max_capex < 0:
            raise ValueError(
                "capex_inr_range cannot contain negative values."
            )

        if min_capex > max_capex:
            raise ValueError(
                "capex_inr_range minimum cannot exceed maximum."
            )

        min_capacity, max_capacity = self.capacity_range

        if min_capacity < 0 or max_capacity < 0:
            raise ValueError(
                "capacity_range cannot contain negative values."
            )

        if min_capacity > max_capacity:
            raise ValueError(
                "capacity_range minimum cannot exceed maximum."
            )

        return self


# Compatibility aliases
TechnologyOption = Technology
TechnologyProfile = Technology
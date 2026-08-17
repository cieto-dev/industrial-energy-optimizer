"""
Industry Domain Model.

Sector-level defaults, temperature ranges, energy splits, and applicable
technologies.

One Factory belongs to one Industry.

Maps to docs/DOMAIN_MODEL.md §2.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EnergySplit(BaseModel):
    """Energy split breakdown between electricity and thermal heat."""

    electricity_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of electricity consumption.",
    )

    thermal_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of thermal/heat consumption.",
    )

    @model_validator(mode="after")
    def validate_total(self) -> "EnergySplit":
        total = self.electricity_pct + self.thermal_pct

        if abs(total - 100.0) > 0.01:
            raise ValueError(
                "electricity_pct + thermal_pct must sum to 100%"
            )

        return self


class Industry(BaseModel):
    """
    Sector-level defaults and constraints.

    One Factory belongs to one Industry.
    """

    industry_id: str = Field(
        ...,
        description=(
            "Unique sector identifier, e.g. textile, food_processing, "
            "cement, steel, chemical, pharma."
        ),
    )

    typical_temperature_range_c: tuple[float, float] = Field(
        ...,
        description="Typical operating temperature range [min_C, max_C].",
    )

    typical_energy_split: EnergySplit = Field(
        ...,
        description="Benchmark electricity versus thermal energy split.",
    )

    applicable_technologies: list[str] = Field(
        ...,
        description="Technology IDs applicable to this industry.",
    )

    sub_process: str = Field(
        ...,
        description=(
            "Specific industrial subprocess, e.g. "
            "'dyeing / wet-processing' for textile."
        ),
    )

    @model_validator(mode="after")
    def validate_temperature_range(self) -> "Industry":
        minimum, maximum = self.typical_temperature_range_c

        if minimum < 0:
            raise ValueError(
                "Temperature range cannot contain a negative value."
            )

        if minimum > maximum:
            raise ValueError(
                "typical_temperature_range_c minimum cannot exceed maximum."
            )

        return self


# Compatibility alias
IndustrySector = Industry
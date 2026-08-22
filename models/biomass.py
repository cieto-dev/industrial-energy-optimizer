"""
models/biomass.py

Domain models for Unit 2.2
Biomass Intelligence Engine.

These models are intentionally independent from the optimizer.
They describe biomass resources and the assessment generated
by decision_engine/biomass/biomass_engine.py.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BiomassResource(BaseModel):
    """
    Raw biomass resource from the Biomass Atlas dataset.
    """

    state: str = Field(..., description="Indian state")
    district: str = Field(..., description="District")

    biomass_type: str = Field(
        ...,
        description="Residue type (Rice Husk, Bagasse, Cotton Stalk...)",
    )

    crop: str = Field(
        ...,
        description="Associated crop",
    )

    annual_availability_tons: float = Field(
        ...,
        ge=0,
        description="Annual surplus biomass availability (tons/year)",
    )

    availability_type: str = Field(
        ...,
        description="Availability category from Atlas",
    )

    year: str = Field(
        ...,
        description="Atlas reference year",
    )

    moisture_percent: float = Field(
        ...,
        ge=0,
        le=100,
    )

    calorific_value_mj_kg: float = Field(
        ...,
        ge=0,
    )

    cost_rs_per_ton: float = Field(
        ...,
        ge=0,
    )

    latitude: float

    longitude: float

    source: str


class BiomassAssessment(BaseModel):
    """
    Output of the Biomass Intelligence Engine.
    """

    biomass_type: str

    crop: str

    state: str

    district: str

    annual_availability_tons: float

    availability_level: str

    residue_match_score: float

    moisture_percent: float

    calorific_value_mj_kg: float

    effective_calorific_value_mj_kg: float

    transport_distance_km: Optional[float]

    transport_cost_inr_per_ton: float

    delivered_cost_inr_per_ton: float

    seasonality_level: str

    seasonality_score: float

    supply_reliability_score: float

    biomass_risk_index: float

    suitability_score: float

    recommendation: str

    reasons: List[str] = Field(
        default_factory=list,
        description="Positive recommendation reasons",
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Important user warnings",
    )

    source: str


class BiomassSummary(BaseModel):
    """
    Compact biomass result for API responses.
    """

    available: bool

    recommended_biomass: Optional[str] = None

    recommended_crop: Optional[str] = None

    availability: Optional[str] = None

    seasonality: Optional[str] = None

    supply_risk: Optional[str] = None

    energy_value: Optional[str] = None

    recommendation: Optional[str] = None

    suitability_score: Optional[float] = None

    delivered_cost_inr_per_ton: Optional[float] = None

    transport_distance_km: Optional[float] = None


class BiomassResult(BaseModel):
    """
    Complete output returned by Unit 2.2.
    """

    available: bool

    state: str

    district: str

    message: Optional[str] = None

    summary: Optional[BiomassSummary] = None

    top_assessment: Optional[BiomassAssessment] = None

    recommendations: List[BiomassAssessment] = Field(
        default_factory=list,
    )

    engine: dict = Field(
        default_factory=dict,
    )
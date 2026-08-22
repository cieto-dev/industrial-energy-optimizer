
"""
Biomass Intelligence Engine
===========================

Unit 2.2 of the Industrial Energy Transition Optimizer.

Purpose
-------
Convert district-level biomass resource data into a transparent,
explainable biomass suitability assessment.

The engine answers:

    "Is biomass a dependable and economically reasonable fuel
     option for this factory, and which residue should be preferred?"

It does NOT:
- mutate the Factory model
- perform final pathway optimization
- make policy/subsidy decisions
- use ML/LLMs
- assume biomass availability is simply True/False

Inputs
------
- factory state + district
- optional preferred biomass type / crop
- factory useful heat demand
- optional transport assumptions
- biomass atlas dataset

Outputs
-------
A ranked list of biomass options containing:
- district availability
- residue match
- seasonality
- supply reliability
- transport distance
- moisture
- effective calorific value
- delivered cost estimate
- suitability score
- biomass risk index
- recommendation status

Source basis
------------
National Biomass Atlas:
    SSS-NIBE / MNRE / ASCI study

MSME biomass context:
    MNRE + GIZ + Grant Thornton Bharat,
    "Decarbonizing MSMEs: Use of Biomass for Green Steam
     and Heat Applications"

Project architecture:
    docs/DOMAIN_MODEL.md
    Master Source
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any, Iterable, Optional

import csv


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_ATLAS_PATH = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "biomass_atlas.csv"
)

# The uploaded Atlas has historical 2015–18 data.
# We therefore make the age penalty explicit rather than pretending
# the Atlas is a live inventory.
ATLAS_REFERENCE_START_YEAR = 2015
ATLAS_REFERENCE_END_YEAR = 2018

# Screening assumptions.
#
# These are engineering/model assumptions, NOT claims from MNRE.
# They are deliberately centralized so they can be replaced later
# with validated project assumptions.
DEFAULT_MAX_DISTANCE_KM = 150.0
DEFAULT_TRANSPORT_COST_INR_PER_TON_KM = 1.50

# Moisture reference for screening. 10% is used only as a neutral
# reference point for relative correction.
REFERENCE_MOISTURE_PCT = 10.0

# A simple screening correction:
#
# effective_LHV = atlas_LHV * (1 - moisture_penalty)
#
# The penalty is capped to avoid producing nonsensical values.
MOISTURE_PENALTY_PER_PCT_ABOVE_REFERENCE = 0.015
MAX_MOISTURE_PENALTY = 0.45

# Reliability is not claimed as an observed statistic because the Atlas
# does not provide actual historical delivery-failure data.
# It is estimated transparently from availability, moisture, seasonality
# proxy and dataset age.
#
# These weights sum to 1.
RELIABILITY_WEIGHTS = {
    "availability": 0.45,
    "quality": 0.20,
    "seasonality": 0.20,
    "data_freshness": 0.15,
}

# Suitability score weights.
#
# The engine must remain explainable. Each weight corresponds directly
# to a visible decision criterion.
SUITABILITY_WEIGHTS = {
    "availability": 0.20,
    "residue_match": 0.10,
    "seasonality": 0.10,
    "supply_reliability": 0.15,
    "transport": 0.10,
    "moisture_quality": 0.10,
    "calorific_value": 0.10,
    "cost": 0.10,
    "risk": 0.05,
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BiomassRecord:
    state: str
    district: str
    biomass_type: str
    crop: str
    annual_availability_tons: float
    availability_type: str
    year: str
    moisture_percent: float
    calorific_value_mj_kg: float
    cost_rs_per_ton: float
    latitude: float
    longitude: float
    source: str


@dataclass(frozen=True)
class BiomassAssessment:
    biomass_type: str
    crop: str
    state: str
    district: str

    # Resource indicators
    annual_availability_tons: float
    availability_level: str
    residue_match_score: float

    # Fuel quality
    moisture_percent: float
    calorific_value_mj_kg: float
    effective_calorific_value_mj_kg: float

    # Logistics
    transport_distance_km: float
    transport_cost_inr_per_ton: float
    delivered_cost_inr_per_ton: float

    # Risk / reliability
    seasonality_level: str
    seasonality_score: float
    supply_reliability_score: float
    biomass_risk_index: float

    # Overall suitability
    suitability_score: float
    recommendation: str

    # Explainability
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    source: str


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _normalise_text(value: str) -> str:
    """Normalize user/data text for comparison."""
    return " ".join(str(value).strip().lower().split())


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _safe_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid numeric value for '{field_name}': {value!r}"
        ) from exc

    if number < 0:
        raise ValueError(
            f"'{field_name}' cannot be negative: {number}"
        )

    return number


def _availability_score(annual_tons: float) -> float:
    """
    Convert annual surplus availability into a transparent screening score.

    Thresholds are model assumptions for MVP screening, not official
    MNRE availability classifications.
    """
    if annual_tons <= 0:
        return 0.0
    if annual_tons < 25_000:
        return 0.25
    if annual_tons < 75_000:
        return 0.50
    if annual_tons < 150_000:
        return 0.75
    return 1.0


def _availability_level(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.50:
        return "Medium"
    if score > 0:
        return "Low"
    return "Unavailable"


def _seasonality_from_biomass_type(biomass_type: str) -> tuple[str, float]:
    """
    Conservative MVP seasonality proxy.

    The uploaded Atlas itself records annual availability but not monthly
    collection calendars. Therefore the engine must not pretend that
    monthly seasonality is measured by the Atlas.

    Instead, the engine classifies common residue families as a screening
    proxy and clearly reports the limitation in warnings.
    """
    biomass = _normalise_text(biomass_type)

    if "bagasse" in biomass:
        return "High", 0.55

    if "straw" in biomass:
        return "Medium", 0.70

    if "husk" in biomass:
        return "Medium", 0.75

    if "residue" in biomass:
        return "Medium", 0.70

    return "Medium", 0.65


def _moisture_score(moisture_pct: float) -> float:
    """
    Screen fuel quality using moisture.

    Lower moisture is better for combustion performance.
    """
    if moisture_pct <= 10:
        return 1.0
    if moisture_pct <= 15:
        return 0.90
    if moisture_pct <= 20:
        return 0.75
    if moisture_pct <= 30:
        return 0.50
    if moisture_pct <= 40:
        return 0.25
    return 0.10


def _moisture_corrected_lhv(
    calorific_value_mj_kg: float,
    moisture_pct: float,
) -> float:
    """
    Calculate a transparent screening-adjusted LHV.

    This is NOT a laboratory proximate/ultimate-analysis replacement.
    It is an MVP correction used to prevent wet residues from receiving
    the same energy value as dry residues.
    """
    excess_moisture = max(0.0, moisture_pct - REFERENCE_MOISTURE_PCT)

    penalty = min(
        excess_moisture * MOISTURE_PENALTY_PER_PCT_ABOVE_REFERENCE,
        MAX_MOISTURE_PENALTY,
    )

    corrected = calorific_value_mj_kg * (1.0 - penalty)

    return max(0.1, corrected)


def _calorific_score(lhv_mj_kg: float) -> float:
    """
    Screen energy quality using LHV.

    These bins are model screening assumptions.
    """
    if lhv_mj_kg >= 15:
        return 1.0
    if lhv_mj_kg >= 14:
        return 0.90
    if lhv_mj_kg >= 13:
        return 0.80
    if lhv_mj_kg >= 12:
        return 0.70
    if lhv_mj_kg >= 10:
        return 0.50
    if lhv_mj_kg >= 8:
        return 0.30
    return 0.15


def _transport_score(distance_km: float) -> float:
    if distance_km <= 25:
        return 1.0
    if distance_km <= 50:
        return 0.90
    if distance_km <= 75:
        return 0.75
    if distance_km <= 100:
        return 0.60
    if distance_km <= 150:
        return 0.40
    if distance_km <= 200:
        return 0.20
    return 0.05


def _cost_score(delivered_cost_inr_per_ton: float) -> float:
    """
    Relative cost score.

    This is intentionally monotonic rather than pretending that one
    national biomass price is universally correct.
    """
    if delivered_cost_inr_per_ton <= 2000:
        return 1.0
    if delivered_cost_inr_per_ton <= 2500:
        return 0.85
    if delivered_cost_inr_per_ton <= 3000:
        return 0.70
    if delivered_cost_inr_per_ton <= 3500:
        return 0.55
    if delivered_cost_inr_per_ton <= 4000:
        return 0.40
    if delivered_cost_inr_per_ton <= 5000:
        return 0.20
    return 0.05


def _risk_level(risk_index: float) -> str:
    """
    Lower risk index is better.
    """
    if risk_index < 0.25:
        return "Low"
    if risk_index < 0.50:
        return "Moderate"
    if risk_index < 0.75:
        return "High"
    return "Very High"


def _risk_score_from_index(risk_index: float) -> float:
    """
    Convert risk index into benefit score where 1 = low risk.
    """
    return _clamp(1.0 - risk_index)


def _distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Haversine great-circle distance.

    This is a geographic straight-line estimate, not road distance.
    The output is intentionally labelled as screening distance.
    """
    radius_km = 6371.0

    phi1 = radians(lat1)
    phi2 = radians(lat2)

    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = (
        sin(delta_phi / 2) ** 2
        + cos(phi1)
        * cos(phi2)
        * sin(delta_lambda / 2) ** 2
    )

    return radius_km * 2 * asin(sqrt(a))


def _parse_year_end(year_value: str) -> int:
    """
    Parse strings such as '2015–18' safely.
    """
    text = str(year_value).replace("–", "-").replace("—", "-")
    pieces = text.split("-")

    if not pieces:
        return ATLAS_REFERENCE_END_YEAR

    try:
        first = int(pieces[0].strip())
    except ValueError:
        return ATLAS_REFERENCE_END_YEAR

    if len(pieces) == 1:
        return first

    try:
        second = pieces[1].strip()
        if len(second) == 2:
            return (first // 100) * 100 + int(second)
        return int(second)
    except ValueError:
        return ATLAS_REFERENCE_END_YEAR


def _data_freshness_score(year_value: str) -> float:
    """
    The current Atlas is historical (2015–18).

    This score makes the uncertainty visible rather than hidden.
    """
    year_end = _parse_year_end(year_value)

    if year_end >= 2024:
        return 1.0
    if year_end >= 2022:
        return 0.90
    if year_end >= 2020:
        return 0.75
    if year_end >= 2018:
        return 0.55
    if year_end >= 2015:
        return 0.40
    return 0.25


def _parse_record(row: dict[str, str]) -> BiomassRecord:
    """
    Convert CSV row into typed BiomassRecord.
    """
    return BiomassRecord(
        state=row["state"].strip(),
        district=row["district"].strip(),
        biomass_type=row["biomass_type"].strip(),
        crop=row["crop"].strip(),
        annual_availability_tons=_safe_float(
            row["annual_availability_tons"],
            "annual_availability_tons",
        ),
        availability_type=row["availability_type"].strip(),
        year=row["year"].strip(),
        moisture_percent=_safe_float(
            row["moisture_percent"],
            "moisture_percent",
        ),
        calorific_value_mj_kg=_safe_float(
            row["calorific_value_mj_kg"],
            "calorific_value_mj_kg",
        ),
        cost_rs_per_ton=_safe_float(
            row["cost_rs_per_ton"],
            "cost_rs_per_ton",
        ),
        latitude=_safe_float(row["latitude"], "latitude"),
        longitude=_safe_float(row["longitude"], "longitude"),
        source=row["source"].strip(),
    )


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def load_biomass_atlas(
    csv_path: str | Path = DEFAULT_ATLAS_PATH,
) -> list[BiomassRecord]:
    """
    Load the project's Biomass Atlas dataset.

    The CSV must contain the existing project's schema.
    """
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Biomass Atlas dataset not found: {path}"
        )

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        required_columns = {
            "state",
            "district",
            "biomass_type",
            "crop",
            "annual_availability_tons",
            "availability_type",
            "year",
            "moisture_percent",
            "calorific_value_mj_kg",
            "cost_rs_per_ton",
            "latitude",
            "longitude",
            "source",
        }

        actual_columns = set(reader.fieldnames or [])
        missing = required_columns - actual_columns

        if missing:
            raise ValueError(
                "Biomass Atlas is missing required columns: "
                + ", ".join(sorted(missing))
            )

        records = [_parse_record(row) for row in reader]

    if not records:
        raise ValueError("Biomass Atlas contains no records.")

    return records


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------


def _district_matches(
    record: BiomassRecord,
    state: str,
    district: str,
) -> bool:
    return (
        _normalise_text(record.state) == _normalise_text(state)
        and _normalise_text(record.district) == _normalise_text(district)
    )


def _residue_match_score(
    record: BiomassRecord,
    preferred_biomass_type: Optional[str],
    preferred_crop: Optional[str],
) -> float:
    """
    Score how closely a record matches a user's preference.

    1.0 = exact biomass type and crop
    0.85 = exact biomass type
    0.70 = exact crop
    0.50 = no preference
    """
    if preferred_biomass_type and _normalise_text(
        record.biomass_type
    ) == _normalise_text(preferred_biomass_type):
        if preferred_crop and _normalise_text(record.crop) == _normalise_text(
            preferred_crop
        ):
            return 1.0
        return 0.85

    if preferred_crop and _normalise_text(record.crop) == _normalise_text(
        preferred_crop
    ):
        return 0.70

    return 0.50


def _relative_availability_score(
    annual_tons: float,
    district_records: Iterable[BiomassRecord],
) -> float:
    """
    Score an individual residue against other resources in the same
    district, while retaining the absolute availability score.

    This prevents a residue with modest absolute volume from being
    automatically treated as poor when it is actually one of the best
    available options locally.
    """
    records = list(district_records)

    max_availability = max(
        (record.annual_availability_tons for record in records),
        default=annual_tons,
    )

    if max_availability <= 0:
        return 0.0

    return _clamp(annual_tons / max_availability)


# ---------------------------------------------------------------------------
# Core assessment
# ---------------------------------------------------------------------------


def assess_biomass(
    *,
    state: str,
    district: str,
    factory_latitude: Optional[float] = None,
    factory_longitude: Optional[float] = None,
    preferred_biomass_type: Optional[str] = None,
    preferred_crop: Optional[str] = None,
    atlas_records: Optional[list[BiomassRecord]] = None,
    max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    transport_cost_inr_per_ton_km: float = (
        DEFAULT_TRANSPORT_COST_INR_PER_TON_KM
    ),
) -> list[BiomassAssessment]:
    """
    Assess all biomass resources in the factory's district.

    Parameters
    ----------
    state:
        Factory state.
    district:
        Factory district.

    factory_latitude / factory_longitude:
        Optional factory location. If omitted, transport distance is
        reported as unavailable and receives a conservative score.

    preferred_biomass_type:
        Optional preferred residue, e.g. "Rice Husk".

    preferred_crop:
        Optional preferred crop, e.g. "Rice".

    atlas_records:
        Optional preloaded records to avoid repeated file reads.

    max_distance_km:
        Screening cutoff for local sourcing.

    transport_cost_inr_per_ton_km:
        Explicit MVP transport-cost assumption.
    """
    if not state or not district:
        raise ValueError("Both state and district are required.")

    if factory_latitude is not None and not (-90 <= factory_latitude <= 90):
        raise ValueError("factory_latitude must be between -90 and 90.")

    if factory_longitude is not None and not (-180 <= factory_longitude <= 180):
        raise ValueError("factory_longitude must be between -180 and 180.")

    if max_distance_km <= 0:
        raise ValueError("max_distance_km must be greater than zero.")

    if transport_cost_inr_per_ton_km < 0:
        raise ValueError(
            "transport_cost_inr_per_ton_km cannot be negative."
        )

    records = atlas_records or load_biomass_atlas()

    district_records = [
        record
        for record in records
        if _district_matches(record, state, district)
    ]

    if not district_records:
        return []

    assessments: list[BiomassAssessment] = []

    for record in district_records:
        availability_abs = _availability_score(
            record.annual_availability_tons
        )

        availability_relative = _relative_availability_score(
            record.annual_availability_tons,
            district_records,
        )

        # Blend absolute and local-relative availability.
        availability_score = (
            0.65 * availability_abs
            + 0.35 * availability_relative
        )

        availability_level = _availability_level(availability_score)

        residue_match = _residue_match_score(
            record,
            preferred_biomass_type,
            preferred_crop,
        )

        seasonality_level, seasonality_score = _seasonality_from_biomass_type(
            record.biomass_type
        )

        moisture_score = _moisture_score(
            record.moisture_percent
        )

        effective_lhv = _moisture_corrected_lhv(
            record.calorific_value_mj_kg,
            record.moisture_percent,
        )

        lhv_score = _calorific_score(effective_lhv)

        freshness_score = _data_freshness_score(record.year)

        if (
            factory_latitude is not None
            and factory_longitude is not None
        ):
            distance_km = _distance_km(
                factory_latitude,
                factory_longitude,
                record.latitude,
                record.longitude,
            )

            transport_score = _transport_score(distance_km)

        else:
            distance_km = float("nan")
            transport_score = 0.40

        transport_cost = (
            0.0
            if distance_km != distance_km
            else distance_km * transport_cost_inr_per_ton_km
        )

        delivered_cost = (
            record.cost_rs_per_ton
            + transport_cost
        )

        cost_score = _cost_score(delivered_cost)

        quality_score = (
            0.60 * moisture_score
            + 0.40 * lhv_score
        )

        reliability_score = (
            RELIABILITY_WEIGHTS["availability"]
            * availability_score
            + RELIABILITY_WEIGHTS["quality"]
            * quality_score
            + RELIABILITY_WEIGHTS["seasonality"]
            * seasonality_score
            + RELIABILITY_WEIGHTS["data_freshness"]
            * freshness_score
        )

        # Risk is deliberately derived from visible reliability drivers.
        risk_index = _clamp(
            1.0 - reliability_score
        )

        # Distance beyond screening range adds explicit risk.
        if distance_km == distance_km and distance_km > max_distance_km:
            excess_distance_fraction = (
                distance_km - max_distance_km
            ) / max_distance_km

            risk_index = _clamp(
                risk_index
                + min(0.30, excess_distance_fraction * 0.15)
            )

        risk_score = _risk_score_from_index(risk_index)

        suitability_score = (
            SUITABILITY_WEIGHTS["availability"]
            * availability_score
            + SUITABILITY_WEIGHTS["residue_match"]
            * residue_match
            + SUITABILITY_WEIGHTS["seasonality"]
            * seasonality_score
            + SUITABILITY_WEIGHTS["supply_reliability"]
            * reliability_score
            + SUITABILITY_WEIGHTS["transport"]
            * transport_score
            + SUITABILITY_WEIGHTS["moisture_quality"]
            * moisture_score
            + SUITABILITY_WEIGHTS["calorific_value"]
            * lhv_score
            + SUITABILITY_WEIGHTS["cost"]
            * cost_score
            + SUITABILITY_WEIGHTS["risk"]
            * risk_score
        )

        warnings: list[str] = []
        reasons: list[str] = []

        if availability_level == "High":
            reasons.append(
                "High district-level surplus availability."
            )
        elif availability_level == "Medium":
            reasons.append(
                "Moderate district-level surplus availability."
            )
        else:
            warnings.append(
                "District availability is not strong enough for a "
                "high-confidence supply decision."
            )

        if seasonality_level == "High":
            warnings.append(
                "Residue family has a stronger seasonal-supply dependency."
            )

        if record.moisture_percent > 20:
            warnings.append(
                "High moisture can reduce useful energy value and "
                "increase handling/combustion challenges."
            )

        if effective_lhv < 10:
            warnings.append(
                "Moisture-corrected calorific value is relatively low."
            )

        if distance_km == distance_km:
            if distance_km <= 50:
                reasons.append(
                    "Biomass source is within a relatively short "
                    "screening distance."
                )
            elif distance_km <= max_distance_km:
                reasons.append(
                    "Biomass remains within the configured local-sourcing "
                    "screening radius."
                )
            else:
                warnings.append(
                    "Source exceeds the configured local-sourcing "
                    "screening radius."
                )
        else:
            warnings.append(
                "Factory coordinates were not supplied, so transport "
                "distance is only a provisional score."
            )

        if delivered_cost <= 3000:
            reasons.append(
                "Screened delivered biomass cost is within the "
                "engine's favourable range."
            )
        else:
            warnings.append(
                "Delivered cost is relatively high under the current "
                "transport assumption."
            )

        if risk_index < 0.25:
            recommendation = "Recommended"
        elif risk_index < 0.50 and suitability_score >= 0.60:
            recommendation = "Conditionally Recommended"
        elif suitability_score >= 0.55:
            recommendation = "Review"
        else:
            recommendation = "Not Recommended"

        # Historical-data warning is mandatory for the current Atlas.
        if freshness_score < 0.60:
            warnings.append(
                "Atlas data is historical; verify current local supply "
                "before investment."
            )

        warnings.append(
            "Atlas availability is a planning indicator, not a guaranteed "
            "commercial supply contract."
        )

        if not reasons:
            reasons.append(
                "No strong positive suitability signal identified."
            )

        assessments.append(
            BiomassAssessment(
                biomass_type=record.biomass_type,
                crop=record.crop,
                state=record.state,
                district=record.district,
                annual_availability_tons=record.annual_availability_tons,
                availability_level=availability_level,
                residue_match_score=round(residue_match, 4),
                moisture_percent=round(record.moisture_percent, 2),
                calorific_value_mj_kg=round(
                    record.calorific_value_mj_kg,
                    3,
                ),
                effective_calorific_value_mj_kg=round(
                    effective_lhv,
                    3,
                ),
                transport_distance_km=(
                    round(distance_km, 2)
                    if distance_km == distance_km
                    else float("nan")
                ),
                transport_cost_inr_per_ton=round(
                    transport_cost,
                    2,
                ),
                delivered_cost_inr_per_ton=round(
                    delivered_cost,
                    2,
                ),
                seasonality_level=seasonality_level,
                seasonality_score=round(
                    seasonality_score,
                    4,
                ),
                supply_reliability_score=round(
                    reliability_score,
                    4,
                ),
                biomass_risk_index=round(
                    risk_index,
                    4,
                ),
                suitability_score=round(
                    suitability_score,
                    4,
                ),
                recommendation=recommendation,
                reasons=tuple(reasons),
                warnings=tuple(warnings),
                source=record.source,
            )
        )

    # Best option first.
    assessments.sort(
        key=lambda item: (
            -item.suitability_score,
            item.biomass_risk_index,
            item.delivered_cost_inr_per_ton,
        )
    )

    return assessments


# ---------------------------------------------------------------------------
# Factory integration
# ---------------------------------------------------------------------------


def assess_factory_biomass(
    factory: Any,
    *,
    factory_latitude: Optional[float] = None,
    factory_longitude: Optional[float] = None,
    preferred_biomass_type: Optional[str] = None,
    preferred_crop: Optional[str] = None,
    atlas_records: Optional[list[BiomassRecord]] = None,
) -> list[BiomassAssessment]:
    """
    Adapter for the project's current Factory model.

    Expected fields:
        factory.state
        factory.district

    Optional fields:
        factory.latitude / factory_latitude
        factory.longitude / factory_longitude

    This keeps the biomass engine independent of Pydantic internals.
    """
    state = getattr(factory, "state", None)
    district = getattr(factory, "district", None)

    if not state or not district:
        raise ValueError(
            "Factory must contain both state and district "
            "for biomass assessment."
        )

    resolved_latitude = (
        factory_latitude
        if factory_latitude is not None
        else getattr(factory, "latitude", None)
    )

    resolved_longitude = (
        factory_longitude
        if factory_longitude is not None
        else getattr(factory, "longitude", None)
    )

    return assess_biomass(
        state=state,
        district=district,
        factory_latitude=resolved_latitude,
        factory_longitude=resolved_longitude,
        preferred_biomass_type=preferred_biomass_type,
        preferred_crop=preferred_crop,
        atlas_records=atlas_records,
    )


# ---------------------------------------------------------------------------
# Result serialization
# ---------------------------------------------------------------------------


def assessment_to_dict(
    assessment: BiomassAssessment,
) -> dict[str, Any]:
    """
    Convert a BiomassAssessment into JSON-safe data.
    """
    data = asdict(assessment)

    # JSON does not have a native NaN-friendly contract in all clients.
    if isinstance(data["transport_distance_km"], float):
        if data["transport_distance_km"] != data["transport_distance_km"]:
            data["transport_distance_km"] = None

    return data


def build_biomass_result(
    assessments: list[BiomassAssessment],
    *,
    state: str,
    district: str,
) -> dict[str, Any]:
    """
    Build a stable API/UI-friendly result.

    The result intentionally contains both machine-readable fields and
    plain-language summary fields.
    """
    if not assessments:
        return {
            "available": False,
            "state": state,
            "district": district,
            "message": (
                "No biomass records were found for this district "
                "in the current Atlas dataset."
            ),
            "recommendations": [],
        }

    top = assessments[0]

    risk_level = _risk_level(top.biomass_risk_index)

    availability_text = top.availability_level

    energy_text = (
        "Good"
        if top.effective_calorific_value_mj_kg >= 13
        else "Moderate"
        if top.effective_calorific_value_mj_kg >= 10
        else "Low"
    )

    return {
        "available": True,
        "state": state,
        "district": district,
        "recommended_biomass": top.biomass_type,
        "recommended_crop": top.crop,
        "summary": {
            "available": availability_text,
            "seasonality": top.seasonality_level,
            "supply_risk": risk_level,
            "energy_value": energy_text,
            "recommendation": top.recommendation,
        },
        "top_assessment": assessment_to_dict(top),
        "recommendations": [
            assessment_to_dict(item)
            for item in assessments
        ],
        "engine": {
            "name": "Biomass Intelligence Engine",
            "version": "1.0.0",
            "historical_atlas_data": True,
            "transparent_scoring": True,
        },
    }

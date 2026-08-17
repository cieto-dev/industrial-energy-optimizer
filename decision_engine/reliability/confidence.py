"""
confidence.py — Data-quality confidence scoring for the Reliability Engine.

Purpose
-------
Score how trustworthy each input variable's base-case value is,
then translate low-confidence variables into *wider* perturbation ranges
for the Monte Carlo sweep in reliability_engine.py.

Design contract
---------------
- A score of 1.0 means the value is fully sourced and verified.
- A score of 0.0 means the value is a pure placeholder / guess.
- The widening_factor() function translates a confidence score into a
  multiplier applied to the [low, high] distance from the base in
  perturbation_config.json.  Low confidence → multiplier > 1 → wider band.
- This module does NOT modify the base value — only the spread.

Principle
---------
Low-confidence inputs MUST widen the perturbation range, never narrow it.
Narrowing on a low-confidence input would be epistemically dishonest
(implying we know more than we do).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Data quality tiers
# ---------------------------------------------------------------------------

# These map to the "source_status" values used in perturbation_config.json
# and knowledge-base JSON files.
SOURCE_STATUS_CONFIDENCE = {
    "verified": 1.0,           # Sourced from a primary, recent, auditable source
    "partially_sourced": 0.65,  # Partially supported by data; some assumptions
    "estimated": 0.55,          # Secondary/indirect source; used with caveats
    "unsourced_assumption": 0.30,  # Pure planning heuristic; must be flagged
    "unavailable": 0.20,        # Explicitly noted as not yet obtainable
    "placeholder": 0.10,        # A stub value; should never reach production
}

# Confidence decay per year for data that has not been re-verified.
# E.g. a verified value that is 2 years old is penalised slightly.
RECENCY_DECAY_PER_YEAR = 0.03  # 3% per year, capped at 0.15 total decay


@dataclass
class VariableConfidence:
    """
    Confidence assessment for a single input variable.

    Attributes
    ----------
    variable_id : str
        Identifier matching the key in perturbation_config.json
        (e.g. 'fuel_price', 'solar_capacity_factor').
    base_score : float
        Confidence in [0.0, 1.0] derived from source_status.
    data_age_years : float
        How many years ago the value was last verified.
    region_verified : bool
        True if the value has been verified for the specific region
        of the factory (state / district), False if a national default
        is being used as a stand-in.
    is_region_default : bool
        True if the value is a national average applied to a region
        without explicit local calibration.
    notes : str
        Human-readable explanation surfaced in sweep metadata output.
    """

    variable_id: str
    base_score: float
    data_age_years: float = 0.0
    region_verified: bool = True
    is_region_default: bool = False
    notes: str = ""

    def final_score(self) -> float:
        """
        Compute the effective confidence score after applying:
        1. Recency decay (age penalty)
        2. Region-default penalty (−0.10 if using a national average)

        Returns a clamped value in [0.05, 1.0].
        """
        score = self.base_score

        # Recency decay
        age_penalty = min(
            self.data_age_years * RECENCY_DECAY_PER_YEAR,
            0.15  # cap at 15%
        )
        score -= age_penalty

        # Region default penalty
        if self.is_region_default:
            score -= 0.10

        return max(0.05, min(1.0, score))

    def widening_factor(self) -> float:
        """
        Translate confidence into a spread-widening multiplier.

        The mapping is designed so that:
        - confidence = 1.0  → factor = 1.0 (no widening)
        - confidence = 0.65 → factor ≈ 1.25 (25% wider spread)
        - confidence = 0.30 → factor ≈ 1.75 (75% wider spread)
        - confidence → 0    → factor = 2.50 (hard cap to avoid explosion)

        Formula: factor = 1 + (1 - confidence) * 1.50, capped at 2.50
        Rationale: a linear inverse relationship is interpretable and
        monotonically correct (lower confidence → always wider), and the
        1.50 slope means a fully unsourced variable (confidence ≈ 0.30)
        gets ~1.75× spread — substantial but not unbounded.
        """
        confidence = self.final_score()
        factor = 1.0 + (1.0 - confidence) * 1.50
        return min(factor, 2.50)


# ---------------------------------------------------------------------------
# Confidence profile builder
# ---------------------------------------------------------------------------

@dataclass
class ConfidenceProfile:
    """
    Aggregated confidence scores for all variables in a sweep.

    Build one from known variable metadata, then pass it to the
    reliability engine to adjust perturbation distribution widths.
    """
    scores: Dict[str, VariableConfidence] = field(default_factory=dict)

    def add(self, vc: VariableConfidence) -> None:
        self.scores[vc.variable_id] = vc

    def widening_factor_for(self, variable_id: str) -> float:
        """
        Return the widening factor for a given variable.
        Falls back to the maximum (2.50) if the variable is not scored —
        unknown provenance is treated as maximally uncertain.
        """
        if variable_id not in self.scores:
            return 2.50
        return self.scores[variable_id].widening_factor()

    def final_score_for(self, variable_id: str) -> float:
        """Return the final confidence score, or 0.05 if unknown."""
        if variable_id not in self.scores:
            return 0.05
        return self.scores[variable_id].final_score()

    def to_metadata(self) -> Dict:
        """
        Serialise the full confidence profile for inclusion in sweep
        output metadata (for reporting and auditability).
        """
        return {
            variable_id: {
                "final_score": vc.final_score(),
                "widening_factor": vc.widening_factor(),
                "notes": vc.notes,
                "region_verified": vc.region_verified,
                "is_region_default": vc.is_region_default,
            }
            for variable_id, vc in self.scores.items()
        }


# ---------------------------------------------------------------------------
# Standard profile factory
# ---------------------------------------------------------------------------

def build_standard_confidence_profile(
    fuel_source_status: str = "partially_sourced",
    fuel_data_age_years: float = 0.0,
    electricity_source_status: str = "partially_sourced",
    electricity_data_age_years: float = 0.0,
    region_verified: bool = True,
    solar_applicable: bool = False,
    biomass_applicable: bool = False,
) -> ConfidenceProfile:
    """
    Build a ConfidenceProfile for a standard factory scenario.

    This is the primary entry point for the reliability_engine.py
    and for tests.  All parameters have safe defaults so the function
    can be called with only the parameters that are actually known.

    Parameters
    ----------
    fuel_source_status : str
        Source status of the fuel price data (from perturbation_config.json
        or fuel_prices.json 'status' field).
    fuel_data_age_years : float
        Years since fuel price data was last verified.
    electricity_source_status : str
        Source status of electricity tariff data.
    electricity_data_age_years : float
        Years since electricity tariff data was last verified.
    region_verified : bool
        False if national defaults are being used for this factory's state.
    solar_applicable : bool
        True if the scenario includes a solar technology.
    biomass_applicable : bool
        True if the scenario includes a biomass technology.

    Returns
    -------
    ConfidenceProfile
        Ready to pass to reliability_engine.run_reliability_sweep().
    """
    profile = ConfidenceProfile()

    # -- fuel_price -----------------------------------------------------------
    profile.add(VariableConfidence(
        variable_id="fuel_price",
        base_score=SOURCE_STATUS_CONFIDENCE.get(
            fuel_source_status, 0.40
        ),
        data_age_years=fuel_data_age_years,
        region_verified=region_verified,
        is_region_default=not region_verified,
        notes=(
            f"Fuel price confidence based on source_status='{fuel_source_status}'. "
            f"Data age: {fuel_data_age_years:.1f} years. "
            f"Region verified: {region_verified}."
        )
    ))

    # -- production_volume ----------------------------------------------------
    # Always unsourced: no factory-level production variance dataset exists.
    profile.add(VariableConfidence(
        variable_id="production_volume",
        base_score=SOURCE_STATUS_CONFIDENCE["unsourced_assumption"],
        data_age_years=0.0,
        region_verified=False,
        is_region_default=True,
        notes=(
            "UNSOURCED ASSUMPTION: production volume variance is a planning "
            "heuristic (no IIP or factory-survey data available in this repo). "
            "Confidence is deliberately low to widen this variable's spread."
        )
    ))

    # -- electricity_tariff ---------------------------------------------------
    profile.add(VariableConfidence(
        variable_id="electricity_tariff",
        base_score=SOURCE_STATUS_CONFIDENCE.get(
            electricity_source_status, 0.55
        ),
        data_age_years=electricity_data_age_years,
        region_verified=region_verified,
        is_region_default=not region_verified,
        notes=(
            f"Electricity tariff confidence based on "
            f"source_status='{electricity_source_status}'. "
            f"State-level data in datasets/electricity_tariffs/ — "
            f"region_verified={region_verified}."
        )
    ))

    # -- capex_overrun --------------------------------------------------------
    # Always unsourced: no MSME overrun dataset exists.
    profile.add(VariableConfidence(
        variable_id="capex_overrun",
        base_score=SOURCE_STATUS_CONFIDENCE["unsourced_assumption"],
        data_age_years=0.0,
        region_verified=False,
        is_region_default=True,
        notes=(
            "UNSOURCED ASSUMPTION: CAPEX overrun range is a planning heuristic. "
            "Replace with MNRE/BEE installation data if available."
        )
    ))

    # -- solar_capacity_factor (only if solar technology present) -------------
    if solar_applicable:
        profile.add(VariableConfidence(
            variable_id="solar_capacity_factor",
            base_score=SOURCE_STATUS_CONFIDENCE["unsourced_assumption"],
            data_age_years=0.0,
            region_verified=False,
            is_region_default=True,
            notes=(
                "UNSOURCED ASSUMPTION: solar capacity factor variance is a heuristic. "
                "No district-level irradiation variance dataset is in this repo. "
                "Replace with MNRE/IMD data for the factory's district."
            )
        ))

    # -- biomass_logistics_cost (only if biomass technology present) ----------
    if biomass_applicable:
        profile.add(VariableConfidence(
            variable_id="biomass_logistics_cost",
            base_score=SOURCE_STATUS_CONFIDENCE["partially_sourced"],
            data_age_years=0.0,
            region_verified=region_verified,
            is_region_default=not region_verified,
            notes=(
                "Biomass logistics cost partially sourced from Biomass Atlas "
                "(seasonal price spike data). High upward tail retained intentionally."
            )
        ))

    return profile

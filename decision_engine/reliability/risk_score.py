"""
risk_score.py — Per-scenario risk categorisation derived from sweep output.

Purpose
-------
Consume the raw Monte Carlo sweep results from reliability_engine.py
and produce:
1. A tornado ranking — ordered list of variables by their contribution
   to payback swing (OAT analysis).
2. Per-scenario exposure tiers for the three roadmap-named risk dimensions:
   - Fuel price volatility exposure
   - Grid reliability / electricity tariff exposure
   - Biomass logistics exposure (only relevant for biomass scenarios)
3. An overall risk tier for the scenario.

Design contract
---------------
- Risk tiers are DERIVED from the real sweep output (oat_swings + spread_ratio),
  not substitutes for it.
- Two scenarios with different technology inputs MUST NOT produce identical
  tier assignments unless their sweep results are genuinely the same.
- The tier labels (LOW / MEDIUM / HIGH / VERY_HIGH) are meaningful only
  because the underlying spread_ratio and OAT swings are model-derived.

Dependency
----------
    ReliabilitySweepResult from reliability_engine.py
    (no direct call into economics/ — uses sweep output only)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------

# Risk tier labels
TIER_LOW       = "LOW"
TIER_MEDIUM    = "MEDIUM"
TIER_HIGH      = "HIGH"
TIER_VERY_HIGH = "VERY_HIGH"

# Spread-ratio thresholds for overall risk tier assignment.
# Rationale:
#   - < 0.15: narrower than gate → anomalously low sensitivity (flag as such)
#   - 0.15–0.30: moderate spread, acceptable for MSME project planning
#   - 0.30–0.50: wide spread, project manager should stress-test assumptions
#   - > 0.50: very wide spread → high uncertainty, recommendation needs caveats
SPREAD_TIER_THRESHOLDS = [
    (0.50, TIER_VERY_HIGH),
    (0.30, TIER_HIGH),
    (0.15, TIER_MEDIUM),
    (0.0,  TIER_LOW),
]

# Per-variable OAT swing thresholds for exposure tier.
# Expressed in years of payback swing.
# A swing > 3 years on a single variable is "HIGH" exposure for that driver.
VARIABLE_SWING_THRESHOLDS = [
    (3.0, TIER_HIGH),
    (1.5, TIER_MEDIUM),
    (0.0, TIER_LOW),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TornadoEntry:
    """One row in the tornado chart."""
    variable_id: str
    swing_years: float         # payback_high_end − payback_low_end (years)
    exposure_tier: str         # LOW / MEDIUM / HIGH
    source_status: str         # From perturbation config audit
    rank: int                  # 1 = biggest driver


@dataclass
class ScenarioRiskScore:
    """
    Risk characterisation for a single technology scenario.

    Attributes
    ----------
    technology_id : str
    scenario_id : str
    spread_ratio : float
        (payback_p90 - payback_p10) / payback_p50 from the sweep.
    overall_tier : str
        Overall risk tier for this scenario: LOW / MEDIUM / HIGH / VERY_HIGH.
    tornado : list[TornadoEntry]
        Variables ranked by payback swing, largest first.
    fuel_volatility_tier : str
        Risk tier for fuel price exposure specifically.
    grid_reliability_tier : str
        Risk tier for electricity tariff exposure specifically.
    biomass_logistics_tier : str | None
        Risk tier for biomass logistics. None if biomass not applicable.
    payback_p10 : float
    payback_p50 : float
    payback_p90 : float
    top_driver : str
        Variable ID of the single biggest payback swing driver.
    unsourced_variables : list[str]
        Variables flagged as unsourced_assumption — audit reminder.
    notes : str
        Human-readable summary surfaced in reports.
    """
    technology_id: str
    scenario_id: str
    spread_ratio: float
    overall_tier: str
    tornado: List[TornadoEntry]
    fuel_volatility_tier: str
    grid_reliability_tier: str
    biomass_logistics_tier: Optional[str]
    payback_p10: float
    payback_p50: float
    payback_p90: float
    top_driver: str
    unsourced_variables: List[str]
    notes: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tier_from_thresholds(
    value: float,
    thresholds: List[Tuple[float, str]],
) -> str:
    """
    Assign a tier by finding the first threshold the value exceeds.
    Thresholds must be sorted descending (highest bound first).
    """
    for cutoff, tier in thresholds:
        if value >= cutoff:
            return tier
    return TIER_LOW


def _build_tornado(
    oat_swings: Dict[str, float],
    sourcing_audit: Dict[str, Dict],
) -> List[TornadoEntry]:
    """
    Build a sorted tornado list from OAT swings.

    Variables are sorted by absolute swing (descending).
    Negative swings (perversely, higher end reduces payback) are kept
    with their sign for transparency but ranked by magnitude.
    """
    entries = []
    for rank, (var_id, swing) in enumerate(
        sorted(oat_swings.items(), key=lambda x: abs(x[1]), reverse=True),
        start=1,
    ):
        source_status = "unknown"
        if var_id in sourcing_audit:
            source_status = sourcing_audit[var_id].get(
                "source_status", "unknown"
            )

        swing_abs = abs(swing)
        exposure_tier = _tier_from_thresholds(
            swing_abs, VARIABLE_SWING_THRESHOLDS
        )

        entries.append(TornadoEntry(
            variable_id=var_id,
            swing_years=round(swing, 4),
            exposure_tier=exposure_tier,
            source_status=source_status,
            rank=rank,
        ))
    return entries


def _make_notes(result_meta: Dict, risk_score: "ScenarioRiskScore") -> str:
    """Generate a plain-English summary note."""
    unsourced = risk_score.unsourced_variables
    unsourced_note = (
        f" Note: {len(unsourced)} variable(s) use unsourced assumptions "
        f"({', '.join(unsourced)}) — replace with sourced data before "
        f"presenting to external stakeholders."
        if unsourced else ""
    )

    driver_note = (
        f"The dominant payback risk driver is '{risk_score.top_driver}' "
        f"(OAT swing = {risk_score.tornado[0].swing_years:.2f} years). "
        if risk_score.tornado else ""
    )

    biomass_note = (
        f"Biomass logistics exposure: {risk_score.biomass_logistics_tier}. "
        if risk_score.biomass_logistics_tier else ""
    )

    return (
        f"Scenario '{risk_score.scenario_id}' overall risk: "
        f"{risk_score.overall_tier}. "
        f"Payback range P10–P90: {risk_score.payback_p10:.1f}–"
        f"{risk_score.payback_p90:.1f} years (median {risk_score.payback_p50:.1f}). "
        f"{driver_note}"
        f"Fuel volatility exposure: {risk_score.fuel_volatility_tier}. "
        f"Grid tariff exposure: {risk_score.grid_reliability_tier}. "
        f"{biomass_note}"
        f"{unsourced_note}"
    ).strip()


# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------

def score_scenario_risk(
    sweep_result,
    biomass_applicable: bool = False,
) -> ScenarioRiskScore:
    """
    Derive a ScenarioRiskScore from a ReliabilitySweepResult.

    Parameters
    ----------
    sweep_result : ReliabilitySweepResult
        Output of reliability_engine.run_reliability_sweep().
    biomass_applicable : bool
        True if the scenario includes biomass technology.
        Controls whether biomass_logistics_tier is populated.

    Returns
    -------
    ScenarioRiskScore
        Fully populated risk characterisation for this scenario.

    Design note
    -----------
    The tier assignments here are ENTIRELY driven by the sweep's own
    numeric outputs (spread_ratio, oat_swings). There is no lookup table
    mapping technology names to fixed tiers — that would be a risk label
    disguised as analysis.
    """
    meta = sweep_result.metadata
    oat_swings = sweep_result.oat_swings
    sourcing_audit = meta.get("variables", {})
    unsourced = meta.get("unsourced_variables", [])

    # -- Overall tier --------------------------------------------------------
    overall_tier = _tier_from_thresholds(
        sweep_result.spread_ratio,
        SPREAD_TIER_THRESHOLDS,
    )

    # -- Tornado ranking ------------------------------------------------------
    tornado = _build_tornado(oat_swings, sourcing_audit)

    # -- Per-variable exposure tiers -----------------------------------------
    fuel_swing = abs(oat_swings.get("fuel_price", 0.0))
    fuel_tier  = _tier_from_thresholds(fuel_swing, VARIABLE_SWING_THRESHOLDS)

    elec_swing = abs(oat_swings.get("electricity_tariff", 0.0))
    grid_tier  = _tier_from_thresholds(elec_swing, VARIABLE_SWING_THRESHOLDS)

    biomass_tier: Optional[str] = None
    if biomass_applicable:
        biomass_swing = abs(oat_swings.get("biomass_logistics_cost", 0.0))
        biomass_tier  = _tier_from_thresholds(
            biomass_swing, VARIABLE_SWING_THRESHOLDS
        )

    # -- Top driver ----------------------------------------------------------
    top_driver = tornado[0].variable_id if tornado else "unknown"

    # -- Assemble result -----------------------------------------------------
    risk_score = ScenarioRiskScore(
        technology_id=meta.get("technology_id", "unknown"),
        scenario_id=meta.get("scenario_id", "unknown"),
        spread_ratio=sweep_result.spread_ratio,
        overall_tier=overall_tier,
        tornado=tornado,
        fuel_volatility_tier=fuel_tier,
        grid_reliability_tier=grid_tier,
        biomass_logistics_tier=biomass_tier,
        payback_p10=sweep_result.payback_p10,
        payback_p50=sweep_result.payback_p50,
        payback_p90=sweep_result.payback_p90,
        top_driver=top_driver,
        unsourced_variables=unsourced,
        notes="",  # populated below after assembly
    )

    risk_score.notes = _make_notes(meta, risk_score)
    return risk_score


def compare_scenarios(
    risk_scores: List[ScenarioRiskScore],
) -> List[ScenarioRiskScore]:
    """
    Return risk scores sorted from lowest overall risk to highest.

    Useful for the optimizer to break ties when scenarios have similar
    MCDA scores — prefer the scenario with lower reliability risk.
    """
    tier_order = {
        TIER_LOW: 0,
        TIER_MEDIUM: 1,
        TIER_HIGH: 2,
        TIER_VERY_HIGH: 3,
    }
    return sorted(
        risk_scores,
        key=lambda rs: (
            tier_order.get(rs.overall_tier, 9),
            rs.spread_ratio,
        ),
    )

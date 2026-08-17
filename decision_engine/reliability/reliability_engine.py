"""
reliability_engine.py — Monte Carlo reliability sweep for payback range analysis.

Purpose
-------
Answer RQ6: "How sensitive is the recommended pathway's payback period to
realistic uncertainty in fuel prices, production volume, solar yield,
and other key variables?"

Design contract
---------------
- The sweep is a real Monte Carlo simulation (not a static risk label).
- All distribution parameters come from perturbation_config.json
  (knowledge-base/finance/perturbation_config.json), not hardcoded inline.
- Confidence scores from confidence.py widen the perturbation spread for
  low-quality inputs, never narrow it.
- The payback calculation calls into decision_engine/economics/payback.py
  directly — no cost math is re-implemented here.
- Output includes payback_p10, payback_p50, payback_p90, and the raw
  distribution array (required by risk_score.py for tornado ranking).
- Variables with source_status="unsourced_assumption" are flagged in the
  metadata output, not silently used.

Key function
------------
run_reliability_sweep(base_case, perturbation_config, n_iterations=5000)
    → ReliabilitySweepResult

Dependency chain
----------------
    baseline/ (BaselineProfile) ✅ → used to derive base-case savings
    economics/payback.py ✅        → called per iteration for payback
    confidence.py ✅               → widens spreads for low-confidence vars
    perturbation_config.json ✅    → distribution parameters
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Internal imports — economics only; no other decision_engine modules touched
# ---------------------------------------------------------------------------
from decision_engine.economics.payback import calculate_payback
from decision_engine.reliability.confidence import (
    ConfidenceProfile,
    build_standard_confidence_profile,
)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PERTURBATION_CONFIG_PATH = (
    _PROJECT_ROOT
    / "knowledge-base"
    / "finance"
    / "perturbation_config.json"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BaseCaseInputs:
    """
    Base-case economic inputs required to compute payback.

    These are the *nominal* values (before perturbation).
    They are immutable within a sweep run — perturbed copies are
    created per iteration, never written back here.

    Parameters
    ----------
    capex_min : float
        Minimum CAPEX estimate in INR (from economics/capex.py output).
    capex_max : float
        Maximum CAPEX estimate in INR. If same as capex_min, it's a
        point estimate.
    baseline_annual_opex : float
        Annual operating cost of the existing (baseline) system, INR/year.
        Derived from baseline_engine output.
    proposed_fuel_cost : float
        Annual fuel cost of the proposed technology, INR/year.
        Varies with fuel_price perturbation factor.
    proposed_electricity_cost : float
        Annual electricity cost of proposed technology, INR/year.
        Varies with electricity_tariff perturbation factor.
    proposed_maintenance_cost : float
        Annual maintenance cost, INR/year. Not perturbed.
    proposed_labour_cost : float
        Annual labour cost, INR/year. Not perturbed.
    proposed_other_cost : float
        Other annual OPEX, INR/year. Not perturbed.
    baseline_fuel_cost : float
        Baseline fuel cost component, INR/year.
        When fuel price rises, the baseline cost also rises
        (saving is the difference), so we track both sides.
    baseline_electricity_cost : float
        Baseline electricity cost component, INR/year.
    solar_fraction : float
        Fraction of energy demand met by solar in proposed system [0.0–1.0].
        Used to scale the solar_capacity_factor perturbation's effect on
        savings. 0.0 for non-solar scenarios.
    biomass_fraction : float
        Fraction of proposed fuel cost that is biomass procurement.
        Used to scale biomass_logistics_cost perturbation.
    technology_id : str
        Technology identifier (for logging and risk_score.py metadata).
    scenario_id : str
        Scenario identifier.
    """
    capex_min: float
    capex_max: float
    baseline_annual_opex: float
    proposed_fuel_cost: float
    proposed_electricity_cost: float
    proposed_maintenance_cost: float
    proposed_labour_cost: float
    proposed_other_cost: float
    baseline_fuel_cost: float
    baseline_electricity_cost: float
    solar_fraction: float = 0.0
    biomass_fraction: float = 0.0
    technology_id: str = "unknown"
    scenario_id: str = "unknown"


@dataclass
class ReliabilitySweepResult:
    """
    Output of run_reliability_sweep().

    Attributes
    ----------
    payback_p10 : float
        10th percentile of payback distribution (years). Optimistic tail.
    payback_p50 : float
        50th percentile / median payback (years).
    payback_p90 : float
        90th percentile payback (years). Adverse tail.
    spread_ratio : float
        (payback_p90 - payback_p10) / payback_p50.
        Gate: must exceed threshold in perturbation_config.json.
    raw_distribution : list[float]
        Full sorted array of all iteration payback values.
        Passed to risk_score.py for tornado analysis.
    oat_swings : dict[str, float]
        One-at-a-time payback swing per variable (high − low),
        used by risk_score.py to build tornado ranking.
        Each value is payback_at_high_end − payback_at_low_end (years).
    metadata : dict
        Sourcing audit: which variables are unsourced_assumption vs sourced,
        n_iterations, confidence widening factors, and gate threshold.
    n_iterations : int
        Number of Monte Carlo iterations actually run.
    gate_passed : bool
        True iff spread_ratio >= threshold.minimum_spread_ratio.
    """
    payback_p10: float
    payback_p50: float
    payback_p90: float
    spread_ratio: float
    raw_distribution: List[float]
    oat_swings: Dict[str, float]
    metadata: Dict
    n_iterations: int
    gate_passed: bool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_perturbation_config(config_path: Optional[Path] = None) -> Dict:
    """Load and return the perturbation config JSON."""
    path = config_path or _DEFAULT_PERTURBATION_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Perturbation config not found: {path}. "
            "Expected at knowledge-base/finance/perturbation_config.json."
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _triangular_sample(low: float, base: float, high: float) -> float:
    """
    Sample from a triangular distribution.

    Uses Python's built-in random.triangular which takes
    (low, high, mode=base).
    """
    return random.triangular(low, high, base)


def _apply_widening(
    low: float,
    base: float,
    high: float,
    widening_factor: float,
) -> tuple[float, float]:
    """
    Widen the [low, high] interval around base by widening_factor.

    The base value is unchanged. The distances from base are scaled:
        new_low  = base - (base - low) * factor
        new_high = base + (high - base) * factor

    Returns (new_low, new_high). Both are clamped so that:
    - new_low >= 0.01 (prevent non-positive multipliers)
    - new_high <= 5.0 (prevent extreme outlier explosion)
    """
    new_low = base - (base - low) * widening_factor
    new_high = base + (high - base) * widening_factor
    new_low = max(0.01, new_low)
    new_high = min(5.0, new_high)
    return new_low, new_high


def _compute_perturbed_payback(
    base_case: BaseCaseInputs,
    factors: Dict[str, float],
) -> Optional[float]:
    """
    Compute payback for one iteration given perturbation factors.

    Perturbation logic:
    - fuel_price: scales both the proposed fuel cost AND baseline fuel cost
      (because if fuel gets expensive, the baseline also gets more expensive,
       so savings = (baseline × factor) − (proposed × factor) = saving × factor).
      Therefore the annual SAVINGS scale by the fuel_price factor.
    - production_volume: scales ALL cost components (both baseline and
      proposed) linearly, so savings also scale by this factor.
    - solar_capacity_factor: a reduction in solar yield reduces the energy
      offset from solar, increasing proposed electricity purchase.
      Effect is proportional to solar_fraction.
    - electricity_tariff: scales electricity costs on both sides.
      If the factory buys electricity for the proposed system, it increases
      proposed opex. It also affects baseline electricity cost.
    - biomass_logistics_cost: scales only the biomass portion of proposed
      fuel cost.
    - capex_overrun: scales capex_min and capex_max upward.

    Returns payback_min_years (optimistic bound for this iteration)
    or None if savings <= 0.
    """
    fp  = factors.get("fuel_price", 1.0)
    pv  = factors.get("production_volume", 1.0)
    scf = factors.get("solar_capacity_factor", 1.0)
    et  = factors.get("electricity_tariff", 1.0)
    blc = factors.get("biomass_logistics_cost", 1.0)
    co  = factors.get("capex_overrun", 1.0)

    # ---- CAPEX (perturbed by overrun factor) --------------------------------
    perturbed_capex_min = base_case.capex_min * co
    perturbed_capex_max = base_case.capex_max * co

    # ---- Proposed OPEX components ------------------------------------------
    # Fuel cost: split biomass vs non-biomass portions
    biomass_share   = base_case.biomass_fraction
    non_biomass_share = 1.0 - biomass_share

    proposed_fuel = base_case.proposed_fuel_cost * (
        non_biomass_share * fp + biomass_share * fp * blc
    )

    # Electricity cost: scaled by tariff perturbation, then adjusted for
    # solar deficit (if solar yield drops, more grid electricity needed).
    # solar_shortfall_factor: 1.0 if full solar, approaching 1.0 + solar_fraction
    # when scf is at its worst.
    solar_shortfall = 0.0
    if base_case.solar_fraction > 0.0:
        # Energy deficit ratio: (1 - scf) of the solar fraction must be
        # bought from the grid at perturbed electricity tariff.
        solar_shortfall = base_case.solar_fraction * (1.0 - scf)

    proposed_elec_base = base_case.proposed_electricity_cost * et
    # Additional electricity cost due to solar underperformance:
    # modelled as a fraction of baseline electricity cost * et * shortfall
    solar_deficit_cost = (
        base_case.baseline_electricity_cost * solar_shortfall * et
    )
    proposed_elec = proposed_elec_base + solar_deficit_cost

    # Other proposed OPEX (not perturbed — deterministic components)
    proposed_maint  = base_case.proposed_maintenance_cost
    proposed_labour = base_case.proposed_labour_cost
    proposed_other  = base_case.proposed_other_cost

    # ---- Production volume scaling -----------------------------------------
    # Production volume scales total energy demand → all fuel and electricity
    # costs on BOTH sides scale proportionally.
    proposed_annual_opex = (
        proposed_fuel
        + proposed_elec
        + proposed_maint
        + proposed_labour
        + proposed_other
    ) * pv

    # ---- Baseline OPEX (perturbed) -----------------------------------------
    baseline_fuel_perturbed  = base_case.baseline_fuel_cost  * fp * pv
    baseline_elec_perturbed  = base_case.baseline_electricity_cost * et * pv
    # Sum remaining (non-energy) baseline opex component
    baseline_non_energy = (
        base_case.baseline_annual_opex
        - base_case.baseline_fuel_cost
        - base_case.baseline_electricity_cost
    ) * pv
    perturbed_baseline_opex = (
        baseline_fuel_perturbed
        + baseline_elec_perturbed
        + baseline_non_energy
    )

    annual_savings = perturbed_baseline_opex - proposed_annual_opex

    result = calculate_payback(
        capex_min=perturbed_capex_min,
        capex_max=perturbed_capex_max,
        annual_savings=annual_savings,
    )

    return result["payback_min_years"]


def _percentile(sorted_values: List[float], pct: float) -> float:
    """
    Compute a percentile from a pre-sorted list.

    pct is in [0, 100].
    Uses linear interpolation between adjacent ranks.
    """
    n = len(sorted_values)
    if n == 0:
        raise ValueError("Cannot compute percentile of empty list.")
    if n == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (n - 1)
    lower = int(rank)
    upper = lower + 1
    if upper >= n:
        return sorted_values[-1]
    frac = rank - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac


def _one_at_a_time_swings(
    base_case: BaseCaseInputs,
    variables: Dict,
    widened_params: Dict[str, Dict],
) -> Dict[str, float]:
    """
    Run one-at-a-time (OAT) perturbation for tornado ranking.

    For each variable, compute payback at the adverse (high) end of its
    distribution, then at the favourable (low) end, holding all other
    variables at their base (1.0). Record swing = payback_high − payback_low.

    A larger positive swing means that variable drives more payback risk.
    """
    swings = {}
    base_factors = {var_id: 1.0 for var_id in variables}

    for var_id, params in widened_params.items():
        # High-end (adverse): highest cost / lowest yield
        high_factors = {**base_factors, var_id: params["high"]}
        high_payback = _compute_perturbed_payback(base_case, high_factors)

        # Low-end (favourable): lowest cost / highest yield
        low_factors = {**base_factors, var_id: params["low"]}
        low_payback = _compute_perturbed_payback(base_case, low_factors)

        if high_payback is None or low_payback is None:
            swings[var_id] = 0.0
        else:
            swings[var_id] = high_payback - low_payback

    return swings


# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------

def run_reliability_sweep(
    base_case: BaseCaseInputs,
    confidence_profile: Optional[ConfidenceProfile] = None,
    n_iterations: int = 5000,
    config_path: Optional[Path] = None,
    random_seed: Optional[int] = None,
) -> ReliabilitySweepResult:
    """
    Run a Monte Carlo reliability sweep and return payback distribution.

    Parameters
    ----------
    base_case : BaseCaseInputs
        Nominal economic inputs for the scenario (CAPEX, OPEX breakdown,
        solar/biomass fractions, technology/scenario IDs).
    confidence_profile : ConfidenceProfile, optional
        Data-quality confidence scores per variable.
        If None, uses build_standard_confidence_profile() with defaults —
        all unsourced variables will still be appropriately widened.
    n_iterations : int
        Number of Monte Carlo samples. Default 5000.
        Minimum 100 for a valid percentile estimate; 5000 recommended for
        stable P10/P90.
    config_path : Path, optional
        Override path to perturbation_config.json. Defaults to
        knowledge-base/finance/perturbation_config.json.
    random_seed : int, optional
        Seed for reproducibility in tests. Production runs should not set
        this (leave None for non-deterministic sampling).

    Returns
    -------
    ReliabilitySweepResult
        See dataclass docstring for full field descriptions.

    Raises
    ------
    FileNotFoundError
        If perturbation_config.json cannot be found.
    ValueError
        If n_iterations < 100.
    RuntimeError
        If more than 90% of iterations produce non-viable savings
        (likely a misconfigured base case, not a reliability problem).
    """
    if n_iterations < 100:
        raise ValueError(
            f"n_iterations must be >= 100 for valid percentile estimates, "
            f"got {n_iterations}."
        )

    if random_seed is not None:
        random.seed(random_seed)

    # -- Load config ----------------------------------------------------------
    config = _load_perturbation_config(config_path)
    variables_config = config.get("variables", {})
    threshold = config.get("threshold", {}).get("minimum_spread_ratio", 0.15)

    # -- Confidence profile ---------------------------------------------------
    if confidence_profile is None:
        confidence_profile = build_standard_confidence_profile(
            solar_applicable=(base_case.solar_fraction > 0.0),
            biomass_applicable=(base_case.biomass_fraction > 0.0),
        )

    # -- Widen distribution parameters based on confidence -------------------
    widened_params: Dict[str, Dict] = {}
    sourcing_audit: Dict[str, Dict] = {}

    for var_id, var_cfg in variables_config.items():
        low  = var_cfg["low"]
        base = var_cfg["base"]
        high = var_cfg["high"]

        wf = confidence_profile.widening_factor_for(var_id)
        new_low, new_high = _apply_widening(low, base, high, wf)

        widened_params[var_id] = {
            "low":  new_low,
            "base": base,
            "high": new_high,
            "original_low":  low,
            "original_high": high,
            "widening_factor": wf,
        }
        sourcing_audit[var_id] = {
            "source_status": var_cfg.get("source_status", "unknown"),
            "source_notes":  var_cfg.get("source_notes", ""),
            "confidence_score": confidence_profile.final_score_for(var_id),
            "widening_factor": wf,
            "effective_low":  new_low,
            "effective_high": new_high,
        }

    # -- One-at-a-time swings (for tornado in risk_score.py) -----------------
    oat_swings = _one_at_a_time_swings(base_case, variables_config, widened_params)

    # -- Monte Carlo loop -----------------------------------------------------
    paybacks: List[float] = []
    non_viable_count = 0

    for _ in range(n_iterations):
        factors = {
            var_id: _triangular_sample(
                widened_params[var_id]["low"],
                widened_params[var_id]["base"],
                widened_params[var_id]["high"],
            )
            for var_id in widened_params
        }

        pb = _compute_perturbed_payback(base_case, factors)
        if pb is None or pb <= 0:
            non_viable_count += 1
        else:
            paybacks.append(pb)

    # Guard: if almost all iterations are non-viable, the base case is wrong
    non_viable_rate = non_viable_count / n_iterations
    if non_viable_rate > 0.90:
        raise RuntimeError(
            f"Over 90% of Monte Carlo iterations produced non-viable savings "
            f"(non_viable_rate={non_viable_rate:.1%}). "
            f"Check base_case inputs: baseline_annual_opex="
            f"{base_case.baseline_annual_opex}, "
            f"proposed costs may exceed baseline across too many scenarios."
        )

    if len(paybacks) < 10:
        raise RuntimeError(
            f"Too few viable payback samples ({len(paybacks)}) to compute "
            f"percentiles. Most iterations had non-positive savings."
        )

    paybacks.sort()

    p10 = _percentile(paybacks, 10)
    p50 = _percentile(paybacks, 50)
    p90 = _percentile(paybacks, 90)

    spread_ratio = (p90 - p10) / p50 if p50 > 0 else 0.0
    gate_passed  = spread_ratio >= threshold

    return ReliabilitySweepResult(
        payback_p10=round(p10, 4),
        payback_p50=round(p50, 4),
        payback_p90=round(p90, 4),
        spread_ratio=round(spread_ratio, 4),
        raw_distribution=paybacks,
        oat_swings=oat_swings,
        n_iterations=n_iterations,
        gate_passed=gate_passed,
        metadata={
            "technology_id":    base_case.technology_id,
            "scenario_id":      base_case.scenario_id,
            "n_viable_samples": len(paybacks),
            "non_viable_rate":  round(non_viable_rate, 4),
            "gate_threshold":   threshold,
            "gate_passed":      gate_passed,
            "spread_ratio":     round(spread_ratio, 4),
            "variables":        sourcing_audit,
            "confidence_profile": confidence_profile.to_metadata(),
            "oat_swings":       oat_swings,
            "unsourced_variables": [
                var_id
                for var_id, audit in sourcing_audit.items()
                if audit["source_status"] == "unsourced_assumption"
            ],
        },
    )

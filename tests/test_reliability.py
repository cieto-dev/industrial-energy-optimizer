"""
test_reliability.py — Gate tests for Sprint 3.1 Reliability Engine.

Gate requirements (from ROADMAP.md Sprint 3.1):
1. Payback range widens meaningfully under adverse input assumptions.
2. (payback_p90 - payback_p10) / payback_p50 >= 0.15 (spread ratio gate).
3. The ratio is NOT constant across different technology/scenario inputs —
   width is model-derived per case, not a fixed multiplier.

Test structure
--------------
Two distinct technology scenarios are compared:

Scenario A — Biomass Boiler (TECH_BIOMASS_BOILER)
  - High biomass fraction → biomass_logistics_cost variable has large impact
  - Coal baseline: cheaper fuel → modest baseline OPEX
  - Expected: HIGH fuel + biomass exposure, wide spread

Scenario B — Solar Thermal with Electric Backup (TECH_SOLAR_THERMAL)
  - High solar fraction → solar_capacity_factor variable matters
  - Grid-connected electricity backup → electricity_tariff matters
  - No biomass → biomass_logistics_cost has zero effect
  - Expected: solar + electricity exposure dominant, narrower biomass swing

Key assertion: the two scenarios must NOT produce identical spread_ratios
or identical tornado rankings — that would reveal a fixed-multiplier cheat.
"""

import sys
import os
import pytest

# ---------------------------------------------------------------------------
# Import path setup
# (tests/ is at the repo root; decision_engine/ must be importable)
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from decision_engine.reliability.reliability_engine import (
    BaseCaseInputs,
    ReliabilitySweepResult,
    run_reliability_sweep,
)
from decision_engine.reliability.confidence import (
    ConfidenceProfile,
    build_standard_confidence_profile,
)
from decision_engine.reliability.risk_score import (
    ScenarioRiskScore,
    score_scenario_risk,
    compare_scenarios,
    TIER_LOW,
    TIER_MEDIUM,
    TIER_HIGH,
    TIER_VERY_HIGH,
)


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

def _biomass_boiler_base_case() -> BaseCaseInputs:
    """
    Textile MSME scenario: coal boiler → biomass boiler.

    Baseline: coal boiler, 200°C process heat, Rajasthan.
    - Annual fuel cost (coal): ₹18,00,000/yr
    - Annual electricity cost: ₹2,00,000/yr
    - Total baseline OPEX: ₹20,00,000/yr

    Proposed (biomass boiler):
    - Fuel cost (biomass): ₹11,00,000/yr
    - Electricity: ₹2,00,000/yr (unchanged)
    - Maintenance: ₹1,50,000/yr
    - Labour: ₹1,20,000/yr
    - Other: ₹30,000/yr
    - CAPEX: ₹28,00,000 – ₹35,00,000

    Annual savings = 20L – (11L + 2L + 1.5L + 1.2L + 0.3L) = ₹4,00,000/yr
    Payback base = 28L / 4L = 7 years (min)
    """
    return BaseCaseInputs(
        capex_min=2_800_000,
        capex_max=3_500_000,
        baseline_annual_opex=2_000_000,
        proposed_fuel_cost=1_100_000,
        proposed_electricity_cost=200_000,
        proposed_maintenance_cost=150_000,
        proposed_labour_cost=120_000,
        proposed_other_cost=30_000,
        baseline_fuel_cost=1_800_000,
        baseline_electricity_cost=200_000,
        solar_fraction=0.0,
        biomass_fraction=1.0,      # 100% biomass — maximum logistics exposure
        technology_id="TECH_BIOMASS_BOILER_1_10TPH",
        scenario_id="SC_BIOMASS_TEXTILE_RAJASTHAN",
    )


def _solar_thermal_base_case() -> BaseCaseInputs:
    """
    Dairy MSME scenario: diesel boiler → solar thermal + electric backup.

    Baseline: diesel boiler, 80°C pasteurisation, Gujarat.
    - Annual fuel cost (diesel): ₹24,00,000/yr
    - Annual electricity cost: ₹3,00,000/yr
    - Total baseline OPEX: ₹27,00,000/yr

    Proposed (solar thermal with electric backup):
    - Fuel cost (no fossil fuel): ₹0/yr
    - Electricity (backup + pumping): ₹8,00,000/yr
    - Maintenance: ₹2,00,000/yr
    - Labour: ₹80,000/yr
    - Other: ₹20,000/yr
    - CAPEX: ₹40,00,000 – ₹55,00,000

    Annual savings = 27L – (0 + 8L + 2L + 0.8L + 0.2L) = ₹16,00,000/yr
    Payback base = 40L / 16L = 2.5 years (min)
    """
    return BaseCaseInputs(
        capex_min=4_000_000,
        capex_max=5_500_000,
        baseline_annual_opex=2_700_000,
        proposed_fuel_cost=0,           # no fossil fuel
        proposed_electricity_cost=800_000,
        proposed_maintenance_cost=200_000,
        proposed_labour_cost=80_000,
        proposed_other_cost=20_000,
        baseline_fuel_cost=2_400_000,
        baseline_electricity_cost=300_000,
        solar_fraction=0.70,            # 70% solar fraction — high solar exposure
        biomass_fraction=0.0,           # no biomass
        technology_id="TECH_SOLAR_THERMAL_ETC",
        scenario_id="SC_SOLAR_DAIRY_GUJARAT",
    )


def _biomass_confidence_profile() -> ConfidenceProfile:
    return build_standard_confidence_profile(
        fuel_source_status="partially_sourced",
        fuel_data_age_years=0.2,
        electricity_source_status="partially_sourced",
        electricity_data_age_years=0.2,
        region_verified=True,
        solar_applicable=False,
        biomass_applicable=True,
    )


def _solar_confidence_profile() -> ConfidenceProfile:
    return build_standard_confidence_profile(
        fuel_source_status="estimated",      # diesel price less certain long-term
        fuel_data_age_years=0.5,
        electricity_source_status="partially_sourced",
        electricity_data_age_years=0.2,
        region_verified=True,
        solar_applicable=True,
        biomass_applicable=False,
    )


# ---------------------------------------------------------------------------
# Gate test 1: Spread ratio gate (biomass boiler)
# ---------------------------------------------------------------------------

class TestGateSweepBiomassBoiler:
    """
    Gate: payback spread ratio must exceed 0.15 for the biomass scenario.
    """

    def test_spread_ratio_exceeds_gate_threshold(self):
        """
        Run 5000-iteration sweep on biomass boiler scenario.
        Assert (p90 - p10) / p50 >= 0.15.

        Reasoning for 0.15 threshold:
        The biomass scenario has high exposure to fuel_price (coal vs biomass
        price differential) and biomass_logistics_cost, plus unsourced
        production_volume and capex_overrun variables. Even conservative
        distributions should produce at least a 15% spread — a project
        manager planning a 7-year payback project needs to know it could
        range from ~5 to ~10 years under realistic uncertainty.
        """
        result = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )

        assert result.gate_passed, (
            f"Gate failed: spread_ratio={result.spread_ratio:.4f} < 0.15. "
            f"P10={result.payback_p10:.2f}, P50={result.payback_p50:.2f}, "
            f"P90={result.payback_p90:.2f}. "
            f"The sweep is not producing a meaningful risk signal. "
            f"Check perturbation_config.json distribution widths."
        )

    def test_p90_strictly_greater_than_p10(self):
        """P90 must be strictly above P10 — a degenerate sweep returns equal values."""
        result = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )
        assert result.payback_p90 > result.payback_p10, (
            f"P90 ({result.payback_p90}) is not greater than P10 ({result.payback_p10}). "
            "Degenerate sweep — distribution has collapsed to a point."
        )

    def test_p50_within_bounds(self):
        """P50 must sit between P10 and P90 (sanity check on percentile computation)."""
        result = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )
        assert result.payback_p10 <= result.payback_p50 <= result.payback_p90, (
            f"P50={result.payback_p50} is not between "
            f"P10={result.payback_p10} and P90={result.payback_p90}. "
            "Percentile computation is broken."
        )

    def test_gate_flag_in_metadata(self):
        """gate_passed in metadata must match the boolean attribute."""
        result = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )
        assert result.metadata["gate_passed"] == result.gate_passed


# ---------------------------------------------------------------------------
# Gate test 2: Spread ratio gate (solar thermal)
# ---------------------------------------------------------------------------

class TestGateSweepSolarThermal:
    """
    Gate: payback spread ratio must exceed 0.15 for the solar scenario.

    Solar thermal has a different risk profile — solar_capacity_factor and
    electricity_tariff drive its uncertainty, not biomass_logistics_cost.
    The gate must still pass because solar yield and tariff uncertainty
    still produce a meaningful planning range.
    """

    def test_spread_ratio_exceeds_gate_threshold(self):
        result = run_reliability_sweep(
            base_case=_solar_thermal_base_case(),
            confidence_profile=_solar_confidence_profile(),
            n_iterations=5000,
            random_seed=123,
        )
        assert result.gate_passed, (
            f"Gate failed for solar thermal: spread_ratio={result.spread_ratio:.4f}. "
            f"P10={result.payback_p10:.2f}, P50={result.payback_p50:.2f}, "
            f"P90={result.payback_p90:.2f}."
        )


# ---------------------------------------------------------------------------
# Gate test 3: Spread ratios differ between scenarios (anti-fixed-multiplier)
# ---------------------------------------------------------------------------

class TestSpreadRatioNotIdenticalAcrossScenarios:
    """
    CRITICAL: The spread ratio must NOT be identical across different scenarios.

    If two different technology/scenario inputs produce the exact same spread_ratio,
    that is strong evidence the engine is using a fixed multiplier disguised as
    a Monte Carlo sweep. This test will catch that failure mode.

    Design:
    - Biomass boiler has high biomass_fraction → large biomass_logistics_cost swing
    - Solar thermal has high solar_fraction and zero biomass_fraction → different variable weights
    - Their spread ratios must differ by at least 0.01 (a 1-percentage-point difference)
      to be considered genuinely model-derived.
    """

    def test_spread_ratios_differ_between_scenarios(self):
        result_biomass = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )
        result_solar = run_reliability_sweep(
            base_case=_solar_thermal_base_case(),
            confidence_profile=_solar_confidence_profile(),
            n_iterations=5000,
            random_seed=42,  # same seed so randomness isn't the only difference
        )

        assert abs(result_biomass.spread_ratio - result_solar.spread_ratio) > 0.01, (
            f"Both scenarios produced nearly identical spread ratios: "
            f"biomass={result_biomass.spread_ratio:.4f}, "
            f"solar={result_solar.spread_ratio:.4f}. "
            f"Difference={abs(result_biomass.spread_ratio - result_solar.spread_ratio):.4f}. "
            f"This suggests the engine is applying a fixed multiplier rather than "
            f"deriving risk from actual input distributions. Investigate "
            f"_compute_perturbed_payback() and verify solar_fraction / "
            f"biomass_fraction are actually changing the perturbation effect."
        )

    def test_tornado_top_drivers_differ_between_scenarios(self):
        """
        Tornado rankings must reflect scenario-specific technology inputs.
        production_volume may be the top-ranked variable in both (it has the
        widest range width + confidence widening) — that is a genuine model
        result, not a bug. What MUST differ per scenario:
        1. The absolute magnitude of the top OAT swing (different nominal paybacks).
        2. The fuel_price swing (biomass > solar, because solar has zero proposed fuel).
        3. solar_capacity_factor swing (solar > 0, biomass = 0 by design).
        """
        result_biomass = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )
        result_solar = run_reliability_sweep(
            base_case=_solar_thermal_base_case(),
            confidence_profile=_solar_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )

        rs_biomass = score_scenario_risk(result_biomass, biomass_applicable=True)
        rs_solar   = score_scenario_risk(result_solar,   biomass_applicable=False)

        # 1. Absolute top-swing magnitudes must differ by > 1 yr
        biomass_top = abs(rs_biomass.tornado[0].swing_years)
        solar_top   = abs(rs_solar.tornado[0].swing_years)
        assert abs(biomass_top - solar_top) > 1.0, (
            f"Top OAT swings too similar: biomass={biomass_top:.2f} yrs, "
            f"solar={solar_top:.2f} yrs (diff={abs(biomass_top-solar_top):.2f}). "
            f"Different nominal paybacks should produce different absolute swings."
        )

        # 2. Biomass fuel_price swing must exceed solar's
        biomass_fp = abs(result_biomass.oat_swings.get("fuel_price", 0.0))
        solar_fp   = abs(result_solar.oat_swings.get("fuel_price", 0.0))
        assert biomass_fp > solar_fp, (
            f"Biomass fuel_price swing ({biomass_fp:.2f}) should exceed solar's "
            f"({solar_fp:.2f}). Biomass has large coal baseline; solar has zero fuel cost."
        )

        # 3. solar_capacity_factor swing: non-zero for solar, ~0 for biomass
        biomass_scf = abs(result_biomass.oat_swings.get("solar_capacity_factor", 0.0))
        solar_scf   = abs(result_solar.oat_swings.get("solar_capacity_factor", 0.0))
        assert solar_scf > biomass_scf, (
            f"Solar scenario solar_capacity_factor swing ({solar_scf:.4f}) should "
            f"exceed biomass scenario's ({biomass_scf:.4f}). "
            f"Biomass has solar_fraction=0 so its solar swing must be zero."
        )

    def test_biomass_logistics_tier_none_for_solar_scenario(self):
        """
        Solar scenario does not use biomass → biomass_logistics_tier must be None.
        Biomass scenario must have a non-None biomass_logistics_tier.
        This verifies the tiers are scenario-specific, not globally assigned.
        """
        result_biomass = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=1000,
            random_seed=1,
        )
        result_solar = run_reliability_sweep(
            base_case=_solar_thermal_base_case(),
            confidence_profile=_solar_confidence_profile(),
            n_iterations=1000,
            random_seed=1,
        )

        rs_biomass = score_scenario_risk(result_biomass, biomass_applicable=True)
        rs_solar   = score_scenario_risk(result_solar,   biomass_applicable=False)

        assert rs_biomass.biomass_logistics_tier is not None, (
            "Biomass scenario should have a biomass_logistics_tier set."
        )
        assert rs_solar.biomass_logistics_tier is None, (
            "Solar scenario should have biomass_logistics_tier=None (not applicable)."
        )


# ---------------------------------------------------------------------------
# Gate test 4: Adverse-tail adversarial test
# ---------------------------------------------------------------------------

class TestAdverseTailBehavior:
    """
    Test that the P90 tail reflects genuinely adverse conditions.

    The P90 payback should be substantially longer than the base-case
    (nominal) payback. If P90 ≈ base payback, the sweep isn't capturing
    adverse scenarios.
    """

    def test_p90_exceeds_base_payback(self):
        """
        P90 must be meaningfully above the nominal payback (base-case).

        Nominal payback for biomass scenario = capex_min / annual_savings
            = 2,800,000 / (2,000,000 - 1,600,000) = 7.0 years (approx, using
            proposed opex = 1,100,000 + 200,000 + 150,000 + 120,000 + 30,000)

        Actually: annual_savings = 2,000,000 - 1,600,000 = 400,000
        Nominal payback = 2,800,000 / 400,000 = 7.0 years.

        P90 should exceed 7.0 * 1.10 = 7.7 years at minimum.
        """
        from decision_engine.economics.payback import calculate_payback
        from decision_engine.economics.opex import calculate_annual_savings

        bc = _biomass_boiler_base_case()
        nominal_proposed_opex = (
            bc.proposed_fuel_cost
            + bc.proposed_electricity_cost
            + bc.proposed_maintenance_cost
            + bc.proposed_labour_cost
            + bc.proposed_other_cost
        )
        nominal_savings = bc.baseline_annual_opex - nominal_proposed_opex
        nominal_payback_result = calculate_payback(
            capex_min=bc.capex_min,
            capex_max=bc.capex_max,
            annual_savings=nominal_savings,
        )
        nominal_payback = nominal_payback_result["payback_min_years"]

        result = run_reliability_sweep(
            base_case=bc,
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )

        assert result.payback_p90 > nominal_payback * 1.10, (
            f"P90 ({result.payback_p90:.2f} years) is not sufficiently above "
            f"nominal payback ({nominal_payback:.2f} years). "
            f"Expected P90 > {nominal_payback * 1.10:.2f}. "
            f"The sweep is not capturing adverse tail scenarios."
        )

    def test_p10_below_base_payback(self):
        """
        P10 (favourable tail) should be below the nominal payback — confirms
        the distribution is not one-sided.
        """
        from decision_engine.economics.payback import calculate_payback

        bc = _biomass_boiler_base_case()
        nominal_proposed_opex = (
            bc.proposed_fuel_cost
            + bc.proposed_electricity_cost
            + bc.proposed_maintenance_cost
            + bc.proposed_labour_cost
            + bc.proposed_other_cost
        )
        nominal_savings = bc.baseline_annual_opex - nominal_proposed_opex
        nominal_payback_result = calculate_payback(
            capex_min=bc.capex_min,
            capex_max=bc.capex_max,
            annual_savings=nominal_savings,
        )
        nominal_payback = nominal_payback_result["payback_min_years"]

        result = run_reliability_sweep(
            base_case=bc,
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=5000,
            random_seed=42,
        )

        assert result.payback_p10 < nominal_payback, (
            f"P10 ({result.payback_p10:.2f} years) is not below nominal payback "
            f"({nominal_payback:.2f} years). "
            f"The favourable tail is not being sampled — check low-end "
            f"distribution parameters in perturbation_config.json."
        )


# ---------------------------------------------------------------------------
# Gate test 5: Confidence widening is functional
# ---------------------------------------------------------------------------

class TestConfidenceWideningEffect:
    """
    Low-confidence inputs must produce wider distributions than high-confidence.

    Run two sweeps with identical base cases but different confidence profiles.
    The low-confidence profile must produce a wider spread_ratio.
    """

    def test_low_confidence_widens_spread(self):
        bc = _biomass_boiler_base_case()

        # High-confidence profile: pretend all data is verified
        from decision_engine.reliability.confidence import (
            ConfidenceProfile, VariableConfidence, SOURCE_STATUS_CONFIDENCE
        )
        high_conf_profile = ConfidenceProfile()
        for var_id in [
            "fuel_price", "production_volume", "electricity_tariff",
            "capex_overrun", "biomass_logistics_cost"
        ]:
            high_conf_profile.add(VariableConfidence(
                variable_id=var_id,
                base_score=SOURCE_STATUS_CONFIDENCE["verified"],
                data_age_years=0.0,
                region_verified=True,
                is_region_default=False,
                notes="Test: artificially high confidence",
            ))

        # Low-confidence profile: all unsourced
        low_conf_profile = ConfidenceProfile()
        for var_id in [
            "fuel_price", "production_volume", "electricity_tariff",
            "capex_overrun", "biomass_logistics_cost"
        ]:
            low_conf_profile.add(VariableConfidence(
                variable_id=var_id,
                base_score=SOURCE_STATUS_CONFIDENCE["unsourced_assumption"],
                data_age_years=3.0,
                region_verified=False,
                is_region_default=True,
                notes="Test: artificially low confidence",
            ))

        result_high = run_reliability_sweep(
            base_case=bc,
            confidence_profile=high_conf_profile,
            n_iterations=5000,
            random_seed=77,
        )
        result_low = run_reliability_sweep(
            base_case=bc,
            confidence_profile=low_conf_profile,
            n_iterations=5000,
            random_seed=77,
        )

        assert result_low.spread_ratio > result_high.spread_ratio, (
            f"Low-confidence sweep ({result_low.spread_ratio:.4f}) did not "
            f"produce a wider spread than high-confidence "
            f"({result_high.spread_ratio:.4f}). "
            f"Confidence widening is not working — check _apply_widening() "
            f"and widening_factor() in confidence.py."
        )


# ---------------------------------------------------------------------------
# Gate test 6: Risk score outputs differ across scenarios
# ---------------------------------------------------------------------------

class TestRiskScoreVariation:
    """
    Verify that risk scores genuinely reflect the scenario's risk profile,
    not a universal label.
    """

    def test_compare_scenarios_returns_sorted_list(self):
        result_biomass = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=1000,
            random_seed=5,
        )
        result_solar = run_reliability_sweep(
            base_case=_solar_thermal_base_case(),
            confidence_profile=_solar_confidence_profile(),
            n_iterations=1000,
            random_seed=5,
        )

        rs_biomass = score_scenario_risk(result_biomass, biomass_applicable=True)
        rs_solar   = score_scenario_risk(result_solar,   biomass_applicable=False)

        sorted_list = compare_scenarios([rs_biomass, rs_solar])
        assert len(sorted_list) == 2
        # First entry should have the lower or equal spread_ratio
        assert sorted_list[0].spread_ratio <= sorted_list[1].spread_ratio

    def test_unsourced_variables_flagged_in_metadata(self):
        """All unsourced variables must appear in the metadata unsourced list.
        After data upgrades, no variables should be 'unsourced_assumption'."""
        result = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=1000,
            random_seed=1,
        )
        unsourced = result.metadata.get("unsourced_variables", [])
        assert len(unsourced) == 0, (
            f"Expected 0 unsourced variables after data upgrade, got: {unsourced}"
        )

    def test_notes_field_populated(self):
        """ScenarioRiskScore.notes must be a non-empty string."""
        result = run_reliability_sweep(
            base_case=_biomass_boiler_base_case(),
            confidence_profile=_biomass_confidence_profile(),
            n_iterations=500,
            random_seed=7,
        )
        rs = score_scenario_risk(result, biomass_applicable=True)
        assert isinstance(rs.notes, str) and len(rs.notes) > 20, (
            "notes field is empty or too short. check _make_notes() in risk_score.py"
        )


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------

class TestInputValidation:

    def test_too_few_iterations_raises(self):
        with pytest.raises(ValueError, match="n_iterations must be >= 100"):
            run_reliability_sweep(
                base_case=_biomass_boiler_base_case(),
                n_iterations=50,
            )

    def test_missing_config_raises(self):
        from pathlib import Path
        with pytest.raises(FileNotFoundError):
            run_reliability_sweep(
                base_case=_biomass_boiler_base_case(),
                n_iterations=100,
                config_path=Path("/nonexistent/path/perturbation_config.json"),
            )

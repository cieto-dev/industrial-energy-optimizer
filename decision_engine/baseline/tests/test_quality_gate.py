"""
Baseline Engine — v2.0 Quality Gate Test Suite
===============================================

Tests E.1, E.2, E.3 from the Baseline Engine Hardening Specification.

Run from the project root:
    python3 -m decision_engine.baseline.tests.test_quality_gate

or directly:
    cd /path/to/industrial-energy-optimizer
    python3 decision_engine/baseline/tests/test_quality_gate.py
"""

import sys
from pathlib import Path

# Allow running from the project root without installing the package.
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from decision_engine.emissions.emission_factors import (
    get_emission_factor_value,
    get_ncv_value,
    load_emission_factors,
)
from knowledge_runtime.repository import KnowledgeRepository

PASS = "\033[92m✔ PASS\033[0m"
FAIL = "\033[91m✘ FAIL\033[0m"


def _check(label: str, condition: bool) -> bool:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    return condition


# ---------------------------------------------------------------------------
# Helpers — calculations that mirror the spec's formulae
# ---------------------------------------------------------------------------

def _calc_scope1(fuel: str, consumption_kg_day: float, operating_days: int) -> float:
    """Annual Scope 1 CO2 (tCO2/yr) using KB v2.0 values only."""
    ncv = get_ncv_value(fuel)                   # MJ/kg  (TJ/kt = MJ/kg numerically)
    ef = get_emission_factor_value(fuel)         # tCO2/TJ
    annual_kg = consumption_kg_day * operating_days
    energy_tj = (annual_kg / 1_000_000.0) * ncv
    return energy_tj * ef


def _calc_scope2(elec_kwh_day: float, operating_days: int,
                 grid_factor_kgco2e_per_kwh: float = 0.7117) -> float:
    """Annual Scope 2 CO2 (tCO2e/yr) using CEA weighted-average default."""
    annual_kwh = elec_kwh_day * operating_days
    return annual_kwh * grid_factor_kgco2e_per_kwh / 1000.0


# ---------------------------------------------------------------------------
# E.1 — Textile Dyeing, Coal-fired Boiler (all High/Medium confidence)
# ---------------------------------------------------------------------------

def test_e1_textile_coal():
    print("\n── E.1 Textile Dyeing · Coal Boiler ──────────────────────────")

    fuel = "coal"
    consumption_kg_day = 500.0
    operating_days = 280
    elec_kwh_day = 800.0

    # Expected from spec §E.1 (derived from KB values only)
    # NCV (coal) = 19.63 TJ/kt = 19.63 MJ/kg
    # EF  (coal) = 96.10 tCO2/TJ
    # Annual coal = 500 × 280 = 140,000 kg
    # E_input = 140,000 × 19.63 MJ/kg = 2,748,200 MJ = 2.7482 TJ
    # CO2_s1  = 2.7482 × 96.10 = 264.1 tCO2/yr  (±1 tCO2 tolerance)
    # CO2_s2  = 800 × 280 × 0.7117 / 1000 = 159.4 tCO2e/yr

    ncv = get_ncv_value(fuel)
    ef  = get_emission_factor_value(fuel)
    co2_s1 = _calc_scope1(fuel, consumption_kg_day, operating_days)
    co2_s2 = _calc_scope2(elec_kwh_day, operating_days)
    e_input_mj = (consumption_kg_day * operating_days) * ncv

    all_ok = True
    all_ok &= _check(f"NCV coal = {ncv} (expected 19.63)", abs(ncv - 19.63) < 0.01)
    all_ok &= _check(f"EF coal = {ef} (expected 96.10)", abs(ef - 96.10) < 0.01)
    all_ok &= _check(
        f"E_input = {e_input_mj:,.0f} MJ (expected ~2,748,200)",
        abs(e_input_mj - 2_748_200) < 100,
    )
    all_ok &= _check(
        f"Scope 1 CO2 = {co2_s1:.1f} tCO2/yr (expected ~264.1)",
        abs(co2_s1 - 264.1) < 1.5,
    )
    all_ok &= _check(
        f"Scope 2 CO2 = {co2_s2:.1f} tCO2e/yr (expected ~159.4)",
        abs(co2_s2 - 159.4) < 1.0,
    )

    # Quality checks — coal EF and NCV are High/Medium; no blocking expected
    ef_record = load_emission_factors()["coal"]
    ef_status = KnowledgeRepository.validate_parameter(ef_record, "emission_factor",
                                                        "emission_factor (coal)")
    ncv_status = KnowledgeRepository.validate_parameter(ef_record, "ncv",
                                                         "ncv (coal)")
    all_ok &= _check("emission_factor.ok = True (High confidence)", ef_status["ok"])
    all_ok &= _check("ncv.ok = True (Medium confidence)", ncv_status["ok"])
    all_ok &= _check("emission_factor has no blocking warnings", len([
        w for w in ef_status["warnings"] if "Low" in w
    ]) == 0)
    all_ok &= _check("ncv has no blocking warnings (Medium != Low)", len([
        w for w in ncv_status["warnings"] if "Low" in w
    ]) == 0)
    all_ok &= _check("firm_recommendation NOT blocked", not ef_status["ok"] is False)

    return all_ok


# ---------------------------------------------------------------------------
# E.2 — Dairy, Biomass Boiler (Low-confidence NCV test)
# ---------------------------------------------------------------------------

def test_e2_dairy_biomass():
    print("\n── E.2 Dairy · Biomass Boiler (Low NCV confidence) ───────────")

    fuel = "biomass"
    consumption_kg_day = 300.0
    operating_days = 300
    elec_kwh_day = 400.0

    # NCV (biomass) = 15.6 MJ/kg  [confidence = "Low"]
    # EF  (biomass) = 100.0 tCO2/TJ [confidence = "High"]
    # Annual biomass = 300 × 300 = 90,000 kg
    # E_input = 90,000 × 15.6 = 1,404,000 MJ = 1.404 TJ
    # CO2_s1  = 1.404 × 100.0 = 140.4 tCO2/yr (biogenic gross)

    ncv = get_ncv_value(fuel)
    ef  = get_emission_factor_value(fuel)
    co2_s1 = _calc_scope1(fuel, consumption_kg_day, operating_days)
    e_input_mj = (consumption_kg_day * operating_days) * ncv

    all_ok = True
    all_ok &= _check(f"NCV biomass = {ncv} (expected 15.6)", abs(ncv - 15.6) < 0.01)
    all_ok &= _check(f"EF biomass = {ef} (expected 100.0)", abs(ef - 100.0) < 0.01)
    all_ok &= _check(
        f"E_input = {e_input_mj:,.0f} MJ (expected 1,404,000)",
        abs(e_input_mj - 1_404_000) < 100,
    )
    all_ok &= _check(
        f"Scope 1 CO2 = {co2_s1:.1f} tCO2/yr (expected 140.4)",
        abs(co2_s1 - 140.4) < 1.0,
    )

    # Critical: NCV confidence is "Low" → must produce a warning but not block
    ef_record = load_emission_factors()["biomass"]
    ncv_status = KnowledgeRepository.validate_parameter(ef_record, "ncv",
                                                         "ncv (biomass)")
    ef_status  = KnowledgeRepository.validate_parameter(ef_record, "emission_factor",
                                                         "emission_factor (biomass)")

    all_ok &= _check("ncv.ok = True (value and source_id present)", ncv_status["ok"])
    all_ok &= _check(
        "ncv.confidence = 'Low' → warning generated",
        any("Low" in w for w in ncv_status["warnings"]),
    )
    all_ok &= _check(
        "ncv is NOT blocking (value is present, source_id present)",
        len(ncv_status["errors"]) == 0,
    )
    all_ok &= _check("emission_factor.ok = True (High confidence)", ef_status["ok"])
    all_ok &= _check(
        "emission_factor has NO Low-confidence warnings",
        not any("Low" in w for w in ef_status["warnings"]),
    )

    print(f"  [INFO] NCV warning: {ncv_status['warnings'][0] if ncv_status['warnings'] else 'none'}")

    return all_ok


# ---------------------------------------------------------------------------
# E.3 — Missing source_id → firm recommendation MUST be blocked
# ---------------------------------------------------------------------------

def test_e3_missing_source_id_blocks():
    print("\n── E.3 Missing source_id → Firm Recommendation Blocked ────────")

    # Construct an artificial parameter record without a source_id
    synthetic_record = {
        "emission_factor": {
            "value": 80.0,
            "unit": "tCO2/TJ",
            "confidence": "High",
            # source_id intentionally absent
            "last_verified": "2026-09-12",
        },
        "ncv": {
            "value": 25.0,
            "unit": "MJ/kg",
            "confidence": "High",
            "source_id": "SRC001",
            "last_verified": "2026-09-12",
        },
    }

    ef_status = KnowledgeRepository.validate_parameter(
        synthetic_record, "emission_factor", "emission_factor (synthetic)"
    )

    all_ok = True
    all_ok &= _check("ef_status.ok = False (no source_id)", not ef_status["ok"])
    all_ok &= _check(
        "error mentions source_id",
        any("source_id" in e for e in ef_status["errors"]),
    )
    all_ok &= _check("no value error (value is present)", not any(
        "no value" in e.lower() for e in ef_status["errors"]
    ))
    print(f"  [INFO] Error: {ef_status['errors'][0] if ef_status['errors'] else 'none'}")

    return all_ok


# ---------------------------------------------------------------------------
# E.4 — Missing value → firm recommendation MUST be blocked
# ---------------------------------------------------------------------------

def test_e4_missing_value_blocks():
    print("\n── E.4 Missing value → Firm Recommendation Blocked ────────────")

    synthetic_record = {
        "capex_per_kw": {
            "value": None,
            "unit": "INR/kW",
            "confidence": "Low",
            "source_id": "SRC_PROJECT_DEFAULTS",
            "last_verified": "2026-09-12",
        }
    }

    status = KnowledgeRepository.validate_parameter(
        synthetic_record, "capex_per_kw", "capex_per_kw (heat_pump)"
    )

    all_ok = True
    all_ok &= _check("status.ok = False (value is None)", not status["ok"])
    all_ok &= _check("error mentions value", any(
        "no value" in e.lower() for e in status["errors"]
    ))
    print(f"  [INFO] Error: {status['errors'][0] if status['errors'] else 'none'}")

    return all_ok


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    print("═" * 60)
    print("  Baseline Engine v2.0 Quality Gate — Test Suite")
    print("═" * 60)

    results = [
        test_e1_textile_coal(),
        test_e2_dairy_biomass(),
        test_e3_missing_source_id_blocks(),
        test_e4_missing_value_blocks(),
    ]

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print()
    print("═" * 60)
    if failed == 0:
        print(f"  \033[92mAll {total} test groups PASSED\033[0m")
    else:
        print(f"  \033[91m{failed}/{total} test groups FAILED\033[0m")
    print("═" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

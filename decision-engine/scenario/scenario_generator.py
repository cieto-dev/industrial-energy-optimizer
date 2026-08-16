import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

TECHNOLOGY_DIR = BASE_DIR / "decision-engine" / "technology"
EMISSION_DIR = BASE_DIR / "decision-engine" / "emissions"

sys.path.insert(0, str(TECHNOLOGY_DIR))
sys.path.insert(0, str(EMISSION_DIR))

from technology_engine import calculate_biogas
from co2_calculator import calculate_biogas_co2


def generate_biogas_scenario(
    existing_fuel,
    heat_demand_kwh_day,
    efficiency=0.80
):
    """Generate a Biogas replacement scenario."""

    technology_result = calculate_biogas(
        heat_demand_kwh_day=heat_demand_kwh_day,
        efficiency=efficiency
    )

    biogas_required = technology_result["biogas_required_m3_day"]

    emission_result = calculate_biogas_co2(
        biogas_required
    )

    return {
        "scenario": "fuel_replacement",
        "existing_fuel": existing_fuel,
        "replacement_technology": "biogas",
        "heat_demand_kwh_day": heat_demand_kwh_day,
        "efficiency": efficiency,
        "biogas_required_m3_day": biogas_required,
        "co2_kg_day": emission_result["co2_kg_day"],
        "co2_tco2_day": emission_result["co2_tco2_day"],
        "feasible": technology_result["feasible"]
    }


if __name__ == "__main__":

    print("Biogas Replacement Scenario")
    print("---------------------------")

    result = generate_biogas_scenario(
        existing_fuel="coal",
        heat_demand_kwh_day=10000,
        efficiency=0.80
    )

    for key, value in result.items():
        print(f"{key}: {value}")

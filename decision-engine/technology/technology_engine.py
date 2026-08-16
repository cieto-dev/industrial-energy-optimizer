import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EMISSION_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "emissions"
    / "emission_factors.json"
)


def load_emission_factors():
    with open(EMISSION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_biogas(
    heat_demand_kwh_day,
    efficiency=0.80
):
    """
    Calculate biogas consumption required for
    a given daily useful heat demand.

    heat_demand_kwh_day:
        Useful heat demand in kWh/day

    efficiency:
        Boiler efficiency as decimal.
        Example: 0.80 = 80%
    """

    if heat_demand_kwh_day <= 0:
        raise ValueError("Heat demand must be greater than zero.")

    if not 0 < efficiency <= 1:
        raise ValueError("Efficiency must be between 0 and 1.")

    factors = load_emission_factors()

    biogas = factors["biogas"]

    ncv_mj_m3 = biogas["ncv"]

    # Convert useful heat from kWh/day to MJ/day
    heat_demand_mj_day = heat_demand_kwh_day * 3.6

    # Required fuel energy
    fuel_energy_mj_day = heat_demand_mj_day / efficiency

    # Biogas volume required
    biogas_m3_day = fuel_energy_mj_day / ncv_mj_m3

    return {
        "technology": "biogas",
        "heat_demand_kwh_day": heat_demand_kwh_day,
        "heat_demand_mj_day": round(heat_demand_mj_day, 2),
        "efficiency": efficiency,
        "efficiency_percent": efficiency * 100,
        "biogas_ncv_mj_m3": ncv_mj_m3,
        "biogas_required_m3_day": round(biogas_m3_day, 2),
        "feasible": True
    }


if __name__ == "__main__":

    print("Biogas Technology Engine")
    print("------------------------")

    result = calculate_biogas(
        heat_demand_kwh_day=10000,
        efficiency=0.80
    )

    for key, value in result.items():
        print(f"{key}: {value}")

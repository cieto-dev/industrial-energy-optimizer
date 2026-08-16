import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EMISSION_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "emission_factors.json"
)


def load_emission_factors():
    with open(EMISSION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_biogas_co2(biogas_m3_day):
    """
    Calculate biogas CO2 emissions using:
    
    Energy = biogas volume × NCV
    CO2 = Energy × emission factor
    """

    factors = load_emission_factors()
    biogas = factors["biogas"]

    ncv_mj_m3 = biogas["ncv"]
    emission_factor_tco2_tj = biogas["emission_factor"]

    energy_mj_day = biogas_m3_day * ncv_mj_m3
    energy_tj_day = energy_mj_day / 1_000_000

    co2_tco2_day = energy_tj_day * emission_factor_tco2_tj

    return {
        "fuel": "biogas",
        "fuel_consumption_m3_day": biogas_m3_day,
        "energy_mj_day": round(energy_mj_day, 2),
        "energy_tj_day": round(energy_tj_day, 6),
        "emission_factor_tco2_tj": emission_factor_tco2_tj,
        "co2_tco2_day": round(co2_tco2_day, 4),
        "co2_kg_day": round(co2_tco2_day * 1000, 2)
    }


if __name__ == "__main__":

    biogas_required = 2263.58

    result = calculate_biogas_co2(biogas_required)

    print("Biogas CO2 Calculator")
    print("---------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

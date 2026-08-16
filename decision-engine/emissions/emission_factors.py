import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EMISSION_FACTORS_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "emission_factors.json"
)


def load_emission_factors():
    """Load standard emission factors from the knowledge base."""

    with open(EMISSION_FACTORS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_emission_factor(fuel):
    """Return emission-factor data for a fuel."""

    fuel = fuel.lower().strip()

    factors = load_emission_factors()

    if fuel not in factors:
        raise ValueError(f"Unknown fuel: {fuel}")

    return factors[fuel]


if __name__ == "__main__":

    print("Emission Factors")
    print("----------------")

    factors = load_emission_factors()

    for fuel, data in factors.items():
        print(
            f"{fuel}: "
            f"{data.get('emission_factor')} "
            f"{data.get('unit')}"
        )

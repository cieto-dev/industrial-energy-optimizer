import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

FUEL_RULES_FILE = BASE_DIR / "knowledge-base" / "constraints" / "fuel.json"
TECHNOLOGY_RULES_FILE = BASE_DIR / "knowledge-base" / "constraints" / "technology_rules.json"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_candidate_technologies(fuel):
    """
    Find technologies that can potentially replace the given fuel.
    """

    fuel = fuel.lower().strip()

    fuel_rules = load_json(FUEL_RULES_FILE)

    if fuel not in fuel_rules:
        return []

    return fuel_rules[fuel]


def match_biogas(fuel, industry=None):
    """
    Check whether biogas is a candidate for replacing the current fuel.
    """

    fuel = fuel.lower().strip()

    fuel_rules = load_json(FUEL_RULES_FILE)
    technology_rules = load_json(TECHNOLOGY_RULES_FILE)

    if fuel not in fuel_rules:
        return False

    if "biogas" not in fuel_rules[fuel]:
        return False

    biogas_rules = technology_rules.get("biogas", {})

    if industry:
        industry = industry.lower().strip()

        allowed_industries = biogas_rules.get(
            "allowed_industries", []
        )

        if industry not in allowed_industries:
            return False

    return fuel in biogas_rules.get("replaces_fuels", [])


if __name__ == "__main__":

    print("Biogas Technology Matcher")
    print("-------------------------")

    test_fuels = [
        "coal",
        "diesel",
        "lpg",
        "natural_gas",
        "biomass"
    ]

    for fuel in test_fuels:

        result = match_biogas(
            fuel,
            industry="textile"
        )

        print(f"{fuel} -> biogas: {result}")

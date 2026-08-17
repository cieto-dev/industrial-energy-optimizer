import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

RULES_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "technology_rules.json"
)


def load_rules():
    with open(RULES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def filter_biogas(
    fuel,
    industry,
    biogas_supply=True,
    gas_cleaning=True,
    gas_storage=True
):
    """
    Check whether biogas is technically eligible
    under the project-level technology rules.
    """

    rules = load_rules()
    biogas_rules = rules.get("biogas")

    if not biogas_rules:
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Biogas rules not found"
        }

    fuel = fuel.lower().strip()
    industry = industry.lower().strip()

    # Check whether biogas can replace the existing fuel
    if fuel not in biogas_rules.get("replaces_fuels", []):
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": f"Biogas is not configured to replace {fuel}"
        }

    # Check industry
    if industry not in biogas_rules.get("allowed_industries", []):
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": f"Industry '{industry}' is not in the project eligibility rules"
        }

    # Check biogas supply
    if biogas_rules.get("requires_biogas_supply") and not biogas_supply:
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Reliable biogas supply is required"
        }

    # Check gas cleaning
    if biogas_rules.get("requires_gas_cleaning") and not gas_cleaning:
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Gas cleaning is required"
        }

    # Check gas storage
    if biogas_rules.get("requires_gas_storage") and not gas_storage:
        return {
            "technology": "biogas",
            "feasible": False,
            "reason": "Gas storage is required"
        }

    return {
        "technology": "biogas",
        "feasible": True,
        "reason": "Biogas satisfies the configured project-level eligibility rules"
    }


if __name__ == "__main__":

    print("Biogas Technology Filter")
    print("------------------------")

    result = filter_biogas(
        fuel="coal",
        industry="textile",
        biogas_supply=True,
        gas_cleaning=True,
        gas_storage=True
    )

    print(result)

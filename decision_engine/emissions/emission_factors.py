"""
Emission-factor and grid-factor loaders.

Fuel emission factors come from knowledge-base/emissions/emission_factors.json.
Grid factors come from knowledge-base/emissions/grid_factors.json and carry an
explicit accounting basis (never a silent numeric default).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]

EMISSION_FACTORS_FILE = (
    BASE_DIR / "knowledge-base" / "emissions" / "emission_factors.json"
)

GRID_FACTORS_FILE = (
    BASE_DIR / "knowledge-base" / "emissions" / "grid_factors.json"
)


def load_emission_factors() -> dict[str, Any]:
    """Load standard fuel emission factors from the knowledge base."""
    with open(EMISSION_FACTORS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_emission_factor(fuel: str) -> dict[str, Any]:
    """Return emission-factor data for a fuel."""
    fuel = fuel.lower().strip()
    factors = load_emission_factors()
    if fuel not in factors:
        raise ValueError(f"Unknown fuel: {fuel}")
    return factors[fuel]


def load_grid_factors() -> dict[str, Any]:
    """Load the full grid-factor knowledge-base document."""
    if not GRID_FACTORS_FILE.exists():
        raise FileNotFoundError(
            f"Grid factors file not found: {GRID_FACTORS_FILE}"
        )
    with open(GRID_FACTORS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_grid_emission_factor(
    basis: str | None = None,
) -> dict[str, Any]:
    """
    Resolve a grid emission factor with full accounting metadata.

    Parameters
    ----------
    basis :
        One of the keys under ``factors`` in grid_factors.json, or None
        to use the project's declared default_basis
        (``weighted_average_including_res_and_captive``).

    Returns
    -------
    dict with at least:
        value, unit, type/basis, reporting_year, source_id, source_type,
        confidence, applicability, accounting_rationale
    """
    data = load_grid_factors()

    if basis is None:
        policy = data.get("accounting_policy", {})
        basis = policy.get(
            "default_basis",
            data.get("default_factor", {}).get(
                "type", "weighted_average_including_res_and_captive"
            ),
        )

    basis = str(basis).strip().lower()

    factors = data.get("factors", {})
    if basis not in factors:
        available = sorted(factors.keys())
        raise ValueError(
            f"Unknown grid emission factor basis '{basis}'. "
            f"Available bases: {available}. "
            "Do not invent or average factors."
        )

    selected = dict(factors[basis])
    selected["type"] = basis
    selected["basis_key"] = basis

    # Attach top-level source / policy context for provenance
    source = data.get("source", {})
    selected.setdefault("source_id", source.get("source_id"))
    selected.setdefault("source_type", source.get("source_type"))
    selected["source_document"] = source.get("document")
    selected["source_version"] = source.get("version")
    selected["source_organization"] = source.get("organization")

    policy = data.get("accounting_policy", {})
    selected["accounting_rationale"] = policy.get("rationale")
    selected["scope2_alignment"] = policy.get("scope2_alignment")
    selected["is_project_default"] = (
        basis == policy.get("default_basis")
    )

    value = selected.get("value")
    if value is None or not isinstance(value, (int, float)):
        raise ValueError(
            f"Grid factor '{basis}' has no numeric value."
        )
    if float(value) < 0:
        raise ValueError(
            f"Grid factor '{basis}' must be non-negative."
        )

    selected["value"] = float(value)
    return selected


if __name__ == "__main__":
    print("Fuel Emission Factors")
    print("---------------------")
    for fuel, data in load_emission_factors().items():
        print(
            f"{fuel}: "
            f"{data.get('emission_factor')} "
            f"{data.get('unit')}"
        )

    print("\nGrid Emission Factors (explicit bases)")
    print("--------------------------------------")
    grid = load_grid_factors()
    for key, f in grid.get("factors", {}).items():
        print(
            f"{key}: {f.get('value')} {f.get('unit')} "
            f"({f.get('reporting_year')})"
        )

    default = get_grid_emission_factor()
    print("\nResolved default:")
    for k, v in default.items():
        print(f"  {k}: {v}")
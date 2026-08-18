"""
convert_datasets.py — CSV → Canonical JSON Converter

Converts raw CSV datasets (biomass atlas, tariffs, temperature ranges,
industrial fuels, district coordinates) into a canonical internal JSON
format under datasets/converted/.

Part of Task 4.1 ETL Pipeline.

Usage:
    python scripts/convert_datasets.py
"""

import csv
import json
import os
import sys
from pathlib import Path


# --------------------------------------------------
# Path Configuration
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
CONVERTED_DIR = DATASETS_DIR / "converted"


def ensure_output_dir():
    """Create the converted output directory if it doesn't exist."""
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Output directory: {CONVERTED_DIR}")


# --------------------------------------------------
# CSV Reading Helper
# --------------------------------------------------

def read_csv(filepath: Path) -> list[dict]:
    """Read a CSV file and return a list of row dictionaries."""

    if not filepath.exists():
        print(f"[WARN] File not found: {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]

    print(f"[INFO] Read {len(rows)} rows from {filepath.name}")
    return rows


def write_json(data: dict, filepath: Path):
    """Write data to a JSON file with pretty formatting."""

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    size_kb = filepath.stat().st_size / 1024
    print(f"[INFO] Wrote {filepath.name} ({size_kb:.1f} KB)")


# --------------------------------------------------
# 1. Biomass Atlas
# --------------------------------------------------

def convert_biomass_atlas():
    """
    Convert biomass_atlas.csv to canonical JSON.

    Input columns: state, district, biomass_type, crop,
        annual_availability_tons, availability_type, year,
        moisture_percent, calorific_value_mj_kg, cost_rs_per_ton,
        latitude, longitude, source
    """

    print("\n--- Converting biomass_atlas.csv ---")
    rows = read_csv(DATASETS_DIR / "biomass_atlas.csv")

    if not rows:
        return

    records = []
    for row in rows:
        record = {
            "state": row.get("state", "").strip(),
            "district": row.get("district", "").strip(),
            "biomass_type": row.get("biomass_type", "").strip(),
            "crop": row.get("crop", "").strip(),
            "annual_availability_tons": _parse_float(
                row.get("annual_availability_tons")
            ),
            "availability_type": row.get("availability_type", "").strip(),
            "year": row.get("year", "").strip(),
            "moisture_percent": _parse_float(
                row.get("moisture_percent")
            ),
            "calorific_value_mj_kg": _parse_float(
                row.get("calorific_value_mj_kg")
            ),
            "cost_rs_per_ton": _parse_float(
                row.get("cost_rs_per_ton")
            ),
            "latitude": _parse_float(row.get("latitude")),
            "longitude": _parse_float(row.get("longitude")),
            "source": row.get("source", "").strip(),
        }
        records.append(record)

    output = {
        "_meta": {
            "source_file": "datasets/biomass_atlas.csv",
            "record_count": len(records),
            "description": "District-wise biomass availability data "
                           "from National Biomass Atlas of India",
        },
        "records": records,
    }

    write_json(output, CONVERTED_DIR / "biomass_atlas.json")


# --------------------------------------------------
# 2. Temperature Ranges
# --------------------------------------------------

def convert_temperature_ranges():
    """
    Convert temperature_ranges.csv to canonical JSON.

    Input columns: technology_id, technology_name,
        min_output_temp_c, max_output_temp_c, temperature_type,
        source, source_reference, notes, official_resource,
        official_resource_url
    """

    print("\n--- Converting temperature_ranges.csv ---")
    rows = read_csv(DATASETS_DIR / "temperature_ranges.csv")

    if not rows:
        return

    records = []
    for row in rows:
        record = {
            "technology_id": row.get("technology_id", "").strip(),
            "technology_name": row.get("technology_name", "").strip(),
            "min_output_temp_c": _parse_float(
                row.get("min_output_temp_c")
            ),
            "max_output_temp_c": _parse_float(
                row.get("max_output_temp_c")
            ),
            "temperature_type": row.get("temperature_type", "").strip(),
            "source": row.get("source", "").strip(),
            "source_reference": row.get("source_reference", "").strip(),
            "notes": row.get("notes", "").strip(),
            "official_resource": row.get("official_resource", "").strip(),
            "official_resource_url": row.get(
                "official_resource_url", ""
            ).strip(),
        }
        records.append(record)

    output = {
        "_meta": {
            "source_file": "datasets/temperature_ranges.csv",
            "record_count": len(records),
            "description": "Technology operating temperature ranges "
                           "from IEA, DOE, and official sources",
        },
        "records": records,
    }

    write_json(output, CONVERTED_DIR / "temperature_ranges.json")


# --------------------------------------------------
# 3. Industrial Fuels
# --------------------------------------------------

def convert_industrial_fuels():
    """
    Convert industrial_fuels.csv to canonical JSON.

    Input columns: Fuel Category, Fuel, Variant / Grade, Unit,
        Typical Industrial Cost ₹/Unit, GCV, GCV Unit,
        CO₂ Factor, CO₂ Unit, Recommended Source
    """

    print("\n--- Converting industrial_fuels.csv ---")
    rows = read_csv(DATASETS_DIR / "industrial_fuels.csv")

    if not rows:
        return

    records = []
    for row in rows:
        record = {
            "fuel_category": row.get("Fuel Category", "").strip(),
            "fuel": row.get("Fuel", "").strip(),
            "variant_grade": row.get("Variant / Grade", "").strip(),
            "unit": row.get("Unit", "").strip(),
            "cost_rs_per_unit": _parse_float(
                row.get("Typical Industrial Cost ₹/Unit")
            ),
            "gcv": _parse_float(row.get("GCV")),
            "gcv_unit": row.get("GCV Unit", "").strip(),
            "co2_factor": _parse_float(row.get("CO₂ Factor")),
            "co2_unit": row.get("CO₂ Unit", "").strip(),
            "source": row.get("Recommended Source", "").strip(),
        }
        records.append(record)

    output = {
        "_meta": {
            "source_file": "datasets/industrial_fuels.csv",
            "record_count": len(records),
            "description": "Industrial fuel properties, costs, and "
                           "emission factors from BEE/IPCC",
        },
        "records": records,
    }

    write_json(output, CONVERTED_DIR / "industrial_fuels.json")


# --------------------------------------------------
# 4. District Coordinates
# --------------------------------------------------

def convert_district_coordinates():
    """
    Convert district_coordinates.csv to canonical JSON.

    Input columns: District, State, Latitude, Longitude
    """

    print("\n--- Converting district_coordinates.csv ---")
    rows = read_csv(DATASETS_DIR / "district_coordinates.csv")

    if not rows:
        return

    records = []
    for row in rows:
        record = {
            "district": row.get("District", "").strip(),
            "state": row.get("State", "").strip(),
            "latitude": _parse_float(row.get("Latitude")),
            "longitude": _parse_float(row.get("Longitude")),
        }
        records.append(record)

    output = {
        "_meta": {
            "source_file": "datasets/district_coordinates.csv",
            "record_count": len(records),
            "description": "District-level geographic coordinates "
                           "for resource lookups",
        },
        "records": records,
    }

    write_json(output, CONVERTED_DIR / "district_coordinates.json")


# --------------------------------------------------
# 5. Electricity Tariffs
# --------------------------------------------------

def convert_electricity_tariffs():
    """
    Convert electricity_tariffs/tariff_master.csv to canonical JSON.

    The tariff_master.csv is the primary tariff file with
    state-level industrial electricity rates.
    """

    print("\n--- Converting electricity_tariffs ---")
    tariff_dir = DATASETS_DIR / "electricity_tariffs"

    # Primary: tariff_master.csv
    rows = read_csv(tariff_dir / "tariff_master.csv")

    if not rows:
        return

    records = []
    for row in rows:
        record = {
            "tariff_id": row.get("tariff_id", "").strip(),
            "state": row.get("state", "").strip(),
            "state_id": row.get("state_id", "").strip(),
            "discom": row.get("discom", "").strip(),
            "discom_id": row.get("discom_id", "").strip(),
            "consumer_category": row.get(
                "consumer_category", ""
            ).strip(),
            "voltage_level_or_load": row.get(
                "voltage_level_or_load", ""
            ).strip(),
            "energy_charge": _parse_float(
                row.get("energy_charge")
            ),
            "energy_charge_unit": row.get(
                "energy_charge_unit", ""
            ).strip(),
            "fixed_charge": _parse_float(
                row.get("fixed_charge")
            ),
            "fixed_charge_unit": row.get(
                "fixed_charge_unit", ""
            ).strip(),
            "demand_charge": _parse_float(
                row.get("demand_charge")
            ),
            "demand_charge_unit": row.get(
                "demand_charge_unit", ""
            ).strip(),
            "effective_from": row.get("effective_from", "").strip(),
            "tariff_year": row.get("tariff_year", "").strip(),
            "has_tod": row.get("has_tod", "N").strip() == "Y",
            "has_slab": row.get("has_slab", "N").strip() == "Y",
            "notes": row.get("notes", "").strip(),
            "official_source": row.get(
                "official_source", ""
            ).strip(),
            "data_status": row.get("data_status", "").strip(),
            "source_type": row.get("source_type", "").strip(),
        }
        records.append(record)

    output = {
        "_meta": {
            "source_file": "datasets/electricity_tariffs/tariff_master.csv",
            "record_count": len(records),
            "description": "State-wise industrial electricity tariffs "
                           "from DISCOM/regulator official sources",
        },
        "records": records,
    }

    write_json(output, CONVERTED_DIR / "electricity_tariffs.json")


# --------------------------------------------------
# Utility
# --------------------------------------------------

def _parse_float(value) -> float | None:
    """Safely parse a string to float, returning None on failure."""

    if value is None:
        return None

    value = str(value).strip()

    if value == "" or value.lower() in ("na", "n/a", "null", "none", "-"):
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    print("=" * 60)
    print("  convert_datasets.py -- CSV -> Canonical JSON Converter")
    print("=" * 60)

    ensure_output_dir()

    convert_biomass_atlas()
    convert_temperature_ranges()
    convert_industrial_fuels()
    convert_district_coordinates()
    convert_electricity_tariffs()

    print("\n" + "=" * 60)
    print("  Conversion complete!")
    print(f"  Output: {CONVERTED_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

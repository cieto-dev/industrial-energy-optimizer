"""
pre_process.py — Clean, Normalize, and Validate Converted Datasets

Reads the canonical JSON files from datasets/converted/, applies
cleaning (trim, normalize names, remove duplicates), validates
(range checks, required fields), and writes cleaned output back.

Part of Task 4.1 ETL Pipeline.

Usage:
    python scripts/pre_process.py
"""

import json
import sys
from pathlib import Path
from collections import Counter


# --------------------------------------------------
# Path Configuration
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONVERTED_DIR = PROJECT_ROOT / "datasets" / "converted"


# --------------------------------------------------
# Validation Report
# --------------------------------------------------

class ValidationReport:
    """Tracks validation results across all datasets."""

    def __init__(self):
        self.datasets = {}
        self._current = None

    def start_dataset(self, name: str):
        self._current = name
        self.datasets[name] = {
            "original_count": 0,
            "cleaned_count": 0,
            "duplicates_removed": 0,
            "warnings": [],
            "errors": [],
        }

    def set_original_count(self, count: int):
        self.datasets[self._current]["original_count"] = count

    def set_cleaned_count(self, count: int):
        self.datasets[self._current]["cleaned_count"] = count

    def set_duplicates_removed(self, count: int):
        self.datasets[self._current]["duplicates_removed"] = count

    def warn(self, message: str):
        self.datasets[self._current]["warnings"].append(message)

    def error(self, message: str):
        self.datasets[self._current]["errors"].append(message)

    def print_report(self):
        print("\n" + "=" * 60)
        print("  VALIDATION REPORT")
        print("=" * 60)

        total_warnings = 0
        total_errors = 0

        for name, stats in self.datasets.items():
            warn_count = len(stats["warnings"])
            err_count = len(stats["errors"])
            total_warnings += warn_count
            total_errors += err_count

            status = "[PASS]" if err_count == 0 else "[FAIL]"
            print(f"\n  {name}: {status}")
            print(f"    Records: {stats['original_count']}"
                  f" -> {stats['cleaned_count']}")

            if stats["duplicates_removed"] > 0:
                print(f"    Duplicates removed: "
                      f"{stats['duplicates_removed']}")

            if warn_count > 0:
                print(f"    Warnings ({warn_count}):")
                for w in stats["warnings"][:5]:
                    print(f"      [!] {w}")
                if warn_count > 5:
                    print(f"      ... and {warn_count - 5} more")

            if err_count > 0:
                print(f"    Errors ({err_count}):")
                for e in stats["errors"][:5]:
                    print(f"      [X] {e}")
                if err_count > 5:
                    print(f"      ... and {err_count - 5} more")

        print(f"\n  TOTAL: {total_warnings} warnings, "
              f"{total_errors} errors")
        print("=" * 60)

        return total_errors == 0


report = ValidationReport()


# --------------------------------------------------
# JSON I/O
# --------------------------------------------------

def load_json(filepath: Path) -> dict | None:
    """Load a JSON file, returning None if not found."""

    if not filepath.exists():
        print(f"[SKIP] Not found: {filepath.name}")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, filepath: Path):
    """Write cleaned data back to JSON."""

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --------------------------------------------------
# Generic Cleaning Utilities
# --------------------------------------------------

def normalize_string(value: str | None) -> str:
    """Strip whitespace from a string value."""

    if value is None:
        return ""
    return str(value).strip()


def normalize_name(value: str | None) -> str:
    """Normalize a place name: strip and title-case."""

    if value is None:
        return ""
    return str(value).strip().title()


def validate_positive(value, field_name: str, row_idx: int) -> bool:
    """Check that a numeric value is positive (if present)."""

    if value is None:
        return True  # None is acceptable (optional field)

    if isinstance(value, (int, float)) and value < 0:
        report.warn(
            f"Row {row_idx}: {field_name} is negative ({value})"
        )
        return False

    return True


def remove_duplicates(
    records: list[dict],
    key_fields: list[str],
) -> list[dict]:
    """Remove duplicate records based on key fields."""

    seen = set()
    unique = []

    for record in records:
        key = tuple(record.get(f) for f in key_fields)
        if key not in seen:
            seen.add(key)
            unique.append(record)

    removed = len(records) - len(unique)
    if removed > 0:
        report.set_duplicates_removed(removed)

    return unique


# --------------------------------------------------
# 1. Biomass Atlas
# --------------------------------------------------

def clean_biomass_atlas():
    """Clean and validate biomass_atlas.json."""

    filepath = CONVERTED_DIR / "biomass_atlas.json"
    data = load_json(filepath)

    if data is None:
        return

    report.start_dataset("biomass_atlas")
    records = data.get("records", [])
    report.set_original_count(len(records))

    cleaned = []
    for i, rec in enumerate(records):
        # Normalize place names
        rec["state"] = normalize_name(rec.get("state"))
        rec["district"] = normalize_name(rec.get("district"))
        rec["biomass_type"] = normalize_string(rec.get("biomass_type"))
        rec["crop"] = normalize_string(rec.get("crop"))

        # Validate required fields
        if not rec["state"]:
            report.error(f"Row {i}: missing state")
            continue
        if not rec["district"]:
            report.error(f"Row {i}: missing district")
            continue

        # Validate numeric ranges
        validate_positive(
            rec.get("annual_availability_tons"),
            "annual_availability_tons", i,
        )
        validate_positive(
            rec.get("cost_rs_per_ton"),
            "cost_rs_per_ton", i,
        )
        validate_positive(
            rec.get("calorific_value_mj_kg"),
            "calorific_value_mj_kg", i,
        )

        # Validate moisture percent 0-100
        moisture = rec.get("moisture_percent")
        if moisture is not None and (moisture < 0 or moisture > 100):
            report.warn(
                f"Row {i}: moisture_percent out of range ({moisture})"
            )

        cleaned.append(rec)

    # Remove duplicates by state+district+biomass_type+crop
    cleaned = remove_duplicates(
        cleaned,
        ["state", "district", "biomass_type", "crop"],
    )

    report.set_cleaned_count(len(cleaned))
    data["records"] = cleaned
    data["_meta"]["record_count"] = len(cleaned)
    data["_meta"]["cleaned"] = True
    save_json(data, filepath)


# --------------------------------------------------
# 2. Temperature Ranges
# --------------------------------------------------

def clean_temperature_ranges():
    """Clean and validate temperature_ranges.json."""

    filepath = CONVERTED_DIR / "temperature_ranges.json"
    data = load_json(filepath)

    if data is None:
        return

    report.start_dataset("temperature_ranges")
    records = data.get("records", [])
    report.set_original_count(len(records))

    cleaned = []
    for i, rec in enumerate(records):
        rec["technology_id"] = normalize_string(
            rec.get("technology_id")
        )
        rec["technology_name"] = normalize_string(
            rec.get("technology_name")
        )

        # Validate required fields
        if not rec["technology_id"]:
            report.error(f"Row {i}: missing technology_id")
            continue

        # Validate temperature range
        min_temp = rec.get("min_output_temp_c")
        max_temp = rec.get("max_output_temp_c")

        if min_temp is not None and max_temp is not None:
            if min_temp > max_temp:
                report.error(
                    f"Row {i}: min_temp ({min_temp}) > "
                    f"max_temp ({max_temp})"
                )
                continue

        if min_temp is not None and min_temp < -273:
            report.error(
                f"Row {i}: min_temp below absolute zero ({min_temp})"
            )
            continue

        cleaned.append(rec)

    cleaned = remove_duplicates(cleaned, ["technology_id"])
    report.set_cleaned_count(len(cleaned))
    data["records"] = cleaned
    data["_meta"]["record_count"] = len(cleaned)
    data["_meta"]["cleaned"] = True
    save_json(data, filepath)


# --------------------------------------------------
# 3. Industrial Fuels
# --------------------------------------------------

def clean_industrial_fuels():
    """Clean and validate industrial_fuels.json."""

    filepath = CONVERTED_DIR / "industrial_fuels.json"
    data = load_json(filepath)

    if data is None:
        return

    report.start_dataset("industrial_fuels")
    records = data.get("records", [])
    report.set_original_count(len(records))

    cleaned = []
    for i, rec in enumerate(records):
        rec["fuel_category"] = normalize_string(
            rec.get("fuel_category")
        )
        rec["fuel"] = normalize_string(rec.get("fuel"))
        rec["variant_grade"] = normalize_string(
            rec.get("variant_grade")
        )

        # Validate required fields
        if not rec["fuel"]:
            report.error(f"Row {i}: missing fuel name")
            continue

        # Validate numeric ranges
        validate_positive(
            rec.get("cost_rs_per_unit"), "cost_rs_per_unit", i
        )
        validate_positive(rec.get("gcv"), "gcv", i)
        validate_positive(rec.get("co2_factor"), "co2_factor", i)

        cleaned.append(rec)

    cleaned = remove_duplicates(
        cleaned, ["fuel", "variant_grade"]
    )
    report.set_cleaned_count(len(cleaned))
    data["records"] = cleaned
    data["_meta"]["record_count"] = len(cleaned)
    data["_meta"]["cleaned"] = True
    save_json(data, filepath)


# --------------------------------------------------
# 4. District Coordinates
# --------------------------------------------------

def clean_district_coordinates():
    """Clean and validate district_coordinates.json."""

    filepath = CONVERTED_DIR / "district_coordinates.json"
    data = load_json(filepath)

    if data is None:
        return

    report.start_dataset("district_coordinates")
    records = data.get("records", [])
    report.set_original_count(len(records))

    cleaned = []
    for i, rec in enumerate(records):
        rec["district"] = normalize_name(rec.get("district"))
        rec["state"] = normalize_name(rec.get("state"))

        # Validate required fields
        if not rec["district"]:
            report.error(f"Row {i}: missing district")
            continue
        if not rec["state"]:
            report.error(f"Row {i}: missing state")
            continue

        # Validate coordinate bounds (India roughly:
        # lat 6-37, lon 68-97)
        lat = rec.get("latitude")
        lon = rec.get("longitude")

        if lat is not None and (lat < 0 or lat > 40):
            report.warn(
                f"Row {i}: latitude ({lat}) out of India range"
            )
        if lon is not None and (lon < 60 or lon > 100):
            report.warn(
                f"Row {i}: longitude ({lon}) out of India range"
            )

        cleaned.append(rec)

    cleaned = remove_duplicates(
        cleaned, ["district", "state"]
    )
    report.set_cleaned_count(len(cleaned))
    data["records"] = cleaned
    data["_meta"]["record_count"] = len(cleaned)
    data["_meta"]["cleaned"] = True
    save_json(data, filepath)


# --------------------------------------------------
# 5. Electricity Tariffs
# --------------------------------------------------

def clean_electricity_tariffs():
    """Clean and validate electricity_tariffs.json."""

    filepath = CONVERTED_DIR / "electricity_tariffs.json"
    data = load_json(filepath)

    if data is None:
        return

    report.start_dataset("electricity_tariffs")
    records = data.get("records", [])
    report.set_original_count(len(records))

    cleaned = []
    for i, rec in enumerate(records):
        rec["state"] = normalize_name(rec.get("state"))
        rec["discom"] = normalize_string(rec.get("discom"))
        rec["tariff_id"] = normalize_string(rec.get("tariff_id"))

        # Validate required fields
        if not rec["state"]:
            report.error(f"Row {i}: missing state")
            continue
        if not rec["tariff_id"]:
            report.error(f"Row {i}: missing tariff_id")
            continue

        # Validate energy charge is reasonable
        energy_charge = rec.get("energy_charge")
        if energy_charge is not None and energy_charge < 0:
            report.warn(
                f"Row {i}: negative energy_charge ({energy_charge})"
            )

        if energy_charge is not None and energy_charge > 50:
            report.warn(
                f"Row {i}: energy_charge seems very high "
                f"({energy_charge} Rs/kVAh)"
            )

        cleaned.append(rec)

    cleaned = remove_duplicates(cleaned, ["tariff_id"])
    report.set_cleaned_count(len(cleaned))
    data["records"] = cleaned
    data["_meta"]["record_count"] = len(cleaned)
    data["_meta"]["cleaned"] = True
    save_json(data, filepath)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    print("=" * 60)
    print("  pre_process.py -- Clean, Normalize, Validate")
    print("=" * 60)

    if not CONVERTED_DIR.exists():
        print("[ERROR] datasets/converted/ not found.")
        print("        Run convert_datasets.py first.")
        sys.exit(1)

    clean_biomass_atlas()
    clean_temperature_ranges()
    clean_industrial_fuels()
    clean_district_coordinates()
    clean_electricity_tariffs()

    passed = report.print_report()

    if not passed:
        print("\n[WARN] Some validations failed. "
              "Review errors above.")
        sys.exit(1)
    else:
        print("\n[OK] All datasets cleaned and validated.")


if __name__ == "__main__":
    main()

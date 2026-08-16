import csv
import json
from pathlib import Path

CSV_FILE = Path("datasets/electricity_tariffs/tariff_master_2026_27_complete_no_empty.csv")
OUTPUT_FILE = Path("knowledge-base/master/tariffs.json")


def clean(value):
    if value is None:
        return ""
    return value.strip()


def convert_value(value):
    value = clean(value)

    if value == "":
        return None

    # Keep IDs, dates, URLs and text as strings.
    return value


def main():
    if not CSV_FILE.exists():
        print(f"ERROR: CSV file not found: {CSV_FILE}")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    tariffs = []

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            tariff = {
                "tariff_id": clean(row["tariff_id"]),
                "state_id": clean(row["state_id"]),
                "discom_id": clean(row["discom_id"]),
                "state": clean(row["state"]),
                "discom": clean(row["discom"]),

                "consumer_category": clean(row["consumer_category"]),
                "voltage_level_or_load": clean(row["voltage_level_or_load"]),

                "energy_charge": convert_value(row["energy_charge"]),
                "energy_charge_unit": clean(row["energy_charge_unit"]),

                "fixed_charge": convert_value(row["fixed_charge"]),
                "fixed_charge_unit": clean(row["fixed_charge_unit"]),

                "demand_charge": convert_value(row["demand_charge"]),
                "demand_charge_unit": clean(row["demand_charge_unit"]),

                "effective_from": clean(row["effective_from"]),
                "tariff_year": clean(row["tariff_year"]),

                "tariff_order_category_label": clean(
                    row["tariff_order_category_label"]
                ),

                "has_tod": clean(row["has_tod"]),
                "has_slab": clean(row["has_slab"]),

                "notes": clean(row["notes"]),
                "official_source": clean(row["official_source"]),

                "data_status": clean(row["data_status"]),
                "source_type": clean(row["source_type"]),
            }

            tariffs.append(tariff)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(tariffs, file, indent=2, ensure_ascii=False)

    print("----------------------------------------")
    print("Tariffs JSON created successfully")
    print("----------------------------------------")
    print(f"CSV rows   : {len(tariffs)}")
    print(f"JSON file  : {OUTPUT_FILE}")

    # Basic validation
    empty_ids = [
        t["tariff_id"]
        for t in tariffs
        if not t["tariff_id"] or not t["state_id"] or not t["discom_id"]
    ]

    if empty_ids:
        print(f"WARNING: {len(empty_ids)} rows have missing IDs")
    else:
        print("ID validation: PASS")

    empty_fields = []

    required_fields = [
        "tariff_id",
        "state_id",
        "discom_id",
        "state",
        "discom",
        "consumer_category",
        "effective_from",
        "tariff_year",
        "official_source",
    ]

    for tariff in tariffs:
        for field in required_fields:
            if not tariff[field]:
                empty_fields.append(
                    (tariff["tariff_id"], field)
                )

    if empty_fields:
        print(f"WARNING: {len(empty_fields)} required fields are empty")
    else:
        print("Required-field validation: PASS")

    print("----------------------------------------")


if __name__ == "__main__":
    main()
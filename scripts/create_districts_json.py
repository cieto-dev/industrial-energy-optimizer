import csv
import json

input_file = "datasets/district_coordinates.csv"
output_file = "knowledge-base/master/districts.json"

state_ids = {
    "Himachal Pradesh": "HP",
    "Punjab": "PB",
    "Uttarakhand": "UK",
    "Haryana": "HR",
    "Uttar Pradesh": "UP",
    "Jammu and Kashmir": "JK",
    "Jammu & Kashmir": "JK"
}

districts = []

with open(input_file, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        district = row["District"].strip()
        state = row["State"].strip()

        state_id = state_ids.get(state)

        if not state_id:
            print(f"WARNING: Unknown state: {state}")
            continue

        district_id = f"{state_id}_{district.upper().replace(' ', '_').replace('-', '_')}"

        districts.append({
            "district_id": district_id,
            "district_name": district,
            "state_id": state_id,
            "latitude": float(row["Latitude"]),
            "longitude": float(row["Longitude"])
        })

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(districts, file, indent=2, ensure_ascii=False)

print(f"Created {len(districts)} districts")
print(f"Output: {output_file}")

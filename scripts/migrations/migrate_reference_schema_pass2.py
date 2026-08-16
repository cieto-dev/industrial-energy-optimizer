#!/usr/bin/env python3
"""Second pass: handles two schema shapes pass 1 doesn't touch.

(a) knowledge-base/finance/*.json: a "sources" dict keyed BY the
    source_id itself (title/publisher/type/pages/... as values) --
    an embedded duplicate of sources.json, just shaped as a dict
    instead of a list.
(b) knowledge-base/industries/{food_processing,chemical,cement}.json:
    source_registry list entries with document/organization/publisher
    but no id/source_id field at all.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KB = REPO / "knowledge-base"
SOURCES_PATH = KB / "references" / "sources.json"

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def save(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

sources = load(SOURCES_PATH)
registered = set(sources.keys())

# --- (a) keyed "sources" dicts in the four finance/*.json files -----------
FINANCE_FILES = [
    KB / "finance" / "electricity_tariffs.json",
    KB / "finance" / "fuel_prices.json",
    KB / "finance" / "subsidies.json",
    KB / "finance" / "technology_costs.json",
]
for f in FINANCE_FILES:
    doc = load(f)
    if "sources" in doc and isinstance(doc["sources"], dict):
        keys = list(doc["sources"].keys())
        collapsible = all(k in registered for k in keys)
        if collapsible and keys:
            doc["sources"] = {k: {"source_id": k} for k in keys}
            save(f, doc)
            print(f"collapsed embedded registry dict in {f.relative_to(REPO)} ({len(keys)} ids)")
        else:
            missing = [k for k in keys if k not in registered]
            print(f"SKIPPED {f.relative_to(REPO)} -- unregistered ids: {missing}")

# --- (b) document/organization-only records, matched by exact title -------
# Maps the exact "document" (or "title") string used in-file to the new
# source_id registered for it in migrate_reference_schema.py's NEW_SOURCES.
TITLE_TO_ID = {
    "Energy Mapping of MSME Food Processing Sector in India / Food Processing Sector Energy Mapping": "bee_food_processing_mapping",
    "Annual Report 2024-25": "mofpi_annual_report",
    "Milk and Milk Product Processing Guidance": "fssai_milk_processing_guidance",
    "Heat Pump Monitor 2026": "iea_heat_pump_monitor_2026",
    "Food processing and post-harvest technology references": "icar_food_processing_reference",
    "Electrifying Industrial Heat in India": "energy_innovation_india_heat_2026",
    "Decarbonizing MSMEs: Use of Biomass for Green Steam and Heat Application": "mnre_giz_biomass_msme",
    "Chemical and Petrochemical Statistics at a Glance 2025": "dcpc_chemical_statistics_2025",
    "Achieving Energy and Resource Efficiency in Chemical Industries": "bee_chemical_efficiency",
    "ADEETIE List of Energy Efficient Technologies": "bee_adeetie",
    "Electrification and Renewables for Industry": "iea_electrification_renewables_industry",
    "Roadmap for Cement Sector Decarbonisation": "niti_cement_decarbonisation_roadmap",
    "PAT Cement Sector Material and Energy Efficient Technology Database": "bee_cement_pat_database",
    "Cement technical reference material": "bis_cement_reference",
    "Driving Energy Efficiency in Heavy Industries - Cement": "iea_heavy_industry_cement",
}

INDUSTRY_FILES = [
    (KB / "industries" / "food_processing.json", "source_registry"),
    (KB / "industries" / "chemical.json", "source_registry"),
    (KB / "industries" / "cement.json", "source_registry"),
]
for f, key in INDUSTRY_FILES:
    doc = load(f)
    records = doc.get(key)
    if not isinstance(records, list):
        continue
    new_records = []
    unmatched = []
    for rec in records:
        title = rec.get("document") or rec.get("title")
        sid = TITLE_TO_ID.get(title)
        if sid and sid in registered:
            new_records.append({"source_id": sid})
        else:
            unmatched.append(title)
            new_records.append(rec)  # leave untouched, flagged below
    doc[key] = new_records
    save(f, doc)
    print(f"{f.relative_to(REPO)}: matched {len(records) - len(unmatched)}/{len(records)}"
          + (f" -- UNMATCHED: {unmatched}" if unmatched else ""))

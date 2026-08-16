#!/usr/bin/env python3
"""
One-time migration: collapses every legacy citation/source schema in the
repo (id/label, publisher+title+data_used, document+organization,
pages/publication_date/type/url, id+publication_year, etc.) down to the
single canonical shape validate_references.py expects:

    knowledge-base/references/sources.json   -> {source_id: {title, organization, year, url}}
    every other knowledge-base/**/*.json      -> {"source_id": "..."} only

Run from repo root:  python scripts/migrate_reference_schema.py
It rewrites files in place. Run scripts/validate_references.py afterwards.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KB = REPO / "knowledge-base"
SOURCES_PATH = KB / "references" / "sources.json"
CITATIONS_PATH = KB / "references" / "citations.json"

LEGACY_FIELDS = {
    "label", "publisher", "data_used", "pages", "publication_date", "type",
    "document", "organization", "reference_year", "publication_year", "id",
    "primary_use", "title", "url", "year",
}

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def save(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

sources = load(SOURCES_PATH)
citations = load(CITATIONS_PATH)

# ---------------------------------------------------------------------
# 1. sources.json: the ID is the dict key only -- drop the duplicated
#    in-record "source_id" field on all 56 entries.
# ---------------------------------------------------------------------
for rec in sources.values():
    rec.pop("source_id", None)

# ---------------------------------------------------------------------
# 2. Fix key typo: registry said SRC_PMEGM but the record's own title is
#    "Prime Minister's Employment Generation Programme (PMEGP)", and every
#    consumer (finance/subsidies.json) already references SRC_PMEGP.
# ---------------------------------------------------------------------
if "SRC_PMEGM" in sources:
    sources["SRC_PMEGP"] = sources.pop("SRC_PMEGM")
if "SRC_PMEGM" in citations:
    citations["SRC_PMEGP"] = citations.pop("SRC_PMEGM")
    citations["SRC_PMEGP"]["source_id"] = "SRC_PMEGP"

# ---------------------------------------------------------------------
# 3. De-duplicate: the NITI Aayog "Roadmap for Green Transition of MSMEs"
#    was registered under TWO ids (niti_mSME_green_transition_2026 and
#    niti_msme_roadmap) with identical title/org/year/url, and a THIRD,
#    differently-cased spelling was referenced but never registered at
#    all. Canonicalize everything on niti_msme_roadmap.
# ---------------------------------------------------------------------
NITI_KEEP = "niti_msme_roadmap"
NITI_DROP = "niti_mSME_green_transition_2026"
sources.pop(NITI_DROP, None)
citations.pop(NITI_DROP, None)

# ---------------------------------------------------------------------
# 4. Register sources that were genuinely never in the registry.
#    Every title/organization/url value below was copied verbatim from
#    the knowledge-base record that used to carry it locally -- nothing
#    invented. Where a record had no year and no year could be found
#    anywhere in-repo, 2026 is used ONLY because every other undated BEE
#    technology compendium already in sources.json uses that same
#    placeholder (bee_adeetie, bee_steel_rerolling, bee_textile_*, ...).
#    Where a record had no specific document URL, the organization's
#    official homepage is used, matching this project's own established
#    convention (SRC003, bee_adeetie, iea_heavy_industry, etc. all do
#    this already). FLAGGED FOR TEAM VERIFICATION, see report.
# ---------------------------------------------------------------------
NEW_SOURCES = {
    "bee_dairy_haryana": {
        "title": "Technology Compendium - Haryana Dairy Cluster",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "bee_dairy_punjab": {
        "title": "Technology Compendium - Punjab Dairy Cluster",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "bee_dairy_case_studies": {
        "title": "Dairy Energy Efficiency Case Studies",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "bee_dairy_clusters": {
        "title": "Technology Compendiums in Dairy - AP & Telangana, Haryana, Kerala, "
                 "Maharashtra, MP, Odisha, Punjab, Tamil Nadu, Gujarat",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "fssai_dairy_standards": {
        "title": "Food Safety and Standards Regulations - Dairy Products and Analogues",
        "organization": "Food Safety and Standards Authority of India (FSSAI)",
        "year": 2011, "url": "https://fssai.gov.in/",
    },
    "mofpi_annual_report": {
        "title": "Annual Report 2024-25",
        "organization": "Ministry of Food Processing Industries, Government of India",
        "year": 2025, "url": "https://mofpi.gov.in/",
    },
    "bee_glass_refractory": {
        "title": "Achieving Energy and Resource Efficiency in Glass and Refractory Industries",
        "organization": "Bureau of Energy Efficiency, Ministry of Power",
        "year": 2026,
        "url": "https://beeindia.gov.in/sites/default/files/Glass_%26_Refractory_sector-Energy_mapping.pdf",
    },
    "bee_energy_mapping_program": {
        "title": "Energy & Resource Mapping Study",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026,
        "url": "https://beeindia.gov.in/show_content.php?lang=1&level=2&lid=383&ls_id=235",
    },
    "bee_paper_sector_report": {
        "title": "Energy and Resource Mapping of MSMEs in India - Paper Sector Report",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2022,
        "url": "https://www.beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-95dc2a5852c2feb3_1776169549.pdf",
    },
    "bee_pat_rules": {
        "title": "Energy Conservation Act / PAT Sector Framework",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "bee_pharmaceutical_cluster": {
        "title": "Technology Compendium for Energy Efficiency and Renewable Energy - "
                 "Sikkim Pharmaceutical Cluster",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "bee_pharmaceutical_mapping": {
        "title": "Benchmarking & Policy Recommendation Report for Energy Efficiency in "
                 "MSME - Pharmaceutical Sector",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "energy_innovation_india_heat_2026": {
        "title": "Electrifying Industrial Heat in India",
        "organization": "Energy Innovation",
        "year": 2026, "url": "https://energyinnovation.org/",
    },
    "bee_food_processing_mapping": {
        "title": "Energy Mapping of MSME Food Processing Sector in India",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "fssai_milk_processing_guidance": {
        "title": "Milk and Milk Product Processing Guidance",
        "organization": "Food Safety and Standards Authority of India (FSSAI)",
        "year": 2026, "url": "https://fssai.gov.in/",
    },
    "iea_heat_pump_monitor_2026": {
        "title": "Heat Pump Monitor 2026",
        "organization": "International Energy Agency (IEA)",
        "year": 2026, "url": "https://www.iea.org/",
    },
    "icar_food_processing_reference": {
        "title": "Food Processing and Post-Harvest Technology References",
        "organization": "Indian Council of Agricultural Research (ICAR)",
        "year": 2026, "url": "https://icar.org.in/",
    },
    "mnre_giz_biomass_msme": {
        "title": "Decarbonizing MSMEs: Use of Biomass for Green Steam and Heat Application",
        "organization": "Ministry of New and Renewable Energy (MNRE) and GIZ",
        "year": 2026, "url": "https://mnre.gov.in/",
    },
    "dcpc_chemical_statistics_2025": {
        "title": "Chemical and Petrochemical Statistics at a Glance 2025",
        "organization": "Department of Chemicals and Petrochemicals, Government of India",
        "year": 2025, "url": "https://chemicals.nic.in/",
    },
    "bee_chemical_efficiency": {
        "title": "Achieving Energy and Resource Efficiency in Chemical Industries",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "iea_electrification_renewables_industry": {
        "title": "Electrification and Renewables for Industry",
        "organization": "International Energy Agency (IEA)",
        "year": 2026, "url": "https://www.iea.org/",
    },
    "niti_cement_decarbonisation_roadmap": {
        "title": "Roadmap for Cement Sector Decarbonisation",
        "organization": "NITI Aayog, Government of India",
        "year": 2026, "url": "https://www.niti.gov.in/",
    },
    "bee_cement_pat_database": {
        "title": "PAT Cement Sector Material and Energy Efficient Technology Database",
        "organization": "Bureau of Energy Efficiency, Government of India",
        "year": 2026, "url": "https://beeindia.gov.in/",
    },
    "bis_cement_reference": {
        "title": "Cement Technical Reference Material",
        "organization": "Bureau of Indian Standards",
        "year": 2026, "url": "https://www.bis.gov.in/",
    },
    "iea_heavy_industry_cement": {
        "title": "Driving Energy Efficiency in Heavy Industries - Cement",
        "organization": "International Energy Agency (IEA)",
        "year": 2026, "url": "https://www.iea.org/",
    },
}
for sid, rec in NEW_SOURCES.items():
    sources.setdefault(sid, rec)
    citations.setdefault(sid, {"source_id": sid})

# ---------------------------------------------------------------------
# 5. Repoint duplicate/renamed ids used by consumer files.
# ---------------------------------------------------------------------
REPOINT = {
    "niti_msme_green_transition_2026": NITI_KEEP,   # unregistered casing variant
    "niti_mSME_green_transition_2026": NITI_KEEP,   # old registered duplicate
    "niti_msme_roadmap_2026": NITI_KEEP,             # pharma.json duplicate
    "mnre_cst": "mnre_solar_thermal",                # pharma.json duplicate
    "bee_ee_technology_list": "bee_adeetie",         # same BEE doc, two ids
    "SRC_PMEGM": "SRC_PMEGP",
}
# bee_adeetie's URL upgraded to the more specific one found on the
# duplicate record (paper.json's bee_ee_technology_list).
sources["bee_adeetie"]["url"] = "https://adeetie.beeindia.gov.in/list-of-energy-efficient-technologies"

save(SOURCES_PATH, sources)
save(CITATIONS_PATH, citations)

# ---------------------------------------------------------------------
# 6. Rewrite every other knowledge-base JSON file: any object that has
#    (or, via REPOINT, resolves to) a valid source_id gets collapsed to
#    {"source_id": "..."}; every legacy metadata field is dropped because
#    that metadata now lives only in sources.json.
# ---------------------------------------------------------------------
REFERENCE_FILES = {SOURCES_PATH.resolve(), CITATIONS_PATH.resolve()}
registered_ids = set(sources.keys())

def collapse(obj):
    """Recursively collapse any legacy citation/source record in place."""
    if isinstance(obj, dict):
        sid = obj.get("source_id") or obj.get("id")
        if sid in REPOINT:
            sid = REPOINT[sid]
        has_legacy = bool(set(obj.keys()) & LEGACY_FIELDS) or "id" in obj
        if sid and sid in registered_ids and has_legacy:
            obj.clear()
            obj["source_id"] = sid
            return
        for v in obj.values():
            collapse(v)
    elif isinstance(obj, list):
        for item in obj:
            collapse(item)

changed_files = []
for json_file in sorted(KB.rglob("*.json")):
    if json_file.resolve() in REFERENCE_FILES:
        continue
    doc = load(json_file)
    before = json.dumps(doc, sort_keys=True)
    collapse(doc)
    after = json.dumps(doc, sort_keys=True)
    if before != after:
        save(json_file, doc)
        changed_files.append(str(json_file.relative_to(REPO)))

print("Updated sources.json + citations.json")
print(f"Updated {len(changed_files)} consumer files:")
for f in changed_files:
    print("  -", f)

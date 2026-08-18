"""
load_knowledge.py — Load Knowledge-Base JSON into Database

Reads knowledge-base/ JSON files and loads them into the SQLite
database using SQLAlchemy Core. Creates SQLite-compatible tables
(no PostgreSQL ENUMs/JSONB) derived from 001_initial_schema.sql.

Part of Task 4.1 ETL Pipeline.

Usage:
    python scripts/load_knowledge.py
"""

import json
import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Text,
    Float,
    Boolean,
    Integer,
    DateTime,
    create_engine,
    inspect,
)
from sqlalchemy.sql import func


# --------------------------------------------------
# Path Configuration
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"
BACKEND_DIR = PROJECT_ROOT / "backend"

# Add backend to path for importing config
sys.path.insert(0, str(BACKEND_DIR))

from config import settings


# --------------------------------------------------
# Database Setup
# --------------------------------------------------

DATABASE_URL = settings.DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
metadata = MetaData()


# --------------------------------------------------
# Table Definitions (SQLite-compatible)
#
# Derived from 001_initial_schema.sql but using TEXT
# instead of PostgreSQL ENUM/JSONB types.
# --------------------------------------------------

industries_table = Table(
    "industries", metadata,
    Column("industry_id", Text, primary_key=True),
    Column("typical_temperature_min_c", Float, nullable=False),
    Column("typical_temperature_max_c", Float, nullable=False),
    Column("typical_energy_split", Text, nullable=False,
           server_default="{}"),
    Column("sub_process", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now()),
)

technologies_table = Table(
    "technologies", metadata,
    Column("technology_id", Text, primary_key=True),
    Column("input_energy_form", Text, nullable=False),
    Column("output_energy_form", Text, nullable=False),
    Column("temperature_min_c", Float, nullable=False),
    Column("temperature_max_c", Float, nullable=False),
    Column("capex_inr_min", Float, nullable=False),
    Column("capex_inr_max", Float, nullable=False),
    Column("opex_inr_per_unit", Float, nullable=False),
    Column("efficiency_pct", Float, nullable=False),
    Column("capacity_min", Float, nullable=True),
    Column("capacity_max", Float, nullable=True),
    Column("capacity_unit", Text, nullable=True),
    Column("lifetime_years", Float, nullable=False),
    Column("emission_factor", Float, nullable=False),
    Column("local_availability_dependent", Boolean, nullable=False,
           server_default="0"),
    Column("constraints", Text, nullable=False,
           server_default="[]"),
    Column("source_citation", Text, nullable=False,
           server_default="{}"),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now()),
)

industry_technologies_table = Table(
    "industry_technologies", metadata,
    Column("industry_id", Text, nullable=False),
    Column("technology_id", Text, nullable=False),
    sa.PrimaryKeyConstraint("industry_id", "technology_id"),
)

# Reference tables for emission/grid factors
emission_factors_table = Table(
    "emission_factors", metadata,
    Column("fuel_id", Text, primary_key=True),
    Column("emission_factor", Float, nullable=False),
    Column("unit", Text, nullable=False),
    Column("ncv", Float, nullable=True),
    Column("ncv_unit", Text, nullable=True),
    Column("input_unit", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

grid_factors_table = Table(
    "grid_factors", metadata,
    Column("factor_type", Text, primary_key=True),
    Column("value", Float, nullable=False),
    Column("unit", Text, nullable=False),
    Column("reporting_year", Text, nullable=True),
    Column("basis", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)


# --------------------------------------------------
# JSON Loading Helpers
# --------------------------------------------------

def load_json_file(filepath: Path) -> dict | None:
    """Load and parse a JSON file."""

    if not filepath.exists():
        print(f"  [SKIP] Not found: {filepath}")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def to_json_string(obj) -> str:
    """Convert a Python object to a JSON string for TEXT columns."""
    return json.dumps(obj, ensure_ascii=False)


# --------------------------------------------------
# 1. Load Industries
# --------------------------------------------------

def load_industries():
    """
    Load knowledge-base/industries/*.json into the industries table.

    Extracts industry_id, temperature ranges, and energy split from
    each industry JSON file.
    """

    print("\n--- Loading Industries ---")
    industries_dir = KNOWLEDGE_BASE / "industries"

    if not industries_dir.exists():
        print("  [ERROR] knowledge-base/industries/ not found")
        return 0

    json_files = sorted([
        f for f in industries_dir.iterdir()
        if f.suffix == ".json" and f.is_file()
    ])

    records = []
    for filepath in json_files:
        data = load_json_file(filepath)
        if data is None:
            continue

        industry_id = data.get(
            "industry_id", filepath.stem
        )

        # Extract temperature range — structure varies by file
        temp_min, temp_max = _extract_temperature_range(data)

        # Extract energy split
        energy_split = _extract_energy_split(data)

        # Extract sub_process
        sub_process = data.get("sub_process")
        if sub_process is None:
            # Some files use "subsector" instead
            sub_process = data.get("subsector", "")

        record = {
            "industry_id": industry_id,
            "typical_temperature_min_c": temp_min,
            "typical_temperature_max_c": temp_max,
            "typical_energy_split": to_json_string(energy_split),
            "sub_process": sub_process,
        }
        records.append(record)
        print(f"  [OK] {industry_id} "
              f"(temp: {temp_min}-{temp_max} C)")

    if records:
        with engine.begin() as conn:
            conn.execute(industries_table.delete())
            conn.execute(industries_table.insert(), records)

    print(f"  Loaded {len(records)} industries")
    return len(records)


def _extract_temperature_range(data: dict) -> tuple[float, float]:
    """
    Extract temperature range from industry JSON.

    Handles multiple formats:
    - {"typical_temperature": {"min": N, "max": N}}
    - {"typical_temperature": {"primary_process_heat_min": N, ...}}
    - {"process_characteristics": {"typical_temperature_range": ...}}
    """

    # Format 1: typical_temperature.min/max
    temp = data.get("typical_temperature", {})
    if isinstance(temp, dict):
        if "min" in temp and "max" in temp:
            return (float(temp["min"]), float(temp["max"]))
        if "primary_process_heat_min" in temp:
            return (
                float(temp["primary_process_heat_min"]),
                float(temp.get(
                    "extended_process_heat_max",
                    temp.get("primary_process_heat_max", 0)
                )),
            )

    # Format 2: process_characteristics.typical_temperature_range
    proc = data.get("process_characteristics", {})
    temp_range = proc.get("typical_temperature_range", {})
    if isinstance(temp_range, dict):
        if "min" in temp_range and "max" in temp_range:
            return (
                float(temp_range["min"]),
                float(temp_range["max"]),
            )

    # Format 3: nested in process_characteristics
    if isinstance(proc, dict):
        temp_data = proc.get("temperature_range", {})
        if isinstance(temp_data, dict):
            if "min_c" in temp_data and "max_c" in temp_data:
                return (
                    float(temp_data["min_c"]),
                    float(temp_data["max_c"]),
                )

    # Fallback: search for any temperature-related keys
    for key in ("temperature_range", "typical_temperature_range_c"):
        val = data.get(key)
        if isinstance(val, (list, tuple)) and len(val) == 2:
            return (float(val[0]), float(val[1]))
        if isinstance(val, dict) and "min" in val:
            return (float(val["min"]), float(val.get("max", 0)))

    # Default fallback
    print(f"    [WARN] No temperature range found, defaulting to 0-0")
    return (0.0, 0.0)


def _extract_energy_split(data: dict) -> dict:
    """Extract energy split from industry JSON."""

    # Direct field
    split = data.get("typical_energy_split")
    if isinstance(split, dict):
        return split

    # Nested in india_sector_context or process_characteristics
    for parent_key in (
        "india_sector_context",
        "process_characteristics",
        "energy_profile",
    ):
        parent = data.get(parent_key, {})
        if isinstance(parent, dict):
            for key in (
                "typical_energy_split",
                "energy_split",
                "energy_split_percent",
            ):
                split = parent.get(key)
                if isinstance(split, dict):
                    return split

    # Try to derive from fuel_mix_percent
    ctx = data.get("india_sector_context", {})
    fuel_mix = ctx.get("fuel_mix_percent", {})
    if fuel_mix:
        elec = (
            fuel_mix.get("grid_electricity", 0)
            + fuel_mix.get("renewable_electricity", 0)
        )
        thermal = 100 - elec
        return {
            "electricity_pct": elec,
            "thermal_pct": thermal,
        }

    return {"electricity_pct": 0, "thermal_pct": 0}


# --------------------------------------------------
# 2. Load Technologies
# --------------------------------------------------

def load_technologies():
    """
    Load knowledge-base/technologies/*.json into the technologies
    table.

    Technology JSON files have varied structures — some are
    structured data, others are text blobs. This loader extracts
    what it can and uses defaults for missing fields.
    """

    print("\n--- Loading Technologies ---")
    tech_dir = KNOWLEDGE_BASE / "technologies"

    if not tech_dir.exists():
        print("  [ERROR] knowledge-base/technologies/ not found")
        return 0

    # Also load temperature_ranges from converted datasets
    # for fallback temperature data
    temp_ranges = _load_temperature_ranges()

    json_files = sorted([
        f for f in tech_dir.iterdir()
        if f.suffix == ".json" and f.is_file()
    ])

    records = []
    for filepath in json_files:
        data = load_json_file(filepath)
        if data is None:
            continue

        tech_id = filepath.stem  # e.g. "biomass", "heat_pump"

        # Get temperature from converted dataset if available
        temp_data = temp_ranges.get(tech_id, {})

        record = {
            "technology_id": tech_id,
            "input_energy_form": _guess_input_form(tech_id),
            "output_energy_form": _guess_output_form(tech_id),
            "temperature_min_c": temp_data.get("min", 0),
            "temperature_max_c": temp_data.get("max", 0),
            "capex_inr_min": 0,
            "capex_inr_max": 0,
            "opex_inr_per_unit": 0,
            "efficiency_pct": 0,
            "capacity_min": None,
            "capacity_max": None,
            "capacity_unit": None,
            "lifetime_years": 20,
            "emission_factor": 0,
            "local_availability_dependent": (
                tech_id in ("biomass", "biogas")
            ),
            "constraints": to_json_string([]),
            "source_citation": to_json_string(
                {"source": "knowledge-base/technologies/" + filepath.name}
            ),
        }

        records.append(record)
        print(f"  [OK] {tech_id} "
              f"(temp: {record['temperature_min_c']}"
              f"-{record['temperature_max_c']} C)")

    if records:
        with engine.begin() as conn:
            conn.execute(technologies_table.delete())
            conn.execute(technologies_table.insert(), records)

    print(f"  Loaded {len(records)} technologies")
    return len(records)


def _load_temperature_ranges() -> dict:
    """
    Load temperature ranges from the converted dataset
    as a fallback source for technology temperatures.
    """

    converted = (
        PROJECT_ROOT / "datasets" / "converted"
        / "temperature_ranges.json"
    )

    if not converted.exists():
        return {}

    with open(converted, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for rec in data.get("records", []):
        # Map technology names to IDs
        name = rec.get("technology_name", "").lower().strip()
        tid = rec.get("technology_id", "")

        # Build name-to-range mapping
        name_map = {
            "biomass": "biomass",
            "biogas": "biogas",
            "electrification": "electrification",
            "heat pump": "heat_pump",
            "solar thermal": "solar_thermal",
            "thermal storage": "thermal_storage",
            "waste heat recovery": "waste_heat_recovery",
            "electricity": "electrification",
        }

        mapped_id = name_map.get(name, name.replace(" ", "_"))

        result[mapped_id] = {
            "min": rec.get("min_output_temp_c", 0) or 0,
            "max": rec.get("max_output_temp_c", 0) or 0,
        }

    return result


def _guess_input_form(tech_id: str) -> str:
    """Map technology ID to input energy form."""

    mapping = {
        "biomass": "biomass",
        "biogas": "biomass",
        "electrification": "electricity",
        "heat_pump": "electricity",
        "solar_thermal": "solar",
        "thermal_storage": "thermal",
        "waste_heat_recovery": "waste_heat",
    }
    return mapping.get(tech_id, "thermal")


def _guess_output_form(tech_id: str) -> str:
    """Map technology ID to output energy form."""

    mapping = {
        "biomass": "steam",
        "biogas": "thermal",
        "electrification": "thermal",
        "heat_pump": "thermal",
        "solar_thermal": "thermal",
        "thermal_storage": "thermal",
        "waste_heat_recovery": "thermal",
    }
    return mapping.get(tech_id, "thermal")


# --------------------------------------------------
# 3. Load Industry↔Technology Junction
# --------------------------------------------------

def load_industry_technologies():
    """
    Populate the industry_technologies junction table.

    Uses a default mapping — all technologies are initially
    applicable to all industries. The decision engine's
    technology_filter.py will narrow this based on temperature
    and other constraints at runtime.
    """

    print("\n--- Loading Industry<->Technology Mappings ---")

    with engine.begin() as conn:
        # Get all industry_ids
        industry_ids = [
            row[0] for row in
            conn.execute(
                sa.text("SELECT industry_id FROM industries")
            ).fetchall()
        ]

        # Get all technology_ids
        technology_ids = [
            row[0] for row in
            conn.execute(
                sa.text("SELECT technology_id FROM technologies")
            ).fetchall()
        ]

        # Clear existing
        conn.execute(industry_technologies_table.delete())

        # Create M:N mappings — all technologies available to
        # all industries; runtime filtering handles feasibility
        records = [
            {
                "industry_id": ind_id,
                "technology_id": tech_id,
            }
            for ind_id in industry_ids
            for tech_id in technology_ids
        ]

        if records:
            conn.execute(
                industry_technologies_table.insert(), records
            )

    count = len(records) if records else 0
    print(f"  Loaded {count} industry<->technology mappings "
          f"({len(industry_ids)} industries x "
          f"{len(technology_ids)} technologies)")
    return count


# --------------------------------------------------
# 4. Load Emission Factors
# --------------------------------------------------

def load_emission_factors():
    """Load emission_factors.json into the emission_factors table."""

    print("\n--- Loading Emission Factors ---")
    filepath = KNOWLEDGE_BASE / "emissions" / "emission_factors.json"
    data = load_json_file(filepath)

    if data is None:
        return 0

    records = []
    for fuel_id, details in data.items():
        if not isinstance(details, dict):
            continue

        record = {
            "fuel_id": fuel_id,
            "emission_factor": details.get("emission_factor", 0),
            "unit": details.get("unit", ""),
            "ncv": details.get("ncv"),
            "ncv_unit": details.get("ncv_unit", ""),
            "input_unit": details.get("input_unit", ""),
            "source_id": details.get("source_id", ""),
            "source_type": details.get("source_type", ""),
        }
        records.append(record)
        print(f"  [OK] {fuel_id}: "
              f"{record['emission_factor']} {record['unit']}")

    if records:
        with engine.begin() as conn:
            conn.execute(emission_factors_table.delete())
            conn.execute(emission_factors_table.insert(), records)

    print(f"  Loaded {len(records)} emission factors")
    return len(records)


# --------------------------------------------------
# 5. Load Grid Factors
# --------------------------------------------------

def load_grid_factors():
    """Load grid_factors.json into the grid_factors table."""

    print("\n--- Loading Grid Factors ---")
    filepath = KNOWLEDGE_BASE / "emissions" / "grid_factors.json"
    data = load_json_file(filepath)

    if data is None:
        return 0

    factors = data.get("factors", {})
    records = []
    for factor_type, details in factors.items():
        if not isinstance(details, dict):
            continue

        record = {
            "factor_type": factor_type,
            "value": details.get("value", 0),
            "unit": details.get("unit", ""),
            "reporting_year": details.get("reporting_year", ""),
            "basis": details.get("basis", ""),
        }
        records.append(record)
        print(f"  [OK] {factor_type}: "
              f"{record['value']} {record['unit']}")

    # Also add the default factor
    default = data.get("default_factor", {})
    if default:
        records.append({
            "factor_type": "default",
            "value": default.get("value", 0),
            "unit": default.get("unit", ""),
            "reporting_year": default.get("reporting_year", ""),
            "basis": default.get("type", ""),
        })
        print(f"  [OK] default: {default.get('value')} "
              f"{default.get('unit')}")

    if records:
        with engine.begin() as conn:
            conn.execute(grid_factors_table.delete())
            conn.execute(grid_factors_table.insert(), records)

    print(f"  Loaded {len(records)} grid factors")
    return len(records)


# --------------------------------------------------
# Main
# --------------------------------------------------

def create_tables():
    """Create all tables (drops existing ones first)."""

    print("\n--- Creating Database Tables ---")
    print(f"  Database: {DATABASE_URL}")

    # Drop and recreate for clean state
    metadata.drop_all(engine)
    metadata.create_all(engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"  Created {len(tables)} tables: {', '.join(tables)}")


def main():
    print("=" * 60)
    print("  load_knowledge.py -- Knowledge Base -> Database")
    print("=" * 60)

    create_tables()

    industries_count = load_industries()
    tech_count = load_technologies()
    junction_count = load_industry_technologies()
    emission_count = load_emission_factors()
    grid_count = load_grid_factors()

    print("\n" + "=" * 60)
    print("  Loading complete!")
    print(f"    Industries:           {industries_count}")
    print(f"    Technologies:         {tech_count}")
    print(f"    Industry<->Tech:        {junction_count}")
    print(f"    Emission Factors:     {emission_count}")
    print(f"    Grid Factors:         {grid_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()

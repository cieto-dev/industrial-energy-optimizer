"""
seed_database.py — Seed Database with Reference Data

Seeds the database with reference data from knowledge-base and
converted datasets. This is the final step of the ETL pipeline.

Can be run standalone (assumes load_knowledge.py has been run)
or with --full-pipeline to run all 4 ETL steps in sequence.

Part of Task 4.1 ETL Pipeline.

Usage:
    python scripts/seed_database.py
    python scripts/seed_database.py --full-pipeline
"""

import json
import sys
import subprocess
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
BACKEND_DIR = PROJECT_ROOT / "backend"
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"
CONVERTED_DIR = PROJECT_ROOT / "datasets" / "converted"

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
# Additional Reference Tables
# (beyond those created by load_knowledge.py)
# --------------------------------------------------

biomass_atlas_table = Table(
    "biomass_atlas", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("state", Text, nullable=False),
    Column("district", Text, nullable=False),
    Column("biomass_type", Text, nullable=False),
    Column("crop", Text, nullable=True),
    Column("annual_availability_tons", Float, nullable=True),
    Column("availability_type", Text, nullable=True),
    Column("year", Text, nullable=True),
    Column("moisture_percent", Float, nullable=True),
    Column("calorific_value_mj_kg", Float, nullable=True),
    Column("cost_rs_per_ton", Float, nullable=True),
    Column("latitude", Float, nullable=True),
    Column("longitude", Float, nullable=True),
    Column("source", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

district_coordinates_table = Table(
    "district_coordinates", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("district", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("latitude", Float, nullable=True),
    Column("longitude", Float, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

industrial_fuels_table = Table(
    "industrial_fuels", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("fuel_category", Text, nullable=False),
    Column("fuel", Text, nullable=False),
    Column("variant_grade", Text, nullable=True),
    Column("unit", Text, nullable=True),
    Column("cost_rs_per_unit", Float, nullable=True),
    Column("gcv", Float, nullable=True),
    Column("gcv_unit", Text, nullable=True),
    Column("co2_factor", Float, nullable=True),
    Column("co2_unit", Text, nullable=True),
    Column("source", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

electricity_tariffs_table = Table(
    "electricity_tariffs", metadata,
    Column("tariff_id", Text, primary_key=True),
    Column("state", Text, nullable=False),
    Column("state_id", Text, nullable=True),
    Column("discom", Text, nullable=True),
    Column("discom_id", Text, nullable=True),
    Column("consumer_category", Text, nullable=True),
    Column("voltage_level_or_load", Text, nullable=True),
    Column("energy_charge", Float, nullable=True),
    Column("energy_charge_unit", Text, nullable=True),
    Column("fixed_charge", Float, nullable=True),
    Column("fixed_charge_unit", Text, nullable=True),
    Column("demand_charge", Float, nullable=True),
    Column("demand_charge_unit", Text, nullable=True),
    Column("effective_from", Text, nullable=True),
    Column("tariff_year", Text, nullable=True),
    Column("has_tod", Boolean, nullable=True),
    Column("has_slab", Boolean, nullable=True),
    Column("notes", Text, nullable=True),
    Column("official_source", Text, nullable=True),
    Column("data_status", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

defaults_table = Table(
    "defaults", metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
    Column("category", Text, nullable=True),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)


# --------------------------------------------------
# JSON Loading Helper
# --------------------------------------------------

def load_json_file(filepath: Path) -> dict | None:
    """Load and parse a JSON file."""

    if not filepath.exists():
        print(f"  [SKIP] Not found: {filepath}")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# 1. Seed Biomass Atlas
# --------------------------------------------------

def seed_biomass_atlas():
    """Seed biomass_atlas table from converted dataset."""

    print("\n--- Seeding Biomass Atlas ---")
    data = load_json_file(CONVERTED_DIR / "biomass_atlas.json")

    if data is None:
        return 0

    records = data.get("records", [])

    if records:
        with engine.begin() as conn:
            # Drop and recreate
            biomass_atlas_table.drop(engine, checkfirst=True)
            biomass_atlas_table.create(engine, checkfirst=True)
            conn.execute(biomass_atlas_table.insert(), records)

    print(f"  Loaded {len(records)} biomass records")
    return len(records)


# --------------------------------------------------
# 2. Seed District Coordinates
# --------------------------------------------------

def seed_district_coordinates():
    """Seed district_coordinates table from converted dataset."""

    print("\n--- Seeding District Coordinates ---")
    data = load_json_file(
        CONVERTED_DIR / "district_coordinates.json"
    )

    if data is None:
        return 0

    records = data.get("records", [])

    if records:
        with engine.begin() as conn:
            district_coordinates_table.drop(
                engine, checkfirst=True
            )
            district_coordinates_table.create(
                engine, checkfirst=True
            )
            conn.execute(
                district_coordinates_table.insert(), records
            )

    print(f"  Loaded {len(records)} district records")
    return len(records)


# --------------------------------------------------
# 3. Seed Industrial Fuels
# --------------------------------------------------

def seed_industrial_fuels():
    """Seed industrial_fuels table from converted dataset."""

    print("\n--- Seeding Industrial Fuels ---")
    data = load_json_file(
        CONVERTED_DIR / "industrial_fuels.json"
    )

    if data is None:
        return 0

    records = data.get("records", [])

    if records:
        with engine.begin() as conn:
            industrial_fuels_table.drop(
                engine, checkfirst=True
            )
            industrial_fuels_table.create(
                engine, checkfirst=True
            )
            conn.execute(
                industrial_fuels_table.insert(), records
            )

    print(f"  Loaded {len(records)} fuel records")
    return len(records)


# --------------------------------------------------
# 4. Seed Electricity Tariffs
# --------------------------------------------------

def seed_electricity_tariffs():
    """Seed electricity_tariffs table from converted dataset."""

    print("\n--- Seeding Electricity Tariffs ---")
    data = load_json_file(
        CONVERTED_DIR / "electricity_tariffs.json"
    )

    if data is None:
        return 0

    records = data.get("records", [])

    if records:
        with engine.begin() as conn:
            electricity_tariffs_table.drop(
                engine, checkfirst=True
            )
            electricity_tariffs_table.create(
                engine, checkfirst=True
            )
            conn.execute(
                electricity_tariffs_table.insert(), records
            )

    print(f"  Loaded {len(records)} tariff records")
    return len(records)


# --------------------------------------------------
# 5. Seed Default Configuration
# --------------------------------------------------

def seed_defaults():
    """Seed system-wide default configuration values."""

    print("\n--- Seeding Defaults ---")

    # Load grid default
    grid_data = load_json_file(
        KNOWLEDGE_BASE / "emissions" / "grid_factors.json"
    )

    grid_default = 0.7117  # fallback
    if grid_data:
        default_factor = grid_data.get("default_factor", {})
        grid_default = default_factor.get("value", grid_default)

    records = [
        {
            "key": "grid_emission_factor",
            "value": str(grid_default),
            "category": "emissions",
            "description": (
                "Default grid emission factor "
                "(kgCO2e/kWh) from CEA Baseline Database"
            ),
        },
        {
            "key": "currency",
            "value": "INR",
            "category": "finance",
            "description": "Default currency for all calculations",
        },
        {
            "key": "discount_rate",
            "value": "0.10",
            "category": "finance",
            "description": "Default discount rate (10%) for NPV",
        },
        {
            "key": "analysis_horizon_years",
            "value": "25",
            "category": "finance",
            "description": (
                "Default project analysis horizon in years"
            ),
        },
        {
            "key": "country",
            "value": "India",
            "category": "general",
            "description": "Target country for the optimizer",
        },
        {
            "key": "platform_version",
            "value": "1.0",
            "category": "general",
            "description": "Platform version",
        },
        {
            "key": "operating_days_per_year",
            "value": "300",
            "category": "general",
            "description": (
                "Default factory operating days per year"
            ),
        },
        {
            "key": "operating_hours_per_day",
            "value": "16",
            "category": "general",
            "description": (
                "Default factory operating hours per day"
            ),
        },
    ]

    with engine.begin() as conn:
        defaults_table.drop(engine, checkfirst=True)
        defaults_table.create(engine, checkfirst=True)
        conn.execute(defaults_table.insert(), records)

    print(f"  Loaded {len(records)} default values")
    return len(records)


# --------------------------------------------------
# Verification
# --------------------------------------------------

def verify_database():
    """Verify all tables have expected data."""

    print("\n" + "=" * 60)
    print("  DATABASE VERIFICATION")
    print("=" * 60)

    with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\n  Tables found: {len(tables)}")

        for table_name in sorted(tables):
            count = conn.execute(
                sa.text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar()
            print(f"    {table_name:30s}  {count:>5} rows")

        # Specific check: 9 industries
        industry_count = conn.execute(
            sa.text("SELECT COUNT(*) FROM industries")
        ).scalar()

        print(f"\n  Gate check: industries = {industry_count}")

        if industry_count == 9:
            print("  [PASS] GATE PASSED: 9 industries loaded")
        else:
            print(f"  [FAIL] GATE FAILED: Expected 9 industries, "
                  f"got {industry_count}")

        # List all industry_ids
        rows = conn.execute(
            sa.text(
                "SELECT industry_id, "
                "typical_temperature_min_c, "
                "typical_temperature_max_c "
                "FROM industries ORDER BY industry_id"
            )
        ).fetchall()

        print("\n  Industries loaded:")
        for row in rows:
            print(f"    {row[0]:20s}  "
                  f"temp: {row[1]}–{row[2]}°C")

    print("=" * 60)


# --------------------------------------------------
# Full Pipeline
# --------------------------------------------------

def run_full_pipeline():
    """
    Run all 4 ETL steps in sequence:
    1. convert_datasets.py
    2. pre_process.py
    3. load_knowledge.py (this module handles it inline)
    4. seed_database.py (this module)
    """

    print("=" * 60)
    print("  FULL ETL PIPELINE")
    print("=" * 60)

    python = sys.executable

    # Step 1: Convert CSV → JSON
    print("\n>>> Step 1/4: convert_datasets.py")
    result = subprocess.run(
        [python, str(SCRIPT_DIR / "convert_datasets.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] convert_datasets.py failed:\n"
              f"{result.stderr}")
        sys.exit(1)

    # Step 2: Clean/Validate
    print("\n>>> Step 2/4: pre_process.py")
    result = subprocess.run(
        [python, str(SCRIPT_DIR / "pre_process.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] pre_process.py failed:\n"
              f"{result.stderr}")
        sys.exit(1)

    # Step 3: Load knowledge base
    print("\n>>> Step 3/4: load_knowledge.py")
    result = subprocess.run(
        [python, str(SCRIPT_DIR / "load_knowledge.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] load_knowledge.py failed:\n"
              f"{result.stderr}")
        sys.exit(1)

    # Step 4: Seed (this module -- run inline)
    print("\n>>> Step 4/4: seed_database.py (inline)")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    full_pipeline = "--full-pipeline" in sys.argv

    if full_pipeline:
        run_full_pipeline()

    print("\n" + "=" * 60)
    print("  seed_database.py -- Seed Reference Data")
    print("=" * 60)

    # Create additional tables
    metadata.create_all(engine, checkfirst=True)

    # Seed reference data from converted datasets
    biomass_count = seed_biomass_atlas()
    district_count = seed_district_coordinates()
    fuels_count = seed_industrial_fuels()
    tariffs_count = seed_electricity_tariffs()
    defaults_count = seed_defaults()

    print("\n" + "=" * 60)
    print("  Seeding complete!")
    print(f"    Biomass Atlas:        {biomass_count}")
    print(f"    Districts:            {district_count}")
    print(f"    Industrial Fuels:     {fuels_count}")
    print(f"    Electricity Tariffs:  {tariffs_count}")
    print(f"    Defaults:             {defaults_count}")
    print("=" * 60)

    # Run verification
    verify_database()


if __name__ == "__main__":
    main()

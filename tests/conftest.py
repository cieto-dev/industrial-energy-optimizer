from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from models.factory import Factory, Quantity
except ImportError:
    Factory = None  # type: ignore[assignment]
    Quantity = None  # type: ignore[assignment]


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def sample_factory() -> Any:
    """
    Reusable deterministic factory fixture.

    Mirrors the project's existing known textile/Tamil Nadu test fixture
    so new tests remain compatible with the current domain model.
    """
    if Factory is None or Quantity is None:
        pytest.skip("Factory model is unavailable")

    return Factory(
        factory_id="TEST-3-10-001",
        name="3.10 Integration Textile MSME",
        industry="textile",
        state="Tamil Nadu",
        district="Coimbatore",
        production_per_day=Quantity(
            value=1000,
            unit="kg/day",
        ),
        operating_hours_per_day=8,
        operating_days_per_year=300,
        current_fuel="coal",
        fuel_consumption=Quantity(
            value=100,
            unit="kg/day",
        ),
        electricity_consumption_kwh_day=1000,
        required_process_temperature_c=180,
        roof_area_sqm=1000,
        available_land_sqm=2000,
        budget_inr=5_000_000,
        grid_reliability_pct=95,
        msme_classification="small",
        udyam_registered=True,
        udyam_number="TEST-3-10-UDYAM",
        annual_turnover_inr=20_000_000,
        plant_and_machinery_or_equipment_investment_inr=8_000_000,
        project_type="energy_efficiency",
        project_cost_inr=2_000_000,
        loan_amount_inr=None,
        existing_or_new_project="existing",
        brownfield_or_greenfield="brownfield",
        cluster_name=None,
        cluster_is_adeetie_identified=None,
        annual_energy_savings_percent=10,
        special_category=None,
    )


@pytest.fixture
def sample_factory_dict(sample_factory: Any) -> dict[str, Any]:
    if hasattr(sample_factory, "model_dump"):
        return copy.deepcopy(sample_factory.model_dump())
    if hasattr(sample_factory, "dict"):
        return copy.deepcopy(sample_factory.dict())
    return copy.deepcopy(sample_factory)


@pytest.fixture
def knowledge_base_root(repo_root: Path) -> Path:
    return repo_root / "knowledge-base"


@pytest.fixture
def datasets_root(repo_root: Path) -> Path:
    return repo_root / "datasets"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def json_loader():
    return load_json
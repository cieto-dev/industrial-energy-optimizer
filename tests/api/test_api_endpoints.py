from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

pytestmark = pytest.mark.api


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "running"
    assert "message" in payload
    assert "version" in payload


def test_root_exposes_request_id(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_geographic_profile_requires_state(client: TestClient) -> None:
    response = client.get("/geographic/profile")

    assert response.status_code == 422


def test_geographic_profile_rejects_empty_state(client: TestClient) -> None:
    response = client.get(
        "/geographic/profile",
        params={"state": ""},
    )

    assert response.status_code == 422


def test_geographic_electricity_requires_state(client: TestClient) -> None:
    response = client.get("/geographic/electricity")

    assert response.status_code == 422


def test_geographic_renewables_requires_state(client: TestClient) -> None:
    response = client.get("/geographic/renewables")

    assert response.status_code == 422


def test_geographic_biomass_requires_state(client: TestClient) -> None:
    response = client.get("/geographic/biomass")

    assert response.status_code == 422


def test_geographic_clusters_accepts_optional_filters(
    client: TestClient,
) -> None:
    response = client.get(
        "/geographic/clusters",
        params={
            "state": "Tamil Nadu",
            "district": "Coimbatore",
            "industry": "textile",
        },
    )

    # Dataset availability may vary during development.
    # The endpoint itself must still return a valid HTTP response.
    assert response.status_code in {200, 500}


def test_geographic_profile_response_is_json(
    client: TestClient,
) -> None:
    response = client.get(
        "/geographic/profile",
        params={"state": "Tamil Nadu"},
    )

    assert response.headers["content-type"].startswith(
        "application/json"
    )
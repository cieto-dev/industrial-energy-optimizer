
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query  # type: ignore[reportMissingImports]

import sys
from pathlib import Path

# Make project root importable when running backend/main.py directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from decision_engine.geographic.geographic_intelligence import (  # noqa: E402
    GeographicIntelligence,
)


router = APIRouter(
    prefix="/api/geographic",
    tags=["Geographic Intelligence"],
)

engine = GeographicIntelligence(repo_root=PROJECT_ROOT)


@router.get("/profile")
def geographic_profile(
    state: str = Query(..., min_length=1),
    district: str | None = Query(default=None),
    industry: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Return location-aware resource, tariff, cluster and coordinate data.
    """

    try:
        return engine.profile_location(
            state=state,
            district=district,
            industry=industry,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Geographic profile generation failed: {exc}",
        ) from exc


@router.get("/recommendations")
def geographic_recommendations(
    state: str = Query(..., min_length=1),
    district: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    technologies: list[str] | None = Query(default=None),
) -> dict[str, Any]:
    """
    Return explainable geographic recommendation signals.
    """

    try:
        return engine.recommendation_signals(
            state=state,
            district=district,
            industry=industry,
            technologies=technologies,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Geographic recommendation generation failed: {exc}",
        ) from exc


@router.get("/biomass")
def biomass_profile(
    state: str = Query(..., min_length=1),
    district: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Return district/state biomass availability.
    """

    try:
        return engine.get_biomass_profile(
            state=state,
            district=district,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Biomass profile generation failed: {exc}",
        ) from exc


@router.get("/electricity")
def electricity_profile(
    state: str = Query(..., min_length=1),
) -> dict[str, Any]:
    """
    Return state electricity tariff / DISCOM information available
    in repository datasets.
    """

    try:
        return engine.get_electricity_profile(
            state=state,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Electricity profile generation failed: {exc}",
        ) from exc


@router.get("/renewables")
def renewable_profile(
    state: str = Query(..., min_length=1),
) -> dict[str, Any]:
    """
    Return renewable-resource availability signals.
    """

    try:
        return engine.get_renewable_profile(
            state=state,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Renewable profile generation failed: {exc}",
        ) from exc


@router.get("/clusters")
def cluster_profile(
    state: str | None = Query(default=None),
    district: str | None = Query(default=None),
    industry: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Return evidence-backed industrial-cluster information.
    """

    try:
        return engine.get_cluster_profile(
            state=state,
            district=district,
            industry=industry,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Cluster profile generation failed: {exc}",
        ) from exc

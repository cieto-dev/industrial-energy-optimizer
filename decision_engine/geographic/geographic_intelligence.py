from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


class GeographicIntelligence:
    """
    Location-aware intelligence layer for the industrial energy optimizer.

    Responsibilities:
    - Resolve a factory location to state/district.
    - Read district biomass availability.
    - Read district coordinates.
    - Read state/DISCOM tariff information where available.
    - Maintain renewable-resource indicators.
    - Maintain industrial-cluster indicators.
    - Generate location-aware recommendations.

    The engine is intentionally deterministic and explainable.
    It does not use ML and does not silently manufacture missing data.
    """

    def __init__(self, repo_root: str | Path | None = None) -> None:
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[2]

        self.repo_root = Path(repo_root)

        self.datasets_dir = self.repo_root / "datasets"
        self.converted_dir = self.datasets_dir / "converted"
        self.tariff_dir = self.datasets_dir / "electricity_tariffs"

        self.biomass_csv = self.datasets_dir / "biomass_atlas.csv"
        self.coordinates_csv = self.datasets_dir / "district_coordinates.csv"

        self.biomass_json = self.converted_dir / "biomass_atlas.json"
        self.coordinates_json = self.converted_dir / "district_coordinates.json"
        self.tariffs_json = self.converted_dir / "electricity_tariffs.json"

        self._biomass_cache: list[dict[str, Any]] | None = None
        self._coordinates_cache: list[dict[str, Any]] | None = None
        self._tariffs_cache: Any = None

    # ------------------------------------------------------------------
    # Generic loaders
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(value: Any) -> str:
        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

    @staticmethod
    def _to_float(value: Any, default: float | None = None) -> float | None:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    @staticmethod
    def _read_json(path: Path) -> Any:
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------

    def load_biomass(self) -> list[dict[str, Any]]:
        if self._biomass_cache is not None:
            return self._biomass_cache

        rows = self._read_csv(self.biomass_csv)

        if not rows:
            json_data = self._read_json(self.biomass_json)

            if isinstance(json_data, list):
                rows = json_data

            elif isinstance(json_data, dict):
                for key in (
                    "records",
                    "data",
                    "biomass",
                    "biomass_atlas",
                ):
                    candidate = json_data.get(key)
                    if isinstance(candidate, list):
                        rows = candidate
                        break

        self._biomass_cache = rows
        return rows

    def load_coordinates(self) -> list[dict[str, Any]]:
        if self._coordinates_cache is not None:
            return self._coordinates_cache

        rows = self._read_csv(self.coordinates_csv)

        if not rows:
            json_data = self._read_json(self.coordinates_json)

            if isinstance(json_data, list):
                rows = json_data

            elif isinstance(json_data, dict):
                for key in (
                    "records",
                    "data",
                    "coordinates",
                    "district_coordinates",
                ):
                    candidate = json_data.get(key)
                    if isinstance(candidate, list):
                        rows = candidate
                        break

        self._coordinates_cache = rows
        return rows

    def load_tariffs(self) -> Any:
        if self._tariffs_cache is not None:
            return self._tariffs_cache

        self._tariffs_cache = self._read_json(self.tariffs_json)

        if self._tariffs_cache is None:
            self._tariffs_cache = {
                "source": "repository dataset unavailable",
                "records": [],
            }

        return self._tariffs_cache

    # ------------------------------------------------------------------
    # Location resolution
    # ------------------------------------------------------------------

    def resolve_location(
        self,
        state: str | None = None,
        district: str | None = None,
    ) -> dict[str, Any]:
        requested_state = self._normalise(state)
        requested_district = self._normalise(district)

        coordinates = self.load_coordinates()

        exact_match: dict[str, Any] | None = None
        district_match: dict[str, Any] | None = None
        state_match: dict[str, Any] | None = None

        for row in coordinates:
            row_state = self._normalise(
                row.get("state")
                or row.get("State")
            )
            row_district = self._normalise(
                row.get("district")
                or row.get("District")
            )

            if requested_state and requested_district:
                if (
                    row_state == requested_state
                    and row_district == requested_district
                ):
                    exact_match = row
                    break

            if requested_district and row_district == requested_district:
                district_match = row

            if requested_state and row_state == requested_state:
                state_match = row

        selected = exact_match or district_match or state_match

        if selected is None:
            return {
                "matched": False,
                "state": state,
                "district": district,
                "latitude": None,
                "longitude": None,
                "match_type": None,
            }

        latitude = self._to_float(
            selected.get("latitude")
            or selected.get("lat")
            or selected.get("Latitude")
        )

        longitude = self._to_float(
            selected.get("longitude")
            or selected.get("lon")
            or selected.get("lng")
            or selected.get("Longitude")
        )

        resolved_state = (
            selected.get("state")
            or selected.get("State")
            or state
        )

        resolved_district = (
            selected.get("district")
            or selected.get("District")
            or district
        )

        match_type = "state"

        if exact_match is not None:
            match_type = "exact"
        elif district_match is not None:
            match_type = "district"

        return {
            "matched": True,
            "state": resolved_state,
            "district": resolved_district,
            "latitude": latitude,
            "longitude": longitude,
            "match_type": match_type,
        }

    # ------------------------------------------------------------------
    # Biomass intelligence
    # ------------------------------------------------------------------

    def get_biomass_profile(
        self,
        state: str | None = None,
        district: str | None = None,
    ) -> dict[str, Any]:
        requested_state = self._normalise(state)
        requested_district = self._normalise(district)

        rows = self.load_biomass()

        matches: list[dict[str, Any]] = []

        for row in rows:
            row_state = self._normalise(
                row.get("state")
                or row.get("State")
            )
            row_district = self._normalise(
                row.get("district")
                or row.get("District")
            )

            if requested_state and row_state != requested_state:
                continue

            if requested_district and row_district != requested_district:
                continue

            matches.append(row)

        total_availability = 0.0
        biomass_types: dict[str, float] = {}
        crop_types: dict[str, float] = {}
        costs: list[float] = []

        for row in matches:
            availability = self._to_float(
                row.get("annual_availability_tons")
                or row.get("annual_availability")
                or row.get("availability_tons"),
                0.0,
            ) or 0.0

            biomass_type = (
                row.get("biomass_type")
                or row.get("Biomass Type")
                or "Unknown"
            )

            crop = (
                row.get("crop")
                or row.get("Crop")
                or "Unknown"
            )

            cost = self._to_float(
                row.get("cost_rs_per_ton")
                or row.get("cost_inr_per_ton")
                or row.get("cost"),
            )

            total_availability += availability
            biomass_types[str(biomass_type)] = (
                biomass_types.get(str(biomass_type), 0.0)
                + availability
            )
            crop_types[str(crop)] = (
                crop_types.get(str(crop), 0.0)
                + availability
            )

            if cost is not None:
                costs.append(cost)

        average_cost = (
            sum(costs) / len(costs)
            if costs
            else None
        )

        if matches:
            status = "available"
        else:
            status = "not_available_in_dataset"

        return {
            "state": state,
            "district": district,
            "status": status,
            "record_count": len(matches),
            "annual_surplus_biomass_tons": round(total_availability, 2),
            "average_biomass_cost_inr_per_ton": (
                round(average_cost, 2)
                if average_cost is not None
                else None
            ),
            "biomass_types": dict(
                sorted(
                    biomass_types.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ),
            "crop_types": dict(
                sorted(
                    crop_types.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ),
            "source": (
                "National Biomass Atlas of India "
                "(SSS-NIBE/MNRE, based on ASCI study)"
            ),
        }

    # ------------------------------------------------------------------
    # DISCOM / tariff intelligence
    # ------------------------------------------------------------------

    def _flatten_records(self, data: Any) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        if isinstance(data, list):
            return [
                item for item in data
                if isinstance(item, dict)
            ]

        if not isinstance(data, dict):
            return records

        for key in (
            "records",
            "data",
            "tariffs",
            "tariff_master",
            "slabs",
            "states",
        ):
            candidate = data.get(key)

            if isinstance(candidate, list):
                records.extend(
                    item for item in candidate
                    if isinstance(item, dict)
                )

            elif isinstance(candidate, dict):
                for value in candidate.values():
                    if isinstance(value, list):
                        records.extend(
                            item for item in value
                            if isinstance(item, dict)
                        )

        return records

    def get_electricity_profile(
        self,
        state: str | None = None,
    ) -> dict[str, Any]:
        requested_state = self._normalise(state)

        data = self.load_tariffs()
        records = self._flatten_records(data)

        matches: list[dict[str, Any]] = []

        for row in records:
            row_state = self._normalise(
                row.get("state")
                or row.get("State")
                or row.get("state_name")
                or row.get("State Name")
            )

            if requested_state and row_state == requested_state:
                matches.append(row)

        discom_names: list[str] = []

        for row in matches:
            discom = (
                row.get("discom")
                or row.get("DISCOM")
                or row.get("discom_name")
                or row.get("DISCOM Name")
            )

            if discom:
                discom_names.append(str(discom))

        # The repository may not yet contain an explicit normalized
        # state-to-DISCOM mapping. Never invent one.
        return {
            "state": state,
            "status": (
                "available"
                if matches
                else "not_available_in_dataset"
            ),
            "record_count": len(matches),
            "discoms": sorted(set(discom_names)),
            "records": matches,
            "source": "Repository electricity tariff datasets",
        }

    # ------------------------------------------------------------------
    # Renewable resource intelligence
    # ------------------------------------------------------------------

    def get_renewable_profile(
        self,
        state: str | None = None,
    ) -> dict[str, Any]:
        """
        Return renewable-resource indicators.

        This intentionally distinguishes between:
        - resource data actually available in the repository
        - recommendations that can only be inferred from technology fit

        At present the repository does not expose a validated state-level
        solar/wind resource dataset in the same way that it exposes biomass
        and tariffs. Therefore no unsupported numeric solar/wind values are
        fabricated here.
        """

        state_name = str(state) if state else None

        return {
            "state": state_name,
            "solar": {
                "status": "not_available_in_repository_dataset",
                "recommendation_signal": (
                    "Evaluate solar/electrification pathways using "
                    "site roof area, grid conditions and tariff data."
                ),
            },
            "wind": {
                "status": "not_available_in_repository_dataset",
                "recommendation_signal": (
                    "Do not score wind resource numerically until a "
                    "validated state/district wind dataset is added."
                ),
            },
            "renewable_electricity": {
                "status": "partially_inferable",
                "recommendation_signal": (
                    "Use tariff and site constraints to compare "
                    "grid electricity against renewable-powered pathways."
                ),
            },
        }

    # ------------------------------------------------------------------
    # Industrial cluster intelligence
    # ------------------------------------------------------------------

    def get_cluster_profile(
        self,
        state: str | None = None,
        district: str | None = None,
        industry: str | None = None,
    ) -> dict[str, Any]:
        """
        Cluster intelligence is currently evidence-aware rather than
        hard-coded as a fabricated district ranking.

        The uploaded research identifies cluster-level importance and
        specific example clusters. We expose those as evidence-backed
        signals until a dedicated machine-readable industrial-cluster
        dataset is added to the repository.
        """

        industry_key = self._normalise(industry)

        examples = []

        # Evidence-backed cluster examples from uploaded project research.
        known_clusters = [
            {
                "cluster": "Panipat textile cluster",
                "industry": "textiles",
                "region": "Haryana",
            },
            {
                "cluster": "Surat textile cluster",
                "industry": "textiles",
                "region": "Gujarat",
            },
            {
                "cluster": "Dehradun pharmaceutical cluster",
                "industry": "pharmaceuticals",
                "region": "Uttarakhand",
            },
            {
                "cluster": "Muzaffarnagar paper cluster",
                "industry": "paper",
                "region": "Uttar Pradesh",
            },
            {
                "cluster": "Raigarh steel cluster",
                "industry": "steel",
                "region": "Chhattisgarh",
            },
            {
                "cluster": "Raipur steel cluster",
                "industry": "steel",
                "region": "Chhattisgarh",
            },
            {
                "cluster": "Sundargarh steel cluster",
                "industry": "steel",
                "region": "Odisha",
            },
            {
                "cluster": "Bellary steel cluster",
                "industry": "steel",
                "region": "Karnataka",
            },
            {
                "cluster": "Jharsuguda steel cluster",
                "industry": "steel",
                "region": "Odisha",
            },
        ]

        requested_state = self._normalise(state)

        for cluster in known_clusters:
            cluster_region = self._normalise(cluster["region"])
            cluster_industry = self._normalise(cluster["industry"])

            if requested_state and cluster_region != requested_state:
                continue

            if industry_key and cluster_industry != industry_key:
                continue

            examples.append(cluster)

        return {
            "state": state,
            "district": district,
            "industry": industry,
            "status": (
                "evidence_examples_available"
                if examples
                else "no_exact_cluster_dataset_match"
            ),
            "cluster_examples": examples,
            "source_notes": [
                "MNRE-GIZ biomass study identifies multiple MSME clusters.",
                "NITI Aayog roadmap emphasizes a cluster-based MSME approach.",
                "CEEW 2026 research evaluates industrial decarbonisation at cluster level.",
            ],
        }

    # ------------------------------------------------------------------
    # Overall geographic intelligence
    # ------------------------------------------------------------------

    def profile_location(
        self,
        state: str | None = None,
        district: str | None = None,
        industry: str | None = None,
    ) -> dict[str, Any]:
        location = self.resolve_location(
            state=state,
            district=district,
        )

        resolved_state = location.get("state") or state
        resolved_district = location.get("district") or district

        biomass = self.get_biomass_profile(
            state=resolved_state,
            district=resolved_district,
        )

        electricity = self.get_electricity_profile(
            state=resolved_state,
        )

        renewable = self.get_renewable_profile(
            state=resolved_state,
        )

        clusters = self.get_cluster_profile(
            state=resolved_state,
            district=resolved_district,
            industry=industry,
        )

        return {
            "location": location,
            "biomass": biomass,
            "discom_electricity": electricity,
            "renewable_resources": renewable,
            "industrial_clusters": clusters,
        }

    # ------------------------------------------------------------------
    # Location-aware recommendation signals
    # ------------------------------------------------------------------

    def recommendation_signals(
        self,
        state: str | None = None,
        district: str | None = None,
        industry: str | None = None,
        technologies: list[str] | None = None,
    ) -> dict[str, Any]:
        profile = self.profile_location(
            state=state,
            district=district,
            industry=industry,
        )

        technologies = technologies or []

        technology_keys = {
            self._normalise(value)
            for value in technologies
        }

        signals: list[dict[str, Any]] = []
        warnings: list[str] = []

        biomass = profile["biomass"]

        annual_biomass = (
            biomass.get("annual_surplus_biomass_tons")
            or 0.0
        )

        if annual_biomass > 0:
            signals.append(
                {
                    "type": "biomass_availability",
                    "priority": "high",
                    "message": (
                        f"District dataset indicates approximately "
                        f"{annual_biomass:,.0f} tonnes/year of surplus "
                        f"biomass availability."
                    ),
                    "supports": [
                        "biomass_boiler",
                        "biomass_heat",
                        "multifuel_boiler",
                    ],
                }
            )
        else:
            warnings.append(
                "No matching district biomass record was found; "
                "biomass should not receive a geographic availability bonus."
            )

        electricity = profile["discom_electricity"]

        if electricity.get("record_count", 0) > 0:
            signals.append(
                {
                    "type": "electricity_tariff",
                    "priority": "high",
                    "message": (
                        "State-level electricity tariff records are available "
                        "and should be incorporated into the electricity pathway "
                        "cost calculation."
                    ),
                    "supports": [
                        "heat_pump",
                        "electric_boiler",
                        "resistance_furnace",
                        "induction_furnace",
                    ],
                }
            )
        else:
            warnings.append(
                "No state tariff record was matched; do not fabricate a "
                "DISCOM tariff for this location."
            )

        renewable = profile["renewable_resources"]

        if renewable["solar"]["status"] != "available":
            warnings.append(
                "Validated numeric solar-resource data is not currently "
                "available in the repository geographic dataset."
            )

        clusters = profile["industrial_clusters"]

        if clusters.get("cluster_examples"):
            signals.append(
                {
                    "type": "industrial_cluster",
                    "priority": "medium",
                    "message": (
                        "Location/industry matches an evidence-backed "
                        "industrial cluster example."
                    ),
                    "supports": [
                        "cluster_procurement",
                        "shared_infrastructure",
                        "esco_model",
                    ],
                }
            )

        # Technology-specific interpretation
        if (
            "biomass" in technology_keys
            or "biomass boiler" in technology_keys
            or "biomass boiler" in technology_keys
        ):
            if annual_biomass <= 0:
                warnings.append(
                    "Biomass technology was requested but the geographic "
                    "dataset does not confirm local surplus biomass."
                )

        return {
            "profile": profile,
            "signals": signals,
            "warnings": warnings,
        }


def build_geographic_profile(
    state: str | None = None,
    district: str | None = None,
    industry: str | None = None,
    technologies: list[str] | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for API and application integration."""

    engine = GeographicIntelligence()

    return engine.recommendation_signals(
        state=state,
        district=district,
        industry=industry,
        technologies=technologies,
    )


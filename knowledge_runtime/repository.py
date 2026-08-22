from __future__ import annotations

from copy import deepcopy
from typing import Any

from .evidence import EvidenceResolver
from .errors import KnowledgeDataError, KnowledgeItemNotFoundError
from .loader import KnowledgeLoader


class KnowledgeRepository:
    """
    Single runtime access layer for project knowledge.

    The decision engine should depend on this class instead of directly
    opening JSON files.

    Supported access patterns include:

        repo.get_biomass(...)
        repo.get_tariff(...)
        repo.get_technology(...)
        repo.get_industry(...)
        repo.get_emission_factor(...)
        repo.get_grid_factor(...)
        repo.get_source(...)
    """

    PATHS = {
        "biomass": "converted/biomass_atlas.json",
        "tariffs": "master/tariffs.json",
        "emission_factors": "emissions/emission_factors.json",
        "grid_factors": "emissions/grid_factors.json",
        "citations": "references/citations.json",
        "sources": "references/sources.json",
    }

    def __init__(
        self,
        loader: KnowledgeLoader | None = None,
    ) -> None:
        self.loader = loader or KnowledgeLoader()
        self.evidence = EvidenceResolver(self.loader)

    # ------------------------------------------------------------------
    # Generic loader access
    # ------------------------------------------------------------------

    def load_knowledge(self, relative_path: str) -> Any:
        """Load any knowledge-base JSON through the centralized loader."""
        return self.loader.load_knowledge_json(relative_path)

    def load_dataset(self, relative_path: str) -> Any:
        """Load any converted dataset JSON through the centralized loader."""
        return self.loader.load_dataset_json(relative_path)

    def clear_cache(self) -> None:
        """Clear the runtime knowledge cache."""
        self.loader.clear_cache()

    # ------------------------------------------------------------------
    # Biomass
    # ------------------------------------------------------------------

    def get_biomass(
        self,
        biomass_id: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Read the converted Biomass Atlas dataset.

        The converted dataset is preserved as-is. This method supports
        optional filtering when records expose a recognizable ID/name field.
        """
        data = self.loader.load_dataset_json("converted/biomass_atlas.json")

        if isinstance(data, dict) and "records" in data:
            records = data["records"]
        else:
            records = self._as_records(data)

        if biomass_id is None:
            return [
                self._with_evidence(record)
                for record in records
            ]

        for record in records:
            identifier = self._first_identifier(
                record,
                (
                    "biomass_id",
                    "id",
                    "biomass_type",
                    "biomass_name",
                    "name",
                ),
            )

            if identifier == biomass_id:
                return self._with_evidence(record)

        raise KnowledgeItemNotFoundError(
            "biomass",
            biomass_id,
        )

    # ------------------------------------------------------------------
    # Tariffs
    # ------------------------------------------------------------------

    def get_tariff(
        self,
        tariff_id: str | None = None,
        *,
        state_id: str | None = None,
        discom_id: str | None = None,
        consumer_category: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        data = self.loader.load_knowledge_json(
            self.PATHS["tariffs"]
        )

        records = self._as_records(data)

        if tariff_id is not None:
            for record in records:
                if (
                    record.get("tariff_id") == tariff_id
                    or record.get("id") == tariff_id
                ):
                    return self._with_evidence(record)

            raise KnowledgeItemNotFoundError(
                "tariff",
                tariff_id,
            )

        filtered = records

        if state_id is not None:
            filtered = [
                record
                for record in filtered
                if record.get("state_id") == state_id
            ]

        if discom_id is not None:
            filtered = [
                record
                for record in filtered
                if record.get("discom_id") == discom_id
            ]

        if consumer_category is not None:
            filtered = [
                record
                for record in filtered
                if record.get("consumer_category") == consumer_category
            ]

        return [
            self._with_evidence(record)
            for record in filtered
        ]

    # ------------------------------------------------------------------
    # Technologies
    # ------------------------------------------------------------------

    def get_technology(
        self,
        technology_id: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        records = self._load_json_directory("technologies")

        if technology_id is None:
            return [
                self._with_evidence(record)
                for record in records
            ]

        for record in records:
            identifier = self._first_identifier(
                record,
                (
                    "technology_id",
                    "id",
                    "technology",
                    "name",
                ),
            )

            if (
                isinstance(identifier, str)
                and identifier.lower() == technology_id.lower()
            ):
                return self._with_evidence(record)

        raise KnowledgeItemNotFoundError(
            "technology",
            technology_id,
        )

    # ------------------------------------------------------------------
    # Industries
    # ------------------------------------------------------------------

    def get_industry(
        self,
        industry_id: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        records = self._load_json_directory("industries")

        if industry_id is None:
            return [
                self._with_evidence(record)
                for record in records
            ]

        for record in records:
            identifier = self._first_identifier(
                record,
                (
                    "industry_id",
                    "id",
                    "industry",
                    "name",
                ),
            )

            if (
                isinstance(identifier, str)
                and identifier.lower() == industry_id.lower()
            ):
                return self._with_evidence(record)

        raise KnowledgeItemNotFoundError(
            "industry",
            industry_id,
        )

    # ------------------------------------------------------------------
    # Emission factors
    # ------------------------------------------------------------------

    def get_emission_factor(
        self,
        fuel_id: str | None = None,
    ) -> dict[str, Any] | dict[str, dict[str, Any]]:
        data = self.loader.load_knowledge_json(
            self.PATHS["emission_factors"]
        )

        if not isinstance(data, dict):
            raise KnowledgeDataError(
                self.PATHS["emission_factors"],
                "expected a JSON object keyed by fuel ID",
            )

        if fuel_id is None:
            result: dict[str, dict[str, Any]] = {}

            for key, value in data.items():
                if not isinstance(value, dict):
                    continue

                result[key] = self._with_evidence(value)

            return result

        if fuel_id not in data:
            raise KnowledgeItemNotFoundError(
                "emission_factor",
                fuel_id,
            )

        value = data[fuel_id]

        if not isinstance(value, dict):
            raise KnowledgeDataError(
                self.PATHS["emission_factors"],
                f"record '{fuel_id}' is not a JSON object",
            )

        return self._with_evidence(value)

    # ------------------------------------------------------------------
    # Grid factors
    # ------------------------------------------------------------------

    def get_grid_factor(
        self,
        factor_id: str | None = None,
    ) -> dict[str, Any] | dict[str, Any]:
        data = self.loader.load_knowledge_json(
            self.PATHS["grid_factors"]
        )

        if not isinstance(data, dict):
            raise KnowledgeDataError(
                self.PATHS["grid_factors"],
                "expected a JSON object",
            )

        if factor_id is None:
            return deepcopy(data)

        if factor_id not in data:
            raise KnowledgeItemNotFoundError(
                "grid_factor",
                factor_id,
            )

        value = data[factor_id]

        if isinstance(value, dict):
            return self._with_evidence(value)

        return {
            "value": value,
            "evidence": self.evidence.resolve(value),
        }

    # ------------------------------------------------------------------
    # Evidence / source access
    # ------------------------------------------------------------------

    def get_source(
        self,
        source_id: str,
    ) -> dict[str, Any]:
        return self.evidence.get_source(source_id)

    def get_evidence(
        self,
        record: Any,
    ) -> list[dict[str, Any]]:
        return self.evidence.resolve(record)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_json_directory(
        self,
        directory_name: str,
    ) -> list[dict[str, Any]]:
        directory = self.loader.resolve_knowledge_path(directory_name)

        if not directory.exists():
            raise KnowledgeDataError(
                directory_name,
                "knowledge-base directory does not exist",
            )

        if not directory.is_dir():
            raise KnowledgeDataError(
                directory_name,
                "expected a directory",
            )

        records: list[dict[str, Any]] = []

        for path in sorted(directory.glob("*.json")):
            relative_path = path.relative_to(
                self.loader.knowledge_base_dir
            )

            data = self.loader.load_knowledge_json(
                str(relative_path)
            )

            if isinstance(data, dict):
                records.append(data)

            elif isinstance(data, list):
                records.extend(
                    item
                    for item in data
                    if isinstance(item, dict)
                )

        return records

    @staticmethod
    def _as_records(
        data: Any,
    ) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [
                item
                for item in data
                if isinstance(item, dict)
            ]

        if isinstance(data, dict):
            records: list[dict[str, Any]] = []

            for key, value in data.items():
                if isinstance(value, dict):
                    record = dict(value)
                    record.setdefault("id", key)
                    records.append(record)

            return records

        raise KnowledgeDataError(
            "runtime dataset",
            "expected a JSON object or JSON array",
        )

    @staticmethod
    def _first_identifier(
        record: dict[str, Any],
        fields: tuple[str, ...],
    ) -> Any:
        for field in fields:
            value = record.get(field)

            if value is not None:
                return value

        return None

    def _with_evidence(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return a defensive copy plus resolved evidence.

        Records without source_id are still valid; they simply receive
        an empty evidence list.
        """
        result = deepcopy(record)

        result["evidence"] = self.evidence.resolve(result)

        return result

from __future__ import annotations

from typing import Any, Iterable

from .evidence import EvidenceResolver
from .errors import KnowledgeDataError, KnowledgeItemNotFoundError
from .loader import KnowledgeLoader


class KnowledgeRepository:
    """
    Single runtime access layer for project knowledge.

    Performance layer:
    - lazy dataset loading
    - indexed lookups
    - cached filtered query results
    - no repeated linear scans for common IDs
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

        # Lazy indexes. None means "not built yet".
        self._technology_index: dict[str, dict[str, Any]] | None = None
        self._industry_index: dict[str, dict[str, Any]] | None = None
        self._biomass_index: dict[str, dict[str, Any]] | None = None

        self._tariff_query_cache: dict[
            tuple[str | None, str | None, str | None],
            list[dict[str, Any]],
        ] = {}

    # ------------------------------------------------------------------
    # Generic access
    # ------------------------------------------------------------------

    def load_knowledge(
        self,
        relative_path: str,
    ) -> Any:
        return self.loader.load_knowledge_json(relative_path)

    def load_dataset(
        self,
        relative_path: str,
    ) -> Any:
        return self.loader.load_dataset_json(relative_path)

    def clear_cache(self) -> None:
        self.loader.clear_cache()

        self._technology_index = None
        self._industry_index = None
        self._biomass_index = None
        self._tariff_query_cache.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _as_records(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, dict) and "records" in data:
            data = data["records"]

        if isinstance(data, list):
            return [
                value
                for value in data
                if isinstance(value, dict)
            ]

        if isinstance(data, dict):
            # If the dict is itself a record with an identifier, return [data]
            if any(k in data for k in ("industry_id", "technology_id", "biomass_id", "tariff_id")):
                return [data]

            # If it has a container key, return its sub-records
            for container_key in ("industries", "technologies", "biomass", "tariffs"):
                if container_key in data and isinstance(data[container_key], dict):
                    return [
                        v for v in data[container_key].values()
                        if isinstance(v, dict)
                    ]

            sub_dicts = [
                value
                for value in data.values()
                if isinstance(value, dict)
            ]
            if sub_dicts:
                return sub_dicts
            return [data]

        raise KnowledgeDataError(
            "runtime",
            "expected JSON object/list containing records",
        )

    @staticmethod
    def _first_identifier(
        record: dict[str, Any],
        candidates: Iterable[str],
    ) -> str | None:
        for key in candidates:
            value = record.get(key)
            if value is None:
                continue

            return str(value)

        return None

    def _with_evidence(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        result = dict(record)
        result["evidence"] = self.evidence.resolve(record)
        return result

    # ------------------------------------------------------------------
    # v2.0 schema helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_value(
        parameter: Any,
        field_name: str = "<unknown>",
    ) -> float | None:
        """
        Safely extract the numeric `.value` from a v2.0 parameter object.

        Accepts either:
          - a nested dict: {"value": <number>, "confidence": ..., ...}
          - a raw scalar (legacy fallback, accepted with a warning)

        Returns None if the value is absent or non-numeric.
        Never raises; callers should check for None and apply
        validate_parameter() for quality-gate decisions.
        """
        if isinstance(parameter, dict):
            raw = parameter.get("value")
        elif isinstance(parameter, (int, float)) and not isinstance(parameter, bool):
            # Legacy scalar — still accepted but not preferred.
            raw = parameter
        else:
            return None

        if raw is None:
            return None

        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_parameter(
        record: dict[str, Any],
        key: str,
    ) -> dict[str, Any] | None:
        """
        Return the full v2.0 parameter object for *key* from *record*.

        Returns None if the key is absent or its value is not a dict.
        Use extract_value() on the result to obtain the numeric value.
        """
        param = record.get(key)
        if isinstance(param, dict):
            return param
        return None

    @staticmethod
    def validate_parameter(
        record: dict[str, Any],
        key: str,
        field_label: str | None = None,
    ) -> dict[str, Any]:
        """
        Quality-gate a single v2.0 parameter and return a structured status.

        Return schema::

            {
                "ok": bool,           # False blocks a firm recommendation
                "value": float|None,
                "confidence": str|None,
                "source_id": str|None,
                "last_verified": str|None,
                "warnings": [str],    # non-empty when confidence is Low
                "errors": [str],      # non-empty when value/source_id absent
            }

        Failsafe rules (per plan §1.1):
          - confidence == "Low"  → ok=True but warnings populated
          - value is None        → ok=False, errors populated
          - source_id is absent  → ok=False, errors populated
        """
        label = field_label or key
        param = record.get(key)
        warnings: list[str] = []
        errors: list[str] = []

        if param is None:
            errors.append(
                f"Required parameter '{label}' is absent. "
                "Cannot produce a firm recommendation without it."
            )
            return {
                "ok": False,
                "value": None,
                "confidence": None,
                "source_id": None,
                "last_verified": None,
                "warnings": warnings,
                "errors": errors,
            }

        # Legacy scalar — wrap it mentally but flag for upgrade.
        if isinstance(param, (int, float)) and not isinstance(param, bool):
            warnings.append(
                f"Parameter '{label}' is a raw scalar (legacy format). "
                "It should be migrated to the v2.0 nested schema."
            )
            return {
                "ok": True,
                "value": float(param),
                "confidence": "Low",
                "source_id": None,
                "last_verified": None,
                "warnings": warnings,
                "errors": errors,
            }

        if not isinstance(param, dict):
            errors.append(
                f"Parameter '{label}' has unexpected type "
                f"({type(param).__name__}). Expected a v2.0 parameter object."
            )
            return {
                "ok": False,
                "value": None,
                "confidence": None,
                "source_id": None,
                "last_verified": None,
                "warnings": warnings,
                "errors": errors,
            }

        raw_value = param.get("value")
        confidence = param.get("confidence")
        source_id = param.get("source_id")
        last_verified = param.get("last_verified")

        numeric_value: float | None = None
        if raw_value is not None:
            try:
                numeric_value = float(raw_value)
            except (TypeError, ValueError):
                errors.append(
                    f"Parameter '{label}' has a non-numeric value: {raw_value!r}."
                )

        if numeric_value is None and raw_value is None:
            errors.append(
                f"Parameter '{label}' has no value. "
                "Cannot produce a firm recommendation without it."
            )

        if not source_id:
            errors.append(
                f"Parameter '{label}' has no source_id. "
                "All quantitative values must be traceable to an allowable source."
            )

        if confidence == "Low":
            warnings.append(
                f"Parameter '{label}' has Low confidence. "
                "Uncertainty ranges should be widened and this warning "
                "must be surfaced to the operator."
            )

        ok = len(errors) == 0
        return {
            "ok": ok,
            "value": numeric_value,
            "confidence": confidence,
            "source_id": source_id,
            "last_verified": last_verified,
            "warnings": warnings,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Index builders
    # ------------------------------------------------------------------

    def _build_index(
        self,
        records: list[dict[str, Any]],
        identifier_fields: tuple[str, ...],
    ) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}

        for record in records:
            identifier = self._first_identifier(
                record,
                identifier_fields,
            )

            if identifier is None:
                continue

            index[identifier.lower()] = record

        return index

    def _get_biomass_index(
        self,
    ) -> dict[str, dict[str, Any]]:
        if self._biomass_index is None:
            data = self.loader.load_dataset_json(
                "converted/biomass_atlas.json",
                shared=True,
            )

            records = self._as_records(data)

            self._biomass_index = self._build_index(
                records,
                (
                    "biomass_id",
                    "id",
                    "biomass_type",
                    "biomass_name",
                    "name",
                ),
            )

        return self._biomass_index

    def _get_technology_index(
        self,
    ) -> dict[str, dict[str, Any]]:
        if self._technology_index is None:
            records = [
                record
                for item in self.loader.load_json_directory(
                    "technologies",
                    base="knowledge-base",
                )
                for record in self._as_records(item)
            ]

            self._technology_index = self._build_index(
                records,
                (
                    "technology_id",
                    "id",
                    "technology",
                    "name",
                ),
            )

        return self._technology_index

    def _get_industry_index(
        self,
    ) -> dict[str, dict[str, Any]]:
        if self._industry_index is None:
            records = [
                record
                for item in self.loader.load_json_directory(
                    "industries",
                    base="knowledge-base",
                )
                for record in self._as_records(item)
            ]

            self._industry_index = self._build_index(
                records,
                (
                    "industry_id",
                    "id",
                    "industry",
                    "name",
                ),
            )

        return self._industry_index

    # ------------------------------------------------------------------
    # Biomass
    # ------------------------------------------------------------------

    def get_biomass(
        self,
        biomass_id: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:

        data = self.loader.load_dataset_json(
            "converted/biomass_atlas.json",
            shared=True,
        )

        records = self._as_records(data)

        if biomass_id is None:
            return [self._with_evidence(r) for r in records]

        index = self._get_biomass_index()

        record = index.get(
            str(biomass_id).strip().lower()
        )

        if record is None:
            raise KnowledgeItemNotFoundError(
                "biomass",
                biomass_id,
            )

        return self._with_evidence(record)

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
            self.PATHS["tariffs"],
            shared=True,
        )

        records = self._as_records(data)

        if tariff_id is not None:
            target = str(tariff_id).strip().lower()

            for record in records:
                current = self._first_identifier(
                    record,
                    ("tariff_id", "id"),
                )

                if (
                    current is not None
                    and current.lower() == target
                ):
                    return self._with_evidence(record)

            raise KnowledgeItemNotFoundError(
                "tariff",
                tariff_id,
            )

        cache_key = (
            state_id,
            discom_id,
            consumer_category,
        )

        cached = self._tariff_query_cache.get(cache_key)

        if cached is not None:
            return cached

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
                if record.get("consumer_category")
                == consumer_category
            ]

        result = [self._with_evidence(r) for r in filtered]
        self._tariff_query_cache[cache_key] = result

        return result

    # ------------------------------------------------------------------
    # Technology
    # ------------------------------------------------------------------

    def get_technology(
        self,
        technology_id: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:

        if technology_id is None:
            return [
                self._with_evidence(r)
                for r in self._get_technology_index().values()
            ]

        target = str(technology_id).strip().lower()

        record = self._get_technology_index().get(target)

        if record is None:
            raise KnowledgeItemNotFoundError(
                "technology",
                technology_id,
            )

        return self._with_evidence(record)

    # ------------------------------------------------------------------
    # Industries
    # ------------------------------------------------------------------

    def get_industry(
        self,
        industry_id: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:

        if industry_id is None:
            return [
                self._with_evidence(r)
                for r in self._get_industry_index().values()
            ]

        target = str(industry_id).strip().lower()

        record = self._get_industry_index().get(target)

        if record is None:
            raise KnowledgeItemNotFoundError(
                "industry",
                industry_id,
            )

        return self._with_evidence(record)

    # ------------------------------------------------------------------
    # Emission factors
    # ------------------------------------------------------------------

    def get_emission_factor(
        self,
        fuel_id: str | None = None,
    ) -> dict[str, Any]:

        data = self.loader.load_knowledge_json(
            self.PATHS["emission_factors"],
            shared=True,
        )

        if not isinstance(data, dict):
            raise KnowledgeDataError(
                self.PATHS["emission_factors"],
                "expected a JSON object keyed by fuel ID",
            )

        if fuel_id is None:
            return {
                key: self._with_evidence(value)
                for key, value in data.items()
                if isinstance(value, dict)
            }

        value = data.get(fuel_id)

        if not isinstance(value, dict):
            raise KnowledgeItemNotFoundError(
                "emission_factor",
                fuel_id,
            )

        return self._with_evidence(value)

    # ------------------------------------------------------------------
    # Grid factors
    # ------------------------------------------------------------------

    def get_grid_factor(
        self,
        factor_id: str | None = None,
    ) -> dict[str, Any]:

        data = self.loader.load_knowledge_json(
            self.PATHS["grid_factors"],
            shared=True,
        )

        if not isinstance(data, dict):
            raise KnowledgeDataError(
                self.PATHS["grid_factors"],
                "expected a JSON object keyed by factor ID",
            )

        if factor_id is None:
            return data

        value = data.get(factor_id)

        if value is None:
            raise KnowledgeItemNotFoundError(
                "grid_factor",
                factor_id,
            )

        return value

    def get_source(
        self,
        source_id: str,
    ) -> dict[str, Any]:
        return self.evidence.get_source(source_id)


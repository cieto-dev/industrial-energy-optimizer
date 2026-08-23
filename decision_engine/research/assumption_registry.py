"""
Assumption Registry
===================

Authoritative resolution of planning / research assumptions with full
provenance. Used by baseline, emissions and economics engines so that
every important numeric default carries an AssumptionRecord.

Task 3.1 requirement: important assumptions must never be silent
hard-coded constants.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from decision_engine.validation.validation_engine import (
    AssumptionRecord,
    EvidenceValidationError,
    ValidationEngine,
)

BASE_DIR = Path(__file__).resolve().parents[2]
CANONICAL_ASSUMPTIONS_PATH = (
    BASE_DIR / "knowledge-base" / "assumptions" / "canonical_assumptions.json"
)
VALIDATION_DEFAULTS_PATH = (
    BASE_DIR / "knowledge-base" / "validation" / "validation_defaults.json"
)


@dataclass(frozen=True)
class ResolvedAssumption:
    """Value + full evidence record returned to calculation engines."""

    value: float
    unit: str
    record: AssumptionRecord

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "unit": self.unit,
            "evidence": asdict(self.record),
        }


class AssumptionRegistry:
    """
    Loads canonical assumptions once and resolves them with validation.
    """

    def __init__(
        self,
        *,
        canonical_path: Path | None = None,
        validation_defaults_path: Path | None = None,
        validation_engine: ValidationEngine | None = None,
    ) -> None:
        self._canonical_path = canonical_path or CANONICAL_ASSUMPTIONS_PATH
        self._validation_defaults_path = (
            validation_defaults_path or VALIDATION_DEFAULTS_PATH
        )
        self._ve = validation_engine or ValidationEngine()
        self._cache: dict[str, ResolvedAssumption] = {}
        self._load()

    def _load(self) -> None:
        data: dict[str, Any] = {}

        # Prefer the dedicated canonical file; fall back to validation_defaults.
        if self._canonical_path.exists():
            with self._canonical_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            thermal = raw.get("thermal_efficiency", {})
            for key, rec in thermal.items():
                data[key] = rec
        elif self._validation_defaults_path.exists():
            with self._validation_defaults_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            planning = raw.get("planning_assumptions", {})
            # Map the keys used in validation_defaults.json
            mapping = {
                "boiler_efficiency": "boiler_efficiency",
                "steam_distribution_efficiency": "steam_distribution_efficiency",
                "process_heat_utilization": "process_heat_utilization",
            }
            for src_key, dst_key in mapping.items():
                if src_key in planning:
                    data[dst_key] = planning[src_key]
                    data[dst_key]["parameter"] = dst_key

        for param, rec in data.items():
            self._register(param, rec)

    def _register(self, parameter: str, raw: dict[str, Any]) -> None:
        try:
            record = AssumptionRecord(
                parameter=raw.get("parameter", parameter),
                value=float(raw["value"]),
                unit=str(raw.get("unit", "pct")),
                source_id=str(raw.get("source_id", "SRC_PROJECT_DEFAULTS")),
                source_type=str(raw.get("source_type", "project_research")),
                source_date=raw.get("source_date"),
                status=str(raw.get("status", "estimated")),
                confidence=str(raw.get("confidence", "low")),
                uncertainty=raw.get("uncertainty")
                or raw.get("notes")
                or "Planning default; replace with measured value when available.",
                notes=raw.get("notes"),
                applicability=raw.get("applicability", "planning_default"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EvidenceValidationError(
                f"Invalid assumption record for '{parameter}': {exc}"
            ) from exc

        # Validate the evidence metadata through the central engine.
        validation = self._ve.validate_assumption_record(record)
        if not validation.passed:
            messages = "; ".join(i.message for i in validation.issues)
            raise EvidenceValidationError(
                f"Assumption '{parameter}' failed evidence validation: {messages}"
            )

        self._cache[parameter] = ResolvedAssumption(
            value=float(record.value),
            unit=record.unit,
            record=record,
        )

    def get(self, parameter: str) -> ResolvedAssumption:
        if parameter not in self._cache:
            raise KeyError(
                f"Assumption '{parameter}' is not registered. "
                "Add it to knowledge-base/assumptions/canonical_assumptions.json "
                "or knowledge-base/validation/validation_defaults.json."
            )
        return self._cache[parameter]

    def get_value(self, parameter: str) -> float:
        return self.get(parameter).value

    def get_thermal_efficiency_bundle(self) -> dict[str, ResolvedAssumption]:
        return {
            "boiler_efficiency": self.get("boiler_efficiency"),
            "steam_distribution_efficiency": self.get(
                "steam_distribution_efficiency"
            ),
            "process_heat_utilization": self.get("process_heat_utilization"),
        }


# Module-level singleton used by calculators.
_REGISTRY: Optional[AssumptionRegistry] = None


def get_assumption_registry() -> AssumptionRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AssumptionRegistry()
    return _REGISTRY
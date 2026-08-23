"""
Industrial Energy Transition Optimizer
======================================

Research Validation, Calibration & Production Safety Engine
------------------------------------------------------------

Task 3.1
~~~~~~~~

This module is the central validation layer for calculation engines.

It does NOT replace the domain engines. Instead it provides a common,
deterministic framework for:

1. unit validation and conversion
2. physical-domain validation
3. research assumption metadata
4. source provenance
5. confidence classification
6. uncertainty flags
7. duplicate/conflicting-parameter detection
8. evidence-quality scoring
9. energy-balance validation
10. emissions-accounting boundary checks
11. tariff/finance input validation
12. deterministic validation reports
13. calibration checks
14. fail-closed behaviour for unsafe assumptions

Design requirements
-------------------
- No silent conversion between incompatible units.
- No silent fallback to invented research values.
- Research-derived parameters carry provenance metadata.
- Historical / estimated / proposed values remain distinguishable.
- Low-confidence values can be consumed for exploration but are visibly flagged.
- Critical missing values can fail validation rather than fabricate an answer.
- Calculations remain standard-library-only.
- Domain modules can consume the returned ValidationResult objects without
  coupling themselves to this implementation.

Canonical calculation conventions
----------------------------------
Energy:
    electricity -> kWh
    thermal internal calculation -> MJ
    reporting -> MJ / GJ / TJ

Emissions:
    internal -> kgCO2e
    reporting -> tCO2e

Money:
    INR

Tariffs:
    INR/kWh
    INR/kW-month
    INR/kVA-month

Physical quantities:
    retain native physical unit when required by the technology/fuel model.

Evidence model
--------------
Each important assumption should be represented by AssumptionRecord:

    parameter
    value
    unit
    source_id
    source_type
    source_date
    status
    confidence
    uncertainty
    notes

This is deliberately compatible with the repository's reference architecture,
which separates parameter citations from full source metadata.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


# =============================================================================
# Exceptions
# =============================================================================


class ValidationEngineError(Exception):
    """Base exception for validation failures."""


class UnitValidationError(ValidationEngineError, ValueError):
    """Raised when a unit is unsupported or incompatible."""


class ParameterValidationError(ValidationEngineError, ValueError):
    """Raised when a parameter violates its declared domain."""


class EvidenceValidationError(ValidationEngineError, ValueError):
    """Raised when provenance/evidence metadata is incomplete."""


class ConflictValidationError(ValidationEngineError, ValueError):
    """Raised when conflicting assumptions are encountered."""


class CalibrationValidationError(ValidationEngineError, ValueError):
    """Raised when a calibration check fails."""


# =============================================================================
# Constants
# =============================================================================


VALID_STATUS = {
    "current",
    "historical",
    "estimated",
    "provisional",
    "proposed",
    "inferred",
    "unknown",
}

VALID_CONFIDENCE = {
    "high",
    "medium",
    "low",
    "unknown",
}

VALID_SOURCE_TYPES = {
    "government",
    "regulator",
    "international_organization",
    "peer_reviewed",
    "academic",
    "industry",
    "vendor",
    "project_research",
    "secondary",
    "unknown",
}

# Confidence weights are intentionally monotonic and transparent.
CONFIDENCE_WEIGHTS = {
    "high": 1.00,
    "medium": 0.75,
    "low": 0.45,
    "unknown": 0.25,
}

# Status weights distinguish current facts from proposals/unknowns.
STATUS_WEIGHTS = {
    "current": 1.00,
    "historical": 0.85,
    "estimated": 0.60,
    "provisional": 0.55,
    "inferred": 0.45,
    "proposed": 0.35,
    "unknown": 0.25,
}

# Source type weights are deliberately conservative.
SOURCE_TYPE_WEIGHTS = {
    "government": 1.00,
    "regulator": 1.00,
    "international_organization": 0.95,
    "peer_reviewed": 0.95,
    "academic": 0.90,
    "industry": 0.70,
    "vendor": 0.45,
    "project_research": 0.60,
    "secondary": 0.50,
    "unknown": 0.25,
}

# ---------------------------------------------------------------------------
# Unit conversion factors
#
# Base quantity for energy internally is MJ.
# ---------------------------------------------------------------------------

ENERGY_TO_MJ = {
    "J": 1.0e-6,
    "kJ": 1.0e-3,
    "MJ": 1.0,
    "GJ": 1.0e3,
    "TJ": 1.0e6,
    "Wh": 3.6e-3,
    "kWh": 3.6,
    "MWh": 3.6e3,
    "GWh": 3.6e6,
}

MASS_TO_KG = {
    "mg": 1.0e-6,
    "g": 1.0e-3,
    "kg": 1.0,
    "t": 1.0e3,
    "tonne": 1.0e3,
    "tonnes": 1.0e3,
    "kt": 1.0e6,
    "Mt": 1.0e9,
}

VOLUME_TO_M3 = {
    "m3": 1.0,
    "Nm3": 1.0,
    "SCM": 1.0,
    "litre": 1.0e-3,
    "L": 1.0e-3,
}

TIME_TO_HOURS = {
    "h": 1.0,
    "hour": 1.0,
    "hours": 1.0,
    "day": 24.0,
    "days": 24.0,
    "month": 24.0 * 30.0,
    "months": 24.0 * 30.0,
    "year": 24.0 * 365.0,
    "years": 24.0 * 365.0,
}

POWER_UNITS = {
    "W": 1.0,
    "kW": 1.0e3,
    "MW": 1.0e6,
    "GW": 1.0e9,
}

EMISSIONS_TO_KG = {
    "kgCO2": 1.0,
    "kgCO2e": 1.0,
    "tCO2": 1.0e3,
    "tCO2e": 1.0e3,
    "MtCO2": 1.0e9,
    "MtCO2e": 1.0e9,
}

# Aliases used to normalize units from repository JSON/CSV files.
UNIT_ALIASES = {
    "kg_co2": "kgCO2",
    "kg_co2e": "kgCO2e",
    "kgco2": "kgCO2",
    "kgco2e": "kgCO2e",
    "tco2": "tCO2",
    "tco2e": "tCO2e",
    "mtco2": "MtCO2",
    "mtco2e": "MtCO2e",
    "kwh": "kWh",
    "mwh": "MWh",
    "gwh": "GWh",
    "mj": "MJ",
    "gj": "GJ",
    "tj": "TJ",
    "kw": "kW",
    "mw": "MW",
    "kg": "kg",
    "tonne": "tonne",
    "tonnes": "tonnes",
    "l": "L",
    "litre": "litre",
    "litres": "litre",
    "m3": "m3",
    "nm3": "Nm3",
    "scm": "SCM",
    "kgco2e/kwh": "kgCO2e/kWh",
    "kgco2/kwh": "kgCO2/kWh",
    "kgco2e_per_kwh": "kgCO2e/kWh",
    "kgco2_per_kwh": "kgCO2/kWh",
    "tco2/mwh": "tCO2/MWh",
    "tco2e/mwh": "tCO2e/MWh",
    "kgco2e/kg": "kgCO2e/kg",
    "kgco2e/mj": "kgCO2e/MJ",
    "kgco2/mj": "kgCO2/MJ",
    "inr/kwh": "INR/kWh",
    "inr/kvah": "INR/kVAh",
    "inr/kg": "INR/kg",
    "inr/litre": "INR/L",
    "inr/l": "INR/L",
    "inr/scm": "INR/SCM",
    "inr/t": "INR/t",
    "inr/tonne": "INR/t",
}

# ---------------------------------------------------------------------------
# Emission accounting categories
# ---------------------------------------------------------------------------

VALID_EMISSION_CATEGORIES = {
    "fossil_combustion",
    "biogenic_combustion",
    "purchased_electricity",
    "renewable_electricity",
    "avoided_emissions",
    "lifecycle",
    "unknown",
}


# =============================================================================
# Helpers
# =============================================================================


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_unit(unit: str) -> str:
    """Return a canonical unit name."""
    text = _clean_text(unit)

    if not text:
        raise UnitValidationError("Unit cannot be empty.")

    direct = UNIT_ALIASES.get(text)
    if direct:
        return direct

    lowered = text.lower()
    return UNIT_ALIASES.get(lowered, text)


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise ParameterValidationError(
            f"{field_name} must be numeric, not boolean."
        )

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError(
            f"{field_name} must be numeric; received {value!r}."
        ) from exc

    if not math.isfinite(result):
        raise ParameterValidationError(
            f"{field_name} must be finite."
        )

    return result


def _validate_range(
    value: float,
    *,
    field_name: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> None:
    if minimum is not None and value < minimum:
        raise ParameterValidationError(
            f"{field_name} must be >= {minimum}; got {value}."
        )

    if maximum is not None and value > maximum:
        raise ParameterValidationError(
            f"{field_name} must be <= {maximum}; got {value}."
        )


def _normalize_status(value: Any) -> str:
    result = _clean_text(value).lower() or "unknown"
    if result not in VALID_STATUS:
        raise EvidenceValidationError(
            f"Unsupported evidence status: {result!r}."
        )
    return result


def _normalize_confidence(value: Any) -> str:
    result = _clean_text(value).lower() or "unknown"
    if result not in VALID_CONFIDENCE:
        raise EvidenceValidationError(
            f"Unsupported confidence value: {result!r}."
        )
    return result


def _normalize_source_type(value: Any) -> str:
    result = _clean_text(value).lower() or "unknown"
    if result not in VALID_SOURCE_TYPES:
        raise EvidenceValidationError(
            f"Unsupported source type: {result!r}."
        )
    return result


def _almost_equal(
    left: float,
    right: float,
    *,
    relative_tolerance: float = 1.0e-9,
    absolute_tolerance: float = 1.0e-9,
) -> bool:
    return math.isclose(
        left,
        right,
        rel_tol=relative_tolerance,
        abs_tol=absolute_tolerance,
    )


# =============================================================================
# Unit system
# =============================================================================


class UnitSystem:
    """
    Deterministic unit conversion service.

    The implementation intentionally refuses arbitrary cross-dimensional
    conversions.
    """

    ENERGY_DIMENSION = "energy"
    MASS_DIMENSION = "mass"
    VOLUME_DIMENSION = "volume"
    TIME_DIMENSION = "time"
    POWER_DIMENSION = "power"
    EMISSIONS_DIMENSION = "emissions"
    EMISSION_FACTOR_DIMENSION = "emission_factor"
    TARIFF_DIMENSION = "tariff"

    def __init__(self) -> None:
        self._dimensions = {
            **{key: self.ENERGY_DIMENSION for key in ENERGY_TO_MJ},
            **{key: self.MASS_DIMENSION for key in MASS_TO_KG},
            **{key: self.VOLUME_DIMENSION for key in VOLUME_TO_M3},
            **{key: self.TIME_DIMENSION for key in TIME_TO_HOURS},
            **{key: self.POWER_DIMENSION for key in POWER_UNITS},
            **{key: self.EMISSIONS_DIMENSION for key in EMISSIONS_TO_KG},
            "kgCO2e/kWh": self.EMISSION_FACTOR_DIMENSION,
            "kgCO2/kWh": self.EMISSION_FACTOR_DIMENSION,
            "tCO2/MWh": self.EMISSION_FACTOR_DIMENSION,
            "tCO2e/MWh": self.EMISSION_FACTOR_DIMENSION,
            "kgCO2e/kg": self.EMISSION_FACTOR_DIMENSION,
            "kgCO2e/MJ": self.EMISSION_FACTOR_DIMENSION,
            "kgCO2/MJ": self.EMISSION_FACTOR_DIMENSION,
            "INR/kWh": self.TARIFF_DIMENSION,
            "INR/kVAh": self.TARIFF_DIMENSION,
            "INR/kg": self.TARIFF_DIMENSION,
            "INR/L": self.TARIFF_DIMENSION,
            "INR/SCM": self.TARIFF_DIMENSION,
            "INR/t": self.TARIFF_DIMENSION,
        }

    def dimension(self, unit: str) -> str:
        normalized = normalize_unit(unit)

        if normalized not in self._dimensions:
            raise UnitValidationError(
                f"Unsupported unit: {unit!r}."
            )

        return self._dimensions[normalized]

    def convert(
        self,
        value: Any,
        from_unit: str,
        to_unit: str,
    ) -> float:
        source = normalize_unit(from_unit)
        target = normalize_unit(to_unit)

        source_dimension = self.dimension(source)
        target_dimension = self.dimension(target)

        if source_dimension != target_dimension:
            raise UnitValidationError(
                f"Incompatible conversion: {source!r} "
                f"({source_dimension}) -> {target!r} "
                f"({target_dimension})."
            )

        quantity = _finite_number(value, "value")

        if source_dimension == self.ENERGY_DIMENSION:
            base_value = quantity * ENERGY_TO_MJ[source]
            return base_value / ENERGY_TO_MJ[target]

        if source_dimension == self.MASS_DIMENSION:
            base_value = quantity * MASS_TO_KG[source]
            return base_value / MASS_TO_KG[target]

        if source_dimension == self.VOLUME_DIMENSION:
            base_value = quantity * VOLUME_TO_M3[source]
            return base_value / VOLUME_TO_M3[target]

        if source_dimension == self.TIME_DIMENSION:
            base_value = quantity * TIME_TO_HOURS[source]
            return base_value / TIME_TO_HOURS[target]

        if source_dimension == self.POWER_DIMENSION:
            base_value = quantity * POWER_UNITS[source]
            return base_value / POWER_UNITS[target]

        if source_dimension == self.EMISSIONS_DIMENSION:
            base_value = quantity * EMISSIONS_TO_KG[source]
            return base_value / EMISSIONS_TO_KG[target]

        raise UnitValidationError(
            f"No conversion implementation for dimension "
            f"{source_dimension!r}."
        )

    def to_mj(self, value: Any, unit: str) -> float:
        return self.convert(value, unit, "MJ")

    def to_kwh(self, value: Any, unit: str) -> float:
        return self.convert(value, unit, "kWh")

    def to_kg(self, value: Any, unit: str) -> float:
        return self.convert(value, unit, "kg")

    def to_tonnes(self, value: Any, unit: str) -> float:
        return self.convert(value, unit, "tonne")

    def to_kgco2e(self, value: Any, unit: str) -> float:
        return self.convert(value, unit, "kgCO2e")


# =============================================================================
# Evidence model
# =============================================================================



@dataclass(frozen=True)
class AssumptionRecord:
    parameter: str
    value: float
    unit: str
    source_id: str
    source_type: str
    status: str
    confidence: str
    uncertainty: str | None = None
    notes: str | None = None
    source_date: str | None = None
    applicability: str | None = None
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        if not _clean_text(self.parameter):
            raise EvidenceValidationError(
                "AssumptionRecord.parameter is required."
            )

        numeric_value = _finite_number(
            self.value,
            "AssumptionRecord.value",
        )

        _validate_range(
            numeric_value,
            field_name=self.parameter,
            minimum=self.min_value,
            maximum=self.max_value,
        )

        normalize_unit(self.unit)

        _normalize_status(self.status)
        _normalize_confidence(self.confidence)
        _normalize_source_type(self.source_type)

        if self.source_id is None and self.confidence == "high":
            raise EvidenceValidationError(
                f"High-confidence parameter {self.parameter!r} "
                "must have source_id."
            )

    @property
    def evidence_score(self) -> float:
        confidence_score = CONFIDENCE_WEIGHTS[
            _normalize_confidence(self.confidence)
        ]
        status_score = STATUS_WEIGHTS[
            _normalize_status(self.status)
        ]
        source_score = SOURCE_TYPE_WEIGHTS[
            _normalize_source_type(self.source_type)
        ]

        return round(
            confidence_score
            * status_score
            * source_score,
            4,
        )

    @property
    def requires_verification(self) -> bool:
        return (
            self.confidence in {"low", "unknown"}
            or self.status in {"estimated", "provisional", "proposed", "unknown"}
        )

    @property
    def is_currently_usable(self) -> bool:
        """
        A conservative production-use gate.

        Low-confidence/proposed parameters may still be displayed for scenario
        analysis, but they should not be treated as authoritative production
        inputs.
        """
        return (
            self.confidence in {"high", "medium"}
            and self.status in {"current", "historical", "inferred"}
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_score"] = self.evidence_score
        data["requires_verification"] = self.requires_verification
        data["is_currently_usable"] = self.is_currently_usable
        return data


@dataclass(frozen=True)
class ParameterCandidate:
    """
    One candidate value for a parameter.

    Used by conflict detection before a canonical parameter is selected.
    """

    parameter: str
    value: float
    unit: str

    source_id: Optional[str] = None
    source_type: str = "unknown"
    source_date: Optional[str] = None
    status: str = "unknown"
    confidence: str = "unknown"
    notes: str = ""

    def to_assumption(self) -> AssumptionRecord:
        return AssumptionRecord(
            parameter=self.parameter,
            value=self.value,
            unit=self.unit,
            source_id=self.source_id,
            source_type=self.source_type,
            source_date=self.source_date,
            status=self.status,
            confidence=self.confidence,
            notes=self.notes,
        )


@dataclass(frozen=True)
class ConflictRecord:
    parameter: str
    candidates: tuple[dict[str, Any], ...]
    severity: str
    reason: str
    resolution: str

    @property
    def is_blocking(self) -> bool:
        return self.severity == "blocking"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =============================================================================
# Validation results
# =============================================================================


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    parameter: Optional[str] = None
    source_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    name: str
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add_issue(
        self,
        code: str,
        severity: str,
        message: str,
        *,
        parameter: Optional[str] = None,
        source_ids: Sequence[str] = (),
    ) -> None:
        self.issues.append(
            ValidationIssue(
                code=code,
                severity=severity,
                message=message,
                parameter=parameter,
                source_ids=tuple(source_ids),
            )
        )

        if severity in {"error", "blocking"}:
            self.passed = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "metrics": dict(self.metrics),
        }


@dataclass
class ValidationReport:
    """
    Aggregated Task 3.1 validation output.
    """

    passed: bool = True

    unit_results: list[ValidationResult] = field(default_factory=list)
    assumption_results: list[ValidationResult] = field(default_factory=list)
    conflict_results: list[ConflictRecord] = field(default_factory=list)
    calibration_results: list[ValidationResult] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)

    evidence_score: float = 0.0

    def absorb(self, result: ValidationResult) -> None:
        if result.name.startswith("unit:"):
            self.unit_results.append(result)
        elif result.name.startswith("assumption:"):
            self.assumption_results.append(result)
        elif result.name.startswith("calibration:"):
            self.calibration_results.append(result)
        else:
            self.calibration_results.append(result)

        if not result.passed:
            self.passed = False

        for issue in result.issues:
            if issue.severity in {"warning"}:
                self.warnings.append(issue.message)
            elif issue.severity in {"error", "blocking"}:
                self.blocking_issues.append(issue.message)

    def add_conflicts(
        self,
        conflicts: Iterable[ConflictRecord],
    ) -> None:
        values = list(conflicts)

        self.conflict_results.extend(values)

        for conflict in values:
            if conflict.is_blocking:
                self.passed = False
                self.blocking_issues.append(
                    f"{conflict.parameter}: {conflict.reason}"
                )
            else:
                self.warnings.append(
                    f"{conflict.parameter}: {conflict.reason}"
                )

    def calculate_evidence_score(
        self,
        assumptions: Sequence[AssumptionRecord],
    ) -> float:
        if not assumptions:
            self.evidence_score = 0.0
            return self.evidence_score

        total = sum(
            item.evidence_score
            for item in assumptions
        )

        self.evidence_score = round(
            total / len(assumptions),
            4,
        )

        return self.evidence_score

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "unit_results": [
                item.to_dict()
                for item in self.unit_results
            ],
            "assumption_results": [
                item.to_dict()
                for item in self.assumption_results
            ],
            "conflict_results": [
                item.to_dict()
                for item in self.conflict_results
            ],
            "calibration_results": [
                item.to_dict()
                for item in self.calibration_results
            ],
            "warnings": list(self.warnings),
            "blocking_issues": list(self.blocking_issues),
            "evidence_score": self.evidence_score,
        }


# =============================================================================
# Core validation engine
# =============================================================================


class ValidationEngine:
    """
    Central Task 3.1 validation service.

    The service is intentionally stateless aside from its unit system and,
    optionally, repository source registries.
    """

    def __init__(
        self,
        *,
        references_root: Optional[str | Path] = None,
        strict: bool = False,
    ) -> None:
        self.units = UnitSystem()
        self.strict = bool(strict)

        self.references_root = (
            Path(references_root)
            if references_root is not None
            else None
        )

        self._sources: dict[str, dict[str, Any]] = {}
        self._citations: dict[str, dict[str, Any]] = {}

        if self.references_root is not None:
            self._load_reference_registry()

    # ------------------------------------------------------------------
    # Reference registry
    # ------------------------------------------------------------------

    def _load_reference_registry(self) -> None:
        sources_path = self.references_root / "sources.json"
        citations_path = self.references_root / "citations.json"

        if sources_path.exists():
            try:
                with sources_path.open(
                    "r",
                    encoding="utf-8",
                ) as handle:
                    payload = json.load(handle)

                if isinstance(payload, dict):
                    self._sources = payload
            except (OSError, json.JSONDecodeError) as exc:
                raise EvidenceValidationError(
                    f"Unable to load sources registry: {exc}"
                ) from exc

        if citations_path.exists():
            try:
                with citations_path.open(
                    "r",
                    encoding="utf-8",
                ) as handle:
                    payload = json.load(handle)

                if isinstance(payload, dict):
                    self._citations = payload
            except (OSError, json.JSONDecodeError) as exc:
                raise EvidenceValidationError(
                    f"Unable to load citations registry: {exc}"
                ) from exc

    def source_exists(self, source_id: str) -> bool:
        return source_id in self._sources

    def citation_exists(self, source_id: str) -> bool:
        return source_id in self._citations

    def validate_source_reference(
        self,
        source_id: Optional[str],
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"assumption:source:{source_id or 'missing'}",
            passed=True,
        )

        if not source_id:
            result.add_issue(
                "MISSING_SOURCE_ID",
                "warning",
                "Parameter has no source_id.",
            )
            return result

        if not self._sources and not self._citations:
            # The engine can operate without a loaded registry. It simply
            # cannot verify the registry membership.
            result.add_issue(
                "REFERENCE_REGISTRY_NOT_LOADED",
                "warning",
                "Reference registry is not loaded; source_id cannot be "
                "verified against repository metadata.",
                source_ids=(source_id,),
            )
            return result

        if not self.source_exists(source_id):
            result.add_issue(
                "SOURCE_NOT_FOUND",
                "error" if self.strict else "warning",
                f"source_id {source_id!r} is absent from sources.json.",
                source_ids=(source_id,),
            )

        if not self.citation_exists(source_id):
            result.add_issue(
                "CITATION_NOT_FOUND",
                "error" if self.strict else "warning",
                f"source_id {source_id!r} is absent from citations.json.",
                source_ids=(source_id,),
            )

        return result

    # ------------------------------------------------------------------
    # Unit validation
    # ------------------------------------------------------------------

    def validate_unit(
        self,
        *,
        name: str,
        value: Any,
        unit: str,
        expected_unit: Optional[str] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"unit:{name}",
            passed=True,
        )

        try:
            numeric = _finite_number(value, name)

            self.units.dimension(unit)

            _validate_range(
                numeric,
                field_name=name,
                minimum=minimum,
                maximum=maximum,
            )

            if expected_unit is not None:
                actual_dimension = self.units.dimension(unit)
                expected_dimension = self.units.dimension(expected_unit)

                if actual_dimension != expected_dimension:
                    result.add_issue(
                        "UNIT_DIMENSION_MISMATCH",
                        "error",
                        (
                            f"{name} uses {unit!r} "
                            f"but expected a unit compatible with "
                            f"{expected_unit!r}."
                        ),
                        parameter=name,
                    )

        except ValidationEngineError as exc:
            result.add_issue(
                "UNIT_VALIDATION_FAILED",
                "error",
                str(exc),
                parameter=name,
            )

        return result

    def validate_energy_conversion(
        self,
        *,
        value: float,
        from_unit: str,
        to_unit: str,
        expected_value: Optional[float] = None,
        relative_tolerance: float = 1.0e-6,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"unit:conversion:{from_unit}->{to_unit}",
            passed=True,
        )

        try:
            converted = self.units.convert(
                value,
                from_unit,
                to_unit,
            )

            result.metrics["converted_value"] = converted
            result.metrics["from_unit"] = normalize_unit(from_unit)
            result.metrics["to_unit"] = normalize_unit(to_unit)

            if expected_value is not None:
                expected = float(expected_value)

                if not math.isclose(
                    converted,
                    expected,
                    rel_tol=relative_tolerance,
                    abs_tol=relative_tolerance,
                ):
                    result.add_issue(
                        "CONVERSION_MISMATCH",
                        "error",
                        (
                            f"Expected {expected} {to_unit} but obtained "
                            f"{converted} {to_unit}."
                        ),
                    )

        except ValidationEngineError as exc:
            result.add_issue(
                "CONVERSION_FAILED",
                "error",
                str(exc),
            )

        return result

    # ------------------------------------------------------------------
    # Assumption validation
    # ------------------------------------------------------------------

    def validate_assumption(
        self,
        assumption: AssumptionRecord,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"assumption:{assumption.parameter}",
            passed=True,
        )

        try:
            _finite_number(
                assumption.value,
                assumption.parameter,
            )

            # Trigger full dataclass validation.
            normalize_unit(assumption.unit)
            _normalize_status(assumption.status)
            _normalize_confidence(assumption.confidence)
            _normalize_source_type(assumption.source_type)

            _validate_range(
                float(assumption.value),
                field_name=assumption.parameter,
                minimum=assumption.min_value,
                maximum=assumption.max_value,
            )

        except ValidationEngineError as exc:
            result.add_issue(
                "ASSUMPTION_VALIDATION_FAILED",
                "error",
                str(exc),
                parameter=assumption.parameter,
            )
            return result

        source_result = self.validate_source_reference(
            assumption.source_id
        )

        for issue in source_result.issues:
            severity = issue.severity

            if (
                issue.code in {
                    "SOURCE_NOT_FOUND",
                    "CITATION_NOT_FOUND",
                }
                and not self.strict
            ):
                severity = "warning"

            result.add_issue(
                issue.code,
                severity,
                issue.message,
                parameter=assumption.parameter,
                source_ids=issue.source_ids,
            )

        if assumption.requires_verification:
            result.add_issue(
                "VERIFICATION_REQUIRED",
                "warning",
                (
                    f"Parameter {assumption.parameter!r} is marked "
                    f"{assumption.status}/{assumption.confidence} "
                    "and should be verified before high-stakes use."
                ),
                parameter=assumption.parameter,
                source_ids=(
                    (assumption.source_id,)
                    if assumption.source_id
                    else ()
                ),
            )

        result.metrics["evidence_score"] = (
            assumption.evidence_score
        )

        result.metrics["production_usable"] = (
            assumption.is_currently_usable
        )

        return result

    validate_assumption_record = validate_assumption

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(
        self,
        candidates: Sequence[ParameterCandidate],
        *,
        relative_tolerance: float = 0.01,
        severity: str = "blocking",
    ) -> list[ConflictRecord]:
        """
        Detect materially different values for the same parameter.

        Candidates are first normalized into a common unit. Values within the
        relative tolerance are treated as effectively equivalent.

        The engine does NOT average conflicting research values.
        """

        grouped: dict[str, list[ParameterCandidate]] = {}

        for candidate in candidates:
            grouped.setdefault(
                candidate.parameter,
                [],
            ).append(candidate)

        conflicts: list[ConflictRecord] = []

        for parameter, values in grouped.items():
            if len(values) <= 1:
                continue

            normalized_values: list[tuple[ParameterCandidate, float]] = []

            # Normalize all candidates to the first candidate's unit.
            target_unit = normalize_unit(values[0].unit)

            for candidate in values:
                normalized = self.units.convert(
                    candidate.value,
                    candidate.unit,
                    target_unit,
                )
                normalized_values.append(
                    (candidate, normalized)
                )

            baseline = normalized_values[0][1]

            materially_different = any(
                not math.isclose(
                    baseline,
                    normalized,
                    rel_tol=relative_tolerance,
                    abs_tol=1.0e-12,
                )
                for _, normalized in normalized_values[1:]
            )

            if not materially_different:
                continue

            serialized_candidates = tuple(
                {
                    **candidate.to_assumption().to_dict(),
                    "normalized_value": normalized,
                    "normalized_unit": target_unit,
                }
                for candidate, normalized in normalized_values
            )

            conflicts.append(
                ConflictRecord(
                    parameter=parameter,
                    candidates=serialized_candidates,
                    severity=severity,
                    reason=(
                        "Multiple materially different values exist for "
                        f"{parameter!r}; no safe canonical value can be "
                        "selected automatically."
                    ),
                    resolution=(
                        "Select and record one authoritative parameter "
                        "value explicitly. Do not average conflicting "
                        "sources."
                    ),
                )
            )

        return conflicts

    # ------------------------------------------------------------------
    # Physics/domain checks
    # ------------------------------------------------------------------

    def validate_efficiency(
        self,
        *,
        parameter: str,
        efficiency: float,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"assumption:{parameter}",
            passed=True,
        )

        numeric = _finite_number(
            efficiency,
            parameter,
        )

        # Efficiency may be expressed either as decimal or percent.
        normalized = numeric * 100 if 0 < numeric <= 1 else numeric

        if normalized <= 0 or normalized > 100:
            result.add_issue(
                "INVALID_EFFICIENCY",
                "error",
                (
                    f"{parameter} must be between 0 and 100%; "
                    f"received {numeric}."
                ),
                parameter=parameter,
            )

        result.metrics["normalized_efficiency_pct"] = normalized

        return result

    def validate_cop(
        self,
        *,
        parameter: str,
        cop: float,
        maximum_plausible_cop: Optional[float] = None,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"assumption:{parameter}",
            passed=True,
        )

        numeric = _finite_number(
            cop,
            parameter,
        )

        if numeric <= 0:
            result.add_issue(
                "INVALID_COP",
                "error",
                f"{parameter} must be > 0; received {numeric}.",
                parameter=parameter,
            )

        if maximum_plausible_cop is not None and numeric > maximum_plausible_cop:
            result.add_issue(
                "COP_OUTSIDE_DECLARED_RANGE",
                "warning",
                (
                    f"{parameter}={numeric} exceeds declared plausibility "
                    f"screen {maximum_plausible_cop}."
                ),
                parameter=parameter,
            )

        result.metrics["cop"] = numeric
        return result

    def validate_temperature_range(
        self,
        *,
        required_temperature_c: float,
        minimum_supported_c: float,
        maximum_supported_c: float,
    ) -> ValidationResult:
        result = ValidationResult(
            name="calibration:temperature_capability",
            passed=True,
        )

        required = _finite_number(
            required_temperature_c,
            "required_temperature_c",
        )

        minimum = _finite_number(
            minimum_supported_c,
            "minimum_supported_c",
        )

        maximum = _finite_number(
            maximum_supported_c,
            "maximum_supported_c",
        )

        if minimum > maximum:
            result.add_issue(
                "INVALID_TECHNOLOGY_RANGE",
                "error",
                "Technology minimum temperature exceeds maximum.",
            )
            return result

        feasible = minimum <= required <= maximum

        result.metrics.update(
            {
                "required_temperature_c": required,
                "minimum_supported_c": minimum,
                "maximum_supported_c": maximum,
                "temperature_feasible": feasible,
            }
        )

        if not feasible:
            result.add_issue(
                "TEMPERATURE_INFEASIBLE",
                "error",
                (
                    f"Required process temperature {required}°C is outside "
                    f"technology range {minimum}–{maximum}°C."
                ),
            )

        return result

    # ------------------------------------------------------------------
    # Energy conservation
    # ------------------------------------------------------------------

    def validate_energy_balance(
        self,
        *,
        input_energy_mj: float,
        useful_energy_mj: float,
        loss_components_mj: Mapping[str, float],
        tolerance_mj: float = 1.0e-6,
    ) -> ValidationResult:
        result = ValidationResult(
            name="calibration:energy_balance",
            passed=True,
        )

        input_value = _finite_number(
            input_energy_mj,
            "input_energy_mj",
        )

        useful_value = _finite_number(
            useful_energy_mj,
            "useful_energy_mj",
        )

        losses = 0.0

        for name, value in loss_components_mj.items():
            numeric = _finite_number(
                value,
                f"loss_components_mj[{name}]",
            )

            if numeric < -tolerance_mj:
                result.add_issue(
                    "NEGATIVE_LOSS",
                    "error",
                    (
                        f"Loss component {name!r} is negative: "
                        f"{numeric} MJ."
                    ),
                    parameter=name,
                )

            losses += numeric

        reconstructed = useful_value + losses
        residual = input_value - reconstructed

        result.metrics.update(
            {
                "input_energy_mj": input_value,
                "useful_energy_mj": useful_value,
                "loss_energy_mj": losses,
                "reconstructed_energy_mj": reconstructed,
                "residual_mj": residual,
                "tolerance_mj": tolerance_mj,
            }
        )

        if abs(residual) > tolerance_mj:
            result.add_issue(
                "ENERGY_BALANCE_FAILED",
                "error",
                (
                    "Energy balance does not close within tolerance: "
                    f"residual={residual} MJ."
                ),
            )

        return result

    # ------------------------------------------------------------------
    # Emissions accounting
    # ------------------------------------------------------------------

    def validate_emission_factor(
        self,
        *,
        parameter: str,
        emission_factor: float,
        emission_factor_unit: str,
        category: str,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"assumption:{parameter}",
            passed=True,
        )

        numeric = _finite_number(
            emission_factor,
            parameter,
        )

        if numeric < 0:
            result.add_issue(
                "NEGATIVE_EMISSION_FACTOR",
                "error",
                (
                    f"{parameter} cannot be negative; "
                    f"received {numeric}."
                ),
                parameter=parameter,
            )

        valid_units = {
            "kgCO2/TJ",
            "tCO2/TJ",
            "kgCO2/kWh",
            "kgCO2e/kWh",
            "kgCO2/kg",
            "tCO2/t",
            "kgCO2/GJ",
        }
        if emission_factor_unit not in valid_units:
            result.add_issue(
                "INVALID_EMISSION_FACTOR_UNIT",
                "error",
                f"Unsupported unit: '{emission_factor_unit}'.",
                parameter=parameter,
            )

        if category not in VALID_EMISSION_CATEGORIES:
            result.add_issue(
                "INVALID_EMISSION_CATEGORY",
                "error",
                (
                    f"Unsupported emissions category {category!r}."
                ),
                parameter=parameter,
            )

        if category == "biogenic_combustion":
            result.add_issue(
                "BIOGENIC_ACCOUNTING_BOUNDARY",
                "warning",
                (
                    "Biogenic combustion CO2 must not automatically be "
                    "treated as equivalent to fossil CO2. Reporting and "
                    "lifecycle accounting boundaries must be explicit."
                ),
                parameter=parameter,
            )

        result.metrics.update(
            {
                "emission_factor": numeric,
                "unit": normalize_unit(emission_factor_unit),
                "category": category,
            }
        )

        return result

    def calculate_grid_emissions(
        self,
        *,
        electricity_kwh: float,
        grid_factor_kgco2e_per_kwh: float,
    ) -> dict[str, float]:
        electricity = _finite_number(
            electricity_kwh,
            "electricity_kwh",
        )

        factor = _finite_number(
            grid_factor_kgco2e_per_kwh,
            "grid_factor_kgco2e_per_kwh",
        )

        _validate_range(
            electricity,
            field_name="electricity_kwh",
            minimum=0,
        )

        _validate_range(
            factor,
            field_name="grid_factor_kgco2e_per_kwh",
            minimum=0,
        )

        emissions_kg = electricity * factor

        return {
            "electricity_kwh": round(
                electricity,
                6,
            ),
            "grid_factor_kgco2e_per_kwh": round(
                factor,
                9,
            ),
            "emissions_kgco2e": round(
                emissions_kg,
                6,
            ),
            "emissions_tco2e": round(
                emissions_kg / 1000,
                9,
            ),
        }

    # ------------------------------------------------------------------
    # Percentage and financial checks
    # ------------------------------------------------------------------

    def validate_percentage(
        self,
        *,
        parameter: str,
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> ValidationResult:
        result = ValidationResult(
            name=f"assumption:{parameter}",
            passed=True,
        )

        numeric = _finite_number(
            value,
            parameter,
        )

        _validate_range(
            numeric,
            field_name=parameter,
            minimum=minimum,
            maximum=maximum,
        )

        result.metrics["value_pct"] = numeric
        return result

    def validate_payback(
        self,
        *,
        capex_inr: float,
        annual_savings_inr: float,
    ) -> ValidationResult:
        result = ValidationResult(
            name="calibration:payback",
            passed=True,
        )

        capex = _finite_number(
            capex_inr,
            "capex_inr",
        )

        savings = _finite_number(
            annual_savings_inr,
            "annual_savings_inr",
        )

        if capex < 0:
            result.add_issue(
                "NEGATIVE_CAPEX",
                "error",
                "CapEx cannot be negative.",
            )

        if savings < 0:
            result.add_issue(
                "NEGATIVE_SAVINGS",
                "error",
                (
                    "Annual savings cannot be negative for a positive "
                    "payback calculation. Negative economics should be "
                    "represented separately as annual loss."
                ),
            )

        if savings > 0:
            payback = capex / savings
            result.metrics["simple_payback_years"] = round(
                payback,
                6,
            )
        else:
            result.metrics["simple_payback_years"] = None
            if capex > 0:
                result.add_issue(
                    "UNDEFINED_PAYBACK",
                    "warning",
                    "Payback is undefined because annual savings are zero.",
                )

        return result

    # ------------------------------------------------------------------
    # Tariff checks
    # ------------------------------------------------------------------

    def validate_tariff(
        self,
        *,
        energy_charge_inr_per_kwh: float,
        demand_charge_inr_per_unit_month: float = 0.0,
        fixed_charge_inr_per_month: float = 0.0,
        electricity_duty_pct: float = 0.0,
        status: str = "unknown",
        confidence: str = "unknown",
    ) -> ValidationResult:
        result = ValidationResult(
            name="calibration:tariff",
            passed=True,
        )

        numeric_fields = {
            "energy_charge_inr_per_kwh": energy_charge_inr_per_kwh,
            "demand_charge_inr_per_unit_month": demand_charge_inr_per_unit_month,
            "fixed_charge_inr_per_month": fixed_charge_inr_per_month,
        }

        for name, value in numeric_fields.items():
            numeric = _finite_number(value, name)

            if numeric < 0:
                result.add_issue(
                    "NEGATIVE_TARIFF_COMPONENT",
                    "error",
                    f"{name} cannot be negative.",
                    parameter=name,
                )

        duty_result = self.validate_percentage(
            parameter="electricity_duty_pct",
            value=electricity_duty_pct,
        )

        for issue in duty_result.issues:
            result.issues.append(issue)

            if issue.severity in {"error", "blocking"}:
                result.passed = False

        normalized_status = _normalize_status(status)
        normalized_confidence = _normalize_confidence(confidence)

        if normalized_status != "current":
            result.add_issue(
                "NON_CURRENT_TARIFF",
                "warning",
                (
                    f"Tariff status is {normalized_status!r}; "
                    "verify current applicability before final investment use."
                ),
            )

        if normalized_confidence not in {"high", "medium"}:
            result.add_issue(
                "LOW_TARIFF_CONFIDENCE",
                "warning",
                (
                    f"Tariff confidence is {normalized_confidence!r}; "
                    "state-specific applicability should be verified."
                ),
            )

        result.metrics.update(
            {
                "status": normalized_status,
                "confidence": normalized_confidence,
            }
        )

        return result

    # ------------------------------------------------------------------
    # Duplicate parameter checks
    # ------------------------------------------------------------------

    def detect_duplicate_defaults(
        self,
        parameter_names: Sequence[str],
    ) -> ValidationResult:
        result = ValidationResult(
            name="calibration:duplicate_parameters",
            passed=True,
        )

        normalized: dict[str, list[str]] = {}

        for name in parameter_names:
            canonical = re.sub(
                r"[^a-z0-9]+",
                "_",
                name.lower().strip(),
            ).strip("_")

            normalized.setdefault(
                canonical,
                [],
            ).append(name)

        for canonical, original_names in normalized.items():
            if len(original_names) > 1:
                result.add_issue(
                    "DUPLICATE_PARAMETER_NAMES",
                    "warning",
                    (
                        f"Parameters {original_names!r} normalize to "
                        f"the same canonical name {canonical!r}. "
                        "Prefer one canonical source of truth."
                    ),
                    parameter=canonical,
                )

        result.metrics["duplicate_groups"] = sum(
            1
            for names in normalized.values()
            if len(names) > 1
        )

        return result

    # ------------------------------------------------------------------
    # Research calibration utilities
    # ------------------------------------------------------------------

    def calibrate_against_range(
        self,
        *,
        parameter: str,
        value: float,
        unit: str,
        reference_min: float,
        reference_max: float,
        reference_source_id: Optional[str] = None,
        tolerance_pct: float = 0.0,
    ) -> ValidationResult:
        """
        Check whether a calculated/default value is within a documented
        reference range.

        This function does not overwrite the value.
        """

        result = ValidationResult(
            name=f"calibration:{parameter}",
            passed=True,
        )

        current = _finite_number(
            value,
            parameter,
        )

        minimum = _finite_number(
            reference_min,
            f"{parameter}.reference_min",
        )

        maximum = _finite_number(
            reference_max,
            f"{parameter}.reference_max",
        )

        if minimum > maximum:
            result.add_issue(
                "INVALID_REFERENCE_RANGE",
                "error",
                "Reference minimum exceeds reference maximum.",
                parameter=parameter,
            )
            return result

        margin = (
            (maximum - minimum)
            * float(tolerance_pct)
            / 100.0
        )

        acceptable_min = minimum - margin
        acceptable_max = maximum + margin

        in_range = (
            acceptable_min <= current <= acceptable_max
        )

        result.metrics.update(
            {
                "value": current,
                "unit": normalize_unit(unit),
                "reference_min": minimum,
                "reference_max": maximum,
                "acceptable_min": acceptable_min,
                "acceptable_max": acceptable_max,
                "reference_source_id": reference_source_id,
                "within_reference_range": in_range,
            }
        )

        if not in_range:
            result.add_issue(
                "OUTSIDE_RESEARCH_RANGE",
                "warning",
                (
                    f"{parameter}={current} {unit} lies outside the "
                    f"documented reference range "
                    f"{minimum}–{maximum} {unit}."
                ),
                parameter=parameter,
                source_ids=(
                    (reference_source_id,)
                    if reference_source_id
                    else ()
                ),
            )

        return result

    # ------------------------------------------------------------------
    # Full assumption-set validation
    # ------------------------------------------------------------------

    def validate_assumption_set(
        self,
        assumptions: Sequence[AssumptionRecord],
    ) -> ValidationReport:
        report = ValidationReport()

        for assumption in assumptions:
            result = self.validate_assumption(
                assumption
            )
            report.absorb(result)

        conflicts = self.detect_conflicts(
            [
                ParameterCandidate(
                    parameter=item.parameter,
                    value=item.value,
                    unit=item.unit,
                    source_id=item.source_id,
                    source_type=item.source_type,
                    source_date=item.source_date,
                    status=item.status,
                    confidence=item.confidence,
                    notes=item.notes,
                )
                for item in assumptions
            ]
        )

        report.add_conflicts(conflicts)
        report.calculate_evidence_score(
            assumptions
        )

        return report

    # ------------------------------------------------------------------
    # Strict production gate
    # ------------------------------------------------------------------

    def require_production_safe(
        self,
        *,
        report: ValidationReport,
    ) -> None:
        """
        Raise an exception when the validation report is not production-safe.

        Warnings are allowed. Blocking/error conditions are not.
        """
        if report.passed:
            return

        details = "; ".join(
            report.blocking_issues
        )

        raise ValidationEngineError(
            "Validation report failed production safety gate: "
            + details
        )


# =============================================================================
# Convenience functions
# =============================================================================


_DEFAULT_ENGINE = ValidationEngine()


def convert_energy(
    value: float,
    from_unit: str,
    to_unit: str,
) -> float:
    """Convenience wrapper for UnitSystem.convert()."""
    return _DEFAULT_ENGINE.units.convert(
        value,
        from_unit,
        to_unit,
    )


def kwh_to_mj(value: float) -> float:
    return _DEFAULT_ENGINE.units.to_mj(
        value,
        "kWh",
    )


def mj_to_kwh(value: float) -> float:
    return _DEFAULT_ENGINE.units.to_kwh(
        value,
        "MJ",
    )


def mj_to_gj(value: float) -> float:
    return _DEFAULT_ENGINE.units.convert(
        value,
        "MJ",
        "GJ",
    )


def tj_to_mj(value: float) -> float:
    return _DEFAULT_ENGINE.units.convert(
        value,
        "TJ",
        "MJ",
    )


def kg_to_tonnes(value: float) -> float:
    return _DEFAULT_ENGINE.units.convert(
        value,
        "kg",
        "tonne",
    )


def kgco2e_to_tco2e(value: float) -> float:
    return _DEFAULT_ENGINE.units.convert(
        value,
        "kgCO2e",
        "tCO2e",
    )


# =============================================================================
# Self-test
# =============================================================================


def run_self_test() -> dict[str, Any]:
    """
    Lightweight deterministic self-test.

    Intended for development/CI sanity checks, not a replacement for pytest.
    """

    engine = ValidationEngine()
    checks: list[dict[str, Any]] = []

    # ---------------------------------------------------------------
    # 1. kWh -> MJ
    # ---------------------------------------------------------------
    conversion = engine.validate_energy_conversion(
        value=1.0,
        from_unit="kWh",
        to_unit="MJ",
        expected_value=3.6,
    )

    checks.append(
        conversion.to_dict()
    )

    # ---------------------------------------------------------------
    # 2. GJ -> MJ
    # ---------------------------------------------------------------
    conversion = engine.validate_energy_conversion(
        value=1.0,
        from_unit="GJ",
        to_unit="MJ",
        expected_value=1000.0,
    )

    checks.append(
        conversion.to_dict()
    )

    # ---------------------------------------------------------------
    # 3. Energy balance
    # ---------------------------------------------------------------
    balance = engine.validate_energy_balance(
        input_energy_mj=1000.0,
        useful_energy_mj=800.0,
        loss_components_mj={
            "boiler": 100.0,
            "distribution": 50.0,
            "process": 50.0,
        },
    )

    checks.append(
        balance.to_dict()
    )

    # ---------------------------------------------------------------
    # 4. Grid emissions
    # ---------------------------------------------------------------
    emissions = engine.calculate_grid_emissions(
        electricity_kwh=1000.0,
        grid_factor_kgco2e_per_kwh=0.7117,
    )

    checks.append(
        {
            "name": "grid_emissions",
            "passed": (
                math.isclose(
                    emissions["emissions_kgco2e"],
                    711.7,
                    rel_tol=1e-9,
                )
            ),
            "metrics": emissions,
        }
    )

    # ---------------------------------------------------------------
    # 5. Efficiency
    # ---------------------------------------------------------------
    efficiency = engine.validate_efficiency(
        parameter="boiler_efficiency",
        efficiency=0.80,
    )

    checks.append(
        efficiency.to_dict()
    )

    # ---------------------------------------------------------------
    # 6. Conflict detection
    # ---------------------------------------------------------------
    conflicts = engine.detect_conflicts(
        [
            ParameterCandidate(
                parameter="example_tariff",
                value=8.0,
                unit="kWh",
                source_id="SRC_A",
                confidence="medium",
            ),
            ParameterCandidate(
                parameter="example_tariff",
                value=10.0,
                unit="kWh",
                source_id="SRC_B",
                confidence="medium",
            ),
        ]
    )

    checks.append(
        {
            "name": "conflict_detection",
            "passed": len(conflicts) == 1,
            "conflicts": [
                item.to_dict()
                for item in conflicts
            ],
        }
    )

    all_passed = all(
        item.get("passed", False)
        for item in checks
    )

    return {
        "passed": all_passed,
        "checks": checks,
    }


if __name__ == "__main__":
    result = run_self_test()

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    if not result["passed"]:
        raise SystemExit(1)
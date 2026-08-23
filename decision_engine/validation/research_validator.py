
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from knowledge_runtime.errors import KnowledgeReferenceError


# ---------------------------------------------------------------------------
# Validation result models
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """
    One machine-readable validation finding.

    severity:
        ERROR   -> recommendation/data must not be treated as research-valid
        WARNING -> output may still be usable, but quality is reduced
        INFO    -> audit metadata
    """

    code: str
    message: str
    severity: str = "ERROR"
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "path": self.path,
        }


@dataclass
class FieldValidationResult:
    """
    Validation state for one recommendation parameter.
    """

    field_name: str
    valid: bool
    traceable: bool
    source_count: int = 0
    source_ids: list[str] = field(default_factory=list)
    research_quality: str = "Low"
    field_validation: str = "Invalid"
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "valid": self.valid,
            "traceable": self.traceable,
            "source_count": self.source_count,
            "source_ids": self.source_ids,
            "research_quality": self.research_quality,
            "field_validation": self.field_validation,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class EvidenceSummary:
    """
    Transparent research/evidence assessment attached to each recommendation.

    This object intentionally exposes the scoring dimensions instead of
    collapsing everything into one unexplained confidence number.
    """

    confidence_pct: float
    evidence_strength: str
    source_count: int
    research_quality: str
    field_validation: str

    missing_citations: list[str] = field(default_factory=list)
    broken_references: list[str] = field(default_factory=list)
    invalid_datasets: list[str] = field(default_factory=list)
    unsupported_recommendations: list[str] = field(default_factory=list)
    untraceable_parameters: list[str] = field(default_factory=list)

    field_results: list[FieldValidationResult] = field(default_factory=list)

    scoring_factors: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence_pct": round(self.confidence_pct, 2),
            "evidence_strength": self.evidence_strength,
            "source_count": self.source_count,
            "research_quality": self.research_quality,
            "field_validation": self.field_validation,
            "missing_citations": list(self.missing_citations),
            "broken_references": list(self.broken_references),
            "invalid_datasets": list(self.invalid_datasets),
            "unsupported_recommendations": list(
                self.unsupported_recommendations
            ),
            "untraceable_parameters": list(self.untraceable_parameters),
            "field_results": [
                result.to_dict() for result in self.field_results
            ],
            "scoring_factors": dict(self.scoring_factors),
        }


@dataclass
class ResearchValidationResult:
    """
    Complete validation report.

    valid:
        True only when there are no blocking ERROR findings.

    recommendation_supported:
        True only when the recommended scenario is sufficiently evidenced
        and traceable.

    confidence_pct:
        Transparent score derived from actual validation dimensions.
    """

    valid: bool
    recommendation_supported: bool
    confidence_pct: float

    evidence_summary: EvidenceSummary

    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "recommendation_supported": self.recommendation_supported,
            "confidence_pct": round(self.confidence_pct, 2),
            "evidence_summary": self.evidence_summary.to_dict(),
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }


# ---------------------------------------------------------------------------
# Required recommendation fields for research validation
# ---------------------------------------------------------------------------


# These are the recommendation values that must be backed by evidence or
# derived from already-evidenced upstream calculations.
#
# We deliberately do NOT require timestamps, IDs, or display-only fields.
RESEARCH_CRITICAL_FIELDS: tuple[str, ...] = (
    "recommended_scenario_id",
    "recommended_technology_sequence",
    "capex_total_inr",
    "annual_opex_inr",
    "payback_range_years",
    "co2_reduction_pct",
    "fossil_fuel_reduction_pct",
    "composite_score",
    "objective_scores",
)


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------


class ResearchValidationFramework:
    """
    Research Validation Framework for the Industrial Energy Transition
    Optimizer.

    Responsibilities
    ----------------
    1. Check that every research-sensitive parameter is traceable.
    2. Detect missing citations.
    3. Detect broken source references.
    4. Detect invalid datasets / evidence payloads.
    5. Reject unsupported recommendations.
    6. Ensure recommendation parameters are internally validated.
    7. Produce a transparent confidence/evidence summary.

    Non-responsibilities
    --------------------
    - Does not rank technologies.
    - Does not alter optimizer scores.
    - Does not invent citations.
    - Does not repair broken evidence silently.
    """

    def __init__(self, evidence_resolver: Any | None = None) -> None:
        self.evidence_resolver = evidence_resolver

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_recommendation(
        self,
        recommendation: Any,
        *,
        evidence_records: Any | None = None,
        all_scenarios: Sequence[Any] | None = None,
        dataset_records: Iterable[Any] | None = None,
    ) -> ResearchValidationResult:
        """
        Validate one complete Recommendation.

        Parameters
        ----------
        recommendation:
            Pydantic model, dataclass, or mapping.

        evidence_records:
            Resolved evidence records attached to the recommendation and/or
            upstream scenario.

        all_scenarios:
            Full candidate scenario set. This is required for proving that
            the selected scenario actually exists and was part of the ranked
            decision set.

        dataset_records:
            Optional records representing the datasets used by the
            recommendation. Invalid records are reported separately.
        """

        data = self._as_mapping(recommendation)

        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        evidence = self._normalise_evidence_records(evidence_records)

        # --------------------------------------------------------------
        # 1. Validate datasets/evidence payload
        # --------------------------------------------------------------

        invalid_dataset_items = self._validate_dataset_records(
            dataset_records
        )

        if invalid_dataset_items:
            for item in invalid_dataset_items:
                errors.append(
                    ValidationIssue(
                        code="INVALID_DATASET",
                        message=item["message"],
                        path=item.get("path"),
                    )
                )

        # --------------------------------------------------------------
        # 2. Verify recommendation scenario exists
        # --------------------------------------------------------------

        recommended_scenario_id = data.get(
            "recommended_scenario_id"
        )

        if not isinstance(recommended_scenario_id, str) or not (
            recommended_scenario_id.strip()
        ):
            errors.append(
                ValidationIssue(
                    code="MISSING_RECOMMENDED_SCENARIO",
                    message=(
                        "Recommendation does not contain a valid "
                        "recommended_scenario_id."
                    ),
                    path="recommended_scenario_id",
                )
            )

        elif all_scenarios is not None:
            scenario_ids = {
                self._scenario_id(item)
                for item in all_scenarios
                if self._scenario_id(item)
            }

            if recommended_scenario_id not in scenario_ids:
                errors.append(
                    ValidationIssue(
                        code="UNSUPPORTED_RECOMMENDATION",
                        message=(
                            f"Recommended scenario "
                            f"'{recommended_scenario_id}' does not exist "
                            "in the candidate scenario set."
                        ),
                        path="recommended_scenario_id",
                    )
                )

        # --------------------------------------------------------------
        # 3. Validate critical fields
        # --------------------------------------------------------------

        field_results: list[FieldValidationResult] = []

        for field_name in RESEARCH_CRITICAL_FIELDS:
            result = self._validate_field(
                recommendation=data,
                field_name=field_name,
                evidence_records=evidence,
            )

            field_results.append(result)

            for issue in result.issues:
                if issue.severity == "ERROR":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        # --------------------------------------------------------------
        # 4. Recommendation-level support checks
        # --------------------------------------------------------------

        unsupported = self._find_unsupported_recommendation_claims(
            data,
            evidence,
        )

        for issue in unsupported:
            if issue.severity == "ERROR":
                errors.append(issue)
            else:
                warnings.append(issue)

        # --------------------------------------------------------------
        # 5. Basic numerical sanity
        # --------------------------------------------------------------

        numerical_issues = self._validate_numerical_sanity(data)

        for issue in numerical_issues:
            if issue.severity == "ERROR":
                errors.append(issue)
            else:
                warnings.append(issue)

        # --------------------------------------------------------------
        # 6. Aggregate evidence dimensions
        # --------------------------------------------------------------

        missing_citations = sorted(
            {
                issue.path or ""
                for issue in errors
                if issue.code == "MISSING_CITATION"
            }
            - {""}
        )

        broken_references = sorted(
            {
                issue.message
                for issue in errors
                if issue.code == "BROKEN_REFERENCE"
            }
        )

        invalid_datasets = sorted(
            {
                issue.message
                for issue in errors
                if issue.code == "INVALID_DATASET"
            }
        )

        unsupported_recommendations = sorted(
            {
                issue.message
                for issue in errors
                if issue.code == "UNSUPPORTED_RECOMMENDATION"
            }
        )

        untraceable_parameters = sorted(
            {
                issue.path or ""
                for issue in errors
                if issue.code == "UNTRACEABLE_PARAMETER"
            }
            - {""}
        )

        total_source_ids = sorted(
            {
                source_id
                for record in evidence
                for source_id in self._source_ids_from_record(record)
            }
        )

        # --------------------------------------------------------------
        # 7. Score confidence transparently
        # --------------------------------------------------------------

        scoring = self._calculate_confidence(
            field_results=field_results,
            source_count=len(total_source_ids),
            missing_citations=missing_citations,
            broken_references=broken_references,
            invalid_datasets=invalid_datasets,
            unsupported_recommendations=unsupported_recommendations,
            untraceable_parameters=untraceable_parameters,
        )

        evidence_strength = self._evidence_strength(
            confidence_pct=scoring["confidence_pct"],
            source_count=len(total_source_ids),
            blocking_errors=len(errors),
        )

        research_quality = self._research_quality(
            confidence_pct=scoring["confidence_pct"],
            field_results=field_results,
            blocking_errors=len(errors),
        )

        field_validation = self._field_validation(
            field_results=field_results,
            blocking_errors=len(errors),
        )

        recommendation_supported = (
            len(
                [
                    issue
                    for issue in errors
                    if issue.code in {
                        "UNSUPPORTED_RECOMMENDATION",
                        "MISSING_CITATION",
                        "BROKEN_REFERENCE",
                        "UNTRACEABLE_PARAMETER",
                    }
                ]
            )
            == 0
        )

        summary = EvidenceSummary(
            confidence_pct=scoring["confidence_pct"],
            evidence_strength=evidence_strength,
            source_count=len(total_source_ids),
            research_quality=research_quality,
            field_validation=field_validation,
            missing_citations=missing_citations,
            broken_references=broken_references,
            invalid_datasets=invalid_datasets,
            unsupported_recommendations=unsupported_recommendations,
            untraceable_parameters=untraceable_parameters,
            field_results=field_results,
            scoring_factors=scoring["factors"],
        )

        return ResearchValidationResult(
            valid=not errors,
            recommendation_supported=recommendation_supported,
            confidence_pct=scoring["confidence_pct"],
            evidence_summary=summary,
            errors=errors,
            warnings=warnings,
        )

    def validate_evidence_chain(
        self,
        record: Any,
    ) -> list[ValidationIssue]:
        """
        Validate an evidence chain without validating a full recommendation.

        The expected architecture is:

            knowledge record
                -> source_id
                -> citations.json
                -> sources.json

        When an EvidenceResolver is provided, the source ID is actively
        resolved. Without one, structural validation still runs.
        """

        issues: list[ValidationIssue] = []

        mapping = self._as_mapping(record)

        source_ids = self._find_source_ids(mapping)

        if not source_ids:
            issues.append(
                ValidationIssue(
                    code="MISSING_CITATION",
                    message="Record has no source_id evidence reference.",
                    path="source_id",
                )
            )
            return issues

        for source_id, path in source_ids:
            if not source_id.strip():
                issues.append(
                    ValidationIssue(
                        code="MISSING_CITATION",
                        message="source_id is empty.",
                        path=path,
                    )
                )
                continue

            if self.evidence_resolver is None:
                continue

            try:
                source = self.evidence_resolver.get_source(source_id)
            except (
                KnowledgeReferenceError,
                KeyError,
                ValueError,
                TypeError,
            ) as exc:
                issues.append(
                    ValidationIssue(
                        code="BROKEN_REFERENCE",
                        message=(
                            f"Unable to resolve source_id '{source_id}': "
                            f"{exc}"
                        ),
                        path=path,
                    )
                )
                continue

            if not isinstance(source, Mapping):
                issues.append(
                    ValidationIssue(
                        code="BROKEN_REFERENCE",
                        message=(
                            f"Resolved source '{source_id}' is not a "
                            "mapping/object."
                        ),
                        path=path,
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Field validation
    # ------------------------------------------------------------------

    def _validate_field(
        self,
        recommendation: Mapping[str, Any],
        field_name: str,
        evidence_records: list[Mapping[str, Any]],
    ) -> FieldValidationResult:
        issues: list[ValidationIssue] = []

        value = recommendation.get(field_name)

        # --------------------------------------------------------------
        # Presence / structural validity
        # --------------------------------------------------------------

        if value is None:
            issues.append(
                ValidationIssue(
                    code="UNTRACEABLE_PARAMETER",
                    message=(
                        f"Required recommendation parameter '{field_name}' "
                        "is missing."
                    ),
                    path=field_name,
                )
            )

            return FieldValidationResult(
                field_name=field_name,
                valid=False,
                traceable=False,
                research_quality="Low",
                field_validation="Invalid",
                issues=issues,
            )

        structural_issue = self._structural_field_issue(
            field_name,
            value,
        )

        if structural_issue is not None:
            issues.append(structural_issue)

        # --------------------------------------------------------------
        # Evidence ownership
        # --------------------------------------------------------------

        related_source_ids = self._find_related_source_ids(
            field_name,
            value,
            evidence_records,
        )

        if field_name not in {
            "recommended_scenario_id",
            "recommended_technology_sequence",
            "composite_score",
        } and not related_source_ids:
            issues.append(
                ValidationIssue(
                    code="MISSING_CITATION",
                    message=(
                        f"Parameter '{field_name}' has no evidence "
                        "source attached to the research chain."
                    ),
                    path=field_name,
                )
            )

        # --------------------------------------------------------------
        # Active source resolution
        # --------------------------------------------------------------

        for source_id in related_source_ids:
            if self.evidence_resolver is None:
                continue

            try:
                resolved = self.evidence_resolver.get_source(
                    source_id
                )
            except (
                KnowledgeReferenceError,
                KeyError,
                ValueError,
                TypeError,
            ) as exc:
                issues.append(
                    ValidationIssue(
                        code="BROKEN_REFERENCE",
                        message=(
                            f"Parameter '{field_name}' references "
                            f"unresolvable source '{source_id}': {exc}"
                        ),
                        path=field_name,
                    )
                )
                continue

            if not isinstance(resolved, Mapping):
                issues.append(
                    ValidationIssue(
                        code="BROKEN_REFERENCE",
                        message=(
                            f"Source '{source_id}' resolved to an invalid "
                            "evidence object."
                        ),
                        path=field_name,
                    )
                )

        valid = not any(
            issue.severity == "ERROR"
            for issue in issues
        )

        traceable = not any(
            issue.code in {
                "MISSING_CITATION",
                "BROKEN_REFERENCE",
                "UNTRACEABLE_PARAMETER",
            }
            for issue in issues
        )

        research_quality = self._field_quality(
            source_count=len(related_source_ids),
            issues=issues,
        )

        field_validation = (
            "Valid"
            if valid
            else "Invalid"
        )

        return FieldValidationResult(
            field_name=field_name,
            valid=valid,
            traceable=traceable,
            source_count=len(related_source_ids),
            source_ids=sorted(related_source_ids),
            research_quality=research_quality,
            field_validation=field_validation,
            issues=issues,
        )

    # ------------------------------------------------------------------
    # Dataset validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_dataset_records(
        dataset_records: Iterable[Any] | None,
    ) -> list[dict[str, str]]:
        if dataset_records is None:
            return []

        invalid: list[dict[str, str]] = []

        for index, record in enumerate(dataset_records):
            path = f"dataset_records[{index}]"

            if record is None:
                invalid.append(
                    {
                        "message": "Dataset record is null.",
                        "path": path,
                    }
                )
                continue

            if isinstance(record, Mapping):
                if not record:
                    invalid.append(
                        {
                            "message": "Dataset record is empty.",
                            "path": path,
                        }
                    )

                if (
                    "source_id" in record
                    and not isinstance(record["source_id"], str)
                ):
                    invalid.append(
                        {
                            "message": (
                                "Dataset record source_id must be a string."
                            ),
                            "path": path,
                        }
                    )

                continue

            if not isinstance(record, (str, int, float, bool)):
                invalid.append(
                    {
                        "message": (
                            "Dataset record must be a mapping or scalar "
                            "primitive."
                        ),
                        "path": path,
                    }
                )

        return invalid

    # ------------------------------------------------------------------
    # Numerical sanity
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_numerical_sanity(
        recommendation: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        percentage_fields = (
            "co2_reduction_pct",
            "fossil_fuel_reduction_pct",
        )

        for field_name in percentage_fields:
            value = recommendation.get(field_name)

            if value is None:
                continue

            if not isinstance(value, (int, float)):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message=(
                            f"'{field_name}' must be numeric."
                        ),
                        path=field_name,
                    )
                )
                continue

            if not 0.0 <= float(value) <= 100.0:
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message=(
                            f"'{field_name}' must be between 0 and 100."
                        ),
                        path=field_name,
                    )
                )

        payback = recommendation.get("payback_range_years")

        if payback is not None:
            if (
                not isinstance(payback, (list, tuple))
                or len(payback) != 2
            ):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message=(
                            "payback_range_years must contain exactly "
                            "two numeric values."
                        ),
                        path="payback_range_years",
                    )
                )
            elif (
                not all(
                    isinstance(value, (int, float))
                    for value in payback
                )
            ):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message=(
                            "payback_range_years values must be numeric."
                        ),
                        path="payback_range_years",
                    )
                )
            elif float(payback[0]) > float(payback[1]):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message=(
                            "payback_range_years lower bound cannot "
                            "exceed the upper bound."
                        ),
                        path="payback_range_years",
                    )
                )

        composite = recommendation.get("composite_score")

        if composite is not None:
            if not isinstance(composite, (int, float)):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message="composite_score must be numeric.",
                        path="composite_score",
                    )
                )
            elif not 0.0 <= float(composite) <= 1.0:
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARAMETER_VALUE",
                        message=(
                            "composite_score must be between 0 and 1."
                        ),
                        path="composite_score",
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Recommendation support
    # ------------------------------------------------------------------

    @staticmethod
    def _find_unsupported_recommendation_claims(
        recommendation: Mapping[str, Any],
        evidence_records: list[Mapping[str, Any]],
    ) -> list[ValidationIssue]:
        """
        Prevent a recommendation from being marked supported merely because
        it has a few citations.

        A recommendation needs:
          - a scenario ID
          - a technology sequence
          - MCDA result
          - evidence records
        """

        issues: list[ValidationIssue] = []

        if not recommendation.get("recommended_technology_sequence"):
            issues.append(
                ValidationIssue(
                    code="UNSUPPORTED_RECOMMENDATION",
                    message=(
                        "Recommendation has no technology sequence, so the "
                        "selected pathway cannot be independently audited."
                    ),
                    path="recommended_technology_sequence",
                )
            )

        objective_scores = recommendation.get("objective_scores")

        if not isinstance(objective_scores, Mapping) or not objective_scores:
            issues.append(
                ValidationIssue(
                    code="UNSUPPORTED_RECOMMENDATION",
                    message=(
                        "Recommendation has no objective_scores payload; "
                        "MCDA selection cannot be audited."
                    ),
                    path="objective_scores",
                )
            )

        if not evidence_records:
            issues.append(
                ValidationIssue(
                    code="UNSUPPORTED_RECOMMENDATION",
                    message=(
                        "Recommendation has no resolved evidence records. "
                        "It cannot be considered research-supported."
                    ),
                    path="explanation",
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Transparent confidence scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_confidence(
        *,
        field_results: Sequence[FieldValidationResult],
        source_count: int,
        missing_citations: Sequence[str],
        broken_references: Sequence[str],
        invalid_datasets: Sequence[str],
        unsupported_recommendations: Sequence[str],
        untraceable_parameters: Sequence[str],
    ) -> dict[str, Any]:
        """
        Transparent confidence scoring.

        Components:
          field coverage        = 35%
          traceability          = 25%
          source breadth        = 10%
          no broken references  = 10%
          dataset validity      = 10%
          recommendation support=10%

        This is intentionally a deterministic evidence score, not ML.
        """

        if field_results:
            valid_fields = sum(
                1 for result in field_results
                if result.valid
            )

            traceable_fields = sum(
                1 for result in field_results
                if result.traceable
            )

            field_coverage = valid_fields / len(field_results)
            traceability = traceable_fields / len(field_results)
        else:
            field_coverage = 0.0
            traceability = 0.0

        source_breadth = min(
            1.0,
            source_count / 5.0,
        )

        reference_health = (
            1.0
            if not broken_references
            else 0.0
        )

        dataset_health = (
            1.0
            if not invalid_datasets
            else 0.0
        )

        recommendation_health = (
            1.0
            if not unsupported_recommendations
            else 0.0
        )

        citation_health = (
            1.0
            if not missing_citations
            else max(
                0.0,
                1.0 - len(missing_citations) / max(
                    len(field_results),
                    1,
                ),
            )
        )

        # Citation health slightly strengthens traceability but does not
        # replace it.
        traceability = (
            traceability * 0.75
            + citation_health * 0.25
        )

        raw_score = (
            field_coverage * 0.35
            + traceability * 0.25
            + source_breadth * 0.10
            + reference_health * 0.10
            + dataset_health * 0.10
            + recommendation_health * 0.10
        )

        # Hard caps prevent an output from appearing "High confidence" when
        # fundamental evidence failures exist.
        if broken_references:
            raw_score = min(raw_score, 0.55)

        if unsupported_recommendations:
            raw_score = min(raw_score, 0.50)

        if untraceable_parameters:
            raw_score = min(raw_score, 0.60)

        if missing_citations:
            raw_score = min(raw_score, 0.70)

        confidence_pct = round(
            max(
                0.0,
                min(
                    100.0,
                    raw_score * 100.0,
                ),
            ),
            2,
        )

        return {
            "confidence_pct": confidence_pct,
            "factors": {
                "field_coverage": round(
                    field_coverage * 100.0,
                    2,
                ),
                "traceability": round(
                    traceability * 100.0,
                    2,
                ),
                "source_breadth": round(
                    source_breadth * 100.0,
                    2,
                ),
                "reference_health": round(
                    reference_health * 100.0,
                    2,
                ),
                "dataset_health": round(
                    dataset_health * 100.0,
                    2,
                ),
                "recommendation_health": round(
                    recommendation_health * 100.0,
                    2,
                ),
            },
        }

    # ------------------------------------------------------------------
    # Quality labels
    # ------------------------------------------------------------------

    @staticmethod
    def _evidence_strength(
        *,
        confidence_pct: float,
        source_count: int,
        blocking_errors: int,
    ) -> str:
        if blocking_errors > 0:
            return "Weak"

        if confidence_pct >= 85.0 and source_count >= 4:
            return "Strong"

        if confidence_pct >= 70.0 and source_count >= 2:
            return "Moderate"

        return "Weak"

    @staticmethod
    def _research_quality(
        *,
        confidence_pct: float,
        field_results: Sequence[FieldValidationResult],
        blocking_errors: int,
    ) -> str:
        if blocking_errors == 0 and confidence_pct >= 85.0:
            return "High"

        if confidence_pct >= 65.0:
            return "Medium"

        return "Low"

    @staticmethod
    def _field_validation(
        *,
        field_results: Sequence[FieldValidationResult],
        blocking_errors: int,
    ) -> str:
        if not field_results:
            return "Low"

        valid_count = sum(
            1 for result in field_results
            if result.valid
        )

        ratio = valid_count / len(field_results)

        if ratio >= 0.90 and blocking_errors == 0:
            return "High"

        if ratio >= 0.65:
            return "Medium"

        return "Low"

    @staticmethod
    def _field_quality(
        *,
        source_count: int,
        issues: Sequence[ValidationIssue],
    ) -> str:
        blocking = [
            issue
            for issue in issues
            if issue.severity == "ERROR"
        ]

        if blocking:
            return "Low"

        if source_count >= 2:
            return "High"

        if source_count == 1:
            return "Medium"

        return "Low"

    # ------------------------------------------------------------------
    # Evidence extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_evidence_records(
        evidence_records: Any,
    ) -> list[Mapping[str, Any]]:
        if evidence_records is None:
            return []

        if isinstance(evidence_records, Mapping):
            return [evidence_records]

        if isinstance(evidence_records, Sequence) and not isinstance(
            evidence_records,
            (str, bytes),
        ):
            return [
                item
                for item in evidence_records
                if isinstance(item, Mapping)
            ]

        return []

    @staticmethod
    def _source_ids_from_record(
        record: Mapping[str, Any],
    ) -> set[str]:
        result: set[str] = set()

        def walk(value: Any) -> None:
            if isinstance(value, Mapping):
                for key, child in value.items():
                    if key == "source_id" and isinstance(child, str):
                        result.add(child)
                    walk(child)

            elif isinstance(value, Sequence) and not isinstance(
                value,
                (str, bytes),
            ):
                for child in value:
                    walk(child)

        walk(record)

        return result

    @staticmethod
    def _find_source_ids(
        record: Mapping[str, Any],
    ) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []

        def walk(value: Any, path: str) -> None:
            if isinstance(value, Mapping):
                for key, child in value.items():
                    child_path = f"{path}.{key}"

                    if key == "source_id":
                        if isinstance(child, str):
                            found.append(
                                (
                                    child,
                                    child_path,
                                )
                            )

                    walk(child, child_path)

            elif isinstance(value, Sequence) and not isinstance(
                value,
                (str, bytes),
            ):
                for index, child in enumerate(value):
                    walk(
                        child,
                        f"{path}[{index}]",
                    )

        walk(record, "$")

        return found

    @staticmethod
    def _find_related_source_ids(
        field_name: str,
        value: Any,
        evidence_records: Sequence[Mapping[str, Any]],
    ) -> set[str]:
        source_ids: set[str] = set()

        # Direct field payload may itself carry source_id.
        if isinstance(value, Mapping):
            source_ids.update(
                ResearchValidationFramework._source_ids_from_record(
                    value
                )
            )

        # Generic evidence records are expected to include parameter_name,
        # field, applies_to, or target_field when the source is specific.
        for record in evidence_records:
            field_candidates = {
                record.get("parameter_name"),
                record.get("field"),
                record.get("target_field"),
                record.get("used_for"),
                record.get("parameter"),
            }

            if field_name in {
                str(candidate)
                for candidate in field_candidates
                if candidate is not None
            }:
                source_ids.update(
                    ResearchValidationFramework._source_ids_from_record(
                        record
                    )
                )

        # If there is no parameter-level mapping, generic recommendation
        # evidence can still support derived values.
        if not source_ids:
            for record in evidence_records:
                source_ids.update(
                    ResearchValidationFramework._source_ids_from_record(
                        record
                    )
                )

        return source_ids

    # ------------------------------------------------------------------
    # Structural helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _structural_field_issue(
        field_name: str,
        value: Any,
    ) -> ValidationIssue | None:
        if field_name == "recommended_technology_sequence":
            if (
                not isinstance(value, Sequence)
                or isinstance(value, (str, bytes))
                or len(value) == 0
            ):
                return ValidationIssue(
                    code="INVALID_PARAMETER_VALUE",
                    message=(
                        "recommended_technology_sequence must be "
                        "a non-empty sequence."
                    ),
                    path=field_name,
                )

        elif field_name in {
            "capex_total_inr",
            "annual_opex_inr",
            "co2_reduction_pct",
            "fossil_fuel_reduction_pct",
            "composite_score",
        }:
            if not isinstance(value, (int, float)):
                return ValidationIssue(
                    code="INVALID_PARAMETER_VALUE",
                    message=(
                        f"'{field_name}' must be numeric."
                    ),
                    path=field_name,
                )

        elif field_name == "payback_range_years":
            if (
                not isinstance(value, (list, tuple))
                or len(value) != 2
            ):
                return ValidationIssue(
                    code="INVALID_PARAMETER_VALUE",
                    message=(
                        "payback_range_years must contain "
                        "exactly two values."
                    ),
                    path=field_name,
                )

        elif field_name == "objective_scores":
            if not isinstance(value, Mapping):
                return ValidationIssue(
                    code="INVALID_PARAMETER_VALUE",
                    message=(
                        "objective_scores must be a mapping."
                    ),
                    path=field_name,
                )

        return None

    @staticmethod
    def _scenario_id(
        scenario: Any,
    ) -> str | None:
        if isinstance(scenario, Mapping):
            value = scenario.get("scenario_id")
        else:
            value = getattr(
                scenario,
                "scenario_id",
                None,
            )

        return value if isinstance(value, str) else None

    @staticmethod
    def _as_mapping(
        value: Any,
    ) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)

        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, Mapping):
                return dict(dumped)

        if hasattr(value, "dict"):
            dumped = value.dict()
            if isinstance(dumped, Mapping):
                return dict(dumped)

        if hasattr(value, "__dict__"):
            return dict(value.__dict__)

        raise TypeError(
            "ResearchValidationFramework expects a mapping, "
            "Pydantic model, dataclass, or object with __dict__."
        )


__all__ = [
    "EvidenceSummary",
    "FieldValidationResult",
    "ResearchValidationFramework",
    "ResearchValidationResult",
    "ValidationIssue",
]

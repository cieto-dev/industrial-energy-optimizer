"""
Explainable Industry Constraint Engine — Unit 2.4.5
====================================================

Purpose
-------
Adds an explainability/evidence layer on top of the existing technical
technology screening engine.

The engine answers:

    "Given the factory's industry and the technology that survived
     technical screening, how should that technology be explained
     for this industry?"

It does NOT replace:
    - technology_rules.json
    - hard technical feasibility checks
    - scenario generation
    - optimization
    - financial ranking

Responsibilities
----------------
1. Load industry-specific explainability rules.
2. Normalize industry and technology identifiers.
3. Evaluate industry eligibility.
4. Return classification, reason and source.
5. Return operational constraints.
6. Return cluster recommendations.
7. Preserve compatibility with the existing screening pipeline.
8. Produce explicit explanations for both allowed and rejected options.

Design principle
----------------
Technical feasibility belongs to the existing technology constraint layer.
Industry explainability belongs here.

This separation keeps the G1 decision boundary clean and auditable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

_INDUSTRY_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "industries"
    / "industry_constraints.json"
)
_CONSTRAINTS_FILE = (
    BASE_DIR
    / "knowledge-base"
    / "constraints"
    / "industry_constraints.json"
)
INDUSTRY_CONSTRAINTS_FILE = (
    _INDUSTRY_FILE if _INDUSTRY_FILE.exists() else _CONSTRAINTS_FILE
)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file and validate that its root is an object.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Industry constraint knowledge base not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in industry constraint file: {file_path}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object in {file_path}"
        )

    return data


def normalize(value: Optional[Any]) -> str:
    """
    Normalize identifiers to the project's canonical style.
    """
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def normalize_list(values: Optional[Iterable[Any]]) -> List[str]:
    """
    Normalize a list while preserving order.
    """
    if values is None:
        return []

    result: List[str] = []

    for value in values:
        normalized = normalize(value)

        if normalized and normalized not in result:
            result.append(normalized)

    return result


def deep_copy_dict(value: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Return a JSON-safe detached dictionary.
    """
    return json.loads(json.dumps(dict(value)))


# ---------------------------------------------------------------------------
# Industry aliases
# ---------------------------------------------------------------------------

INDUSTRY_ALIASES: Dict[str, str] = {
    "textile_dyeing": "textile",
    "textile_processing": "textile",
    "textile_manufacturing": "textile",
    "food": "food_processing",
    "food_and_beverage": "food_processing",
    "food_manufacturing": "food_processing",
    "pharma": "pharmaceutical",
    "pharmaceuticals": "pharmaceutical",
    "chemical_processing": "chemical",
    "chemicals": "chemical",
    "pulp_paper": "paper",
    "pulp_and_paper": "paper",
    "iron_steel": "steel",
    "metallurgy": "steel",
    "foundry": "steel",
    "foundries": "steel",
}


# ---------------------------------------------------------------------------
# Technology aliases
# ---------------------------------------------------------------------------

TECHNOLOGY_ALIASES: Dict[str, str] = {
    "heatpump": "heat_pump",
    "heat-pump": "heat_pump",
    "electricboiler": "electric_boiler",
    "electric-boiler": "electric_boiler",
    "biomass": "biomass_boiler",
    "biomass_boiler": "biomass_boiler",
    "solarthermal": "solar_thermal",
    "solarpv": "solar_pv",
    "thermalstorage": "thermal_storage",
    "whr": "waste_heat_recovery",
    "waste_heat": "waste_heat_recovery",
    "induction": "induction_furnace",
    "induction_furnace": "induction_furnace",
    "resistance": "resistance_furnace",
    "resistance_furnace": "resistance_furnace",
    "eaf": "electric_arc_furnace",
    "electric_arc": "electric_arc_furnace",
    "plasma": "plasma_technology",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class IndustryConstraintEngine:
    """
    Evidence-backed industry-to-technology explainability engine.

    Example
    -------
    >>> engine = IndustryConstraintEngine()
    >>> result = engine.evaluate("textile", "heat_pump")
    >>> result["classification"]
    'preferred'
    """

    def __init__(
        self,
        constraints_file: Path = INDUSTRY_CONSTRAINTS_FILE,
    ) -> None:
        self.constraints_file = constraints_file
        self.data = load_json(constraints_file)

        industries = self.data.get("industries")

        if not isinstance(industries, Mapping):
            raise ValueError(
                "industry_constraints.json must contain an 'industries' object."
            )

        self.industries: Dict[str, Dict[str, Any]] = {
            normalize(industry_id): deep_copy_dict(industry_data)
            for industry_id, industry_data in industries.items()
            if isinstance(industry_data, Mapping)
        }

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_industry(industry: Optional[str]) -> str:
        """
        Resolve an industry name to the canonical project identifier.
        """
        normalized = normalize(industry)

        if not normalized:
            return ""

        return INDUSTRY_ALIASES.get(
            normalized,
            normalized,
        )

    @staticmethod
    def normalize_technology(technology: Optional[str]) -> str:
        """
        Resolve a technology name to the canonical project identifier.
        """
        normalized = normalize(technology)

        if not normalized:
            return ""

        return TECHNOLOGY_ALIASES.get(
            normalized,
            normalized,
        )

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def industry_exists(self, industry: Optional[str]) -> bool:
        """
        Return True if the industry exists in the explainability KB.
        """
        canonical = self.normalize_industry(industry)
        return canonical in self.industries

    def get_industry(self, industry: str) -> Dict[str, Any]:
        """
        Return the complete industry definition.
        """
        canonical = self.normalize_industry(industry)

        if not canonical:
            raise ValueError("Industry is required.")

        if canonical not in self.industries:
            raise KeyError(
                f"Industry '{industry}' is not present in "
                "industry_constraints.json."
            )

        return deep_copy_dict(self.industries[canonical])

    def get_technology_rule(
        self,
        industry: str,
        technology: str,
    ) -> Dict[str, Any]:
        """
        Return the industry-specific technology rule.
        """
        industry_data = self.get_industry(industry)

        technology_rules = industry_data.get("technologies", {})

        if not isinstance(technology_rules, Mapping):
            raise ValueError(
                f"Industry '{industry}' has no valid technologies object."
            )

        canonical_technology = self.normalize_technology(technology)

        rule = technology_rules.get(canonical_technology)

        if not isinstance(rule, Mapping):
            raise KeyError(
                f"Technology '{technology}' has no industry-specific "
                f"rule for industry '{industry}'."
            )

        return deep_copy_dict(rule)

    # ------------------------------------------------------------------
    # Industry evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        industry: str,
        technology: str,
        technical_feasible: Optional[bool] = None,
        technical_reasons: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an industry/technology pair.

        Parameters
        ----------
        industry:
            Factory industry identifier.

        technology:
            Technology identifier.

        technical_feasible:
            Optional result from the existing technical constraint engine.
            This is deliberately separate from industry applicability.

        technical_reasons:
            Optional technical rejection reasons.

        Returns
        -------
        dict
            Explainable recommendation object.
        """

        canonical_industry = self.normalize_industry(industry)
        canonical_technology = self.normalize_technology(technology)

        if not canonical_industry:
            raise ValueError("Industry is required.")

        if not canonical_technology:
            raise ValueError("Technology is required.")

        if canonical_industry not in self.industries:
            return {
                "industry": canonical_industry,
                "technology": canonical_technology,
                "classification": "unknown_industry",
                "allowed": False,
                "reason": (
                    f"Industry '{industry}' is not present in the "
                    "industry knowledge base."
                ),
                "source": None,
                "operational_constraints": [],
                "cluster_recommendations": [],
                "technical_feasible": technical_feasible,
                "technical_reasons": list(
                    technical_reasons or []
                ),
                "feasible": False,
            }

        industry_data = self.industries[canonical_industry]

        technology_rules = industry_data.get("technologies", {})

        if not isinstance(technology_rules, Mapping):
            return {
                "industry": canonical_industry,
                "technology": canonical_technology,
                "classification": "configuration_error",
                "allowed": False,
                "reason": (
                    "Industry knowledge base has an invalid technologies "
                    "definition."
                ),
                "source": None,
                "operational_constraints": [],
                "cluster_recommendations": [],
                "technical_feasible": technical_feasible,
                "technical_reasons": list(
                    technical_reasons or []
                ),
                "feasible": False,
            }

        rule = technology_rules.get(canonical_technology)

        if not isinstance(rule, Mapping):
            return {
                "industry": canonical_industry,
                "technology": canonical_technology,
                "classification": "not_defined",
                "allowed": False,
                "reason": (
                    f"No industry-specific applicability rule exists for "
                    f"'{canonical_technology}' in '{canonical_industry}'."
                ),
                "source": None,
                "operational_constraints": [],
                "cluster_recommendations": [],
                "technical_feasible": technical_feasible,
                "technical_reasons": list(
                    technical_reasons or []
                ),
                "feasible": False,
            }

        classification = str(
            rule.get("classification", "conditional")
        ).strip().lower()

        allowed = bool(
            rule.get(
                "allowed",
                classification not in {
                    "not_preferred_for_primary_high_temperature_heat",
                    "not_recommended",
                    "excluded",
                },
            )
        )

        reason = str(
            rule.get(
                "reason",
                "No explanation was supplied for this recommendation.",
            )
        ).strip()

        source = rule.get("source")

        operational_constraints = [
            str(item)
            for item in rule.get("operational_constraints", [])
            if str(item).strip()
        ]

        cluster_recommendations = [
            str(item)
            for item in rule.get("cluster_recommendations", [])
            if str(item).strip()
        ]

        technical_reason_list = [
            str(item)
            for item in (technical_reasons or [])
            if str(item).strip()
        ]

        # Industry and technical feasibility are separate gates.
        final_feasible = allowed

        if technical_feasible is False:
            final_feasible = False

        return {
            "industry": canonical_industry,
            "technology": canonical_technology,
            "classification": classification,
            "allowed": allowed,
            "reason": reason,
            "source": source,
            "operational_constraints": operational_constraints,
            "cluster_recommendations": cluster_recommendations,
            "technical_feasible": technical_feasible,
            "technical_reasons": technical_reason_list,
            "reasons": [reason] if reason else [],
            "feasible": final_feasible,
        }

    # ------------------------------------------------------------------
    # Batch evaluation
    # ------------------------------------------------------------------

    def evaluate_technologies(
        self,
        industry: str,
        technologies: Iterable[str],
        technical_results: Optional[
            Mapping[str, Mapping[str, Any]]
        ] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple technologies for one industry.

        technical_results may look like:

        {
            "heat_pump": {
                "feasible": True,
                "reasons": []
            },
            "electric_boiler": {
                "feasible": False,
                "reasons": ["Grid capacity exceeded."]
            }
        }
        """

        results: List[Dict[str, Any]] = []

        for technology in technologies:
            canonical_technology = self.normalize_technology(
                technology
            )

            technical_data = (
                technical_results.get(canonical_technology, {})
                if technical_results
                else {}
            )

            technical_feasible = technical_data.get(
                "feasible"
            )

            technical_reasons = technical_data.get(
                "reasons",
                technical_data.get(
                    "technical_reasons",
                    [],
                ),
            )

            results.append(
                self.evaluate(
                    industry=industry,
                    technology=canonical_technology,
                    technical_feasible=technical_feasible,
                    technical_reasons=technical_reasons,
                )
            )

        return results

    evaluate_many = evaluate_technologies

    # ------------------------------------------------------------------
    # Preferred / allowed technologies
    # ------------------------------------------------------------------

    def get_recommended_technologies(
        self,
        industry: str,
        classifications: Optional[Iterable[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return industry technologies filtered by classification.

        Default order is preserved from the JSON knowledge base.
        """
        industry_data = self.get_industry(industry)

        technology_rules = industry_data.get(
            "technologies",
            {},
        )

        if not isinstance(technology_rules, Mapping):
            return []

        allowed_classifications = (
            {
                normalize(item)
                for item in classifications
            }
            if classifications
            else {
                "preferred",
                "preferred_for_steelmaking",
                "preferred_for_low_temperature",
                "preferred_for_steam",
                "preferred_efficiency_measure",
                "preferred_as_enabler",
            }
        )

        results: List[Dict[str, Any]] = []

        for technology, rule in technology_rules.items():
            if not isinstance(rule, Mapping):
                continue

            classification = normalize(
                rule.get(
                    "classification",
                    "",
                )
            )

            if classification not in allowed_classifications:
                continue

            result = self.evaluate(
                industry=industry,
                technology=technology,
            )

            results.append(result)

        return results

    def get_all_technologies(
        self,
        industry: str,
    ) -> List[Dict[str, Any]]:
        """
        Return every explainability rule for an industry.
        """
        industry_data = self.get_industry(industry)

        technology_rules = industry_data.get(
            "technologies",
            {},
        )

        if not isinstance(technology_rules, Mapping):
            return []

        results: List[Dict[str, Any]] = []

        for technology in technology_rules.keys():
            results.append(
                self.evaluate(
                    industry=industry,
                    technology=technology,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Explanation helpers
    # ------------------------------------------------------------------

    def explain(
        self,
        industry: str,
        technology: str,
        technical_feasible: Optional[bool] = None,
        technical_reasons: Optional[Iterable[str]] = None,
    ) -> str:
        """
        Produce a compact human-readable explanation.
        """
        result = self.evaluate(
            industry=industry,
            technology=technology,
            technical_feasible=technical_feasible,
            technical_reasons=technical_reasons,
        )

        status = (
            "feasible"
            if result["feasible"]
            else "not feasible"
        )

        source = result.get("source") or "industry knowledge base"

        message = (
            f"{result['technology']} is classified as "
            f"{result['classification']} for "
            f"{result['industry']}. "
            f"Recommendation is {status}. "
            f"Reason: {result['reason']} "
            f"Source: {source}."
        )

        if result["technical_reasons"]:
            message += (
                " Technical screening notes: "
                + "; ".join(result["technical_reasons"])
                + "."
            )

        return message

    # ------------------------------------------------------------------
    # Pipeline integration
    # ------------------------------------------------------------------

    def enrich_screening_result(
        self,
        industry: str,
        screening_result: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Add industry explanation fields to an existing technical
        screening result without changing its original fields.

        Expected screening_result shape is flexible. Common examples:

        {
            "technology": "heat_pump",
            "feasible": true,
            "reasons": []
        }

        or:

        {
            "technology": "heat_pump",
            "allowed": true,
            "rejection_reasons": []
        }
        """

        technology = (
            screening_result.get("technology")
            or screening_result.get("technology_id")
        )

        if not technology:
            raise ValueError(
                "Screening result must contain 'technology' "
                "or 'technology_id'."
            )

        technical_feasible = screening_result.get(
            "feasible"
        )

        if technical_feasible is None:
            technical_feasible = screening_result.get(
                "technical_feasible"
            )

        technical_reasons = (
            screening_result.get("reasons")
            or screening_result.get("technical_reasons")
            or screening_result.get("rejection_reasons")
            or []
        )

        explanation = self.evaluate(
            industry=industry,
            technology=str(technology),
            technical_feasible=technical_feasible,
            technical_reasons=technical_reasons,
        )

        enriched = dict(screening_result)

        enriched.update(
            {
                "classification": explanation["classification"],
                "allowed": explanation["allowed"],
                "reason": explanation["reason"],
                "source": explanation["source"],
                "operational_constraints": explanation[
                    "operational_constraints"
                ],
                "cluster_recommendations": explanation[
                    "cluster_recommendations"
                ],
                "industry_feasible": explanation["allowed"],
                "explainable_feasible": explanation["feasible"],
            }
        )

        return enriched


# ---------------------------------------------------------------------------
# Functional API
# ---------------------------------------------------------------------------

_default_engine: Optional[IndustryConstraintEngine] = None


def get_engine() -> IndustryConstraintEngine:
    """
    Return a cached engine instance.
    """
    global _default_engine

    if _default_engine is None:
        _default_engine = IndustryConstraintEngine()

    return _default_engine


def evaluate_industry_technology(
    industry: str,
    technology: str,
    technical_feasible: Optional[bool] = None,
    technical_reasons: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """
    Functional wrapper for callers that do not need to instantiate
    IndustryConstraintEngine manually.
    """
    return get_engine().evaluate(
        industry=industry,
        technology=technology,
        technical_feasible=technical_feasible,
        technical_reasons=technical_reasons,
    )


def explain_industry_technology(
    industry: str,
    technology: str,
    technical_feasible: Optional[bool] = None,
    technical_reasons: Optional[Iterable[str]] = None,
) -> str:
    """
    Functional human-readable explanation wrapper.
    """
    return get_engine().explain(
        industry=industry,
        technology=technology,
        technical_feasible=technical_feasible,
        technical_reasons=technical_reasons,
    )


def enrich_screening_result(
    industry: str,
    screening_result: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Functional wrapper for pipeline integration.
    """
    return get_engine().enrich_screening_result(
        industry=industry,
        screening_result=screening_result,
    )


# ---------------------------------------------------------------------------
# Lightweight self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = IndustryConstraintEngine()

    example = engine.evaluate(
        industry="textile_dyeing",
        technology="heat_pump",
        technical_feasible=True,
        technical_reasons=[],
    )

    print(json.dumps(example, indent=2))
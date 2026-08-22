"""
Technology Decision Pipeline
============================

Combines:

Unit 2.3
---------
Technical screening

Unit 2.4
---------
Industry constraint evaluation

Output:
-------
Fully screened technologies ready for scenario generation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from decision_engine.technology.technology_filter import (
    screen_technology,
)

from decision_engine.technology.industry_constraint_engine import (
    IndustryConstraintEngine,
)


class TechnologyDecisionPipeline:
    """
    Runs all technology decision stages before scenario generation.
    """

    def __init__(self):

        self.industry_engine = IndustryConstraintEngine()

    # -------------------------------------------------------------

    def evaluate_factory(
        self,
        factory: Dict[str, Any],
        candidate_technologies: List[str],
    ) -> List[Dict[str, Any]]:

        industry = (
            factory.get("industry")
            or factory.get("industry_id")
            or ""
        )

        final_results = []

        for technology in candidate_technologies:

            # -------------------------
            # Unit 2.3
            # -------------------------

            tech_result = screen_technology(
                technology,
                factory,
            )

            if not tech_result["allowed"]:
                final_results.append(
                    {
                        "technology": technology,
                        "allowed": False,
                        "stage": "technical_screening",
                        "classification": "rejected",
                        "reasons": tech_result["reasons"],
                    }
                )
                continue

            # -------------------------
            # Unit 2.4
            # -------------------------

            industry_result = (
                self.industry_engine.evaluate(
                    industry=industry,
                    technology=technology,
                )
            )

            final_results.append(
                {
                    "technology": technology,
                    "allowed": industry_result["allowed"],
                    "classification": industry_result[
                        "classification"
                    ],
                    "stage": "industry_constraints",
                    "reasons": (
                        tech_result["reasons"]
                        + industry_result["reasons"]
                    ),
                    "operational_constraints":
                        industry_result[
                            "operational_constraints"
                        ],
                    "cluster_recommendations":
                        industry_result[
                            "cluster_recommendations"
                        ],
                }
            )

        return final_results
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


# ---------------------------------------------------------------------------
# Criterion names
# ---------------------------------------------------------------------------

CRITERION_TECHNICAL = "technical"
CRITERION_FINANCIAL = "financial"
CRITERION_RESOURCE = "resource"
CRITERION_POLICY = "policy"
CRITERION_RISK = "risk"
CRITERION_TECHNOLOGY_MATURITY = "technology_maturity"
CRITERION_IMPLEMENTATION_COMPLEXITY = "implementation_complexity"
CRITERION_SUPPLY_RELIABILITY = "supply_reliability"
CRITERION_ELECTRICITY_DEPENDENCE = "electricity_dependence"
CRITERION_BIOMASS_DEPENDENCE = "biomass_dependence"
CRITERION_CARBON_REDUCTION = "carbon_reduction"
CRITERION_CONFIDENCE = "confidence"

# Backward-compatible aliases used by ranking / reports / dashboard
CRITERION_COST = "cost"
CRITERION_EMISSIONS = "emissions"


CRITERIA = (
    CRITERION_TECHNICAL,
    CRITERION_FINANCIAL,
    CRITERION_RESOURCE,
    CRITERION_POLICY,
    CRITERION_RISK,
    CRITERION_TECHNOLOGY_MATURITY,
    CRITERION_IMPLEMENTATION_COMPLEXITY,
    CRITERION_SUPPLY_RELIABILITY,
    CRITERION_ELECTRICITY_DEPENDENCE,
    CRITERION_BIOMASS_DEPENDENCE,
    CRITERION_CARBON_REDUCTION,
    CRITERION_CONFIDENCE,
)


# ---------------------------------------------------------------------------
# Default weights (sum = 1.00)
# Research-informed balance for Indian MSME energy-transition pathways.
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    CRITERION_TECHNICAL: 0.12,
    CRITERION_FINANCIAL: 0.12,
    CRITERION_RESOURCE: 0.08,
    CRITERION_POLICY: 0.06,
    CRITERION_RISK: 0.10,
    CRITERION_TECHNOLOGY_MATURITY: 0.08,
    CRITERION_IMPLEMENTATION_COMPLEXITY: 0.06,
    CRITERION_SUPPLY_RELIABILITY: 0.10,
    CRITERION_ELECTRICITY_DEPENDENCE: 0.05,
    CRITERION_BIOMASS_DEPENDENCE: 0.05,
    CRITERION_CARBON_REDUCTION: 0.12,
    CRITERION_CONFIDENCE: 0.06,
}

WEIGHT_SUM_TOLERANCE = 1e-9


# ---------------------------------------------------------------------------
# Direction of each criterion
# True  -> higher raw value is better (benefit)
# False -> lower raw value is better (cost-type)
# ---------------------------------------------------------------------------

CRITERION_IS_BENEFIT = {
    CRITERION_TECHNICAL: True,
    CRITERION_FINANCIAL: True,
    CRITERION_RESOURCE: True,
    CRITERION_POLICY: True,
    CRITERION_RISK: False,
    CRITERION_TECHNOLOGY_MATURITY: True,
    CRITERION_IMPLEMENTATION_COMPLEXITY: False,
    CRITERION_SUPPLY_RELIABILITY: True,
    CRITERION_ELECTRICITY_DEPENDENCE: False,
    CRITERION_BIOMASS_DEPENDENCE: False,
    CRITERION_CARBON_REDUCTION: True,
    CRITERION_CONFIDENCE: True,
}


@dataclass(frozen=True)
class Weights:
    """
    Normalised MCDA weights.

    Values are fractions in [0, 1] and must sum to 1.0.
    """

    technical: float = DEFAULT_WEIGHTS[CRITERION_TECHNICAL]
    financial: float = DEFAULT_WEIGHTS[CRITERION_FINANCIAL]
    resource: float = DEFAULT_WEIGHTS[CRITERION_RESOURCE]
    policy: float = DEFAULT_WEIGHTS[CRITERION_POLICY]
    risk: float = DEFAULT_WEIGHTS[CRITERION_RISK]
    technology_maturity: float = DEFAULT_WEIGHTS[CRITERION_TECHNOLOGY_MATURITY]
    implementation_complexity: float = DEFAULT_WEIGHTS[
        CRITERION_IMPLEMENTATION_COMPLEXITY
    ]
    supply_reliability: float = DEFAULT_WEIGHTS[CRITERION_SUPPLY_RELIABILITY]
    electricity_dependence: float = DEFAULT_WEIGHTS[
        CRITERION_ELECTRICITY_DEPENDENCE
    ]
    biomass_dependence: float = DEFAULT_WEIGHTS[CRITERION_BIOMASS_DEPENDENCE]
    carbon_reduction: float = DEFAULT_WEIGHTS[CRITERION_CARBON_REDUCTION]
    confidence: float = DEFAULT_WEIGHTS[CRITERION_CONFIDENCE]

    def __post_init__(self) -> None:
        for criterion in CRITERIA:
            value = getattr(self, criterion)
            if value < 0:
                raise ValueError(
                    f"Weight '{criterion}' cannot be negative, got {value}."
                )

        total = sum(getattr(self, criterion) for criterion in CRITERIA)
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(
                f"MCDA weights must sum to 1.0, got {total:.6f}."
            )

    def as_dict(self) -> dict[str, float]:
        return {criterion: getattr(self, criterion) for criterion in CRITERIA}

    @classmethod
    def default(cls) -> "Weights":
        return cls()

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, float]) -> "Weights":
        """
        Build weights from a partial/full mapping.

        Supplied values replace the defaults. The result is normalized
        automatically so callers can provide relative priorities.
        """
        raw = {
            criterion: float(mapping.get(criterion, DEFAULT_WEIGHTS[criterion]))
            for criterion in CRITERIA
        }

        for criterion, value in raw.items():
            if value < 0:
                raise ValueError(
                    f"Weight '{criterion}' cannot be negative, got {value}."
                )

        total = sum(raw.values())
        if total <= 0:
            raise ValueError("At least one MCDA weight must be positive.")

        normalized = {c: v / total for c, v in raw.items()}

        return cls(
            technical=normalized[CRITERION_TECHNICAL],
            financial=normalized[CRITERION_FINANCIAL],
            resource=normalized[CRITERION_RESOURCE],
            policy=normalized[CRITERION_POLICY],
            risk=normalized[CRITERION_RISK],
            technology_maturity=normalized[CRITERION_TECHNOLOGY_MATURITY],
            implementation_complexity=normalized[
                CRITERION_IMPLEMENTATION_COMPLEXITY
            ],
            supply_reliability=normalized[CRITERION_SUPPLY_RELIABILITY],
            electricity_dependence=normalized[CRITERION_ELECTRICITY_DEPENDENCE],
            biomass_dependence=normalized[CRITERION_BIOMASS_DEPENDENCE],
            carbon_reduction=normalized[CRITERION_CARBON_REDUCTION],
            confidence=normalized[CRITERION_CONFIDENCE],
        )


def default_weights() -> Weights:
    """Return the documented default MCDA weight set."""
    return Weights.default()
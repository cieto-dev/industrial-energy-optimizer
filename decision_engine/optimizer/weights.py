"""
weights.py — MCDA criterion weights for cost / emissions / risk.

Purpose
-------
Store the relative importance of the three ranking objectives defined in
docs/DOMAIN_MODEL.md §4 (`objective_scores`) and docs/ROADMAP.md Sprint 3.2.

Weight policy (documented before implementation, per
docs/DECISION_ENGINE_ARCHITECTURE.md open item)
------------------------------------------------
- **Default set:** one shared default for all 9 industries (Sprint 0 Decision 2:
  a single recommendation engine, configuration-driven — not per-industry
  weight tables in MVP).
- **Adjustable:** callers may override via `Weights.from_mapping()` or by
  passing a `Weights` instance into `optimization_engine.optimize()`.
  Overrides are validated (non-negative, sum to 1.0). Unspecified keys keep
  the documented defaults.
- **Not fixed-hidden:** defaults are explicit constants below, not buried in
  mcda.py. Changing priorities must change this module or an explicit override.
- **Not least-cost-only:** cost is 40%, not 100%. Emissions + risk together
  are 60%, which is what allows a more expensive pathway to outrank a cheap
  high-emission / high-risk one.

Criteria (higher benefit score = better, after mcda.py normalisation)
---------------------------------------------------------------------
- cost      — better economics (lower lifecycle cost)
- emissions — greater decarbonisation (lower pathway CO2)
- risk      — lower operational / supply uncertainty (from reliability/)

Dependency
----------
None. Downstream: mcda.py, optimization_engine.py.
Does not import economics/, emissions/, or reliability/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


# ---------------------------------------------------------------------------
# Default weight set
# ---------------------------------------------------------------------------

CRITERION_COST = "cost"
CRITERION_EMISSIONS = "emissions"
CRITERION_RISK = "risk"

CRITERIA = (CRITERION_COST, CRITERION_EMISSIONS, CRITERION_RISK)

# Sum must be 1.0. Cost is deliberately not dominant.
DEFAULT_COST_WEIGHT = 0.40
DEFAULT_EMISSIONS_WEIGHT = 0.35
DEFAULT_RISK_WEIGHT = 0.25

WEIGHT_SUM_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Weights:
    """
    Normalised MCDA weights for the three DOMAIN_MODEL objectives.

    All values are fractions in [0, 1] and must sum to 1.0.
    """

    cost: float = DEFAULT_COST_WEIGHT
    emissions: float = DEFAULT_EMISSIONS_WEIGHT
    risk: float = DEFAULT_RISK_WEIGHT

    def __post_init__(self) -> None:
        for name in CRITERIA:
            value = getattr(self, name)
            if value < 0:
                raise ValueError(
                    f"Weight '{name}' cannot be negative, got {value}."
                )
        total = self.cost + self.emissions + self.risk
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.6f} "
                f"(cost={self.cost}, emissions={self.emissions}, "
                f"risk={self.risk})."
            )

    def as_dict(self) -> dict[str, float]:
        return {
            CRITERION_COST: self.cost,
            CRITERION_EMISSIONS: self.emissions,
            CRITERION_RISK: self.risk,
        }

    @classmethod
    def default(cls) -> "Weights":
        """Documented MVP default set (adjustable, not industry-specific)."""
        return cls()

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, float]) -> "Weights":
        """
        Build weights from a partial or full mapping.

        Missing keys fall back to the documented defaults, then the result
        is re-normalised so the three values still sum to 1.0. This lets a
        factory owner emphasise emissions without having to restate every
        weight.
        """
        raw = {
            CRITERION_COST: float(
                mapping.get(CRITERION_COST, DEFAULT_COST_WEIGHT)
            ),
            CRITERION_EMISSIONS: float(
                mapping.get(CRITERION_EMISSIONS, DEFAULT_EMISSIONS_WEIGHT)
            ),
            CRITERION_RISK: float(
                mapping.get(CRITERION_RISK, DEFAULT_RISK_WEIGHT)
            ),
        }
        total = sum(raw.values())
        if total <= 0:
            raise ValueError("At least one weight must be positive.")
        return cls(
            cost=raw[CRITERION_COST] / total,
            emissions=raw[CRITERION_EMISSIONS] / total,
            risk=raw[CRITERION_RISK] / total,
        )

    @classmethod
    def cost_only(cls) -> "Weights":
        """
        Degenerate set used only to demonstrate least-cost ranking.

        Production recommendations must not use this. Tests use it to prove
        that default weights and cost-only weights produce different winners.
        """
        return cls(cost=1.0, emissions=0.0, risk=0.0)


def default_weights() -> Weights:
    """Public helper matching the ROADMAP item for a default weight set."""
    return Weights.default()

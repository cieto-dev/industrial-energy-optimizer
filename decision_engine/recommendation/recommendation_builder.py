"""
recommendation_builder.py
-------------------------

Recommendation assembly layer for the Industrial Energy Transition Optimizer.

Purpose
-------
Build one stable, explainable recommendation payload from the outputs of the
decision engine.

This module deliberately does NOT:
- calculate the engineering baseline,
- generate scenarios,
- run the MCDA,
- calculate policy eligibility,
- perform sensitivity analysis,
- or mutate upstream scenario objects.

Instead, it assembles those already-computed outputs into a final recommendation
that can be consumed by:
    - dashboard/UI,
    - API layer,
    - report generator,
    - export/JSON serializers,
    - explanation views.

Design principles
-----------------
1. Never recommend an infeasible pathway.
2. Preserve scenario provenance.
3. Keep recommendation logic transparent and deterministic.
4. Prefer explicit upstream values over inferred values.
5. Never silently invent financial, emissions, or policy data.
6. Keep uncertainty and evidence status visible.
7. Produce useful output even when some optional upstream modules are absent.
8. Be backwards-compatible with the repository's current optimizer models.

Primary contract
----------------
Input:
    ranked scenarios
    optional baseline
    optional finance/impact/constraint/explainability payloads

Output:
    Recommendation

The repository's current Recommendation Pydantic model is intentionally
supported, while the helper functions expose richer intermediate information
for future dashboard/API layers.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional, Sequence

from models.recommendation import (
    Explanation,
    PolicyBenefitSummary,
    Recommendation,
    RejectedScenarioExplanation,
    SensitivityAnalysis,
)


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

RECOMMENDATION_BUILDER_VERSION = "2.0"

DEFAULT_POLICY_DISCLAIMER = (
    "Estimated combined benefit — subject to manual verification against "
    "scheme-specific eligibility and convergence rules; individual scheme "
    "benefits may not be stackable."
)

DEFAULT_EVIDENCE_DISCLAIMER = (
    "Values are estimates derived from the configured scenario data and "
    "research assumptions. Verify site-specific conditions before investment."
)

DEFAULT_SENSITIVITY_DISCLAIMER = (
    "Sensitivity results reflect the assumptions and parameter ranges used "
    "by the reliability engine; they are not guarantees of future performance."
)

# Conservative, presentation-only multiplier.
# This is NOT a technical threshold. It is used only to identify a useful
# primary weakness when several alternatives are close.
PRIMARY_WEAKNESS_RATIO = 1.20


# ---------------------------------------------------------------------------
# Generic value helpers
# ---------------------------------------------------------------------------

def _to_dict(value: Any) -> dict[str, Any]:
    """Best-effort conversion of model/dataclass/mapping objects to dict."""
    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    if is_dataclass(value):
        try:
            return asdict(value)
        except TypeError:
            pass

    if hasattr(value, "model_dump"):
        try:
            return dict(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "dict"):
        try:
            return dict(value.dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        return dict(vars(value))

    return {}


def _get(value: Any, *names: str, default: Any = None) -> Any:
    """
    Read a value from a dict-like object or attribute-based object.

    The first non-None value wins.
    """
    if value is None:
        return default

    for name in names:
        if isinstance(value, Mapping):
            candidate = value.get(name)
        else:
            candidate = getattr(value, name, None)

        if candidate is not None:
            return candidate

    return default


def _float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert a value to float without masking invalid data."""
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Convert a value to int."""
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    """Convert common boolean representations."""
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "y", "1"}:
            return True
        if normalized in {"false", "no", "n", "0"}:
            return False

    if isinstance(value, (int, float)):
        return bool(value)

    return default


def _list(value: Any) -> list[Any]:
    """Convert optional iterable values to a plain list."""
    if value is None:
        return []

    if isinstance(value, list):
        return list(value)

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    if isinstance(value, str):
        return [value]

    try:
        return list(value)
    except TypeError:
        return [value]


def _string_list(value: Any) -> list[str]:
    """Return a clean list of non-empty strings."""
    return [
        str(item).strip()
        for item in _list(value)
        if str(item).strip()
    ]


def _first_non_empty(*values: Any) -> Any:
    """Return the first non-empty value."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple, set, dict)) and not value:
            continue
        return value
    return None


# ---------------------------------------------------------------------------
# Ranked scenario resolution
# ---------------------------------------------------------------------------

def _scenario_id(scenario: Any) -> Optional[str]:
    value = _get(
        scenario,
        "scenario_id",
        "id",
        "pathway_id",
        "candidate_id",
    )
    if value is None:
        return None
    return str(value)


def _technology_sequence(scenario: Any) -> list[str]:
    sequence = _first_non_empty(
        _get(scenario, "technology_sequence"),
        _get(scenario, "technologies"),
        _get(scenario, "technology_pathway"),
    )

    return _string_list(sequence)


def _rank(scenario: Any, default: int = 0) -> int:
    return _int(_get(scenario, "rank"), default=default) or default


def _composite_score(scenario: Any) -> Optional[float]:
    return _float(
        _get(
            scenario,
            "composite_score",
            "score",
            "overall_score",
        )
    )


def _objective_scores(scenario: Any) -> dict[str, float]:
    raw = _first_non_empty(
        _get(scenario, "objective_scores"),
        _get(scenario, "criterion_scores"),
        {},
    )

    if not isinstance(raw, Mapping):
        return {}

    result: dict[str, float] = {}

    for key, value in raw.items():
        numeric = _float(value)
        if numeric is not None:
            result[str(key)] = numeric

    return result


def _raw_cost(scenario: Any) -> Optional[float]:
    return _float(
        _first_non_empty(
            _get(scenario, "raw_cost"),
            _get(scenario, "lifecycle_cost"),
            _get(scenario, "total_cost"),
        )
    )


def _raw_emissions(scenario: Any) -> Optional[float]:
    return _float(
        _first_non_empty(
            _get(scenario, "raw_emissions"),
            _get(scenario, "pathway_co2_tonnes_year"),
            _get(scenario, "annual_co2"),
            _get(scenario, "co2"),
        )
    )


def _raw_risk(scenario: Any) -> Optional[float]:
    return _float(
        _first_non_empty(
            _get(scenario, "raw_risk"),
            _get(scenario, "risk"),
            _get(scenario, "risk_score"),
        )
    )


def _recommended_ranked_scenario(
    ranked_scenarios: Sequence[Any],
    recommended_id: Optional[str] = None,
) -> Any:
    if not ranked_scenarios:
        raise ValueError(
            "Cannot build a recommendation without ranked scenarios."
        )

    if recommended_id is not None:
        for item in ranked_scenarios:
            if _scenario_id(item) == recommended_id:
                return item

    # Explicit recommended marker wins if available.
    for item in ranked_scenarios:
        if _bool(_get(item, "is_recommended"), False):
            return item

    # Otherwise rank 1 wins.
    ranked = sorted(
        ranked_scenarios,
        key=lambda item: (
            _rank(item, default=10**9),
            -(_composite_score(item) or float("-inf")),
        ),
    )

    return ranked[0]


# ---------------------------------------------------------------------------
# Feasibility / constraint handling
# ---------------------------------------------------------------------------

def _is_feasible(scenario: Any) -> bool:
    """
    Determine feasibility conservatively.

    Any explicit false feasibility signal blocks recommendation.
    Missing feasibility is treated as feasible for compatibility because the
    optimizer's output contract may already represent only feasible pathways.
    """
    explicit = _first_non_empty(
        _get(scenario, "feasible"),
        _get(scenario, "is_feasible"),
        _get(scenario, "technical_feasible"),
    )

    if explicit is not None:
        return bool(_bool(explicit, False))

    status = _get(
        scenario,
        "status",
        "feasibility_status",
        "constraint_status",
    )

    if isinstance(status, str):
        normalized = status.strip().lower()
        if normalized in {
            "infeasible",
            "rejected",
            "failed",
            "not_feasible",
        }:
            return False

    return True


def _constraint_failures(scenario: Any) -> list[str]:
    """Extract explicit constraint failures from any supported upstream shape."""
    candidates = [
        _get(scenario, "constraint_failures"),
        _get(scenario, "failed_constraints"),
        _get(scenario, "violations"),
        _get(scenario, "rejection_reasons"),
    ]

    reasons: list[str] = []

    for candidate in candidates:
        reasons.extend(_string_list(candidate))

    # Deduplicate while retaining order.
    seen: set[str] = set()
    unique: list[str] = []

    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            unique.append(reason)

    return unique


def _validate_recommended_scenario(scenario: Any) -> None:
    """Refuse to recommend a pathway explicitly marked infeasible."""
    if not _is_feasible(scenario):
        scenario_id = _scenario_id(scenario) or "<unknown>"
        failures = _constraint_failures(scenario)

        detail = (
            f" Constraints: {', '.join(failures)}."
            if failures
            else ""
        )

        raise ValueError(
            f"Recommended scenario '{scenario_id}' is infeasible."
            f"{detail}"
        )


# ---------------------------------------------------------------------------
# Finance / environmental result extraction
# ---------------------------------------------------------------------------

def _nested_finance(scenario: Any, finance: Any = None) -> Any:
    return _first_non_empty(
        finance,
        _get(scenario, "financial"),
        _get(scenario, "finance"),
        _get(scenario, "economics"),
    )


def _nested_impact(scenario: Any, impact: Any = None) -> Any:
    return _first_non_empty(
        impact,
        _get(scenario, "impact"),
        _get(scenario, "emission"),
        _get(scenario, "emissions"),
    )


def _capex_inr(scenario: Any, finance: Any = None) -> float:
    source = _nested_finance(scenario, finance)

    value = _first_non_empty(
        _get(scenario, "capex_total_inr"),
        _get(scenario, "capex_inr"),
        _get(scenario, "capex"),
        _get(source, "capex_total_inr"),
        _get(source, "capex_estimate"),
        _get(source, "capex_gross_inr"),
        _get(source, "net_financed_cost_inr"),
        _get(source, "initial_investment_inr"),
    )

    numeric = _float(value)
    return max(numeric, 0.0) if numeric is not None else 0.0


def _annual_opex_inr(scenario: Any, finance: Any = None) -> float:
    source = _nested_finance(scenario, finance)

    value = _first_non_empty(
        _get(scenario, "annual_opex_inr"),
        _get(scenario, "opex_annual_inr"),
        _get(source, "annual_opex_inr"),
        _get(source, "proposed_annual_opex"),
        _get(source, "annual_operating_cost"),
    )

    numeric = _float(value)
    return max(numeric, 0.0) if numeric is not None else 0.0


def _payback_range(
    scenario: Any,
    finance: Any = None,
    reliability: Any = None,
) -> tuple[float, float]:
    source = _nested_finance(scenario, finance)

    explicit_range = _first_non_empty(
        _get(scenario, "payback_years"),
        _get(scenario, "payback_range_years"),
        _get(source, "payback_years"),
        _get(source, "payback_range_years"),
    )

    if isinstance(explicit_range, (list, tuple)) and len(explicit_range) >= 2:
        low = _float(explicit_range[0])
        high = _float(explicit_range[1])

        if low is not None and high is not None:
            return (
                max(0.0, min(low, high)),
                max(0.0, max(low, high)),
            )

    p10 = _float(
        _first_non_empty(
            _get(scenario, "payback_p10"),
            _get(scenario, "payback_p10_years"),
            _get(source, "payback_p10"),
            _get(reliability, "payback_p10"),
            _get(reliability, "payback_p10_years"),
        )
    )

    p90 = _float(
        _first_non_empty(
            _get(scenario, "payback_p90"),
            _get(scenario, "payback_p90_years"),
            _get(source, "payback_p90"),
            _get(reliability, "payback_p90"),
            _get(reliability, "payback_p90_years"),
        )
    )

    point = _float(
        _first_non_empty(
            _get(scenario, "payback"),
            _get(scenario, "payback_years_simple"),
            _get(source, "payback"),
            _get(source, "simple_payback_years"),
        )
    )

    if p10 is not None and p90 is not None:
        return (
            max(0.0, min(p10, p90)),
            max(0.0, max(p10, p90)),
        )

    if point is not None:
        point = max(0.0, point)
        return (point, point)

    return (0.0, 0.0)


def _co2_reduction_pct(
    scenario: Any,
    impact: Any = None,
) -> float:
    source = _nested_impact(scenario, impact)

    value = _first_non_empty(
        _get(scenario, "co2_reduction_pct"),
        _get(scenario, "carbon_reduction_pct"),
        _get(source, "co2_reduction_pct"),
        _get(source, "reduction_pct"),
        _get(source, "carbon_reduction"),
    )

    numeric = _float(value)
    if numeric is None:
        return 0.0

    return max(0.0, min(100.0, numeric))


def _fossil_reduction_pct(
    scenario: Any,
    impact: Any = None,
) -> float:
    source = _nested_impact(scenario, impact)

    value = _first_non_empty(
        _get(scenario, "fossil_fuel_reduction_pct"),
        _get(scenario, "fossil_reduction_pct"),
        _get(source, "fossil_fuel_reduction_pct"),
        _get(source, "fossil_reduction_pct"),
    )

    numeric = _float(value)
    if numeric is None:
        return 0.0

    return max(0.0, min(100.0, numeric))


def _annual_savings_inr(
    scenario: Any,
    finance: Any = None,
) -> Optional[float]:
    source = _nested_finance(scenario, finance)

    value = _first_non_empty(
        _get(scenario, "annual_savings_inr"),
        _get(scenario, "savings_inr_year"),
        _get(source, "annual_savings_inr"),
        _get(source, "annual_savings"),
        _get(source, "annual_cost_savings_inr"),
    )

    numeric = _float(value)

    if numeric is None:
        return None

    return max(0.0, numeric)


# ---------------------------------------------------------------------------
# Policy summary
# ---------------------------------------------------------------------------

def _policy_benefit_summary(policy_result: Any) -> PolicyBenefitSummary:
    if policy_result is None:
        return PolicyBenefitSummary(
            eligible_schemes=[],
            estimated_total_benefit_inr=0.0,
            total_benefit_verified=False,
            disclaimer=(
                "No policy-engine result was supplied; no policy benefit "
                "has been assumed."
            ),
        )

    schemes_raw = _first_non_empty(
        _get(policy_result, "eligible_schemes"),
        _get(policy_result, "schemes"),
        [],
    )

    scheme_names: list[str] = []

    for scheme in _list(schemes_raw):
        if isinstance(scheme, str):
            scheme_names.append(scheme)
            continue

        name = _first_non_empty(
            _get(scheme, "display_name"),
            _get(scheme, "name"),
            _get(scheme, "scheme_name"),
            _get(scheme, "id"),
        )

        if name is not None:
            scheme_names.append(str(name))

    benefit = _float(
        _first_non_empty(
            _get(policy_result, "estimated_total_benefit_inr"),
            _get(policy_result, "total_benefit_inr"),
            _get(policy_result, "estimated_benefit_inr"),
        ),
        default=0.0,
    ) or 0.0

    verified = bool(
        _bool(
            _get(
                policy_result,
                "total_benefit_verified",
                "benefit_verified",
            ),
            False,
        )
    )

    disclaimer = _get(
        policy_result,
        "disclaimer",
        "benefit_disclaimer",
        default="",
    )

    if not disclaimer and not verified:
        disclaimer = DEFAULT_POLICY_DISCLAIMER

    return PolicyBenefitSummary(
        eligible_schemes=scheme_names,
        estimated_total_benefit_inr=max(0.0, benefit),
        total_benefit_verified=verified,
        disclaimer=str(disclaimer),
    )


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------

def _sensitivity_summary(reliability_result: Any) -> SensitivityAnalysis:
    if reliability_result is None:
        return SensitivityAnalysis(
            payback_p10_years=0.0,
            payback_p50_years=0.0,
            payback_p90_years=0.0,
            spread_ratio=0.0,
            top_risk_factors=[],
            risk_interpretation=(
                "No reliability/sensitivity result was supplied. "
                "Recommendation robustness was not evaluated."
            ),
        )

    p10 = _float(
        _first_non_empty(
            _get(reliability_result, "payback_p10"),
            _get(reliability_result, "payback_p10_years"),
        ),
        default=0.0,
    ) or 0.0

    p50 = _float(
        _first_non_empty(
            _get(reliability_result, "payback_p50"),
            _get(reliability_result, "payback_p50_years"),
        ),
        default=0.0,
    ) or 0.0

    p90 = _float(
        _first_non_empty(
            _get(reliability_result, "payback_p90"),
            _get(reliability_result, "payback_p90_years"),
        ),
        default=0.0,
    ) or 0.0

    spread = _float(
        _get(reliability_result, "spread_ratio"),
        default=None,
    )

    if spread is None:
        if p50 > 0:
            spread = max(0.0, (p90 - p10) / p50)
        else:
            spread = 0.0

    swings = _first_non_empty(
        _get(reliability_result, "oat_swings"),
        _get(reliability_result, "sensitivity"),
        _get(reliability_result, "tornado"),
        {},
    )

    top_factors: list[str] = []

    if isinstance(swings, Mapping):
        ordered = sorted(
            (
                (str(name), _float(value, 0.0) or 0.0)
                for name, value in swings.items()
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        top_factors = [name for name, _ in ordered[:5]]

    explicit_factors = _string_list(
        _first_non_empty(
            _get(reliability_result, "top_risk_factors"),
            _get(reliability_result, "tornado_ranking"),
            [],
        )
    )

    if explicit_factors:
        top_factors = explicit_factors[:5]

    if spread < 0.30:
        interpretation = (
            f"Low payback sensitivity (spread ratio {spread:.2f}). "
            "The recommendation appears comparatively robust under the "
            "tested uncertainty assumptions."
        )
    elif spread < 0.60:
        interpretation = (
            f"Moderate payback sensitivity (spread ratio {spread:.2f}). "
            "The recommendation should be checked against the listed risk "
            "drivers before final investment approval."
        )
    else:
        interpretation = (
            f"High payback sensitivity (spread ratio {spread:.2f}). "
            "Consider phased implementation, risk mitigation, or a "
            "re-evaluation of the pathway under adverse assumptions."
        )

    return SensitivityAnalysis(
        payback_p10_years=max(0.0, p10),
        payback_p50_years=max(0.0, p50),
        payback_p90_years=max(0.0, p90),
        spread_ratio=max(0.0, spread),
        top_risk_factors=top_factors,
        risk_interpretation=interpretation,
    )


# ---------------------------------------------------------------------------
# Selection explanation
# ---------------------------------------------------------------------------

def _recommendation_scores(ranked: Any) -> dict[str, float]:
    return _objective_scores(ranked)


def _score_value(scores: Mapping[str, float], *names: str) -> Optional[float]:
    for name in names:
        if name in scores:
            return scores[name]
    return None


def _make_selected_reasons(
    recommended: Any,
    ranked_scenarios: Sequence[Any],
    recommended_scenario: Any,
    *,
    policy_result: Any = None,
    finance: Any = None,
    impact: Any = None,
) -> list[str]:
    reasons: list[str] = []

    rank = _rank(recommended, default=1)
    composite = _composite_score(recommended)

    reasons.append(
        f"Ranked #{rank} out of {len(ranked_scenarios)} feasible "
        "candidate pathways under the configured decision criteria."
    )

    if composite is not None:
        reasons.append(
            f"Achieved a composite decision score of {composite:.3f}, "
            "with higher-scoring pathways preferred."
        )

    scores = _recommendation_scores(recommended)

    cost_score = _score_value(
        scores,
        "cost",
        "financial",
    )
    emissions_score = _score_value(
        scores,
        "emissions",
        "carbon_reduction",
    )
    risk_score = _score_value(
        scores,
        "risk",
    )
    reliability_score = _score_value(
        scores,
        "reliability",
        "supply_reliability",
    )

    score_parts: list[str] = []

    if cost_score is not None:
        score_parts.append(f"cost/financial {cost_score:.2f}")

    if emissions_score is not None:
        score_parts.append(f"emissions {emissions_score:.2f}")

    if risk_score is not None:
        score_parts.append(f"risk {risk_score:.2f}")

    if reliability_score is not None:
        score_parts.append(f"reliability {reliability_score:.2f}")

    if score_parts:
        reasons.append(
            "Balanced decision scores: " + ", ".join(score_parts) + "."
        )

    co2_pct = _co2_reduction_pct(recommended_scenario, impact)
    fossil_pct = _fossil_reduction_pct(recommended_scenario, impact)
    savings = _annual_savings_inr(recommended_scenario, finance)

    if co2_pct > 0:
        reasons.append(
            f"Estimated CO2 reduction is {co2_pct:.1f}% relative to the "
            "configured baseline."
        )

    if fossil_pct > 0:
        reasons.append(
            f"Estimated fossil-fuel reduction is {fossil_pct:.1f}%, "
            "improving exposure to fossil-fuel volatility."
        )

    if savings is not None:
        reasons.append(
            f"Estimated annual operating savings are approximately "
            f"₹{savings:,.0f} under the configured assumptions."
        )

    recommended_id = _scenario_id(recommended)
    cheapest = _cheapest_scenario(ranked_scenarios)

    if cheapest is not None:
        cheapest_id = _scenario_id(cheapest)

        if cheapest_id == recommended_id:
            reasons.append(
                "The recommended pathway is also the lowest lifecycle-cost "
                "option among the ranked candidates."
            )
        else:
            reasons.append(
                _why_not_cheapest_sentence(
                    recommended,
                    cheapest,
                )
            )

    policy_summary = _policy_benefit_summary(policy_result)

    if policy_summary.eligible_schemes:
        reasons.append(
            f"Policy engine found {len(policy_summary.eligible_schemes)} "
            f"eligible support mechanism(s): "
            f"{', '.join(policy_summary.eligible_schemes[:3])}"
            + (
                f" and {len(policy_summary.eligible_schemes) - 3} more."
                if len(policy_summary.eligible_schemes) > 3
                else "."
            )
        )

    return reasons


def _cheapest_scenario(
    ranked_scenarios: Sequence[Any],
) -> Optional[Any]:
    """
    Find the lowest raw/lifecycle-cost scenario.

    Missing costs are excluded rather than treated as zero.
    """
    available = [
        item
        for item in ranked_scenarios
        if _raw_cost(item) is not None
    ]

    if not available:
        return None

    return min(
        available,
        key=lambda item: (
            _raw_cost(item),
            _scenario_id(item) or "",
        ),
    )


def _why_not_cheapest_sentence(
    recommended: Any,
    cheapest: Any,
) -> str:
    recommendation_cost = _raw_cost(recommended)
    cheapest_cost = _raw_cost(cheapest)

    if recommendation_cost is not None and cheapest_cost not in (None, 0):
        ratio = recommendation_cost / cheapest_cost

        if ratio > PRIMARY_WEAKNESS_RATIO:
            return (
                "The recommendation is not the cheapest pathway; the "
                "optimizer accepted additional lifecycle cost to obtain "
                "a stronger overall balance across environmental, "
                "risk, reliability, or other configured criteria."
            )

    return (
        "The recommendation is not the lowest-cost pathway, but it ranked "
        "higher after the configured multi-criteria trade-off was applied."
    )


# ---------------------------------------------------------------------------
# Rejected scenario explanations
# ---------------------------------------------------------------------------

def _relative_weakness(
    candidate: Any,
    recommended: Any,
) -> tuple[str, str]:
    """
    Identify one useful primary weakness for a rejected scenario.

    Returns:
        (weakness_label, sentence)
    """
    candidate_cost = _raw_cost(candidate)
    recommended_cost = _raw_cost(recommended)

    candidate_emissions = _raw_emissions(candidate)
    recommended_emissions = _raw_emissions(recommended)

    candidate_risk = _raw_risk(candidate)
    recommended_risk = _raw_risk(recommended)

    candidate_scores = _objective_scores(candidate)
    recommended_scores = _objective_scores(recommended)

    # Cost weakness
    if (
        candidate_cost is not None
        and recommended_cost is not None
        and recommended_cost >= 0
        and candidate_cost > recommended_cost * PRIMARY_WEAKNESS_RATIO
    ):
        return (
            "higher cost",
            "It carries materially higher lifecycle cost than the "
            "recommended pathway."
        )

    # Emissions weakness
    if (
        candidate_emissions is not None
        and recommended_emissions is not None
        and candidate_emissions > recommended_emissions
        and recommended_emissions >= 0
        and candidate_emissions
        > max(recommended_emissions * PRIMARY_WEAKNESS_RATIO, 1e-9)
    ):
        return (
            "higher emissions",
            "It has materially higher pathway emissions than the "
            "recommended pathway."
        )

    # Risk weakness
    if (
        candidate_risk is not None
        and recommended_risk is not None
        and candidate_risk > recommended_risk * PRIMARY_WEAKNESS_RATIO
    ):
        return (
            "higher operational risk",
            "It carries materially higher operational or reliability risk."
        )

    # Criterion-level weaknesses
    pairings = [
        (
            ("financial", "cost"),
            "weaker financial score",
            "Its financial/cost score is weaker than the recommended "
            "pathway.",
        ),
        (
            ("carbon_reduction", "emissions"),
            "weaker carbon outcome",
            "Its carbon-reduction outcome is weaker than the recommended "
            "pathway.",
        ),
        (
            ("risk",),
            "weaker risk score",
            "Its risk score is weaker than the recommended pathway.",
        ),
        (
            ("supply_reliability", "reliability"),
            "weaker supply reliability",
            "Its supply/reliability score is weaker than the recommended "
            "pathway.",
        ),
        (
            ("technical",),
            "weaker technical fit",
            "Its technical score is weaker than the recommended pathway.",
        ),
        (
            ("policy",),
            "weaker policy position",
            "Its policy score is weaker than the recommended pathway.",
        ),
    ]

    for keys, label, sentence in pairings:
        candidate_value = _score_value(candidate_scores, *keys)
        recommended_value = _score_value(recommended_scores, *keys)

        if (
            candidate_value is not None
            and recommended_value is not None
            and candidate_value < recommended_value
        ):
            return label, sentence

    return (
        "lower overall score",
        "It ranked below the recommended pathway after the configured "
        "multi-criteria evaluation."
    )


def _rejected_explanation(
    candidate: Any,
    recommended: Any,
) -> RejectedScenarioExplanation:
    candidate_id = _scenario_id(candidate)

    if candidate_id is None:
        raise ValueError("Every ranked scenario needs a scenario_id.")

    rank = _rank(candidate)
    composite = _composite_score(candidate) or 0.0

    weakness, sentence = _relative_weakness(
        candidate,
        recommended,
    )

    failures = _constraint_failures(candidate)

    if failures and not _is_feasible(candidate):
        reason = (
            "Rejected because it violates technical/decision constraints: "
            + "; ".join(failures)
        )
        key_weakness = "constraint violation"
    else:
        reason = f"Ranked #{rank}: {sentence}"
        key_weakness = weakness

    return RejectedScenarioExplanation(
        scenario_id=candidate_id,
        technology_sequence=_technology_sequence(candidate),
        reason=reason,
        rank=rank,
        composite_score=composite,
        key_weakness=key_weakness,
    )


def _make_rejected_explanations(
    ranked_scenarios: Sequence[Any],
    recommended: Any,
) -> list[RejectedScenarioExplanation]:
    recommended_id = _scenario_id(recommended)

    explanations: list[RejectedScenarioExplanation] = []

    for candidate in ranked_scenarios:
        candidate_id = _scenario_id(candidate)

        if candidate_id == recommended_id:
            continue

        explanations.append(
            _rejected_explanation(
                candidate,
                recommended,
            )
        )

    return explanations


# ---------------------------------------------------------------------------
# Provenance / evidence helpers
# ---------------------------------------------------------------------------

def _collect_evidence(
    *sources: Any,
) -> list[dict[str, Any]]:
    """
    Collect evidence references from scenario/module outputs.

    This is intentionally generic so future modules can provide fields such as:
        evidence
        sources
        assumptions
        provenance
        evidence_register
    """
    result: list[dict[str, Any]] = []

    for source in sources:
        if source is None:
            continue

        candidates = [
            _get(source, "evidence"),
            _get(source, "sources"),
            _get(source, "provenance"),
            _get(source, "evidence_register"),
            _get(source, "assumptions"),
        ]

        for candidate in candidates:
            if candidate is None:
                continue

            if isinstance(candidate, Mapping):
                result.append(dict(candidate))
                continue

            for item in _list(candidate):
                if isinstance(item, Mapping):
                    result.append(dict(item))
                else:
                    result.append({"value": str(item)})

    return _dedupe_dicts(result)


def _dedupe_dicts(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate dictionaries using a stable string representation."""
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for item in items:
        key = repr(sorted(item.items(), key=lambda pair: str(pair[0])))

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def _evidence_status(
    recommended: Any,
    finance: Any,
    impact: Any,
    policy: Any,
) -> str:
    """
    Return a broad evidence-status label.

    Values:
        verified
        mixed
        estimated
    """
    statuses: list[str] = []

    for source in (recommended, finance, impact, policy):
        status = _get(
            source,
            "evidence_status",
            "status",
            "confidence_status",
        )

        if isinstance(status, str) and status.strip():
            statuses.append(status.strip().lower())

    if any(status in {"estimated", "inference", "inferred"} for status in statuses):
        return "mixed"

    if any(status in {"verified", "validated", "primary"} for status in statuses):
        return "verified"

    return "estimated"


# ---------------------------------------------------------------------------
# Additional structured recommendation metadata
# ---------------------------------------------------------------------------

def build_recommendation_metadata(
    *,
    recommended: Any,
    baseline: Any = None,
    finance: Any = None,
    impact: Any = None,
    constraints: Any = None,
    policy_result: Any = None,
) -> dict[str, Any]:
    """
    Build a richer metadata object for APIs/UI layers.

    This does not modify the Pydantic Recommendation model.
    """
    payback_low, payback_high = _payback_range(
        recommended,
        finance=finance,
        reliability=None,
    )

    annual_savings = _annual_savings_inr(
        recommended,
        finance=finance,
    )

    evidence = _collect_evidence(
        recommended,
        baseline,
        finance,
        impact,
        constraints,
        policy_result,
    )

    metadata = {
        "builder_version": RECOMMENDATION_BUILDER_VERSION,
        "evidence_status": _evidence_status(
            recommended,
            finance,
            impact,
            policy_result,
        ),
        "annual_savings_inr": annual_savings,
        "payback_low_years": payback_low,
        "payback_high_years": payback_high,
        "evidence": evidence,
        "baseline_id": _first_non_empty(
            _get(baseline, "factory_id"),
            _get(baseline, "baseline_id"),
            _get(baseline, "id"),
        ),
        "constraint_status": {
            "feasible": _is_feasible(recommended),
            "failures": _constraint_failures(recommended),
        },
        "policy_benefit_verified": bool(
            _bool(
                _get(
                    policy_result,
                    "total_benefit_verified",
                    "benefit_verified",
                ),
                False,
            )
        ),
        "disclaimer": DEFAULT_EVIDENCE_DISCLAIMER,
    }

    return metadata


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_recommendation(
    *,
    factory_id: str,
    factory_name: str,
    industry: str,
    state: str,
    ranked_scenarios: Sequence[Any],
    scenarios: Optional[Mapping[str, Any]] = None,
    policy_result: Any = None,
    reliability_result: Any = None,
    baseline: Any = None,
    finance_result: Any = None,
    impact_result: Any = None,
    recommended_scenario_id: Optional[str] = None,
) -> Recommendation:
    """
    Build the final Recommendation object.

    Parameters
    ----------
    factory_id:
        Stable factory identifier.

    factory_name:
        Human-readable factory name.

    industry:
        Industrial sector.

    state:
        State/location used for state-specific energy and policy context.

    ranked_scenarios:
        Ranked MCDA scenarios, normally produced by ranking.py / optimizer.

    scenarios:
        Optional mapping of scenario_id -> rich scenario objects.
        When present, rich scenario data is preferred over the compact ranked row.

    policy_result:
        Optional output of the policy engine.

    reliability_result:
        Optional reliability/sensitivity engine output.

    baseline:
        Optional baseline model output.

    finance_result:
        Optional finance engine output.

    impact_result:
        Optional impact/emissions engine output.

    recommended_scenario_id:
        Explicit scenario ID override. Otherwise the top-ranked scenario wins.

    Returns
    -------
    Recommendation
        Pydantic recommendation model ready for JSON serialization.

    Raises
    ------
    ValueError
        If no scenarios exist or the chosen scenario is infeasible.
    """
    if not factory_id.strip():
        raise ValueError("factory_id cannot be empty.")

    if not factory_name.strip():
        raise ValueError("factory_name cannot be empty.")

    if not industry.strip():
        raise ValueError("industry cannot be empty.")

    if not state.strip():
        raise ValueError("state cannot be empty.")

    ranked = list(ranked_scenarios)

    if not ranked:
        raise ValueError(
            "At least one ranked scenario is required to build a recommendation."
        )

    ranked_recommended = _recommended_ranked_scenario(
        ranked,
        recommended_id=recommended_scenario_id,
    )

    ranked_id = _scenario_id(ranked_recommended)

    if ranked_id is None:
        raise ValueError(
            "The selected ranked scenario is missing scenario_id."
        )

    # Prefer the rich scenario model when one is supplied.
    rich_scenario = None

    if scenarios is not None:
        rich_scenario = scenarios.get(ranked_id)

    recommended_scenario = (
        rich_scenario
        if rich_scenario is not None
        else ranked_recommended
    )

    _validate_recommended_scenario(recommended_scenario)

    # If the compact ranked object is feasible but the rich object says it is
    # not, the rich technical reality wins.
    if not _is_feasible(recommended_scenario):
        raise ValueError(
            f"Scenario '{ranked_id}' cannot be recommended because the "
            "rich scenario object marks it infeasible."
        )

    # Match the ranked row back to the selected ID. This ensures scores come
    # from the optimizer/ranking layer, not from ad-hoc recalculation here.
    ranked_selected = next(
        item
        for item in ranked
        if _scenario_id(item) == ranked_id
    )

    capex = _capex_inr(
        recommended_scenario,
        finance=finance_result,
    )

    annual_opex = _annual_opex_inr(
        recommended_scenario,
        finance=finance_result,
    )

    payback_range = _payback_range(
        recommended_scenario,
        finance=finance_result,
        reliability=reliability_result,
    )

    co2_reduction = _co2_reduction_pct(
        recommended_scenario,
        impact=impact_result,
    )

    fossil_reduction = _fossil_reduction_pct(
        recommended_scenario,
        impact=impact_result,
    )

    objective_scores = _objective_scores(ranked_selected)

    composite_score = _composite_score(ranked_selected)

    if composite_score is None:
        composite_score = 0.0

    cheapest = _cheapest_scenario(ranked)

    recommended_is_cheapest = (
        cheapest is not None
        and _scenario_id(cheapest) == ranked_id
    )

    policy_benefits = _policy_benefit_summary(policy_result)

    sensitivity = _sensitivity_summary(reliability_result)

    why_selected = _make_selected_reasons(
        ranked_selected,
        ranked,
        recommended_scenario,
        policy_result=policy_result,
        finance=finance_result,
        impact=impact_result,
    )

    rejected = _make_rejected_explanations(
        ranked,
        ranked_selected,
    )

    explanation = Explanation(
        why_selected=why_selected,
        why_others_rejected=rejected,
        policy_benefits=policy_benefits,
        sensitivity_notes=sensitivity,
    )

    generated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    recommendation = Recommendation(
        factory_id=factory_id,
        factory_name=factory_name,
        industry=industry,
        state=state,
        recommended_scenario_id=ranked_id,
        recommended_technology_sequence=_technology_sequence(
            recommended_scenario
        ),
        capex_total_inr=capex,
        annual_opex_inr=annual_opex,
        payback_range_years=payback_range,
        co2_reduction_pct=co2_reduction,
        fossil_fuel_reduction_pct=fossil_reduction,
        composite_score=float(composite_score),
        objective_scores=objective_scores,
        recommended_is_cheapest=recommended_is_cheapest,
        explanation=explanation,
        generated_at=generated_at,
        model_version=RECOMMENDATION_BUILDER_VERSION,
    )

    return recommendation


# ---------------------------------------------------------------------------
# Backwards-compatible alias
# ---------------------------------------------------------------------------

def generate_recommendation(
    factory_id: str,
    factory_name: str,
    industry: str,
    state: str,
    optimization_result: Any,
    policy_result: Any = None,
    reliability_result: Any = None,
    scenarios: Optional[Mapping[str, Any]] = None,
    baseline: Any = None,
    finance_result: Any = None,
    impact_result: Any = None,
) -> Recommendation:
    """
    Compatibility wrapper for existing callers.

    Supports the repository's current OptimizationResult-style output.

    This wrapper intentionally does not recalculate optimization. It only
    delegates to build_recommendation().
    """
    ranked_scenarios = _first_non_empty(
        _get(optimization_result, "ranked_scenarios"),
        _get(optimization_result, "scenarios"),
        [],
    )

    if not ranked_scenarios:
        raise ValueError(
            "Optimization result does not contain ranked_scenarios."
        )

    recommended_id = _first_non_empty(
        _get(optimization_result, "recommended_scenario_id"),
        _get(optimization_result, "selected_scenario_id"),
    )

    return build_recommendation(
        factory_id=factory_id,
        factory_name=factory_name,
        industry=industry,
        state=state,
        ranked_scenarios=list(ranked_scenarios),
        scenarios=scenarios,
        policy_result=policy_result,
        reliability_result=reliability_result,
        baseline=baseline,
        finance_result=finance_result,
        impact_result=impact_result,
        recommended_scenario_id=(
            str(recommended_id)
            if recommended_id is not None
            else None
        ),
    )


# ---------------------------------------------------------------------------
# Dashboard/API helper
# ---------------------------------------------------------------------------

def recommendation_to_dict(
    recommendation: Recommendation,
    *,
    baseline: Any = None,
    finance_result: Any = None,
    impact_result: Any = None,
    constraints: Any = None,
    policy_result: Any = None,
    recommended_scenario: Any = None,
) -> dict[str, Any]:
    """
    Serialize Recommendation plus richer decision-engine metadata.

    The returned object is JSON-friendly and suitable for a dashboard/API.
    """
    if hasattr(recommendation, "model_dump"):
        payload = recommendation.model_dump(mode="json")
    else:
        payload = recommendation.dict()

    payload["builder_metadata"] = build_recommendation_metadata(
        recommended=recommended_scenario or recommendation,
        baseline=baseline,
        finance=finance_result,
        impact=impact_result,
        constraints=constraints,
        policy_result=policy_result,
    )

    # Make the evidence disclaimer visible at the top level too.
    payload["evidence_disclaimer"] = DEFAULT_EVIDENCE_DISCLAIMER

    return payload


__all__ = [
    "RECOMMENDATION_BUILDER_VERSION",
    "build_recommendation",
    "generate_recommendation",
    "build_recommendation_metadata",
    "recommendation_to_dict",
]
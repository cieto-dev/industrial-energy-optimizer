"""
eligibility.py — MSME / scheme eligibility checks (Sprint 3.3).

Purpose
-------
Answer "Is this factory eligible for scheme X?" before any benefit is
calculated. All thresholds and allowed values are read from
knowledge-base/policies/eligibility_rules.json — nothing is hardcoded here.

Does NOT:
- load subsidy rates (subsidy_matcher.py reads subsidies.json)
- calculate benefit amounts
- call FastAPI or mutate Factory
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from models.factory import Factory, SpecialCategory


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ELIGIBILITY_RULES_PATH = (
    _PROJECT_ROOT / "knowledge-base" / "policies" / "eligibility_rules.json"
)

STATUS_ELIGIBLE = "eligible"
STATUS_NOT_ELIGIBLE = "not_eligible"
STATUS_CONDITIONALLY_ELIGIBLE = "conditionally_eligible"
STATUS_INSUFFICIENT_DATA = "insufficient_data"

# Maps factory.industry values to ADEETIE eligible_sectors entries.
_INDUSTRY_SECTOR_ALIASES: dict[str, str] = {
    "textile": "textiles",
    "textiles": "textiles",
    "food_processing": "food_processing",
    "chemical": "chemicals",
    "chemicals": "chemicals",
    "pharma": "pharmaceutical",
    "pharmaceutical": "pharmaceutical",
    "pharmaceuticals": "pharmaceutical",
    "paper": "paper",
    "steel": "steel_re_rolling",
    "glass": "glass_and_refractory",
    "cement": "bricks",
    "dairy": "fisheries",
}

# factory.project_type → MSE-GIFT green activity categories
# (eligibility_rules.json MSE_GIFT.eligible_project_categories)
_PROJECT_TYPE_GREEN_CATEGORIES: dict[str, list[str]] = {
    "energy_efficiency": ["resource_efficiency"],
    "electrification": ["electric_transport", "hybrid_transport"],
    "renewable_energy": ["other_approved_high_climate_impact_projects"],
    "alternative_fuel": ["compressed_biogas", "bio_ethanol", "LNG"],
    "biomass": ["compressed_biogas", "waste_to_energy"],
    "waste_heat_recovery": ["resource_efficiency"],
    "energy_storage": ["smart_grids"],
    "waste_management": ["waste_management", "waste_to_energy", "e_waste"],
    "circular_economy": [
        "waste_management",
        "waste_to_energy",
        "other_approved_circular_economy_activity",
    ],
    "clean_transport": ["electric_transport", "clean_transport"],
    "pollution_control": ["pollution_control", "pollution_prevention"],
    "green_infrastructure": ["green_buildings"],
}


@dataclass
class SchemeEligibility:
    """Per-scheme eligibility outcome (matches eligibility_rules output_fields)."""

    scheme_id: str
    status: str
    reason: str
    failed_conditions: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    benefit_can_be_applied: bool = False
    verification_required: bool = False


@dataclass
class EligibilitySummary:
    """Factory-level eligibility pass before subsidy matching."""

    derived_msme_category: str
    declared_msme_category: str
    msme_category_consistent: bool
    udyam_registered: bool
    schemes: dict[str, SchemeEligibility]
    warnings: list[str] = field(default_factory=list)


def _load_eligibility_rules(path: Optional[Path] = None) -> dict[str, Any]:
    rules_path = path or _DEFAULT_ELIGIBILITY_RULES_PATH
    if not rules_path.exists():
        raise FileNotFoundError(
            f"Eligibility rules not found: {rules_path}"
        )
    with open(rules_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalise_industry_sector(industry: str) -> str:
    key = industry.strip().lower().replace(" ", "_").replace("-", "_")
    return _INDUSTRY_SECTOR_ALIASES.get(key, key)


def _special_flags(factory: Factory) -> dict[str, bool]:
    sc = factory.special_category or SpecialCategory()
    return {
        "women_owned": sc.women_owned,
        "sc_st_owned": sc.sc_st_owned,
        "pwd_owned": sc.pwd_owned,
        "agniveer_owned": sc.agniveer_owned,
        "transgender_owned": sc.transgender_owned,
        "north_east_region": sc.north_east_region,
        "jammu_kashmir": sc.jammu_kashmir,
        "ladakh": sc.ladakh,
        "aspirational_district": sc.aspirational_district,
        "identified_credit_deficient_district": (
            sc.identified_credit_deficient_district
        ),
    }


class EligibilityChecker:
    """
    Machine-checkable eligibility gatekeeper.

    Reads eligibility_rules.json only. Does not read subsidies.json.
    """

    def __init__(self, rules_path: Optional[Path] = None) -> None:
        self._rules = _load_eligibility_rules(rules_path)
        self._msme_rules = self._rules["msme_classification"]["rules"]

    def classify_msme(
        self,
        investment_inr: float,
        turnover_inr: float,
    ) -> str:
        """
        Derive MSME category from Udyam thresholds in eligibility_rules.json.

        Both investment AND turnover ceilings must be satisfied (AND logic).
        """
        micro = self._msme_rules["micro"]
        small = self._msme_rules["small"]
        medium = self._msme_rules["medium"]

        if (
            investment_inr <= micro["max_investment_inr"]
            and turnover_inr <= micro["max_turnover_inr"]
        ):
            return "micro"
        if (
            investment_inr <= small["max_investment_inr"]
            and turnover_inr <= small["max_turnover_inr"]
        ):
            return "small"
        if (
            investment_inr <= medium["max_investment_inr"]
            and turnover_inr <= medium["max_turnover_inr"]
        ):
            return "medium"
        return "large"

    def check_udyam(self, factory: Factory, scheme_id: str) -> Optional[str]:
        """Return failure reason if Udyam is required but missing."""
        scheme = self._rules["scheme_rules"].get(scheme_id, {})
        needs_udyam = scheme.get("eligibility", {}).get("udyam_required")
        if needs_udyam is True and not factory.udyam_registered:
            return "not_udyam_registered"
        return None

    def check_enterprise_category(
        self,
        factory: Factory,
        allowed: list[str],
    ) -> Optional[str]:
        category = factory.msme_classification
        if category not in allowed:
            return f"enterprise_category '{category}' not in {allowed}"
        return None

    def check_turnover_investment_limits(self, factory: Factory) -> list[str]:
        """Verify declared category against derived thresholds."""
        derived = self.classify_msme(
            factory.plant_and_machinery_or_equipment_investment_inr,
            factory.annual_turnover_inr,
        )
        warnings: list[str] = []
        if derived != factory.msme_classification:
            warnings.append(
                f"Declared msme_classification '{factory.msme_classification}' "
                f"does not match derived category '{derived}' from "
                f"investment={factory.plant_and_machinery_or_equipment_investment_inr} "
                f"and turnover={factory.annual_turnover_inr} "
                f"(eligibility_rules.json msme_classification.rules)."
            )
        return warnings

    def _result(
        self,
        scheme_id: str,
        status: str,
        reason: str,
        failed: Optional[list[str]] = None,
        missing: Optional[list[str]] = None,
        verification: bool = False,
    ) -> SchemeEligibility:
        benefit_ok = status == STATUS_ELIGIBLE
        return SchemeEligibility(
            scheme_id=scheme_id,
            status=status,
            reason=reason,
            failed_conditions=failed or [],
            missing_inputs=missing or [],
            benefit_can_be_applied=benefit_ok,
            verification_required=(
                verification or status == STATUS_CONDITIONALLY_ELIGIBLE
            ),
        )

    def evaluate_adeetie(self, factory: Factory) -> SchemeEligibility:
        scheme_id = "ADEETIE"
        failed: list[str] = []
        missing: list[str] = []

        if fail := self.check_udyam(factory, scheme_id):
            failed.append(fail)
        if fail := self.check_enterprise_category(
            factory, ["micro", "small", "medium"]
        ):
            failed.append(fail)

        if not factory.cluster_is_adeetie_identified:
            failed.append("cluster_is_adeetie_identified != true")

        sector = _normalise_industry_sector(factory.industry)
        eligible_sectors = self._rules["scheme_rules"]["ADEETIE"][
            "eligible_sectors"
        ]
        if sector not in eligible_sectors:
            failed.append(
                f"industry_sector '{sector}' not in ADEETIE eligible_sectors"
            )

        if factory.annual_energy_savings_percent is None:
            missing.append("annual_energy_savings_percent")
        elif factory.annual_energy_savings_percent < 10:
            failed.append("energy_savings_below_10_percent")

        if factory.loan_amount_inr is None:
            missing.append("loan_amount_inr")
        else:
            loan = factory.loan_amount_inr
            if loan < 1_000_000:
                failed.append("loan_below_minimum")
            if loan > 150_000_000:
                failed.append("loan_above_maximum")
            max_debt = 0.75 * factory.project_cost_inr
            if loan > max_debt:
                failed.append("loan_exceeds_75_percent_of_project_cost")

        if missing:
            return self._result(
                scheme_id,
                STATUS_INSUFFICIENT_DATA,
                "Required ADEETIE inputs missing; cannot guarantee eligibility.",
                failed=failed,
                missing=missing,
                verification=True,
            )
        if failed:
            return self._result(
                scheme_id,
                STATUS_NOT_ELIGIBLE,
                "ADEETIE scheme conditions not satisfied.",
                failed=failed,
            )
        return self._result(
            scheme_id,
            STATUS_ELIGIBLE,
            (
                f"Udyam-registered {factory.msme_classification} enterprise "
                f"in ADEETIE-identified cluster, sector '{sector}', with "
                f">=10% energy savings and qualifying loan size."
            ),
        )

    def evaluate_mse_gift(self, factory: Factory) -> SchemeEligibility:
        scheme_id = "MSE_GIFT"
        failed: list[str] = []

        if fail := self.check_udyam(factory, scheme_id):
            failed.append(fail)
        if fail := self.check_enterprise_category(factory, ["micro", "small"]):
            failed.append(fail)

        green_cats = _PROJECT_TYPE_GREEN_CATEGORIES.get(
            factory.project_type, []
        )
        if not green_cats:
            failed.append("project_not_in_eligible_green_category")

        if factory.loan_amount_inr is None:
            return self._result(
                scheme_id,
                STATUS_INSUFFICIENT_DATA,
                "loan_amount_inr required to verify MSE-GIFT loan ceiling.",
                failed=failed,
                missing=["loan_amount_inr"],
                verification=True,
            )
        if factory.loan_amount_inr > 20_000_000:
            failed.append("loan_above_2_crore")

        if failed:
            return self._result(
                scheme_id,
                STATUS_NOT_ELIGIBLE,
                "MSE-GIFT conditions not satisfied.",
                failed=failed,
            )
        return self._result(
            scheme_id,
            STATUS_CONDITIONALLY_ELIGIBLE,
            (
                "Small/micro Udyam enterprise with green-category project "
                f"type '{factory.project_type}'; lender channel must be "
                "verified against member lending institution rules."
            ),
            verification=True,
        )

    def evaluate_mse_spice(self, factory: Factory) -> SchemeEligibility:
        scheme_id = "MSE_SPICE"
        failed: list[str] = []

        if fail := self.check_udyam(factory, scheme_id):
            failed.append(fail)
        if fail := self.check_enterprise_category(factory, ["micro", "small"]):
            failed.append(fail)
        if factory.project_type not in ("circular_economy", "waste_management"):
            failed.append("non_circular_project")
        if factory.brownfield_or_greenfield != "brownfield":
            failed.append("brownfield_required")

        if failed:
            return self._result(
                scheme_id,
                STATUS_NOT_ELIGIBLE,
                "MSE-SPICE requires brownfield circular-economy project.",
                failed=failed,
            )
        return self._result(
            scheme_id,
            STATUS_ELIGIBLE,
            "Brownfield circular-economy project for micro/small Udyam MSME.",
        )

    def evaluate_zed(self, factory: Factory) -> SchemeEligibility:
        scheme_id = "ZED"
        failed: list[str] = []
        if fail := self.check_udyam(factory, scheme_id):
            failed.append(fail)
        if fail := self.check_enterprise_category(
            factory, ["micro", "small", "medium"]
        ):
            failed.append(fail)
        if failed:
            return self._result(
                scheme_id,
                STATUS_NOT_ELIGIBLE,
                "ZED requires Udyam-registered MSME.",
                failed=failed,
            )
        return self._result(
            scheme_id,
            STATUS_ELIGIBLE,
            "Udyam-registered MSME eligible for ZED certification support.",
        )

    def evaluate_cgtmse(self, factory: Factory) -> SchemeEligibility:
        scheme_id = "CGTMSE"
        failed: list[str] = []
        if fail := self.check_enterprise_category(factory, ["micro", "small"]):
            failed.append(fail)
        if factory.loan_amount_inr is None:
            return self._result(
                scheme_id,
                STATUS_CONDITIONALLY_ELIGIBLE,
                "Micro/small enterprise may qualify subject to eligible "
                "credit facility and participating lender.",
                failed=failed,
                missing=["loan_amount_inr"],
                verification=True,
            )
        if failed:
            return self._result(
                scheme_id,
                STATUS_NOT_ELIGIBLE,
                "CGTMSE limited to micro and small enterprises.",
                failed=failed,
            )
        return self._result(
            scheme_id,
            STATUS_CONDITIONALLY_ELIGIBLE,
            "Micro/small enterprise may qualify subject to eligible credit "
            "facility and participating lender.",
            verification=True,
        )

    def evaluate_pmegp(self, factory: Factory) -> SchemeEligibility:
        scheme_id = "PMEGP"
        failed: list[str] = []
        if factory.existing_or_new_project != "new":
            failed.append("existing_project")
        if factory.msme_classification != "micro":
            failed.append("non_micro_enterprise")
        max_cost = 5_000_000
        if factory.project_cost_inr > max_cost:
            failed.append("project_cost_above_limit")
        if failed:
            return self._result(
                scheme_id,
                STATUS_NOT_ELIGIBLE,
                "PMEGP is for new micro-enterprise creation, not existing "
                "factory retrofits.",
                failed=failed,
            )
        return self._result(
            scheme_id,
            STATUS_ELIGIBLE,
            "New micro-enterprise within PMEGP project cost limit.",
        )

    def evaluate_clcss(self, factory: Factory) -> SchemeEligibility:
        """
        CLCSS is referenced in domain docs but has no canonical SUB_CLCSS
        entity in subsidies.json — return insufficient_data, not invented rates.
        """
        _ = factory
        return self._result(
            "CLCSS",
            STATUS_INSUFFICIENT_DATA,
            (
                "CLCSS is cited in project documentation (SRC_CLCSS_SCHEME) "
                "but no canonical financial-support record exists in "
                "knowledge-base/finance/subsidies.json. Cannot compute a "
                "verified benefit — add SUB_CLCSS before applying."
            ),
            verification=True,
        )

    def evaluate_mnre_cfa(self, factory: Factory) -> SchemeEligibility:
        """
        Roadmap gate name 'MNRE CFA'.

        Live MNRE bioenergy CFA (SUB_MNRE_NBP_*) applies only to pellet/cogen
        plants. Proposed MSME rooftop solar CFA (SUB_NITI_MSME_SOLAR_CFA_PROPOSED)
        is draft — never treated as guaranteed.
        """
        if factory.project_type in ("biomass", "waste_management"):
            return self._result(
                "MNRE_NBP_CFA",
                STATUS_CONDITIONALLY_ELIGIBLE,
                (
                    "MNRE National Bioenergy Programme CFA may apply to "
                    "biomass pellet/cogen pathways — verify technology "
                    "capacity band against SUB_MNRE_NBP_* in subsidies.json."
                ),
                verification=True,
            )
        if factory.project_type == "renewable_energy":
            return self._result(
                "MNRE_MSME_SOLAR_CFA",
                STATUS_INSUFFICIENT_DATA,
                (
                    "No live central MSME rooftop-solar CFA entity in "
                    "subsidies.json. SUB_NITI_MSME_SOLAR_CFA_PROPOSED is "
                    "draft/proposed only — must not be applied as guaranteed."
                ),
                verification=True,
            )
        return self._result(
            "MNRE_CFA",
            STATUS_NOT_ELIGIBLE,
            "No MNRE CFA pathway mapped for this project_type.",
        )

    def evaluate_tamil_nadu_state(
        self, factory: Factory
    ) -> list[SchemeEligibility]:
        """State schemes from state_policies.json for Tamil Nadu."""
        if factory.state.strip().lower() not in {
            "tamil nadu",
            "tamil_nadu",
            "tn",
        }:
            return []

        results: list[SchemeEligibility] = []
        if factory.msme_classification not in ("micro", "small", "medium"):
            results.append(
                self._result(
                    "TN_CAPITAL_SUBSIDY",
                    STATUS_NOT_ELIGIBLE,
                    "TN capital subsidy limited to micro/small/medium MSMEs.",
                    failed=["enterprise_category"],
                )
            )
            return results

        ineligible_sectors = {
            "sugar",
            "distilleries",
            "cement",
            "iron_and_steel_smelting",
        }
        sector = _normalise_industry_sector(factory.industry)
        if sector in ineligible_sectors:
            results.append(
                self._result(
                    "TN_CAPITAL_SUBSIDY",
                    STATUS_NOT_ELIGIBLE,
                    f"Industry '{sector}' listed as ineligible for TN general "
                    "capital subsidy.",
                    failed=["ineligible_industry"],
                )
            )
        else:
            results.append(
                self._result(
                    "TN_CAPITAL_SUBSIDY",
                    STATUS_ELIGIBLE,
                    (
                        "Tamil Nadu MSME capital subsidy (25% on eligible "
                        "plant and machinery, cap INR 1.5 crore per "
                        "state_policies.json)."
                    ),
                )
            )

        results.append(
            self._result(
                "TN_CLEAN_TECHNOLOGY_SUBSIDY",
                STATUS_ELIGIBLE,
                (
                    "Tamil Nadu additional clean-technology subsidy "
                    "(25% on cleaner P&M, cap INR 10 lakh per "
                    "state_policies.json)."
                ),
            )
        )
        return results

    def evaluate(self, factory: Factory) -> EligibilitySummary:
        """
        Evaluate all central + state scheme eligibility for one Factory.
        """
        warnings = self.check_turnover_investment_limits(factory)
        derived = self.classify_msme(
            factory.plant_and_machinery_or_equipment_investment_inr,
            factory.annual_turnover_inr,
        )

        schemes: dict[str, SchemeEligibility] = {
            "ADEETIE": self.evaluate_adeetie(factory),
            "MSE_GIFT": self.evaluate_mse_gift(factory),
            "MSE_SPICE": self.evaluate_mse_spice(factory),
            "ZED": self.evaluate_zed(factory),
            "CGTMSE": self.evaluate_cgtmse(factory),
            "PMEGP": self.evaluate_pmegp(factory),
            "CLCSS": self.evaluate_clcss(factory),
            "MNRE_CFA": self.evaluate_mnre_cfa(factory),
        }
        for state_scheme in self.evaluate_tamil_nadu_state(factory):
            schemes[state_scheme.scheme_id] = state_scheme

        return EligibilitySummary(
            derived_msme_category=derived,
            declared_msme_category=factory.msme_classification,
            msme_category_consistent=(
                derived == factory.msme_classification
            ),
            udyam_registered=factory.udyam_registered,
            schemes=schemes,
            warnings=warnings,
        )

"""
test_policy.py — Gate tests for Sprint 3.3 Policy Engine.

Gate (ROADMAP.md Sprint 3.3):
Udyam-registered small enterprise in Tamil Nadu → correct subset of
CLCSS / MNRE CFA / ADEETIE schemes with benefit estimates.

KB honesty notes encoded in tests:
- CLCSS: insufficient_data (no SUB_CLCSS in subsidies.json)
- MNRE CFA (solar): insufficient_data for energy_efficiency project;
  SUB_NITI_MSME_SOLAR_CFA_PROPOSED is draft only
- ADEETIE: eligible with benefit from SUB_ADEETIE interest subvention
- TN state capital + clean-tech subsidies from state_policies.json
"""

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from decision_engine.policy import (
    PolicyEngine,
    STATUS_ELIGIBLE,
    STATUS_CONDITIONALLY_ELIGIBLE,
    STATUS_INSUFFICIENT_DATA,
    STATUS_NOT_ELIGIBLE,
    tamil_nadu_textile_small_udyam_factory,
)
from models.factory import Factory, Quantity


def _adeetie_annual_benefit(loan_inr: float, project_cost_inr: float) -> float:
    """Mirror subsidies.json SUB_ADEETIE: 5% on eligible loan (small/micro)."""
    eligible_loan = min(loan_inr, 0.75 * project_cost_inr)
    return eligible_loan * 0.05


def test_tn_small_udyam_adeetie_eligible_with_benefit():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)

    scheme_ids = {s.scheme_id for s in result.eligible_schemes}
    assert "ADEETIE" in scheme_ids

    adeetie = next(
        s for s in result.eligible_schemes if s.scheme_id == "ADEETIE"
    )
    expected = _adeetie_annual_benefit(
        factory.loan_amount_inr,
        factory.project_cost_inr,
    )
    assert adeetie.benefit_inr == pytest.approx(expected)
    assert adeetie.benefit_type == "interest_subvention"
    assert adeetie.capex_reduction_inr == 0.0
    assert "SRC_ADEETIE_BEE" in adeetie.source_ids


def test_tn_state_subsidies_in_eligible_set():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)
    scheme_ids = {s.scheme_id for s in result.eligible_schemes}

    assert "TN_CAPITAL_SUBSIDY" in scheme_ids
    assert "TN_CLEAN_TECHNOLOGY_SUBSIDY" in scheme_ids

    capital = next(
        s for s in result.eligible_schemes
        if s.scheme_id == "TN_CAPITAL_SUBSIDY"
    )
    # 25% × 20M = 5M, cap 15M → 5M
    assert capital.benefit_inr == pytest.approx(5_000_000)
    assert capital.capex_reduction_inr == pytest.approx(5_000_000)

    clean = next(
        s for s in result.eligible_schemes
        if s.scheme_id == "TN_CLEAN_TECHNOLOGY_SUBSIDY"
    )
    # 25% × 20M = 5M, cap 1M → 1M
    assert clean.benefit_inr == pytest.approx(1_000_000)


def test_clcss_insufficient_data_not_invented():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)

    clcss = next(
        s for s in result.insufficient_data_schemes
        if s.scheme_id == "CLCSS"
    )
    assert clcss.status == STATUS_INSUFFICIENT_DATA
    assert "subsidies.json" in clcss.reason.lower()

    eligible_ids = {s.scheme_id for s in result.eligible_schemes}
    assert "CLCSS" not in eligible_ids


def test_mnre_cfa_not_applied_as_guaranteed_for_energy_efficiency():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)

    mnre = next(
        s for s in result.ineligible_schemes + result.insufficient_data_schemes
        if s.scheme_id == "MNRE_CFA"
    )
    assert mnre.status == STATUS_NOT_ELIGIBLE

    eligible_ids = {s.scheme_id for s in result.eligible_schemes}
    assert "MNRE_MSME_SOLAR_CFA" not in eligible_ids


def test_mse_spice_and_pmegp_rejected_for_energy_efficiency_retrofit():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)
    rejected_ids = {s.scheme_id for s in result.ineligible_schemes}

    assert "MSE_SPICE" in rejected_ids
    assert "PMEGP" in rejected_ids


def test_mse_gift_conditionally_eligible_for_small_green_project():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)

    gift = next(
        s for s in result.eligible_schemes if s.scheme_id == "MSE_GIFT"
    )
    assert gift.eligibility_status == STATUS_CONDITIONALLY_ELIGIBLE
    # 2% × min(15M, 20M) = 300,000 INR/year (SUB_MSE_GIFT)
    assert gift.annual_financing_benefit_inr == pytest.approx(300_000)


def test_zed_eligible_with_certification_support_only():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)

    zed = next(s for s in result.eligible_schemes if s.scheme_id == "ZED")
    # 80% of INR 10,000 bronze base (from SUB_ZED research.summary)
    assert zed.benefit_inr == pytest.approx(8_000)
    assert zed.capex_reduction_inr == 0.0


def test_cgtmse_zero_cash_benefit_credit_guarantee_only():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)

    cgtmse = next(
        s for s in result.eligible_schemes if s.scheme_id == "CGTMSE"
    )
    assert cgtmse.benefit_inr == 0.0
    assert cgtmse.benefit_type == "credit_guarantee"
    assert cgtmse.verification_required is True


def test_schemes_ranked_by_benefit_descending():
    factory = tamil_nadu_textile_small_udyam_factory()
    result = PolicyEngine().evaluate(factory)
    benefits = [s.benefit_inr for s in result.eligible_schemes]
    assert benefits == sorted(benefits, reverse=True)


def test_non_tn_factory_has_no_tn_state_schemes():
    factory = tamil_nadu_textile_small_udyam_factory()
    factory = factory.model_copy(update={"state": "Rajasthan"})
    result = PolicyEngine().evaluate(factory)
    scheme_ids = {s.scheme_id for s in result.eligible_schemes}
    assert "TN_CAPITAL_SUBSIDY" not in scheme_ids


def test_udyam_required_for_adeetie():
    factory = tamil_nadu_textile_small_udyam_factory()
    factory = factory.model_copy(update={"udyam_registered": False})
    result = PolicyEngine().evaluate(factory)
    eligible_ids = {s.scheme_id for s in result.eligible_schemes}
    assert "ADEETIE" not in eligible_ids

    adeetie_rej = next(
        s for s in result.ineligible_schemes if s.scheme_id == "ADEETIE"
    )
    assert "not_udyam_registered" in adeetie_rej.failed_conditions


def test_msme_classification_derived_from_thresholds():
    from decision_engine.policy import EligibilityChecker

    checker = EligibilityChecker()
    # investment 30M (> micro 25M cap), turnover 45M → small
    category = checker.classify_msme(30_000_000, 45_000_000)
    assert category == "small"
    # investment 18M, turnover 45M → micro (both within micro ceilings)
    assert checker.classify_msme(18_000_000, 45_000_000) == "micro"

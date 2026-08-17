"""
Policy Evaluation Engine — Sprint 3.3.

Public API
----------
PolicyEngine.evaluate(factory)  → PolicyEvaluationResult
EligibilityChecker            → scheme-level eligibility only
SubsidyMatcher                → benefit estimates from subsidies.json
"""

from decision_engine.policy.eligibility import (
    EligibilityChecker,
    EligibilitySummary,
    SchemeEligibility,
    STATUS_ELIGIBLE,
    STATUS_NOT_ELIGIBLE,
    STATUS_CONDITIONALLY_ELIGIBLE,
    STATUS_INSUFFICIENT_DATA,
)
from decision_engine.policy.policy_engine import (
    PolicyEngine,
    PolicyEvaluationResult,
    tamil_nadu_textile_small_udyam_factory,
)
from decision_engine.policy.subsidy_matcher import (
    SchemeBenefit,
    SubsidyMatcher,
    SubsidyMatchResult,
)

__all__ = [
    "EligibilityChecker",
    "EligibilitySummary",
    "PolicyEngine",
    "PolicyEvaluationResult",
    "SchemeBenefit",
    "SchemeEligibility",
    "SubsidyMatcher",
    "SubsidyMatchResult",
    "STATUS_ELIGIBLE",
    "STATUS_NOT_ELIGIBLE",
    "STATUS_CONDITIONALLY_ELIGIBLE",
    "STATUS_INSUFFICIENT_DATA",
    "tamil_nadu_textile_small_udyam_factory",
]

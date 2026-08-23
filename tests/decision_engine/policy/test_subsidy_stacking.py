import pytest
from unittest.mock import MagicMock
from decision_engine.policy.subsidy_matcher import SubsidyMatcher, SchemeBenefit

class TestSubsidyStacking:
    def setup_method(self):
        # We only test _validate_stacking so we don't need real JSONs
        self.matcher = SubsidyMatcher(
            central_path=None,
            state_path=None,
            subsidies_path=None
        )

    def _mock_benefit(
        self, scheme_id, group, rank, benefit_inr=1000.0
    ):
        return SchemeBenefit(
            scheme_id=scheme_id,
            display_name=scheme_id,
            eligibility_status="eligible",
            benefit_type="mock_type",
            benefit_inr=benefit_inr,
            capex_reduction_inr=benefit_inr,
            annual_financing_benefit_inr=0.0,
            eligible_cost_inr=benefit_inr * 2,
            calculation_notes="Mocked",
            source_ids=[],
            verification_required=False,
            financial_support_reference=None,
            policy_relevance_score=1.0,
            eligibility_confidence_score=1.0,
            verification_burden_score=1.0,
            ranking_score=rank,
            stackable=True,
            stack_group=group,
        )

    def test_two_schemes_same_group(self):
        """highest-ranked scheme survives in the same group."""
        factory = MagicMock()
        
        b1 = self._mock_benefit("S1", "group_A", rank=10)
        b2 = self._mock_benefit("S2", "group_A", rank=20) # higher rank

        stack_ok, notes, accepted = self.matcher._validate_stacking(
            factory, [b1, b2]
        )

        assert not stack_ok
        assert len(accepted) == 1
        assert accepted[0].scheme_id == "S2"
        # verification flag behavior check
        assert accepted[0].verification_required is True

    def test_schemes_different_groups(self):
        """schemes in different groups do not conflict."""
        factory = MagicMock()

        b1 = self._mock_benefit("S1", "group_A", rank=10)
        b2 = self._mock_benefit("S2", "group_B", rank=20)

        stack_ok, notes, accepted = self.matcher._validate_stacking(
            factory, [b1, b2]
        )

        assert stack_ok
        assert len(accepted) == 2
        assert {b.scheme_id for b in accepted} == {"S1", "S2"}
        assert accepted[0].verification_required is True
        assert accepted[1].verification_required is True

    def test_no_stack_group(self):
        """no stack group means no conflict."""
        factory = MagicMock()

        b1 = self._mock_benefit("S1", None, rank=10)
        b2 = self._mock_benefit("S2", None, rank=20)

        stack_ok, notes, accepted = self.matcher._validate_stacking(
            factory, [b1, b2]
        )

        assert stack_ok
        assert len(accepted) == 2
        assert {b.scheme_id for b in accepted} == {"S1", "S2"}

    def test_capital_subsidy_cross_conflict(self):
        """capital_subsidy_same_cost conflicts with state_capital_subsidy."""
        factory = MagicMock()

        b1 = self._mock_benefit("Central", "capital_subsidy_same_cost", rank=10)
        b2 = self._mock_benefit("State", "state_capital_subsidy", rank=20)

        stack_ok, notes, accepted = self.matcher._validate_stacking(
            factory, [b1, b2]
        )

        assert not stack_ok
        assert len(accepted) == 1
        assert accepted[0].scheme_id == "State"



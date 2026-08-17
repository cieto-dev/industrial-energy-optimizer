from pydantic import BaseModel
from typing import Optional

class FinancialModel(BaseModel):
    capex_gross_inr: float
    eligible_subsidy_inr: float
    interest_subvention_pct: float
    net_financed_cost_inr: float
    npv_inr: Optional[float] = None
    simple_payback_years: float

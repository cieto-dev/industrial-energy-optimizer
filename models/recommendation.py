from pydantic import BaseModel
from typing import List, Any
from datetime import datetime

class RejectedScenarioExplanation(BaseModel):
    scenario_id: str
    reason: str

class Explanation(BaseModel):
    why_selected: List[str]
    why_others_rejected: List[RejectedScenarioExplanation]

class Recommendation(BaseModel):
    factory_id: str
    recommended_scenario_id: str
    all_scenarios: List[Any]  # Placeholder for Scenario model, can be updated once Scenario is implemented
    explanation: Explanation
    sensitivity_notes: List[str]
    generated_at: datetime

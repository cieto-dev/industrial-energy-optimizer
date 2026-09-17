import sys
import json
from pathlib import Path

_PROJECT_ROOT = Path("/Users/adi/Desktop/industrial-energy-optimizer")
sys.path.insert(0, str(_PROJECT_ROOT))

from backend.apis.optimization_api import run_optimization, OptimizationRequest, FactoryProfileRequest
from decision_engine.policy.policy_engine import tamil_nadu_textile_small_udyam_factory

factory = tamil_nadu_textile_small_udyam_factory()
req_factory = FactoryProfileRequest(**factory.model_dump())
request = OptimizationRequest(factory=req_factory)

res = run_optimization(request)

with open("/Users/adi/Desktop/industrial-energy-optimizer/api_response.json", "w") as f:
    json.dump(res, f, indent=2)

print("Successfully wrote response to api_response.json")

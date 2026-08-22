from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError

from auth import get_current_user
from models.factory import Factory


router = APIRouter(
    prefix="/policies",
    tags=["Policies"]
)


class PolicyRequest(BaseModel):
    """
    Request wrapper for policy evaluation.

    The API request model is intentionally independent from the
    Factory domain model so the HTTP contract is not tightly coupled
    to the internal domain model.
    """

    factory: dict


@router.post("/evaluate")
def evaluate_policy(
    request: PolicyRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Evaluate policy eligibility using the supplied factory profile.
    """

    try:
        factory = Factory.model_validate(request.factory)

        from decision_engine.policy.policy_engine import PolicyEngine

        policy_engine = PolicyEngine()
        result = policy_engine.evaluate(factory)

        return {
            "status": "success",
            "factory": factory.model_dump(),
            "policy_evaluation": result.to_dict(),
            "message": "Policy evaluation completed"
        }

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Invalid factory data",
                "errors": exc.errors()
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Policy evaluation failed",
                "error": str(exc)
            }
        )
from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


@router.get("")
def health_check():
    """
    Check whether the backend service is running.
    """

    return {
        "status": "healthy",
        "service": "Industrial Energy Transition Optimizer",
        "version": "1.0"
    }
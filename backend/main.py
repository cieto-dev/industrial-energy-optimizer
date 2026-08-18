import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from logger import logger, generate_request_id

from apis.health_api import router as health_router
from apis.industry_api import router as industry_router
from apis.technology_api import router as technology_router
from apis.policy_api import router as policy_router
from apis.optimization_api import router as optimization_router
from apis.recommendation_api import router as recommendation_router
from apis.report_api import router as report_router
from apis.auth_api import router as auth_router


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Industrial Energy Transition Optimizer",
    description="Backend API for industrial energy transition optimization",
    version="1.0",
    debug=settings.DEBUG
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request ID Middleware
# --------------------------------------------------

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):

    request_id = generate_request_id()
    request.state.request_id = request_id

    logger.info(
        f"Request started | "
        f"request_id={request_id} | "
        f"method={request.method} | "
        f"path={request.url.path}"
    )

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    logger.info(
        f"Request completed | "
        f"request_id={request_id} | "
        f"status_code={response.status_code}"
    )

    return response


# --------------------------------------------------
# Register API Routers
# --------------------------------------------------

app.include_router(health_router)
app.include_router(industry_router)
app.include_router(technology_router)
app.include_router(policy_router)
app.include_router(optimization_router)
app.include_router(recommendation_router)
app.include_router(auth_router)
app.include_router(report_router)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Industrial Energy Transition Optimizer API",
        "status": "running",
        "version": "1.0"
    }
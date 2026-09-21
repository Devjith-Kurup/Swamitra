from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.routes_crop import router as crops_router
from app.api.routes_weather import router as weather_router
from app.api.routes_yield import router as yield_router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.services.crop_service import get_crop_service
from app.services.yield_service import get_yield_service
configure_logging(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML models on startup
    get_crop_service()
    get_yield_service()
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered agricultural decision-support API for Indian farmers.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(crops_router, prefix="/api/v1")
app.include_router(weather_router, prefix="/api/v1")
app.include_router(yield_router, prefix="/api/v1")

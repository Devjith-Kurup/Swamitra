from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered agricultural decision-support API for Indian farmers.",
)

app.include_router(health_router)

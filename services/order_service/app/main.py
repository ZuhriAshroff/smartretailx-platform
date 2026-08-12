import logging
import os

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import SERVICE_NAME
from app.consumers import start_order_consumers
from app.database import Base, engine
from app.routers import orders
from libs.common.db import wait_for_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("order_service")

app = FastAPI(
    title="SmartRetailX - Order Processing Service",
    description="Order lifecycle management with event-driven inventory reservation.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(orders.router)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting %s", SERVICE_NAME)
    wait_for_db(engine)
    Base.metadata.create_all(bind=engine)
    if os.getenv("DISABLE_CONSUMERS") != "1":
        start_order_consumers()
    logger.info("%s ready", SERVICE_NAME)


@app.get("/v1/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}

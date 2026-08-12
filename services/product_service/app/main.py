import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import SERVICE_NAME
from app.database import Base, engine
from app.routers import products
from libs.common.db import wait_for_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("product_service")

app = FastAPI(
    title="SmartRetailX - Product Catalogue Service",
    description="Product CRUD, search and pagination.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(products.router)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting %s", SERVICE_NAME)
    wait_for_db(engine)
    Base.metadata.create_all(bind=engine)
    logger.info("%s ready", SERVICE_NAME)


@app.get("/v1/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}

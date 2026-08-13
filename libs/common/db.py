"""Database connection helpers with startup retry logic.

Containers in docker-compose start in parallel, so the Postgres server for a
given service may not yet be accepting connections when the FastAPI app boots.
`wait_for_db` polls until the database is reachable before the app proceeds.
"""
from __future__ import annotations

import logging
import time

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("smartretailx.db")


def wait_for_db(engine: Engine, retries: int = 30, delay_seconds: float = 2.0) -> None:
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database is reachable after %d attempt(s)", attempt)
            return
        except OperationalError as exc:
            if attempt >= retries:
                logger.error("Database unreachable after %d attempts, giving up", attempt)
                raise
            logger.warning(
                "Database not ready (attempt %d/%d): %s. Retrying in %.1fs...",
                attempt, retries, exc, delay_seconds,
            )
            time.sleep(delay_seconds)

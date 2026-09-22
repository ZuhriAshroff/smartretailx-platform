"""Optional CORS middleware, enabled only when CORS_ALLOWED_ORIGINS is set.

Locally, the Nginx gateway (nginx/nginx.conf) sets CORS headers itself, so
services don't need this. On AWS, the frontend (S3 static website) and the
API (ALB) are different origins with no shared gateway in front of them, so
each service must set its own Access-Control-Allow-Origin.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors(app: FastAPI) -> None:
    origins = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    if not origins:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

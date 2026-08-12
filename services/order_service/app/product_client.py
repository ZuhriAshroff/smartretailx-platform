"""Secure service-to-service client for the Product Catalogue Service.

The customer's own bearer token is forwarded on the outbound request so the
Product Catalogue Service applies the exact same JWT/RBAC checks it would for
a direct client call - there is no separate service-account bypass.
"""
from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.config import PRODUCT_SERVICE_URL

logger = logging.getLogger("order_service.product_client")


class ProductNotFoundError(Exception):
    pass


def get_product(product_id: int, authorization_header: str) -> dict:
    url = f"{PRODUCT_SERVICE_URL}/v1/products/{product_id}"
    try:
        response = httpx.get(url, headers={"Authorization": authorization_header}, timeout=5.0)
    except httpx.RequestError as exc:
        logger.error("Product Catalogue Service unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product Catalogue Service is currently unavailable",
        ) from exc

    if response.status_code == 404:
        raise ProductNotFoundError(f"Product {product_id} not found")
    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    response.raise_for_status()
    return response.json()

#!/usr/bin/env python3
"""Seeds the SmartRetailX platform with demo data:

- One admin account and one customer account (plus a warehouse_staff account)
- 10 catalogue products across a few categories
- An inventory record for every product

Run this AFTER `docker-compose up --build` once all services report healthy:

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r scripts/requirements.txt
    python3 scripts/seed_data.py

The script talks directly to each service's published host port. It bootstraps
itself past the auth chicken-and-egg problem by minting a short-lived admin
JWT locally using the same shared JWT_SECRET_KEY every service trusts - this
mirrors how a trusted internal job/CLI would authenticate against these APIs.
"""
from __future__ import annotations

import os
import sys
import time

import jwt
import requests

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "smartretailx-super-secret-dev-key-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8004")

SERVICES_TO_WAIT_FOR = {
    "user_service": f"{USER_SERVICE_URL}/v1/health",
    "product_service": f"{PRODUCT_SERVICE_URL}/v1/health",
    "order_service": os.getenv("ORDER_SERVICE_URL", "http://localhost:8003") + "/v1/health",
    "inventory_service": f"{INVENTORY_SERVICE_URL}/v1/health",
    "notification_service": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8005") + "/v1/health",
}

ADMIN_EMAIL = "admin@smartretailx.com"
ADMIN_PASSWORD = "Admin123!"
CUSTOMER_EMAIL = "customer@smartretailx.com"
CUSTOMER_PASSWORD = "Customer123!"
STAFF_EMAIL = "staff@smartretailx.com"
STAFF_PASSWORD = "Staff123!"

PRODUCTS = [
    {"sku": "SR-ELEC-001", "name": "Wireless Noise-Cancelling Headphones", "category": "Electronics", "price": 89.99, "description": "Over-ear Bluetooth headphones with active noise cancellation."},
    {"sku": "SR-ELEC-002", "name": "4K Ultra HD Smart TV 55\"", "category": "Electronics", "price": 449.00, "description": "55-inch 4K smart television with HDR support."},
    {"sku": "SR-ELEC-003", "name": "Portable Bluetooth Speaker", "category": "Electronics", "price": 34.50, "description": "Compact waterproof speaker with 12-hour battery life."},
    {"sku": "SR-GROC-001", "name": "Organic Rolled Oats 1kg", "category": "Groceries", "price": 3.20, "description": "Whole grain rolled oats, organic certified."},
    {"sku": "SR-GROC-002", "name": "Extra Virgin Olive Oil 500ml", "category": "Groceries", "price": 6.75, "description": "Cold-pressed extra virgin olive oil."},
    {"sku": "SR-GROC-003", "name": "Fair Trade Ground Coffee 250g", "category": "Groceries", "price": 5.40, "description": "Medium roast, ethically sourced ground coffee."},
    {"sku": "SR-HOME-001", "name": "Stainless Steel Cookware Set", "category": "Home & Kitchen", "price": 129.99, "description": "10-piece stainless steel pots and pans set."},
    {"sku": "SR-HOME-002", "name": "Memory Foam Pillow", "category": "Home & Kitchen", "price": 22.00, "description": "Ergonomic memory foam pillow with cooling gel layer."},
    {"sku": "SR-FASH-001", "name": "Men's Waterproof Jacket", "category": "Fashion", "price": 74.99, "description": "Breathable waterproof jacket for outdoor use."},
    {"sku": "SR-FASH-002", "name": "Women's Running Shoes", "category": "Fashion", "price": 64.50, "description": "Lightweight running shoes with cushioned sole."},
]

DEFAULT_STOCK_QUANTITY = 100
DEFAULT_REORDER_LEVEL = 15


def wait_for_services(retries: int = 30, delay_seconds: float = 2.0) -> None:
    print("Waiting for all services to become healthy...")
    for name, url in SERVICES_TO_WAIT_FOR.items():
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    print(f"  [ok] {name} is healthy")
                    break
            except requests.RequestException:
                pass
            print(f"  [..] waiting for {name} (attempt {attempt}/{retries})")
            time.sleep(delay_seconds)
        else:
            print(f"  [!!] {name} never became healthy, aborting", file=sys.stderr)
            sys.exit(1)


def mint_bootstrap_admin_token() -> str:
    payload = {
        "sub": "0",
        "email": "bootstrap-seed-script@smartretailx.com",
        "role": "admin",
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_user_if_missing(bootstrap_token: str, email: str, password: str, full_name: str, role: str) -> None:
    response = requests.post(
        f"{USER_SERVICE_URL}/v1/users",
        json={"email": email, "password": password, "full_name": full_name, "role": role},
        headers={"Authorization": f"Bearer {bootstrap_token}"},
        timeout=5,
    )
    if response.status_code == 201:
        print(f"  [created] {role} account: {email}")
    elif response.status_code == 409:
        print(f"  [exists]  {role} account already present: {email}")
    else:
        print(f"  [error] failed to create {email}: {response.status_code} {response.text}", file=sys.stderr)


def login(email: str, password: str) -> str:
    response = requests.post(
        f"{USER_SERVICE_URL}/v1/auth/login", json={"email": email, "password": password}, timeout=5
    )
    response.raise_for_status()
    return response.json()["access_token"]


def seed_products(admin_token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {admin_token}"}
    created_products = []
    for product in PRODUCTS:
        response = requests.post(f"{PRODUCT_SERVICE_URL}/v1/products", json=product, headers=headers, timeout=5)
        if response.status_code == 201:
            print(f"  [created] product {product['sku']} - {product['name']}")
            created_products.append(response.json())
        elif response.status_code == 409:
            print(f"  [exists]  product already present: {product['sku']}")
            search = requests.get(
                f"{PRODUCT_SERVICE_URL}/v1/products", params={"q": product["sku"]}, headers=headers, timeout=5
            ).json()
            matches = [p for p in search["items"] if p["sku"] == product["sku"]]
            if matches:
                created_products.append(matches[0])
        else:
            print(f"  [error] failed to create product {product['sku']}: {response.status_code} {response.text}", file=sys.stderr)
    return created_products


def seed_inventory(admin_token: str, products: list[dict]) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    for product in products:
        response = requests.post(
            f"{INVENTORY_SERVICE_URL}/v1/inventory",
            json={
                "product_id": product["id"],
                "sku": product["sku"],
                "quantity_available": DEFAULT_STOCK_QUANTITY,
                "reorder_level": DEFAULT_REORDER_LEVEL,
            },
            headers=headers,
            timeout=5,
        )
        if response.status_code == 201:
            print(f"  [created] inventory for {product['sku']}: {DEFAULT_STOCK_QUANTITY} units")
        elif response.status_code == 409:
            # The inventory_service consumer may have already auto-created a
            # zero-stock row in reaction to the product.created event -
            # top it up to the demo stock quantity instead.
            patch_response = requests.patch(
                f"{INVENTORY_SERVICE_URL}/v1/inventory/{product['id']}",
                json={"quantity_delta": DEFAULT_STOCK_QUANTITY, "reorder_level": DEFAULT_REORDER_LEVEL},
                headers=headers,
                timeout=5,
            )
            if patch_response.status_code == 200:
                print(f"  [topped up] inventory for {product['sku']} (auto-provisioned by event consumer)")
            else:
                print(f"  [error] failed to top up inventory for {product['sku']}: {patch_response.status_code}", file=sys.stderr)
        else:
            print(f"  [error] failed to create inventory for {product['sku']}: {response.status_code} {response.text}", file=sys.stderr)


def main() -> None:
    # /v1/health isn't reachable through path-based routers that only expose
    # specific prefixes (e.g. the AWS ALB — only /v1/auth, /v1/products, etc.
    # are routed, not the bare health path), so this step only makes sense
    # against a target where every service's health endpoint is directly
    # reachable (local docker-compose). Skip it when seeding a remote/routed
    # deployment you've already confirmed is up some other way.
    if os.getenv("SKIP_HEALTH_CHECK") != "1":
        wait_for_services()

    print("\nBootstrapping accounts...")
    bootstrap_token = mint_bootstrap_admin_token()
    create_user_if_missing(bootstrap_token, ADMIN_EMAIL, ADMIN_PASSWORD, "Site Administrator", "admin")
    create_user_if_missing(bootstrap_token, STAFF_EMAIL, STAFF_PASSWORD, "Warehouse Operative", "warehouse_staff")
    create_user_if_missing(bootstrap_token, CUSTOMER_EMAIL, CUSTOMER_PASSWORD, "Demo Customer", "customer")

    print("\nLogging in as admin...")
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)

    print("\nSeeding products...")
    products = seed_products(admin_token)

    print("\nSeeding inventory...")
    seed_inventory(admin_token, products)

    print("\nDone. Demo accounts:")
    print(f"  admin:    {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  staff:    {STAFF_EMAIL} / {STAFF_PASSWORD}")
    print(f"  customer: {CUSTOMER_EMAIL} / {CUSTOMER_PASSWORD}")


if __name__ == "__main__":
    main()

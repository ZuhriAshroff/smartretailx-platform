# SmartRetailX — Distributed Microservices Platform

A cloud-native, event-driven implementation of the SmartRetailX case study: five
independent FastAPI microservices, each with its own PostgreSQL database,
communicating asynchronously over RabbitMQ and fronted by an Nginx API
gateway. Built to satisfy Task 2 (Distributed Microservices and API
Development) of the COMP60010 assignment, with supporting pieces for Tasks 3
(JWT/RBAC security), 4 (event-driven real-time sync) and 7 (monitoring).

## Architecture

```
                              ┌─────────────────┐
                              │  Nginx Gateway   │  :8080
                              │  (/v1/* routing) │
                              └─────────┬────────┘
              ┌───────────┬─────────────┼─────────────┬───────────┐
              │           │             │             │           │
        ┌─────▼────┐┌─────▼─────┐┌──────▼─────┐┌──────▼──────┐┌───▼────────┐
        │  User    ││  Product  ││   Order    ││  Inventory  ││Notification│
        │  :8001   ││  :8002    ││   :8003    ││   :8004     ││   :8005    │
        └─────┬────┘└─────┬─────┘└──────┬─────┘└──────┬──────┘└───┬────────┘
              │           │             │             │           │
        ┌─────▼────┐┌─────▼─────┐┌──────▼─────┐┌──────▼──────┐┌───▼────────┐
        │ user_db  ││product_db ││  order_db  ││inventory_db ││notif._db   │
        │ Postgres ││ Postgres  ││  Postgres  ││  Postgres   ││ Postgres   │
        └──────────┘└───────────┘└────────────┘└─────────────┘└────────────┘
                              │             │             │           │
                              └─────────────┴──────┬──────┴───────────┘
                                                    │
                                          ┌─────────▼─────────┐
                                          │      RabbitMQ      │
                                          │ topic exchange:     │
                                          │ smartretailx.events │
                                          └─────────────────────┘
```

Every service also exposes Swagger UI (`/docs`) and a Prometheus `/metrics`
endpoint directly, and is independently reachable on its own published port
for local development, in addition to being routed through the gateway.

### Event flow (RabbitMQ topic exchange `smartretailx.events`)

| Routing key               | Published by          | Consumed by            | Effect |
|----------------------------|------------------------|-------------------------|--------|
| `user.registered`          | User Management        | Notification            | Welcome notification |
| `product.created`          | Product Catalogue      | Inventory, Notification | Auto-provisions a zero-stock inventory row |
| `product.updated`          | Product Catalogue      | Notification            | Audit notification |
| `product.deleted`          | Product Catalogue      | Notification            | Audit notification |
| `order.created`            | Order Processing       | Inventory, Notification | Inventory attempts to reserve stock |
| `inventory.reserved`       | Inventory Management   | Order, Notification     | Order moves `pending` → `confirmed` |
| `inventory.insufficient`   | Inventory Management   | Order, Notification     | Order moves `pending` → `cancelled`; ops team alerted |
| `inventory.updated`        | Inventory Management   | Notification            | Audit notification |
| `inventory.low_stock`      | Inventory Management   | Notification            | Warehouse team alerted |
| `order.status_changed`     | Order Processing       | Notification            | Customer notified of status change |

The Notification Service binds its queue to the wildcard routing key `#`, so
it receives (and stores a record for) every event on the exchange - this is
its role as the platform's central fan-in for real-time updates.

Every consumer runs as a **daemon background thread started on FastAPI
startup**, with its own reconnect loop (`libs/common/rabbitmq.py`). Both the
database connection and the RabbitMQ connection are established with retry
logic (`libs/common/db.py`, `libs/common/rabbitmq.py`) because docker-compose
starts all containers in parallel - Postgres and RabbitMQ are frequently not
yet accepting connections when a service's `uvicorn` process boots.

### Order lifecycle

```
pending --(inventory.reserved)--> confirmed --(staff PATCH)--> shipped --(staff PATCH)--> delivered
   |
   +------(inventory.insufficient)--> cancelled
```

`pending → confirmed/cancelled` happens automatically and asynchronously via
RabbitMQ. `confirmed → shipped → delivered` are manual transitions performed
by `admin`/`warehouse_staff` via `PATCH /v1/orders/{id}/status`.

## Services

| Service               | Port | Responsibility |
|------------------------|------|-----------------|
| User Management        | 8001 | Registration, login, JWT issuance, RBAC user administration |
| Product Catalogue       | 8002 | Product CRUD, free-text search, pagination |
| Order Processing        | 8003 | Order placement/lifecycle, calls Product Catalogue for pricing, emits/consumes events |
| Inventory Management     | 8004 | Stock levels, reserves stock on new orders, restocking |
| Notification Service    | 8005 | Consumes every event, stores/"sends" notifications |

## Security model

- **JWT (HS256), shared secret** (`JWT_SECRET_KEY`) trusted by all five
  services - a token issued by User Management is verified statelessly by
  every other service (no per-request auth service round trip).
- **RBAC** with three roles: `customer`, `admin`, `warehouse_staff`, enforced
  via the `require_roles(...)` FastAPI dependency in `libs/common/security.py`.
- **Secure service-to-service calls**: when Order Processing needs a
  product's price, it forwards the *caller's own bearer token* to the Product
  Catalogue Service (`services/order_service/app/product_client.py`) rather
  than using a privileged bypass - the downstream service applies the exact
  same auth/RBAC checks it would for a direct client call.
- Passwords are hashed with bcrypt (`passlib`), never stored or logged in
  plaintext.

## Prerequisites

- Docker and Docker Compose (v2 `docker compose` or `docker-compose`)
- Python 3.11+ locally, only if you want to run `scripts/seed_data.py` or the
  test suites outside a container

## Running the platform

```bash
docker-compose up --build
```

This starts: 5 Postgres databases, RabbitMQ (management UI on
http://localhost:15672, default user/pass `smartretailx`/`smartretailx`), the
5 microservices, and the Nginx gateway on http://localhost:8080.

Wait for all five `/v1/health` checks to return `{"status": "ok"}` (or watch
the logs - each service logs `<name> ready` once its DB and RabbitMQ
connections succeed), then seed demo data:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
python3 scripts/seed_data.py
```

This creates an admin, a warehouse_staff, and a customer account, 10 catalogue
products across several categories, and a matching inventory record for each
(topping up whatever the `product.created` event consumer already
auto-provisioned). Demo credentials are printed at the end and are also listed
below:

| Role             | Email                          | Password      |
|------------------|----------------------------------|----------------|
| admin            | admin@smartretailx.com          | Admin123!      |
| warehouse_staff  | staff@smartretailx.com          | Staff123!      |
| customer         | customer@smartretailx.com       | Customer123!   |

### Monitoring stack (separate compose file)

```bash
docker-compose -f docker-compose.monitoring.yml up --build
```

- Prometheus: http://localhost:9090 (scrapes `/metrics` on all 5 services every 10s)
- Grafana: http://localhost:3000 (default admin/admin) - the "SmartRetailX
  Platform Overview" dashboard and Prometheus datasource are auto-provisioned.

This must be started *after* the main stack, since it joins the
`smartretailx_net` network created by `docker-compose.yml`.

### Postman collection

`postman/SmartRetailX.postman_collection.json` + `postman/SmartRetailX.postman_environment.json`
cover all 5 services (40 requests) through the gateway, including a deliberate
negative RBAC test per service (wrong role / missing token → expect
403/401). Import both files into Postman, select the "SmartRetailX Local"
environment, and run the three login requests in "1. User Management
Service" first - every other request depends on the `admin_token` /
`staff_token` / `customer_token` variables they set. Requires
`scripts/seed_data.py` to have been run first.

Can also be run headlessly via [Newman](https://www.npmjs.com/package/newman)
for CI or report evidence:

```bash
npx newman run postman/SmartRetailX.postman_collection.json \
  -e postman/SmartRetailX.postman_environment.json --delay-request 300
```

### API documentation

Every service publishes Swagger UI directly and via the gateway:

- Direct: http://localhost:8001/docs ... http://localhost:8005/docs
- Via gateway: http://localhost:8080/docs/user, `/docs/product`, `/docs/order`,
  `/docs/inventory`, `/docs/notification`

All REST routes are versioned under `/v1/`.

## Running the tests

Each service has its own isolated test suite (SQLite in-memory-on-disk DB,
RabbitMQ publishing mocked, no Docker required):

```bash
cd services/user_service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest tests -v
```

Repeat for `product_service`, `order_service`, `inventory_service`, and
`notification_service`. Every service has at least 5 unit tests (pure
CRUD/logic, no HTTP layer) and 3+ integration tests (via `TestClient`,
exercising auth/RBAC and the full request/response cycle), plus dedicated
tests that invoke each consumer's event handler directly to prove the
event-driven behaviour (stock reservation, order status transitions,
notification fan-out) without needing a live broker.

## Project layout

```
libs/common/            Shared JWT/RBAC, DB retry, and RabbitMQ helpers used by every service
services/<name>/app/    FastAPI app: main.py, config.py, database.py, models.py, schemas.py,
                         crud.py, events.py (publishers), consumers.py (subscribers), routers/
services/<name>/tests/  pytest suite (unit + integration) for that service
services/<name>/Dockerfile
nginx/nginx.conf         API gateway routing
monitoring/              Prometheus config + Grafana provisioning/dashboards
scripts/seed_data.py     Demo data seeding script
docker-compose.yml               Core platform (5 services, 5 databases, RabbitMQ, gateway)
docker-compose.monitoring.yml    Prometheus + Grafana (separate stack)
```

## Environment variables

See `.env.example` for the full list. Copy it to `.env` before customising:

```bash
cp .env.example .env
```

Key variables: `JWT_SECRET_KEY` (must be identical across all services - it
is), `RABBITMQ_URL`, `POSTGRES_USER`/`POSTGRES_PASSWORD` (one schema per
service, same credentials reused across the 5 Postgres containers for
simplicity).

## Notes on design choices

- **One database per service**: each service owns its schema exclusively;
  no service reaches into another's database directly. Order Processing's
  need for product pricing is satisfied by a synchronous, authenticated HTTP
  call, not a shared table.
- **Stateless JWT verification**: RBAC dependencies decode and check the
  token's `role` claim only - they do not look the user up in the database on
  every request, which is why a locally-minted bootstrap admin token (used by
  `scripts/seed_data.py`) works even before any user exists in the database.
  This is a deliberate, common microservices pattern; it does mean a
  revoked/deleted user's existing token remains valid until it expires.
- **Soft deletes for products** (`is_active` flag) rather than hard deletes,
  since orders reference product data by id and historical orders should
  remain intelligible.

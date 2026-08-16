# SmartRetailX Frontend

React + Vite + TypeScript + Tailwind CSS SPA covering both the customer storefront and the admin/staff back office, talking to the SmartRetailX microservices through the API gateway.

## Prerequisites

- Node.js 20+
- The SmartRetailX backend running locally (`docker-compose up --build` from the repo root) on `http://localhost:8080`, or a deployed API gateway/ALB URL.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if not using localhost:8080
npm run dev
```

Opens on `http://localhost:5173` by default.

## Build

```bash
npm run build
```

Outputs the production build to `frontend/dist/`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8080` | Base URL of the API gateway (local nginx gateway, or the AWS ALB DNS name in production) |

## Demo accounts

Seeded by `scripts/seed_data.py` at the repo root:

| Role | Email | Password |
|---|---|---|
| admin | admin@smartretailx.com | Admin123! |
| warehouse_staff | staff@smartretailx.com | Staff123! |
| customer | customer@smartretailx.com | Customer123! |

## Structure

```
src/
  api/            Axios client + one thin module per backend domain (auth, products, orders, inventory, users, notifications)
  auth/           AuthContext (JWT decode/store), PrivateRoute / RoleRoute guards
  components/     Shared UI: Layout/nav, Toast, Pagination, StatusBadge
  pages/          Customer pages: Login, Register, Products (browse + order builder), Orders (history), Notifications
  pages/admin/    Admin/staff pages: Orders (all orders + status transitions), Products (CRUD), Inventory (stock + low-stock alerts), Users (CRUD + roles)
```

Role gating: `admin` and `warehouse_staff` see the admin nav; inventory and order-status management are shared between them (matching the backend RBAC), while product and user management are admin-only.

## Docker (local dev / preview)

```bash
docker build -t smartretailx-frontend --build-arg VITE_API_BASE_URL=http://localhost:8080 .
docker run -p 8090:80 smartretailx-frontend
```

Serves the built SPA via nginx with client-side routing fallback (`nginx.conf`). Note the `VITE_API_BASE_URL` is baked in at build time (Vite env vars are compile-time), so rebuild the image if the API URL changes.

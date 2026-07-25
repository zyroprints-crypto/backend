# Zyro Prints — Backend

AI-powered multi-vendor printing marketplace backend. FastAPI + PostgreSQL +
SQLAlchemy 2.x, built with Clean Architecture (router → service → repository →
model) and dependency injection throughout.

## Quick start (Docker)

```bash
cp .env.example .env        # edit SECRET_KEY / REFRESH_SECRET_KEY at minimum
docker compose up --build
```

This starts: FastAPI (`:8000`), PostgreSQL, Redis, MinIO (S3-compatible
storage, console at `:9001`), a Celery worker, and Celery beat. Migrations run
automatically on container start (`alembic upgrade head`).

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

Seed demo data (admin/vendor/customer accounts + a sample product):

```bash
docker compose exec api python -m scripts.seed_data
```

## Local dev (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL/REDIS_URL at local services
alembic upgrade head
uvicorn app.main:app --reload
```

## Running tests

```bash
pytest tests/ -v
```

Tests run against an in-memory SQLite database for speed and isolation
(models use portable column types — see `app/common/db_types.py` — that
render as native `UUID`/`JSONB`/`ARRAY` on PostgreSQL and safe equivalents on
SQLite). Production always runs on PostgreSQL as specified.

## Project structure

```
app/
  core/            # config, db session, JWT/password security, Redis, Celery, logging, exceptions
  middleware/       # global error handler, rate limiting, request logging
  common/           # base ORM mixins, generic repository, pagination, response envelope,
                     # auth/role dependencies, S3-compatible storage, portable column types
  modules/
    auth/           # register, password login, OTP login, refresh, forgot/reset password
    users/          # profile, addresses
    vendors/        # store registration, profile, bank details, admin approve/suspend, geo "nearby"
    categories/      # hierarchical categories (supports Wedding Invitations > Royal Wedding, etc.)
    products/       # custom-print products + variants (stock, price, images, customization)
    documents/      # document upload + print-settings + INSTANT PRICING ENGINE (app/modules/documents/pricing.py)
    cart/           # cart, wishlist, favorite shops
    orders/         # checkout, order state machine, coupons, status history
    payments/       # gateway abstraction (Razorpay/Stripe/PhonePe) + COD, vendor settlements
    reviews/        # ratings, vendor replies, auto-recomputed vendor rating
    notifications/  # email/SMS/push records + Celery dispatch tasks
    ai/              # Zyro AI Smart Assistant endpoints (print-setting recommendation, product
                     # suggestions, chat, description generation)
    delivery/       # delivery task tracking (future-ready for platform delivery partners)
    admin/          # coupon management, user suspension, vendor approval listing, platform
                     # settings, audit log
    search/         # unified vendor + product search (ILIKE-based; swap for Elasticsearch at scale)
    analytics/      # vendor and platform dashboards
alembic/            # migration environment (imports all models for autogenerate)
scripts/seed_data.py
tests/
```

Every module follows the same layering:
`router.py` (HTTP + auth/role guards) → `service.py` (business logic, transactions)
→ `repository.py` (DB queries, extends `BaseRepository`) → `models.py` (SQLAlchemy) /
`schemas.py` (Pydantic request/response contracts).

## What's fully implemented

- JWT access + refresh tokens, OTP login/verification (Redis-backed), forgot/reset password
- Role-based access control (customer / vendor / delivery_partner / admin) via FastAPI dependencies
- Document-printing instant price calculator: color/B&W, paper size & GSM, copies, single/double
  side, spiral/staple binding, lamination, cover page, premium paper, express delivery surcharge
  — pure, unit-tested function in `app/modules/documents/pricing.py`
- Full order lifecycle with an explicit vendor-side status state machine
  (placed → accepted/rejected → printing → ready → out_for_delivery → delivered, plus pause/cancel)
- Coupon system (platform-wide or vendor-scoped, percentage discount, usage caps, min order, expiry)
- Soft delete + `created_at`/`updated_at` on every table via a shared mixin
- S3-compatible storage abstraction (works with AWS S3, MinIO, R2, Spaces) with upload validation
  (extension allowlist, size limit)
- Redis-backed rate limiting middleware, structured logging, global exception handling with a
  consistent `{success, message, data}` response envelope
- Celery + Redis for background work (document AI analysis, notification dispatch, vendor
  settlement batches, GST invoice generation hooks)

## What's intentionally a stub / extension point

Real-world "complete" here means these are correct, swappable interfaces with a working contract
— not fantasy implementations wired to nothing:

- **Payment gateways** (`app/modules/payments/gateways.py`): abstraction is real and used by the
  service layer; the actual Razorpay/Stripe/PhonePe SDK calls are placeholders — drop in
  credentials + SDK calls, the rest of the checkout flow doesn't change.
- **AI Smart Assistant** (`app/modules/ai/service.py`): endpoints and contracts are real and
  return sensible rule-based responses today; `_call_llm()` is the single point to wire to an
  actual LLM provider.
- **Notifications** (email/SMS/push): tasks and DB records are real; the actual SMTP/SMS/FCM SDK
  calls are marked with `# TODO`-style comments in `app/modules/notifications/tasks.py`.
- **Google Login**: schema included in spec but not wired — add a `google-auth` token verification
  call in `AuthService` following the same pattern as `verify_otp_and_login`.
- **Geo search** (`VendorRepository.nearby`): Python/haversine filtering, fine for hundreds of
  vendors. At scale, switch to PostGIS (`geography` column + `ST_DWithin`) — the repository method
  signature doesn't need to change.
- **Full-text search**: ILIKE-based today; swap `SearchService` internals for Elasticsearch/
  OpenSearch/Meilisearch behind the same interface.
- **File-type parsing** (real page counts for uploaded PDF/DOCX/PPTX): `documents/tasks.py`'s
  `analyze_document` task is where you'd add PyMuPDF/python-docx/python-pptx page-count extraction
  and content-safety scanning.

## Integration testing

`scripts/integration_check.py` boots the real backend (SQLite by default) plus
a throwaway Redis instance, applies actual Alembic migrations, and exercises
the API exactly the way the frontend's Axios services do — register, login,
refresh, OTP, vendor onboarding + admin approval, category/product creation,
search, cart, checkout, order listing, and error-response shapes. Useful as a
fast contract check whenever either side changes:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/integration_check.py
```

Requires `redis-server` on PATH (installed automatically in CI/Docker; on a
dev machine, `apt install redis-server` / `brew install redis`).

## Database migrations

The initial migration (`alembic/versions/fdc5b834c32f_initial_schema.py`)
already exists and creates all 21 domain tables — verified by applying it
against a live database in `scripts/integration_check.py`. Apply it with:

```bash
alembic upgrade head
```

For future schema changes:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Note: this project's models use custom portable column types
(`app/common/db_types.py`, for cross-Postgres/SQLite compatibility) which
`alembic revision --autogenerate` renders as fully-qualified but doesn't
auto-import — `alembic/script.py.mako` already accounts for this, but if you
hand-write a migration, remember to `import app.common.db_types`.

## Security notes

- Passwords hashed with bcrypt (passlib)
- Access tokens (short-lived) and refresh tokens (long-lived) are signed with **separate**
  secrets so a leaked access token can't be replayed as a refresh token
- All monetary amounts are stored as integer paise/cents to avoid floating-point rounding issues
- Soft delete everywhere — nothing is hard-deleted, supporting audit/recovery requirements
- Rate limiting is IP + fixed-window via Redis; swap for a gateway-level limiter (Kong, AWS WAF)
  at higher scale

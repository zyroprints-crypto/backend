"""
Zyro Prints backend entrypoint.
Run in dev with: uvicorn app.main:app --reload
Run in prod via the Dockerfile's CMD (gunicorn + uvicorn workers).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.maintenance_mode import MaintenanceModeMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

from app.modules.admin.router import router as admin_router
from app.modules.ai.router import router as ai_router
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.categories.router import router as categories_router
from app.modules.delivery.router import router as delivery_router
from app.modules.documents.router import router as documents_router
from app.modules.notifications.router import router as notifications_router
from app.modules.orders.router import router as orders_router
from app.modules.payments.router import router as payments_router
from app.modules.products.router import router as products_router
from app.modules.reviews.router import router as reviews_router
from app.modules.search.router import router as search_router
from app.modules.users.router import router as users_router
from app.modules.vendors.router import router as vendors_router

configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered multi-vendor printing marketplace backend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MaintenanceModeMiddleware)

register_exception_handlers(app)

API_PREFIX = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(vendors_router, prefix=API_PREFIX)
app.include_router(categories_router, prefix=API_PREFIX)
app.include_router(products_router, prefix=API_PREFIX)
app.include_router(documents_router, prefix=API_PREFIX)
app.include_router(cart_router, prefix=API_PREFIX)
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(payments_router, prefix=API_PREFIX)
app.include_router(reviews_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)
app.include_router(delivery_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME, "env": settings.ENV}

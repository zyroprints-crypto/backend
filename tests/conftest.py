"""
Pytest fixtures: in-memory SQLite engine (fast, no external services) wired
into the FastAPI dependency_overrides for get_db, plus a TestClient.
Note: production runs on PostgreSQL; SQLite is used here purely for fast,
isolated unit/integration tests of request/response and business-logic wiring.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
import app.modules.users.models  # noqa
import app.modules.vendors.models  # noqa
import app.modules.categories.models  # noqa
import app.modules.products.models  # noqa
import app.modules.documents.models  # noqa
import app.modules.cart.models  # noqa
import app.modules.orders.models  # noqa
import app.modules.payments.models  # noqa
import app.modules.reviews.models  # noqa
import app.modules.notifications.models  # noqa
import app.modules.delivery.models  # noqa
import app.modules.admin.models  # noqa

from app.main import app


@pytest.fixture()
def db_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

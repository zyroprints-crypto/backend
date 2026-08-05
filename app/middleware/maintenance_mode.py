"""
Blocks non-admin requests platform-wide when maintenance mode is enabled
(admin toggles this via PUT /api/v1/admin/maintenance-mode). Reads the
'role' claim straight out of the JWT — no DB user lookup — so this stays
cheap even though it runs on every request.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.database import SessionLocal
from app.core.security import decode_token

# Always reachable, even mid-maintenance: health checks, docs, admin's own
# endpoints (so an admin can log in and flip maintenance mode back off),
# and login/refresh (so an admin has a way to authenticate at all).
ALWAYS_ALLOWED_PREFIXES = (
    "/health", "/docs", "/redoc", "/openapi.json",
    "/api/v1/admin", "/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/otp",
)


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in ALWAYS_ALLOWED_PREFIXES):
            return await call_next(request)

        enabled, message = self._maintenance_state()
        if enabled:
            role = self._role_from_request(request)
            if role != "admin":
                return JSONResponse(status_code=503, content={"success": False, "message": message})

        return await call_next(request)

    def _maintenance_state(self) -> tuple[bool, str]:
        db = SessionLocal()
        try:
            from app.modules.admin.models import PlatformSetting
            rows = db.query(PlatformSetting).filter(
                PlatformSetting.key.in_(["maintenance_mode", "maintenance_message"]),
                PlatformSetting.is_deleted.is_(False),
            ).all()
            values = {row.key: row.value for row in rows}
            enabled = values.get("maintenance_mode") == "true"
            message = values.get("maintenance_message") or "Zyro Prints is temporarily down for maintenance. Please check back soon."
            return enabled, message
        except Exception:
            # If the settings table isn't reachable for any reason, fail
            # open rather than taking the whole platform down.
            return False, ""
        finally:
            db.close()

    def _role_from_request(self, request: Request) -> str | None:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return None
        token = auth_header[7:]
        try:
            payload = decode_token(token, token_type="access")
            return payload.get("role")
        except ValueError:
            return None

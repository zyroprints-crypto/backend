"""Domain-level exceptions. Raised by services, translated to HTTP by handlers in main.py."""


class AppError(Exception):
    """Base class for all predictable, handled application errors."""

    status_code: int = 400

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404


class AlreadyExistsError(AppError):
    status_code = 409


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class ValidationAppError(AppError):
    status_code = 422


class RateLimitedError(AppError):
    status_code = 429

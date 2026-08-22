"""Standardized domain/API exceptions.

Every error surfaced to an API client is one of these types. The DRF exception
handler (``apps.core.handlers``) renders them into a consistent envelope and
never leaks stack traces. HTTP status codes are attached so the handler can map
them without branching on isinstance in views.
"""

from __future__ import annotations

from typing import Any, Optional

from rest_framework import status
from rest_framework.exceptions import APIException


class BaseDomainError(APIException):
    """Root of the standardized error hierarchy."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_type = "SystemError"
    default_detail = "An error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        details: Optional[Any] = None,
        code: Optional[str] = None,
    ) -> None:
        self.message = message or self.default_detail
        self.details = details
        self.code = code
        super().__init__(detail=self.message)


class ValidationError(BaseDomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_type = "ValidationError"
    default_detail = "The submitted data is invalid."


class AuthenticationError(BaseDomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_type = "AuthenticationError"
    default_detail = "Authentication is required."


class AuthorizationError(BaseDomainError):
    status_code = status.HTTP_403_FORBIDDEN
    error_type = "AuthorizationError"
    default_detail = "You do not have permission to perform this action."


class NotFoundError(BaseDomainError):
    status_code = status.HTTP_404_NOT_FOUND
    error_type = "NotFoundError"
    default_detail = "The requested resource was not found."


class ConflictError(BaseDomainError):
    status_code = status.HTTP_409_CONFLICT
    error_type = "ConflictError"
    default_detail = "The request conflicts with the current state."


class BusinessRuleError(BaseDomainError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_type = "BusinessRuleError"
    default_detail = "The operation violates a business rule."


class ThrottledError(BaseDomainError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_type = "ThrottledError"
    default_detail = "Too many requests. Please slow down and retry later."


class SystemError(BaseDomainError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "SystemError"
    default_detail = "An unexpected system error occurred."

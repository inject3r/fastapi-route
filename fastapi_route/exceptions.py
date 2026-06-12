"""
HTTP exceptions and validation errors for FastAPI Route.

This module defines exception classes for:
1. HTTP errors that can be raised in route handlers (404, 403, etc.)
2. Route validation errors for build-time checking (duplicate routes, invalid handlers)

The HTTP exceptions follow FastAPI's convention and are automatically
converted to proper JSON responses by the exception handler.

The validation errors are used during the build process to ensure route
files are correctly structured before the application starts.
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# HTTP Exceptions (Runtime)
# ============================================================

class HTTPException(Exception):
    """
    HTTP exception that can be raised in route handlers.
    
    When raised, this exception is caught by the global exception handler
    and converted to a JSON response with the appropriate status code.
    
    Example:
        raise HTTPException(404, "User not found")
        raise HTTPException(403, "Access denied")
    
    Args:
        status_code: HTTP status code (e.g., 404, 403, 500)
        detail: Human-readable error message
        headers: Optional response headers to include
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.detail = detail or self._get_default_detail(status_code)
        self.headers = headers or {}
        super().__init__(self.detail)
    
    @staticmethod
    def _get_default_detail(status_code: int) -> str:
        """Get default detail message for standard status codes."""
        defaults = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
        }
        return defaults.get(status_code, "HTTP Error")


class BadRequestException(HTTPException):
    """400 Bad Request exception - request malformed or invalid."""
    def __init__(self, detail: str = "Bad Request", headers: Dict[str, str] = None):
        super().__init__(400, detail, headers)


class UnauthorizedException(HTTPException):
    """401 Unauthorized exception - authentication required."""
    def __init__(self, detail: str = "Unauthorized", headers: Dict[str, str] = None):
        super().__init__(401, detail, headers)


class ForbiddenException(HTTPException):
    """403 Forbidden exception - authenticated but not authorized."""
    def __init__(self, detail: str = "Forbidden", headers: Dict[str, str] = None):
        super().__init__(403, detail, headers)


class NotFoundException(HTTPException):
    """404 Not Found exception - resource does not exist."""
    def __init__(self, detail: str = "Not Found", headers: Dict[str, str] = None):
        super().__init__(404, detail, headers)


class MethodNotAllowedException(HTTPException):
    """405 Method Not Allowed exception - HTTP method not supported."""
    def __init__(self, detail: str = "Method Not Allowed", headers: Dict[str, str] = None):
        super().__init__(405, detail, headers)


class ConflictException(HTTPException):
    """409 Conflict exception - resource state conflict."""
    def __init__(self, detail: str = "Conflict", headers: Dict[str, str] = None):
        super().__init__(409, detail, headers)


# ============================================================
# Route Validation Errors (Build-time)
# ============================================================

@dataclass
class RouteValidationError:
    """
    Represents a route validation error discovered during build.
    
    These errors are collected and reported to the user before the
    build process completes, preventing broken routes from being deployed.
    
    Attributes:
        error_type: Categorized error type (e.g., DUPLICATE_ROUTE)
        message: Human-readable error description
        file_path: Source file where the error occurred
        details: Additional structured error data
    """
    error_type: str
    message: str
    file_path: Optional[Path] = None
    details: Dict[str, Any] = field(default_factory=dict)


class RouteStructureError(Exception):
    """
    Exception raised for route structure violations during build.
    
    Wraps multiple validation errors and formats them for display.
    """
    
    def __init__(self, errors: List[RouteValidationError]):
        self.errors = errors
        self.message = self._format_message()
        super().__init__(self.message)
    
    def _format_message(self) -> str:
        """Format all errors into a readable message."""
        lines = ["Route structure validation failed:"]
        for error in self.errors:
            lines.append(f"  - {error.error_type}: {error.message}")
            if error.file_path:
                lines.append(f"    File: {error.file_path}")
        return "\n".join(lines)


class DuplicateMethodError(RouteValidationError):
    """
    Duplicate HTTP method in the same route file.
    
    Example: Two GET functions defined in the same route.py file.
    """
    def __init__(self, file_path: Path, method: str, line_numbers: List[int]):
        super().__init__(
            error_type="DUPLICATE_METHOD",
            message=f"Duplicate '{method}' method defined at lines {line_numbers}",
            file_path=file_path,
            details={"method": method, "line_numbers": line_numbers}
        )


class DuplicateRouteError(RouteValidationError):
    """
    Duplicate route path with the same HTTP method across different files.
    
    Example: Two files both define GET /users (maybe in different groups).
    """
    def __init__(self, path: str, method: str, files: List[Path]):
        super().__init__(
            error_type="DUPLICATE_ROUTE",
            message=f"Duplicate route '{method} {path}' defined in multiple files",
            details={"path": path, "method": method, "files": [str(f) for f in files]}
        )


class InvalidHandlerError(RouteValidationError):
    """
    Invalid handler function signature.
    """
    def __init__(self, file_path: Path, handler_name: str, issue: str):
        super().__init__(
            error_type="INVALID_HANDLER",
            message=f"Invalid handler '{handler_name}': {issue}",
            file_path=file_path,
            details={"handler": handler_name, "issue": issue}
        )


class CircularGroupError(RouteValidationError):
    """
    Circular reference detected in route groups.
    
    Example: (group1)/(group2)/(group1) would cause infinite nesting.
    """
    def __init__(self, groups: List[str]):
        super().__init__(
            error_type="CIRCULAR_GROUP",
            message=f"Circular group reference detected: {' -> '.join(groups)}",
            details={"groups": groups}
        )
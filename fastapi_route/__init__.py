"""FastAPI Route - File-based routing for FastAPI"""

from .app import create_app, FastAPIRouterApp
from .version import __version__
from .routing.router import Router
from .request import Request
from .response import Response, JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from .exceptions import (
    HTTPException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    MethodNotAllowedException,
)

__all__ = [
    "create_app",
    "FastAPIRouterApp",
    "__version__",
    "Router",
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "HTTPException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "MethodNotAllowedException",
]
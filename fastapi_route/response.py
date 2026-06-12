"""
Custom Response classes that mimic FastAPI's Response interface.

This module provides response classes for returning different content types
from route handlers. While returning plain dictionaries or strings works
automatically, these classes give fine-grained control over status codes,
headers, and content types.

Available response types:
- Response: Base class for all responses
- JSONResponse: JSON-formatted responses (auto-detected from dict returns)
- HTMLResponse: HTML content with text/html content type
- PlainTextResponse: Plain text content
- RedirectResponse: HTTP redirects (302 by default)

Usage:
    from fastapi_route import HTMLResponse, RedirectResponse
    
    def GET(request: Request):
        return HTMLResponse(content="<h1>Hello</h1>")
    
    def GET(request: Request):
        return RedirectResponse(url="/login")
"""

from typing import Any, Dict, Optional, Union
import json


class Response:
    """
    Base Response class for all HTTP responses.
    
    This class provides the foundation for all custom response types,
    handling content rendering and ASGI integration.
    
    Attributes:
        content: Response body content (string, bytes, or any)
        status_code: HTTP status code (200, 404, 500, etc.)
        headers: Dictionary of response headers
        media_type: Content-Type header value
    """
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "text/plain"
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = media_type
    
    def render(self) -> bytes:
        """
        Render the response content to bytes for transmission.
        
        Handles conversion of various content types:
        - None -> empty bytes
        - bytes -> unchanged
        - str -> encoded to UTF-8
        - other -> converted to string then encoded
        
        Returns:
            Response body as bytes
        """
        if self.content is None:
            return b""
        if isinstance(self.content, bytes):
            return self.content
        if isinstance(self.content, str):
            return self.content.encode()
        return str(self.content).encode()
    
    async def __call__(self, scope, receive, send):
        """
        Make the response callable for ASGI integration.
        
        This method implements the ASGI interface, allowing the response
        to be used directly with ASGI servers.
        
        Args:
            scope: ASGI connection scope
            receive: ASGI receive channel
            send: ASGI send channel for the response
        """
        body = self.render()
        headers = [
            (b"content-type", self.media_type.encode()),
            (b"content-length", str(len(body)).encode()),
        ]
        for key, value in self.headers.items():
            headers.append((key.encode(), value.encode()))
        
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


class JSONResponse(Response):
    """
    JSON response with application/json content type.
    
    Automatically serializes Python objects to JSON. Note that returning
    a dict directly from a handler also creates a JSON response; this
    class is useful when you need to set custom status codes or headers.
    
    Example:
        return JSONResponse(
            content={"user": "alice"},
            status_code=201,
            headers={"X-Custom": "value"}
        )
    """
    
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            content=json.dumps(content, ensure_ascii=False, indent=2),
            status_code=status_code,
            headers=headers,
            media_type="application/json"
        )


class HTMLResponse(Response):
    """
    HTML response with text/html content type.
    
    Example:
        return HTMLResponse(content="<h1>Hello World</h1>")
    """
    
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/html"
        )


class PlainTextResponse(Response):
    """
    Plain text response with text/plain content type.
    
    Example:
        return PlainTextResponse(content="Hello, world!")
    """
    
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/plain"
        )


class RedirectResponse(Response):
    """
    HTTP redirect response.
    
    Sends a redirect to the specified URL with the given status code.
    Default status code is 302 (temporary redirect). Use 301 for permanent.
    
    Example:
        # Temporary redirect
        return RedirectResponse(url="/new-location")
        
        # Permanent redirect
        return RedirectResponse(url="/new-permanent", status_code=301)
    """
    
    def __init__(
        self,
        url: str,
        status_code: int = 302,
        headers: Optional[Dict[str, str]] = None,
    ):
        headers = headers or {}
        headers["Location"] = url
        super().__init__(
            content=f"Redirecting to {url}",
            status_code=status_code,
            headers=headers,
            media_type="text/plain"
        )
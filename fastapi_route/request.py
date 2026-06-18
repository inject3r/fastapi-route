"""
Custom Request object with security limits and FastAPI compatibility.

Provides a unified request interface for route handlers, abstracting away
the underlying ASGI/Starlette/FastAPI details. Supports same properties
and methods as FastAPI's Request with built-in size limits:

- method: HTTP method (GET, POST, etc.)
- url: Full request URL
- path: URL path
- query_params: Dictionary of query parameters
- headers: Dictionary of request headers
- body(): Raw request body as bytes (with size limit)
- json(): Parsed JSON body (with size limit)
- form(): Parsed form data (with size limit)

Security Features:
- Configurable max request body size
- Prevents DoS attacks via large payloads
- Graceful error handling for oversized requests
"""

from typing import Any, Dict, Optional, Union
from json import JSONDecodeError
import json
from urllib.parse import unquote


# Default 10MB limit to prevent DoS attacks
DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024


class PayloadTooLargeError(Exception):
    """Raised when request body exceeds configured size limit."""
    pass


class Request:
    """
    Custom Request class with security limits and FastAPI compatibility.
    
    This request object is created for each HTTP request and passed to
    route handlers. It provides convenient methods for accessing request
    data without exposing ASGI implementation details.
    
    Security:
    - Enforces max_body_size limit (default 10MB)
    - Raises PayloadTooLargeError when exceeded
    - Prevents memory exhaustion from large uploads
    
    Example:
        def GET(request: Request):
            name = request.query_params.get("name", "World")
            return {"message": f"Hello {name}"}
        
        async def POST(request: Request):
            try:
                data = await request.json()
                return {"received": data}
            except PayloadTooLargeError:
                return {"error": "Request body too large"}, 413
    """
    
    def __init__(self, scope: Dict[str, Any], max_body_size: int = DEFAULT_MAX_BODY_SIZE):
        """
        Initialize the request from an ASGI scope dictionary.
        
        Args:
            scope: ASGI scope containing request metadata
            max_body_size: Maximum allowed request body size in bytes (default 10MB)
        """
        self.scope = scope
        self.max_body_size = max_body_size
        self._fastapi_request = None  # Reference to original FastAPI request
        self._body = None              # Cached raw body bytes
        self._json_body = None         # Cached parsed JSON
        self._form_data = None         # Cached parsed form data
    
    @property
    def method(self) -> str:
        """Get the HTTP method of the request (GET, POST, PUT, etc.)."""
        return self.scope.get("method", "GET")
    
    @property
    def url(self) -> str:
        """
        Get the full request URL including scheme, host, port, and path.
        
        Returns:
            Full URL string (e.g., "http://localhost:8000/users/123")
        """
        scheme = self.scope.get("scheme", "http")
        server = self.scope.get("server", ["localhost", 8000])
        host = server[0] if isinstance(server, (list, tuple)) else "localhost"
        port = server[1] if isinstance(server, (list, tuple)) and len(server) > 1 else 8000
        path = self.scope.get("path", "/")
        return f"{scheme}://{host}:{port}{path}"
    
    @property
    def path(self) -> str:
        """Get the URL path of the request (e.g., "/users/123")."""
        return self.scope.get("path", "/")
    
    @property
    def query_params(self) -> Dict[str, str]:
        """
        Get query parameters as a dictionary.
        
        Returns:
            Dictionary mapping parameter names to values.
            Values are URL-decoded automatically.
        
        Example:
            Request to "/search?q=hello&page=2" returns {"q": "hello", "page": "2"}
        """
        query_string = self.scope.get("query_string", b"").decode()
        params = {}
        if query_string:
            for pair in query_string.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    params[key] = unquote(value)
        return params
    
    @property
    def headers(self) -> Dict[str, str]:
        """
        Get request headers as a dictionary.
        
        Returns:
            Dictionary with lowercased header names and string values.
        
        Example:
            {"content-type": "application/json", "authorization": "Bearer token"}
        """
        headers = {}
        for key, value in self.scope.get("headers", []):
            headers[key.decode().lower()] = value.decode()
        return headers
    
    async def body(self) -> bytes:
        """
        Get the raw request body as bytes with size limit enforcement.
        
        Enforces max_body_size to prevent DoS attacks via large payloads.
        
        Returns:
            Raw request body bytes
            
        Raises:
            PayloadTooLargeError: If body exceeds max_body_size
        """
        if self._body is None:
            if self._fastapi_request:
                self._body = await self._fastapi_request.body()
            else:
                self._body = b""
            
            # Check size limit
            if len(self._body) > self.max_body_size:
                raise PayloadTooLargeError(
                    f"Request body ({len(self._body)} bytes) exceeds limit ({self.max_body_size} bytes)"
                )
        
        return self._body
    
    async def json(self) -> Any:
        """
        Parse the request body as JSON with size limit enforcement.
        
        Enforces max_body_size limit before parsing JSON.
        
        Returns:
            Parsed JSON data (dict, list, str, int, etc.)
        
        Raises:
            PayloadTooLargeError: If body exceeds max_body_size
            ValueError: If body contains invalid JSON
        """
        if self._json_body is None:
            body = await self.body()  # Size check happens here
            if body:
                try:
                    self._json_body = json.loads(body.decode())
                except JSONDecodeError:
                    raise ValueError("Invalid JSON body")
            else:
                self._json_body = None
        return self._json_body
    
    async def form(self) -> Dict[str, str]:
        """
        Parse the request body as URL-encoded form data.
        
        Returns:
            Dictionary of form field names to values (URL-decoded)
        """
        if self._form_data is None:
            body = await self.body()
            self._form_data = {}
            if body:
                try:
                    decoded = body.decode()
                    for pair in decoded.split("&"):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            self._form_data[key] = unquote(value)
                except Exception:
                    pass
        return self._form_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a query parameter by key with optional default value.
        
        Args:
            key: Parameter name
            default: Value to return if parameter not found
        
        Returns:
            Parameter value or default
        """
        return self.query_params.get(key, default)
    
    def __getitem__(self, key: str) -> str:
        """
        Get a query parameter using bracket notation.
        
        Args:
            key: Parameter name
        
        Returns:
            Parameter value
        
        Raises:
            KeyError: If parameter not found
        """
        return self.query_params[key]
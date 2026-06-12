"""
Custom Request object that mimics FastAPI's Request interface.

This class provides a unified request interface for route handlers,
abstracting away the underlying ASGI/Starlette/FastAPI details.
It supports the same properties and methods as FastAPI's Request:

- method: HTTP method (GET, POST, etc.)
- url: Full request URL
- path: URL path
- query_params: Dictionary of query parameters
- headers: Dictionary of request headers
- body(): Raw request body as bytes
- json(): Parsed JSON body
- form(): Parsed form data

The custom request object is passed to route handlers instead of the
FastAPI request, allowing the framework to remain decoupled from FastAPI
internals and making it easier to swap the underlying server if needed.
"""

from typing import Any, Dict, Optional, Union
from json import JSONDecodeError
import json
from urllib.parse import unquote


class Request:
    """
    Custom Request class that provides a FastAPI-compatible interface.
    
    This request object is created for each incoming HTTP request and
    passed to route handlers. It provides convenient methods for accessing
    request data without exposing the underlying ASGI implementation.
    
    The request object supports both sync and async handlers, with body
    and JSON parsing available as async methods to avoid blocking.
    
    Example:
        def GET(request: Request):
            name = request.query_params.get("name", "World")
            return {"message": f"Hello {name}"}
        
        async def POST(request: Request):
            data = await request.json()
            return {"received": data}
    """
    
    def __init__(self, scope: Dict[str, Any]):
        """
        Initialize the request from an ASGI scope dictionary.
        
        Args:
            scope: ASGI scope containing request metadata
        """
        self.scope = scope
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
        Get the raw request body as bytes.
        
        This is an async method because reading the body may involve
        awaiting chunks from the network.
        
        Returns:
            Raw request body bytes
        """
        if self._body is None:
            if self._fastapi_request:
                self._body = await self._fastapi_request.body()
            else:
                self._body = b""
        return self._body
    
    async def json(self) -> Any:
        """
        Parse the request body as JSON.
        
        This is an async method that reads the body and parses it.
        
        Returns:
            Parsed JSON data (dict, list, str, int, etc.)
        
        Raises:
            ValueError: If the body contains invalid JSON
        """
        if self._json_body is None:
            body = await self.body()
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
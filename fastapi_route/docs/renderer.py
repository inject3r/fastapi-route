"""
Renders documentation as an ASGI endpoint for the FastAPI application.

This module provides the documentation renderer that generates HTML documentation
from collected route metadata. It includes caching to avoid regenerating the
documentation on every request when routes haven't changed.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from ..response import HTMLResponse
from .generator import DocsGenerator
from .collector import DocsCollector


class DocsRenderer:
    """
    ASGI endpoint for serving API documentation.
    
    This class is responsible for:
    - Generating documentation HTML from route metadata
    - Caching documentation data for performance
    - Detecting route changes to invalidate cache
    - Providing OpenAPI/Swagger compatible JSON output
    
    The renderer is designed to be efficient in development mode by
    caching the documentation until routes actually change.
    """
    
    def __init__(self, registry, custom_template: Optional[str] = None):
        """
        Initialize the documentation renderer.
        
        Args:
            registry: RouteRegistry containing all registered routes
            custom_template: Optional custom HTML template string to use
                            instead of the default template
        """
        self.registry = registry
        self.custom_template = custom_template
        self._cached_docs_data = None
        self._cached_routes_hash = None
    
    def _get_routes_hash(self) -> str:
        """
        Generate a hash of current routes to detect changes.
        
        This hash is based on route paths and HTTP methods only, not on
        handler implementations. This allows us to detect when new routes
        are added or existing routes are modified, triggering a documentation
        refresh.
        
        Returns:
            Hash string representing the current set of routes
        """
        routes = self.registry.get_all()
        # Create a stable representation of routes (sorted for consistency)
        route_strings = [f"{r.method}:{r.path}" for r in routes]
        return str(hash(tuple(sorted(route_strings))))
    
    async def __call__(self, request) -> HTMLResponse:
        """
        Handle the documentation request and return HTML response.
        
        This method is called when the user visits the /docs endpoint.
        It regenerates documentation only when routes have changed,
        using cached data otherwise for performance.
        
        Args:
            request: The FastAPI request object (may be None for static generation)
            
        Returns:
            HTMLResponse containing the generated documentation page
        """
        current_hash = self._get_routes_hash()
        
        # Only regenerate if routes have changed since last request
        if self._cached_docs_data is None or self._cached_routes_hash != current_hash:
            collector = DocsCollector(self.registry)
            self._cached_docs_data = collector.collect_all()
            self._cached_routes_hash = current_hash
        
        generator = DocsGenerator(self._cached_docs_data, self.custom_template)
        html = generator.generate_html()
        
        return HTMLResponse(content=html)
    
    def get_swagger_json(self) -> Dict[str, Any]:
        """
        Generate OpenAPI/Swagger compatible JSON specification.
        
        This method converts the collected route data into the OpenAPI 3.0
        format, which can be consumed by tools like Swagger UI, Postman,
        and other API clients.
        
        The generated spec includes:
        - API info (title, version, description)
        - All routes with their HTTP methods
        - Parameter definitions (path and query)
        - Basic response structure
        
        Returns:
            Dictionary containing OpenAPI 3.0 specification
        """
        # Ensure we have fresh data
        if self._cached_docs_data is None:
            collector = DocsCollector(self.registry)
            self._cached_docs_data = collector.collect_all()
        
        docs_data = self._cached_docs_data
        
        # Build OpenAPI root object
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": docs_data["info"]["name"],
                "version": docs_data["info"]["version"],
                "description": docs_data["info"].get("description", ""),
            },
            "paths": {},
        }
        
        # Build paths object from routes
        for route in docs_data["routes"]:
            path = route["path"]
            method = route["method"].lower()
            
            # Initialize path object if not already present
            if path not in openapi["paths"]:
                openapi["paths"][path] = {}
            
            # Add route to paths object
            openapi["paths"][path][method] = {
                "summary": route["handler_name"],
                "description": route["docstring"],
                "parameters": [
                    {
                        "name": p["name"],
                        "in": p["type"],
                        "required": p["required"],
                        "description": p.get("description", ""),
                    }
                    for p in route.get("parameters", [])
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                    }
                },
            }
        
        return openapi
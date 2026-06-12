"""
Core router class for programmatic route management.

This module provides an alternative to filesystem-based routing, allowing
routes to be defined programmatically in code. While file-based routing
is the primary feature of FastAPI Route, this class is available for
cases where dynamic route registration is needed.

Use cases for programmatic routing:
- Routes that need to be conditionally registered based on configuration
- Routes that are generated dynamically at runtime
- Testing and mocking scenarios
- Integration with existing code that expects programmatic registration
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from ..types import RouteInfo
from ..utils.logger import logger


class Router:
    """
    Programmatic router as an alternative to filesystem routing.
        
    This class allows adding routes directly in code rather than through
    the filesystem. It maintains a simple in-memory registry of routes
    that can be used alongside filesystem-discovered routes.

    The class is designed as a singleton (using class-level state) so that
    routes added from anywhere in the code are accessible globally.

    Note: For new projects, file-based routing is recommended for better
    organization and developer experience.
    """
    
    # Class-level route storage: method -> path -> RouteInfo
    _routes: Dict[str, Dict[str, RouteInfo]] = {}
    
    @classmethod
    def add_route(cls, method: str, path: str, handler: Any) -> None:
        """
        Add a route programmatically.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: URL path pattern (can contain {param} placeholders)
            handler: Callable function that handles the request
            
        Example:
            def my_handler(request):
                return {"message": "Hello"}
            
            Router.add_route("GET", "/hello", my_handler)
        """
        if method not in cls._routes:
            cls._routes[method] = {}
        
        route_info = RouteInfo(
            path=path,
            method=method,
            handler=handler,
            file_path=Path("<programmatic>"),
            is_dynamic="{" in path,
            param_names=[]  # Will be populated during scanning
        )
        
        cls._routes[method][path] = route_info
        logger.debug(f"Added programmatic route: {method.upper()} {path}")
    
    @classmethod
    def get_routes(cls) -> List[RouteInfo]:
        """
        Get all programmatically added routes.
        
        Returns:
            List of RouteInfo objects for all programmatic routes
        """
        routes = []
        for method_routes in cls._routes.values():
            routes.extend(method_routes.values())
        return routes
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear all programmatically added routes.
        
        This is primarily useful for testing to ensure a clean state
        between test cases. It resets the class-level route storage.
        """
        cls._routes = {}
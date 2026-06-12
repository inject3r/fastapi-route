"""
Context data provider for custom handlers (docs.py, not-found.py).

This module provides a clean, typed interface for custom handlers to access
application data including configuration, route information, and statistics.
The context object is passed to custom handlers to give them awareness of
the application state without exposing internal implementation details.
"""

from typing import Dict, Any, List
from pathlib import Path
from ..core.registry import RouteRegistry
from ..config.loader import ConfigLoader


class CustomHandlerContext:
    """
    Provides read-only access to application data for custom handlers.
    
    This context object is passed to custom handlers like docs.py and
    not-found.py, allowing them to access:
    - Application configuration (config dict)
    - Registered routes (all or filtered by method)
    - Route statistics (counts by method, dynamic vs static)
    - Project information (name, version)
    
    The context is designed to be safe and read-only - handlers cannot
    modify application state through this interface.
    """
    
    def __init__(self, registry: RouteRegistry):
        """
        Initialize context with route registry.
        
        Args:
            registry: RouteRegistry containing all registered routes
        """
        self.registry = registry
        self._config = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """
        Get application configuration as a dictionary.
        
        Returns:
            Dictionary containing key configuration values:
            - app_name: Application display name
            - debug: Debug mode flag
            - cors_enabled: CORS middleware status
            - route_dir: Routes directory path
            - docs_enabled: Documentation toggle
        """
        if self._config is None:
            config = ConfigLoader.load()
            self._config = {
                "app_name": config.app_name,
                "debug": config.debug,
                "cors_enabled": config.cors_enabled,
                "route_dir": config.route_dir,
                "docs_enabled": config.docs_enabled,
            }
        return self._config
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """
        Get all registered routes as a list of dictionaries.
        
        Each route dictionary contains:
        - path: URL path pattern (may contain {param} placeholders)
        - method: HTTP method (GET, POST, etc.)
        - is_dynamic: Whether the route has path parameters
        - param_names: List of dynamic parameter names
        - file_path: Source file where the route is defined
        
        Returns:
            List of route dictionaries
        """
        routes = []
        for route in self.registry.get_all():
            routes.append({
                "path": route.path,
                "method": route.method,
                "is_dynamic": route.is_dynamic,
                "param_names": route.param_names,
                "file_path": str(route.file_path),
            })
        return routes
    
    def get_routes_by_method(self, method: str) -> List[Dict[str, Any]]:
        """
        Get routes filtered by HTTP method.
        
        Args:
            method: HTTP method to filter by (case insensitive)
            
        Returns:
            List of route dictionaries for the specified method
        """
        routes = []
        for route in self.registry.get_all():
            if route.method.upper() == method.upper():
                routes.append({
                    "path": route.path,
                    "method": route.method,
                    "is_dynamic": route.is_dynamic,
                    "param_names": route.param_names,
                })
        return routes
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate and return route statistics.
        
        Returns:
            Dictionary containing:
            - total_routes: Total number of registered routes
            - dynamic_routes: Count of routes with path parameters
            - static_routes: Count of routes without path parameters
            - methods: Dictionary mapping method names to counts
        """
        routes = self.registry.get_all()
        methods = {}
        dynamic_count = 0
        
        for route in routes:
            method = route.method
            methods[method] = methods.get(method, 0) + 1
            if route.is_dynamic:
                dynamic_count += 1
        
        return {
            "total_routes": len(routes),
            "dynamic_routes": dynamic_count,
            "static_routes": len(routes) - dynamic_count,
            "methods": methods,
        }
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get high-level project information.
        
        Returns:
            Dictionary containing:
            - name: Application name from config
            - version: FastAPI Route package version
            - routes_count: Total number of registered routes
        """
        return {
            "name": self.config.get("app_name", "FastAPI Route App"),
            "version": self._get_version(),
            "routes_count": len(self.registry.get_all()),
        }
    
    def _get_version(self) -> str:
        """
        Get FastAPI Route package version.
        
        Returns:
            Version string (e.g., "0.1.1") or "0.1.1" if version cannot be read
        """
        try:
            from ..version import __version__
            return __version__
        except ImportError:
            return "0.1.1"
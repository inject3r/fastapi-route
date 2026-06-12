"""
Compiles route information into FastAPI-compatible format.

This module provides utilities for converting internal route representations
into structures that can be directly used by FastAPI for route registration.
It organizes routes by HTTP method for efficient registration.
"""

from typing import Dict, Any, List
from ..types import RouteInfo


class RouteCompiler:
    """
    Compiles routes for FastAPI registration.
    
    This class takes a list of RouteInfo objects and organizes them into
    a structure grouped by HTTP method. This makes it easy to register
    routes with FastAPI's method-specific decorators (app.get, app.post, etc.).
    
    The compiled output is a dictionary mapping HTTP methods to lists of
    route dictionaries containing the path, handler function, and metadata.
    """
    
    @staticmethod
    def compile_routes(routes: List[RouteInfo]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compile routes into a FastAPI-compatible structure grouped by method.
        
        Args:
            routes: List of RouteInfo objects to compile
            
        Returns:
            Dictionary mapping HTTP methods to lists of route dictionaries.
            Each route dictionary contains:
            - path: URL path pattern (may contain {param} placeholders)
            - handler: The route handler function
            - is_dynamic: Whether the route has path parameters
            - param_names: List of dynamic parameter names
            
        Example output:
            {
                "get": [
                    {"path": "/", "handler": <function>, "is_dynamic": False, "param_names": []},
                    {"path": "/users/{user_id}", "handler": <function>, "is_dynamic": True, "param_names": ["user_id"]}
                ],
                "post": [
                    {"path": "/users", "handler": <function>, "is_dynamic": False, "param_names": []}
                ]
            }
        """
        compiled: Dict[str, List[Dict[str, Any]]] = {
            "get": [],
            "post": [],
            "put": [],
            "patch": [],
            "delete": [],
        }
        
        for route in routes:
            method = route.method.lower()
            if method in compiled:
                compiled[method].append({
                    "path": route.path,
                    "handler": route.handler,
                    "is_dynamic": route.is_dynamic,
                    "param_names": route.param_names,  # List of parameter names
                })
        
        return compiled
"""
Route registry for storing and managing all discovered routes.

This module provides a central registry that stores RouteInfo objects
and provides methods for querying routes by various criteria. It handles
duplicate detection and maintains separate indexes for efficient lookups.
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from pathlib import Path

from ..types import RouteInfo
from ..utils.logger import logger


class RouteRegistry:
    """
    Central registry for storing and querying routes.
    
    The registry maintains multiple indexes:
    - Method -> Path -> RouteInfo (for fast lookups)
    - Flat list of all routes (for iteration)
    
    Features:
    - Duplicate detection with warnings
    - Method-based filtering
    - Dynamic route identification
    - Conflict detection for production builds
    """
    
    def __init__(self):
        """Initialize empty registry with method-based route storage."""
        # Nested dict: HTTP method -> URL path -> RouteInfo
        self._routes: Dict[str, Dict[str, RouteInfo]] = defaultdict(dict)
        # Flat list for simple iteration
        self._all_routes: List[RouteInfo] = []
    
    def register(self, route: RouteInfo) -> None:
        """
        Register a single route in the registry.
        
        If a route with the same method and path already exists, a warning
        is logged but the route is NOT added (to prevent overriding).
        
        Args:
            route: RouteInfo object containing route metadata
        """
        method = route.method.lower()
        path = route.path
        
        # Check for existing route with same method and path
        if path in self._routes[method]:
            existing = self._routes[method][path]
            logger.warning(
                f"Route conflict: {method.upper()} {path} already registered "
                f"from {existing.file_path}"
            )
        else:
            # Store the route in both indexes
            self._routes[method][path] = route
            self._all_routes.append(route)
            logger.debug(f"Registered route: {method.upper()} {path}")
    
    def get(self, method: str, path: str) -> Optional[RouteInfo]:
        """
        Retrieve a route by HTTP method and URL path.
        
        Args:
            method: HTTP method (GET, POST, etc.) - case insensitive
            path: URL path pattern
            
        Returns:
            RouteInfo object if found, None otherwise
        """
        return self._routes.get(method.lower(), {}).get(path)
    
    def get_all(self) -> List[RouteInfo]:
        """
        Get a copy of all registered routes.
        
        Returns:
            List of all RouteInfo objects in registration order
        """
        return self._all_routes.copy()
    
    def get_by_method(self, method: str) -> List[RouteInfo]:
        """
        Get all routes for a specific HTTP method.
        
        Args:
            method: HTTP method to filter by (case insensitive)
            
        Returns:
            List of RouteInfo objects matching the method
        """
        return list(self._routes.get(method.lower(), {}).values())
    
    def get_dynamic_routes(self) -> List[RouteInfo]:
        """
        Get all routes that contain dynamic path parameters.
        
        Dynamic routes have path parameters like /users/{user_id}.
        
        Returns:
            List of RouteInfo objects where is_dynamic is True
        """
        return [r for r in self._all_routes if r.is_dynamic]
    
    def has_route(self, method: str, path: str) -> bool:
        """
        Check whether a route exists for the given method and path.
        
        Args:
            method: HTTP method (case insensitive)
            path: URL path pattern
            
        Returns:
            True if route exists, False otherwise
        """
        return path in self._routes.get(method.lower(), {})
    
    def get_conflicts(self) -> List[Tuple[str, str, Path]]:
        """
        Detect duplicate routes (same method and path from different files).
        
        This is used during build to prevent ambiguous routing where
        two different route files would handle the same URL pattern.
        
        Returns:
            List of tuples (method, path, file_path) for each duplicate
            route that was found. The first occurrence is not included,
            only subsequent duplicates.
        """
        conflicts = []
        seen: Dict[Tuple[str, str], Path] = {}
        
        for route in self._all_routes:
            key = (route.method, route.path)
            if key in seen:
                # This is a duplicate - add to conflicts
                conflicts.append((route.method, route.path, route.file_path))
            else:
                # First time seeing this route
                seen[key] = route.file_path
        
        return conflicts
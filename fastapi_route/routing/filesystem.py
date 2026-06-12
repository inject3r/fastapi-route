"""
Filesystem-based router discovery for FastAPI Route.

This module provides the main interface for discovering routes from the
filesystem. It wraps the RouteScanner and provides convenient methods
for scanning and refreshing routes.
"""

from pathlib import Path
from typing import List

from ..core.scanner import RouteScanner
from ..types import RouteInfo
from ..utils.logger import logger


class FileSystemRouter:
    """
    Main router class for filesystem-based routing.
        
    This class serves as the primary interface for route discovery,
    wrapping the lower-level RouteScanner with convenience methods.
    Routes are defined by the file system structure rather than code annotations.

    Usage:
        router = FileSystemRouter("routes")
        routes = router.scan()      # Discover all routes
        routes = router.refresh()   # Force rescan
    """
    
    def __init__(self, routes_dir: str = "routes"):
        """
        Initialize the filesystem router.
        
        Args:
            routes_dir: Directory containing route files (relative to project root)
        """
        self.routes_dir = routes_dir
        self.scanner = RouteScanner(routes_dir)
    
    def scan(self) -> List[RouteInfo]:
        """
        Scan the filesystem and return all discovered routes.
        
        This method performs a fresh scan of the routes directory
        and returns all valid RouteInfo objects. Routes that fail
        to load (syntax errors, import errors) are recorded but
        not returned.
        
        Returns:
            List of RouteInfo objects for successfully loaded routes
        """
        return self.scanner.scan()
    
    def refresh(self) -> List[RouteInfo]:
        """
        Refresh and rescan routes, clearing any cached state.
        
        This method is useful during development when route files
        have been added, removed, or modified. It forces a complete
        rescan of the filesystem.
        
        Returns:
            List of RouteInfo objects after rescan
        """
        logger.info("Refreshing routes...")
        return self.scan()
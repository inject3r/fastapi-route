"""
Route validation and error checking system.

This module validates route structure and detects various types of conflicts:
- Duplicate HTTP methods within the same file
- Duplicate routes (same method and path) across different files
- Invalid handler function signatures
- Circular references in route groups

All validation errors are collected and can be reported to the user
with helpful error messages and line numbers.
"""

from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import re
import inspect

from ..types import RouteInfo
from ..exceptions import (
    RouteValidationError,
    DuplicateMethodError,
    DuplicateRouteError,
    InvalidHandlerError,
    CircularGroupError
)
from ..utils.logger import logger


class RouteValidator:
    """
    Validates route structure and detects conflicts across the route tree.
    
    This validator performs multiple validation passes:
    1. Per-file validation (duplicate methods, handler signatures)
    2. Cross-file validation (duplicate routes after path normalization)
    3. Route group validation (circular references in parentheses groups)
    
    Validation is non-destructive and collects all errors for reporting.
    """
    
    def __init__(self):
        """Initialize empty validator state."""
        self.errors: List[RouteValidationError] = []
        self._method_counts: Dict[Path, Dict[str, List[int]]] = {}
        self._route_map: Dict[Tuple[str, str], List[Tuple[Path, str]]] = {}
        self._group_hierarchy: Dict[str, List[str]] = {}
    
    def validate_all(self, routes: List[RouteInfo]) -> List[RouteValidationError]:
        """
        Validate all routes and return collected errors.
        
        This is the main entry point for validation. It performs all
        validation passes and returns a list of errors.
        
        Args:
            routes: List of RouteInfo objects to validate
            
        Returns:
            List of RouteValidationError objects (empty if no errors)
        """
        self.errors = []
        self._method_counts = {}
        self._route_map = {}
        self._group_hierarchy = {}
        
        # Group routes by source file for per-file validation
        routes_by_file: Dict[Path, List[RouteInfo]] = {}
        for route in routes:
            if route.file_path not in routes_by_file:
                routes_by_file[route.file_path] = []
            routes_by_file[route.file_path].append(route)
        
        # Per-file validation passes
        for file_path, file_routes in routes_by_file.items():
            self._validate_file_methods(file_path, file_routes)
            self._validate_handler_signatures(file_routes)
        
        # Cross-file validation passes
        self._validate_no_duplicate_routes(routes)
        self._validate_groups(routes)
        
        return self.errors
    
    def filter_valid_routes(self, routes: List[RouteInfo]) -> List[RouteInfo]:
        """
        Filter out problematic routes, keep only valid ones.
        
        This method removes routes that have validation errors, keeping
        only the first occurrence of duplicate routes and excluding
        routes from files with critical errors.
        
        Args:
            routes: Original list of RouteInfo objects
            
        Returns:
            Filtered list containing only valid routes
        """
        if not self.errors:
            return routes
        
        # Track which routes/paths to remove
        duplicate_keys: Set[Tuple[str, str]] = set()
        invalid_files: Set[Path] = set()
        
        for error in self.errors:
            if error.error_type == "DUPLICATE_ROUTE":
                path = error.details.get("path", "")
                method = error.details.get("method", "")
                duplicate_keys.add((method, path))
                # Mark all files involved in the duplicate
                files = error.details.get("files", [])
                for f in files:
                    if isinstance(f, str):
                        invalid_files.add(Path(f))
                    elif isinstance(f, Path):
                        invalid_files.add(f)
            elif error.error_type == "DUPLICATE_METHOD" and error.file_path:
                invalid_files.add(error.file_path)
            elif error.error_type == "INVALID_HANDLER" and error.file_path:
                invalid_files.add(error.file_path)
        
        # Filter the routes
        filtered = []
        seen_keys: Set[Tuple[str, str]] = set()
        
        for route in routes:
            key = (route.method, route.path)
            
            # Skip if the source file has validation errors
            if route.file_path in invalid_files:
                logger.warning(f"Skipping route from invalid file: {route.file_path}")
                continue
            
            # For duplicate routes, keep only the first occurrence
            if key in duplicate_keys:
                if key not in seen_keys:
                    seen_keys.add(key)
                    filtered.append(route)
                    logger.info(f"Keeping first occurrence of: {route.method} {route.path}")
                else:
                    logger.warning(f"Skipping duplicate: {route.method} {route.path} from {route.file_path}")
            else:
                filtered.append(route)
        
        return filtered
    
    def has_errors(self) -> bool:
        """Check if any validation errors exist."""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[RouteValidationError]:
        """Get all validation errors."""
        return self.errors
    
    def _validate_file_methods(self, file_path: Path, routes: List[RouteInfo]) -> None:
        """
        Check for duplicate HTTP methods within the same file.
        
        A single route file cannot have two handlers for the same HTTP method.
        For example, two GET functions in the same file is not allowed.
        
        Args:
            file_path: Path to the route file
            routes: List of routes from this file
        """
        method_lines: Dict[str, List[int]] = {}
        
        for route in routes:
            method = route.method
            try:
                # Attempt to get the line number where the handler is defined
                line_no = inspect.getsourcelines(route.handler)[1]
            except (OSError, TypeError):
                line_no = 0
            
            if method not in method_lines:
                method_lines[method] = []
            method_lines[method].append(line_no)
        
        # Report duplicates
        for method, lines in method_lines.items():
            if len(lines) > 1:
                error = DuplicateMethodError(file_path, method, lines)
                self.errors.append(error)
                logger.error(f"Duplicate {method} method in {file_path} at lines {lines}")
    
    def _validate_handler_signatures(self, routes: List[RouteInfo]) -> None:
        """
        Validate handler function signatures.
        
        All route handlers must accept at least one parameter (the request).
        More parameters (context, path params, query params) are optional.
        
        Args:
            routes: List of routes to validate
        """
        for route in routes:
            sig = inspect.signature(route.handler)
            params = list(sig.parameters.keys())
            
            if len(params) == 0:
                error = InvalidHandlerError(
                    route.file_path,
                    route.handler.__name__,
                    "Handler must accept at least 'request' parameter"
                )
                self.errors.append(error)
                logger.error(f"Invalid handler {route.handler.__name__} in {route.file_path}: missing request parameter")
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize a route path by removing group markers.
        
        This allows comparing routes that are functionally identical
        but organized in different groups.
        
        Example: "/(auth)/profile" and "/profile" both normalize to "/profile"
        
        Args:
            path: Original route path
            
        Returns:
            Normalized path with group markers removed
        """
        normalized = re.sub(r'\([^)]+\)', '', path)
        normalized = re.sub(r'/+', '/', normalized)
        if normalized != "/" and normalized.endswith("/"):
            normalized = normalized[:-1]
        return normalized if normalized else "/"
    
    def _validate_no_duplicate_routes(self, routes: List[RouteInfo]) -> None:
        """
        Check for duplicate routes across different files.
        
        Two routes with the same HTTP method and same normalized path
        (after removing group markers) are considered duplicates.
        
        Args:
            routes: List of all routes to check
        """
        route_map: Dict[Tuple[str, str], List[Tuple[Path, str]]] = {}
        
        for route in routes:
            normalized_path = self._normalize_path(route.path)
            key = (route.method, normalized_path)
            if key not in route_map:
                route_map[key] = []
            route_map[key].append((route.file_path, route.path))
        
        for (method, normalized_path), items in route_map.items():
            if len(items) > 1:
                original_paths = [orig for _, orig in items]
                files = [f for f, _ in items]
                
                error = DuplicateRouteError(normalized_path, method, files)
                self.errors.append(error)
                logger.error(
                    f"Duplicate route {method} {normalized_path} defined in: "
                    f"{[str(f) for f in files]} from paths: {original_paths}"
                )
    
    def _validate_groups(self, routes: List[RouteInfo]) -> None:
        """
        Validate route groups for circular references.
        
        Detects cycles in group nesting like: (group1)/(group2)/(group1)
        which would cause infinite recursion.
        
        Args:
            routes: List of all routes to check
        """
        # Build group relationship graph
        groups: Dict[str, List[str]] = {}
        
        for route in routes:
            # Extract all group names from the path
            group_pattern = r'\(([^)]+)\)'
            matches = re.findall(group_pattern, route.path)
            
            # Build parent-child relationships
            for i, group in enumerate(matches):
                if i < len(matches) - 1:
                    parent = matches[i]
                    child = matches[i + 1]
                    if parent not in groups:
                        groups[parent] = []
                    if child not in groups[parent]:
                        groups[parent].append(child)
        
        # Detect cycles using DFS
        visited = set()
        recursion_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            recursion_stack.add(node)
            path.append(node)
            
            for neighbor in groups.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in recursion_stack:
                    cycle_path = path + [neighbor]
                    error = CircularGroupError(cycle_path)
                    self.errors.append(error)
                    logger.error(f"Circular group reference: {' -> '.join(cycle_path)}")
                    return True
            
            recursion_stack.remove(node)
            path.pop()
            return False
        
        for group in groups:
            if group not in visited:
                has_cycle(group, [])
    
    def print_errors(self) -> None:
        """
        Print all validation errors to console in a formatted, readable way.
        
        This is used during build to give users clear feedback about what
        needs to be fixed in their route definitions.
        """
        if not self.errors:
            print("No validation errors found.")
            return
        
        print("\n" + "=" * 60)
        print("ROUTE VALIDATION ERRORS")
        print("=" * 60)
        
        for error in self.errors:
            print(f"\n[{error.error_type}]")
            print(f"  {error.message}")
            if error.file_path:
                print(f"  File: {error.file_path}")
            if error.details:
                print(f"  Details: {error.details}")
        
        print("\n" + "=" * 60)
        print(f"Total: {len(self.errors)} error(s)")
        print("=" * 60 + "\n")
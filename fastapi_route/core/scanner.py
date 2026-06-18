"""
File system scanner with detailed error reporting.

Scans routes directory recursively, discovers route files, and extracts HTTP
method handlers. Supports dynamic routes, catch-all routes, and route groups.

Error Handling:
- Static analysis (syntax checking) before import
- Detailed error messages with file/line context
- Graceful recovery from individual route failures
- Aggregated error reporting
"""

import importlib.util
import sys
import re
import traceback
import ast
from pathlib import Path
from typing import List, Optional, Tuple

from ..types import RouteInfo
from ..constants import (
    ROUTE_FILES, PARAM_DIR_PREFIX, PARAM_DIR_SUFFIX,
    GROUP_DIR_PREFIX, GROUP_DIR_SUFFIX, HTTP_METHODS
)
from ..utils.logger import logger
from .validator import RouteValidator


class RouteScanner:
    """
    Scans filesystem and discovers route modules with detailed error reporting.
    
    The scanner walks through the routes directory, identifies route files,
    and extracts HTTP method handlers (GET, POST, PUT, etc.). Supports:
    - Static routes: routes/about/route.py → /about
    - Dynamic routes: routes/users/[user_id]/route.py → /users/{user_id}
    - Catch-all routes: routes/docs/[...slug]/route.py → /docs/{slug}
    - Route groups: routes/(auth)/profile/route.py → /profile
    
    Error Reporting:
    - Syntax errors with line numbers and context
    - Import errors with detailed tracebacks
    - Validation errors with specific field information
    - All errors are aggregated and reported before failing
    """
    
    def __init__(self, routes_dir: str = "routes"):
        """
        Initialize scanner with routes directory path.
        
        Args:
            routes_dir: Directory containing route files (relative to project root)
        """
        self.routes_dir = Path(routes_dir)
        self._failed_routes: List[Tuple[str, Path, str]] = []
        self.validator = RouteValidator()
        self._has_critical_errors = False
    
    def scan(self) -> List[RouteInfo]:
        """
        Scan routes directory and return all discovered valid routes.
        
        Returns:
            List of RouteInfo objects for all successfully loaded routes.
            Returns empty list if any critical errors are found.
        """
        # Early exit if routes directory doesn't exist
        if not self.routes_dir.exists():
            logger.warning(f"Routes directory not found: {self.routes_dir}")
            return []
        
        routes = []
        self._failed_routes = []
        self._has_critical_errors = False
        
        # Walk through all Python files in routes directory
        for file_path in self.routes_dir.rglob("*.py"):
            if file_path.name in ROUTE_FILES:
                # First pass: validate file structure without importing
                file_errors = self._validate_file_structure(file_path)
                if file_errors:
                    route_path = self._build_route_path(file_path)
                    for error in file_errors:
                        self._failed_routes.append((route_path, file_path, error))
                    self._has_critical_errors = True
                    continue
                
                # Second pass: actually import and extract handlers
                discovered, has_error = self._process_route_file(file_path)
                routes.extend(discovered)
                if has_error:
                    self._has_critical_errors = True
        
        # Final validation pass for cross-file conflicts
        validation_errors = self.validator.validate_all(routes)
        
        if validation_errors:
            self.validator.print_errors()
            logger.error(f"Route validation found {len(validation_errors)} issues - build aborted")
            self._has_critical_errors = True
            # Prevent broken builds - don't return any routes if validation fails
            return []
        
        # Report any failed routes
        if self._failed_routes:
            logger.error(f"Failed to load {len(self._failed_routes)} route files:")
            for route_path, file_path, error_msg in self._failed_routes:
                logger.error(f"  ✗ {route_path}: {error_msg}")
            logger.error("Cannot proceed - fix the errors above and try again")
            return []
        
        if routes:
            logger.info(f"✓ Discovered {len(routes)} routes successfully")
        else:
            logger.warning("No routes found in directory")
        
        return routes
    
    def has_critical_errors(self) -> bool:
        """Check if there are critical errors that prevent building."""
        return self._has_critical_errors or len(self._failed_routes) > 0
    
    def _validate_file_structure(self, file_path: Path) -> List[str]:
        """
        Validate file structure using static analysis (no imports).
        
        Checks:
        - Duplicate function names (e.g., two GET handlers)
        - Python syntax errors with detailed context
        
        Args:
            file_path: Path to the route file
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse abstract syntax tree
            tree = ast.parse(content, filename=str(file_path))
            
            # Track function names to detect duplicates
            function_names = {}
            http_methods_upper = [m.upper() for m in HTTP_METHODS]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    if func_name in http_methods_upper:
                        if func_name in function_names:
                            line_no = node.lineno
                            prev_line = function_names[func_name]
                            errors.append(
                                f"Duplicate {func_name} handler at lines {prev_line} and {line_no}"
                            )
                        else:
                            function_names[func_name] = node.lineno
            
            # Check for Python syntax errors
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                error_msg = f"Syntax error line {e.lineno}: {e.msg}"
                if e.text:
                    error_msg += f"\n  {e.text.rstrip()}"
                    if e.offset:
                        error_msg += f"\n  {' ' * (e.offset - 1)}^"
                errors.append(error_msg)
                    
        except Exception as e:
            errors.append(f"Failed to read file: {str(e)}")
        
        return errors
    
    def get_failed_routes(self) -> List[Tuple[str, Path, str]]:
        """
        Get list of routes that failed to load.
        
        Returns:
            List of tuples (url_path, file_path, error_message)
        """
        return self._failed_routes
    
    def get_validation_errors(self):
        """Get validation errors from the RouteValidator."""
        return self.validator.get_errors()
    
    def _process_route_file(self, file_path: Path) -> Tuple[List[RouteInfo], bool]:
        """
        Process a single route file and extract HTTP method handlers.
        
        Args:
            file_path: Path to the route file
            
        Returns:
            Tuple of (discovered_routes, has_error)
        """
        routes = []
        has_error = False
        
        # Build URL path from folder structure
        route_path = self._build_route_path(file_path)
        
        # Import the module dynamically
        module, error_msg = self._import_module(file_path)
        if module is None:
            self._failed_routes.append((route_path, file_path, error_msg))
            return routes, True
        
        # Look for HTTP method handlers (GET, POST, PUT, PATCH, DELETE)
        for method in HTTP_METHODS:
            try:
                handler = getattr(module, method.upper(), None)
                if handler and callable(handler):
                    # Extract dynamic parameter names from path
                    param_names = re.findall(r"\{([^}]+)\}", route_path)
                    
                    route_info = RouteInfo(
                        path=route_path,
                        method=method.upper(),
                        handler=handler,
                        file_path=file_path,
                        is_dynamic=len(param_names) > 0,
                        param_names=param_names
                    )
                    routes.append(route_info)
                    logger.debug(f"Found route: {method.upper()} {route_path}")
            except Exception as e:
                logger.error(f"Error processing {method.upper()} in {file_path}: {e}")
                continue
        
        return routes, has_error
    
    def _import_module(self, file_path: Path) -> Tuple[Optional[object], str]:
        """
        Dynamically import a Python module with proper error handling.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Tuple of (imported_module, error_message)
        """
        try:
            # Build module name from file path
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = file_path
            
            module_name = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")
            
            # Pre-flight syntax check
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                error_msg = f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
                if e.text:
                    error_msg += f"\n{e.text}\n{' ' * (e.offset or 0)}^"
                return None, error_msg
            
            # Clear cached module if present (for hot reload)
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Create and execute module spec
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return None, f"Failed to create module spec for {file_path}"
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            return module, ""
            
        except Exception as e:
            tb = traceback.format_exc()
            return None, f"Unexpected error: {type(e).__name__}: {str(e)}\n{tb}"
    
    def _build_route_path(self, file_path: Path) -> str:
        """
        Convert file path to URL route path.
        
        Handles:
        - Normal directories: api/users -> /api/users
        - Dynamic params: [user_id] -> {user_id}
        - Cache-all params: [...slug] -> {slug}
        - Route groups: (auth) -> (ignored, doesn't affect URL)
        
        Args:
            file_path: Path to the route file
            
        Returns:
            URL path pattern (e.g., /users/{user_id})
        """
        try:
            relative = file_path.relative_to(self.routes_dir)
        except ValueError:
            return "/"
        
        # Get directory path components (excluding the filename)
        parts = list(relative.parts)
        if parts:
            parts = parts[:-1]  # Remove the filename
        
        # Transform each component
        url_parts = []
        for part in parts:
            # Dynamic parameter: [user_id] -> {user_id}
            if part.startswith(PARAM_DIR_PREFIX) and part.endswith(PARAM_DIR_SUFFIX):
                # Cache-all parameter: [...slug] -> {slug}
                if part.startswith("[...") and part.endswith("]"):
                    param_name = part[4:-1]
                    url_parts.append(f"{{{param_name}}}")
                # Regular dynamic parameter
                else:
                    param_name = part[1:-1]
                    url_parts.append(f"{{{param_name}}}")
            # Route group: (auth) - ignored, doesn't affect URL
            elif part.startswith(GROUP_DIR_PREFIX) and part.endswith(GROUP_DIR_SUFFIX):
                continue
            # Normal directory
            else:
                url_parts.append(part)
        
        # Build final path
        if not url_parts:
            return "/"
        
        return "/" + "/".join(url_parts)
"""
Parses route files and extracts route information via static analysis.

This module provides static parsing of route Python files using the AST
(Abstract Syntax Tree) module. It extracts decorator-based route definitions
without executing the code, which is useful for documentation generation
and route discovery in environments where dynamic import is not possible.

Note: FastAPI Route primarily uses file-based routing (folder structure)
rather than decorator-based routing. This parser exists for compatibility
with decorator-style route definitions and for documentation extraction.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..utils.logger import logger


class RouteParser:
    """
    Parses route.py files statically using AST analysis.
    
    This parser extracts route information from Python files without
    executing them. It looks for decorated functions with HTTP method
    decorators (@get, @post, @put, @patch, @delete).
    
    The parser is useful for:
    - Generating documentation without importing code
    - Validating route structure before import
    - Detecting decorator-based routes in legacy code
    
    Note: For new projects, file-based routing (folder structure) is
    the recommended approach over decorator-based routing.
    """
    
    @staticmethod
    def parse_route_file(file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse a route file and extract decorator-based route information.
        
        Args:
            file_path: Path to the Python route file
            
        Returns:
            List of route dictionaries, each containing:
            - method: HTTP method (get, post, put, patch, delete)
            - path: URL path pattern
            - handler: Name of the handler function
            
        Example:
            Given a file with:
                @get("/users")
                def get_users():
                    pass
            
            Returns: [{"method": "get", "path": "/users", "handler": "get_users"}]
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the abstract syntax tree
            tree = ast.parse(content)
            routes = []
            
            # Walk through all function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check each decorator on the function
                    for decorator in node.decorator_list:
                        route_info = RouteParser._parse_decorator(decorator, node.name)
                        if route_info:
                            routes.append(route_info)
            
            return routes
        
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    @staticmethod
    def _parse_decorator(decorator: ast.expr, func_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse a decorator AST node to extract route information.
        
        Supports decorators in the form:
        - @get("/path")
        - @post("/path")
        - @put("/path")
        - @patch("/path")
        - @delete("/path")
        
        Args:
            decorator: AST node representing the decorator
            func_name: Name of the function being decorated
            
        Returns:
            Route dictionary or None if the decorator is not a valid
            HTTP method decorator
        """
        # Handle @get("/path") style decorators (Call nodes)
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                method = decorator.func.id.lower()
                # Check if it's a valid HTTP method
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    path = "/"
                    # Extract the path argument
                    for arg in decorator.args:
                        # Handle Python 3.7 and below (ast.Str)
                        if isinstance(arg, ast.Str):
                            path = arg.s
                        # Handle Python 3.8+ (ast.Constant)
                        elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            path = arg.value
                    
                    return {
                        "method": method,
                        "path": path,
                        "handler": func_name
                    }
        
        return None
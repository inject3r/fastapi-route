"""
Validate custom handler files (not-found.py and docs.py).

This module validates the structure and content of user-defined custom handler
files before they are loaded. It checks for:
- Valid Python syntax
- Required function definitions (handler or GET)
- Correct function signatures (must accept request parameter)
- No duplicate definitions
- No imports from fastapi (use fastapi_route instead)
"""

import ast
from pathlib import Path
from typing import Tuple, List


class CustomHandlerValidator:
    """
    Validates custom handler files (not-found.py and docs.py).
    
    This validator performs static analysis on custom handler files to ensure
    they meet the required structure before they are imported and executed.
    Validation is done at the AST level, so no code is actually executed
    during validation.
    
    Validation checks:
    - Syntax correctness (Python compilation)
    - Presence of required function (handler or GET)
    - Function signature (at least one parameter)
    - No duplicate function definitions
    - No disallowed imports (fastapi is not allowed)
    """
    
    def validate_not_found_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate not-found.py file structure.
        
        not-found.py must define either:
        - `handler(request, context)` - Recommended for full control
        - `GET(request, context)` - Alternative naming
        
        Args:
            file_path: Path to the not-found.py file
            
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the abstract syntax tree
            tree = ast.parse(content, filename=str(file_path))
            
            # Track function definitions
            has_handler = False
            has_get = False
            has_post = False
            
            # Analyze function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check handler function
                    if node.name == 'handler':
                        has_handler = True
                        args = node.args.args
                        if len(args) == 0:
                            errors.append(
                                "'handler' function must accept at least 'request' parameter"
                            )
                        elif args and getattr(args[0], 'arg', '') != 'request':
                            errors.append(
                                "First parameter of 'handler' should be 'request'"
                            )
                    
                    # Check GET function
                    elif node.name == 'GET':
                        has_get = True
                        args = node.args.args
                        if len(args) == 0:
                            errors.append(
                                "'GET' function must accept at least 'request' parameter"
                            )
                        elif args and getattr(args[0], 'arg', '') != 'request':
                            errors.append(
                                "First parameter of 'GET' should be 'request'"
                            )
                    
                    # Check POST function (for informational purposes, not required)
                    elif node.name == 'POST':
                        has_post = True
                        args = node.args.args
                        if len(args) == 0:
                            errors.append(
                                "'POST' function must accept at least 'request' parameter"
                            )
                        elif args and getattr(args[0], 'arg', '') != 'request':
                            errors.append(
                                "First parameter of 'POST' should be 'request'"
                            )
            
            # Ensure at least one handler exists
            if not (has_handler or has_get):
                errors.append("not-found.py must define 'handler' or 'GET' function")
            
            # Prevent conflicting definitions
            if has_handler and has_get:
                errors.append("Cannot define both 'handler' and 'GET' in not-found.py")
            
            # Check for disallowed imports
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if alias.name.startswith('fastapi_route.'):
                            # Imports from fastapi_route are allowed
                            pass
                        elif alias.name.startswith('fastapi.'):
                            errors.append(
                                f"Cannot import from fastapi directly: {alias.name}"
                            )
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Error validating file: {str(e)}")
        
        return len(errors) == 0, errors
    
    def validate_docs_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate docs.py file structure.
        
        docs.py must define either:
        - `handler(request, context)` - Recommended for full control
        - `GET(request, context)` - Alternative naming
        
        Args:
            file_path: Path to the docs.py file
            
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the abstract syntax tree
            tree = ast.parse(content, filename=str(file_path))
            
            # Track function definitions
            has_handler = False
            has_get = False
            
            # Analyze function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check handler function
                    if node.name == 'handler':
                        has_handler = True
                        args = node.args.args
                        if len(args) == 0:
                            errors.append(
                                "'handler' function must accept at least 'request' parameter"
                            )
                        elif args and getattr(args[0], 'arg', '') != 'request':
                            errors.append(
                                "First parameter of 'handler' should be 'request'"
                            )
                    
                    # Check GET function
                    elif node.name == 'GET':
                        has_get = True
                        args = node.args.args
                        if len(args) == 0:
                            errors.append(
                                "'GET' function must accept at least 'request' parameter"
                            )
                        elif args and getattr(args[0], 'arg', '') != 'request':
                            errors.append(
                                "First parameter of 'GET' should be 'request'"
                            )
            
            # Ensure at least one handler exists
            if not (has_handler or has_get):
                errors.append("docs.py must define 'handler' or 'GET' function")
            
            # Prevent conflicting definitions
            if has_handler and has_get:
                errors.append("Cannot define both 'handler' and 'GET' in docs.py")
            
            # Check for disallowed imports
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if alias.name.startswith('fastapi_route.'):
                            # Imports from fastapi_route are allowed
                            pass
                        elif alias.name.startswith('fastapi.'):
                            errors.append(
                                f"Cannot import from fastapi directly: {alias.name}"
                            )
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Error validating file: {str(e)}")
        
        return len(errors) == 0, errors
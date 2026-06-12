"""
Validator for custom middleware.py file.

This module validates the structure and content of user-defined middleware
files before they are loaded. It checks for:
- Valid Python syntax
- Required function signatures
- Appropriate parameter names
- No duplicate function definitions
- No disallowed imports from fastapi
"""

import ast
from pathlib import Path
from typing import Tuple, List


class MiddlewareValidator:
    """
    Validates middleware.py file structure and function signatures.
    
    This validator performs static analysis on middleware.py files to ensure
    they meet the required structure before being imported and executed.
    Validation is done at the AST level, so no code is actually executed
    during validation.
    
    Required function signature:
    - Must accept at least 2 parameters (request, call_next)
    - Parameter names should be 'request' and 'call_next' (recommended)
    
    Supported function names:
    - 'middleware' (preferred)
    - 'handler' (alternative)
    - 'on_request' (alternative)
    
    Only one middleware function should be defined per file.
    """
    
    def validate_middleware_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate middleware.py file structure.
        
        Args:
            file_path: Path to the middleware.py file
            
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the abstract syntax tree
            tree = ast.parse(content, filename=str(file_path))
            
            # Track detected middleware functions
            has_middleware = False
            has_handler = False
            has_on_request = False
            
            # Analyze function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check 'middleware' function (preferred name)
                    if node.name == 'middleware':
                        has_middleware = True
                        args = node.args.args
                        if len(args) < 2:
                            errors.append(
                                "'middleware' function must accept at least 2 parameters "
                                "(request, call_next)"
                            )
                        elif len(args) >= 2:
                            first_arg = getattr(args[0], 'arg', '')
                            second_arg = getattr(args[1], 'arg', '')
                            if first_arg != 'request':
                                errors.append(
                                    "First parameter of 'middleware' should be 'request'"
                                )
                            if second_arg != 'call_next':
                                errors.append(
                                    "Second parameter of 'middleware' should be 'call_next'"
                                )
                    
                    # Check 'handler' function (alternative name)
                    elif node.name == 'handler':
                        has_handler = True
                        args = node.args.args
                        if len(args) < 2:
                            errors.append(
                                "'handler' function must accept at least 2 parameters "
                                "(request, call_next)"
                            )
                        elif len(args) >= 2:
                            first_arg = getattr(args[0], 'arg', '')
                            second_arg = getattr(args[1], 'arg', '')
                            if first_arg != 'request':
                                errors.append(
                                    "First parameter of 'handler' should be 'request'"
                                )
                            if second_arg != 'call_next':
                                errors.append(
                                    "Second parameter of 'handler' should be 'call_next'"
                                )
                    
                    # Check 'on_request' function (alternative name)
                    elif node.name == 'on_request':
                        has_on_request = True
                        args = node.args.args
                        if len(args) < 2:
                            errors.append(
                                "'on_request' function must accept at least 2 parameters "
                                "(request, call_next)"
                            )
            
            # Ensure at least one middleware function is defined
            if not (has_middleware or has_handler or has_on_request):
                errors.append(
                    "middleware.py must define 'middleware', 'handler', or 'on_request' function"
                )
            
            # Prevent multiple middleware definitions (ambiguity)
            if sum([has_middleware, has_handler, has_on_request]) > 1:
                errors.append(
                    "Cannot define multiple middleware functions "
                    "(define only one: middleware, handler, or on_request)"
                )
            
            # Validate Python syntax
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
                if e.text:
                    errors.append(f"  {e.text.rstrip()}")
                    errors.append(f"  {' ' * (e.offset or 0)}^")
            
            # Check for disallowed imports (direct fastapi imports)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if alias.name.startswith('fastapi.'):
                            errors.append(
                                f"Cannot import from fastapi directly: {alias.name}. "
                                "Use fastapi_route instead."
                            )
            
        except Exception as e:
            errors.append(f"Error validating file: {str(e)}")
        
        return len(errors) == 0, errors
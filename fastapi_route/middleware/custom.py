"""
Custom middleware loader for user-defined middleware.

This module handles loading custom middleware from a middleware.py file
in the project root. It supports hot reloading, validation, and caching
to efficiently manage middleware in both development and production.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Callable, Any, Tuple
from datetime import datetime

from ..utils.logger import logger
from .validator import MiddlewareValidator


class CustomMiddlewareLoader:
    """
    Loads custom middleware from middleware.py file.
    
    This loader handles:
    - Loading the middleware module from the project root
    - Validating the middleware structure and function signature
    - Caching the middleware for performance
    - Hot reloading when the file changes
    - Error reporting for invalid middleware
    
    The middleware file must define one of:
    - `middleware(request, call_next)` - Preferred name
    - `handler(request, call_next)` - Alternative name
    - `on_request(request, call_next)` - Alternative name
    
    The function should accept two parameters (request and call_next)
    and return a response or await call_next(request).
    """
    
    _cached_middleware = None
    _cached_mtime = None
    _last_error = None
    
    @classmethod
    def load_middleware(cls, project_root: Path, force_reload: bool = False) -> Tuple[Optional[Callable], Optional[str]]:
        """
        Load custom middleware from middleware.py with caching and hot reload.
        
        Args:
            project_root: Root directory of the project
            force_reload: If True, bypass cache and force reload
            
        Returns:
            Tuple of (middleware_function, error_message)
            - middleware_function: The middleware callable, or None if not found/invalid
            - error_message: Error description if loading failed, None otherwise
        """
        middleware_path = project_root / "middleware.py"
        
        # File doesn't exist - clear cache and return
        if not middleware_path.exists():
            if cls._cached_middleware is not None:
                logger.debug("middleware.py removed, clearing cache")
                cls._cached_middleware = None
                cls._cached_mtime = None
            return None, None
        
        # Check if file has been modified since last load
        current_mtime = middleware_path.stat().st_mtime
        
        if not force_reload and cls._cached_middleware is not None and cls._cached_mtime == current_mtime:
            logger.debug("Using cached middleware")
            return cls._cached_middleware, None
        
        # File changed or first load - process it
        logger.info(f"Loading middleware from middleware.py (modified at {datetime.fromtimestamp(current_mtime)})")
        
        # Validate the file structure first (AST analysis)
        validator = MiddlewareValidator()
        is_valid, errors = validator.validate_middleware_file(middleware_path)
        
        if not is_valid:
            error_msg = "\n".join(errors)
            logger.error(f"Invalid middleware.py file: {error_msg}")
            cls._last_error = error_msg
            cls._cached_middleware = None
            cls._cached_mtime = None
            return None, error_msg
        
        # Import the module
        module, error = cls._import_middleware_module(middleware_path)
        
        if module is None:
            logger.error(f"Failed to load middleware.py: {error}")
            cls._last_error = error
            cls._cached_middleware = None
            cls._cached_mtime = None
            return None, error
        
        # Look for the middleware function (multiple naming conventions supported)
        middleware_func = None
        if hasattr(module, 'middleware'):
            middleware_func = module.middleware
            logger.info("Loaded custom middleware (using 'middleware' function)")
        elif hasattr(module, 'handler'):
            middleware_func = module.handler
            logger.info("Loaded custom middleware (using 'handler' function)")
        elif hasattr(module, 'on_request'):
            middleware_func = module.on_request
            logger.info("Loaded custom middleware (using 'on_request' function)")
        else:
            error_msg = "middleware.py must define 'middleware', 'handler', or 'on_request' function"
            logger.error(error_msg)
            cls._last_error = error_msg
            cls._cached_middleware = None
            cls._cached_mtime = None
            return None, error_msg
        
        # Verify the loaded object is actually callable
        if not callable(middleware_func):
            error_msg = "Middleware must be a callable function"
            logger.error(error_msg)
            cls._last_error = error_msg
            cls._cached_middleware = None
            cls._cached_mtime = None
            return None, error_msg
        
        # Cache successfully loaded middleware
        cls._cached_middleware = middleware_func
        cls._cached_mtime = current_mtime
        cls._last_error = None
        
        return middleware_func, None
    
    @classmethod
    def _import_middleware_module(cls, file_path: Path) -> Tuple[Optional[Any], Optional[str]]:
        """
        Import middleware module from file path.
        
        Args:
            file_path: Path to middleware.py file
            
        Returns:
            Tuple of (module, error_message)
        """
        try:
            # Read and syntax-check the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validate Python syntax before import
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                return None, f"Syntax error at line {e.lineno}: {e.msg}"
            
            # Create unique module name to avoid collisions
            module_name = f"custom_middleware_{file_path.stem}"
            
            # Remove any cached version for hot reload
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Load the module using importlib
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return None, "Failed to create module spec"
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            return module, None
            
        except Exception as e:
            import traceback
            return None, f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    
    @classmethod
    def reload(cls, project_root: Path) -> Tuple[Optional[Callable], Optional[str]]:
        """
        Force reload middleware, bypassing cache completely.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Tuple of (middleware_function, error_message)
        """
        cls._cached_middleware = None
        cls._cached_mtime = None
        return cls.load_middleware(project_root, force_reload=True)
    
    @classmethod
    def get_last_error(cls) -> Optional[str]:
        """
        Get the most recent error message from middleware loading.
        
        Returns:
            Error message string, or None if no error occurred
        """
        return cls._last_error
"""
Load custom not-found and docs handlers with hot reload support.

This module handles dynamic loading of user-defined custom handlers
(not-found.py and docs.py) with file watching and automatic reloading
when files change. It includes validation, caching, and error handling.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Tuple, Any
from datetime import datetime

from ..utils.logger import logger
from .validator import CustomHandlerValidator


class CustomHandlerLoader:
    """
    Loads and manages custom handler files with hot reload support.
    
    This loader handles two types of custom handlers:
    - not-found.py: Custom 404 page handler
    - docs.py: Custom documentation page handler
    
    Features:
    - Automatic detection of file changes via mtime checking
    - Caching to avoid unnecessary reloads
    - Validation of handler signatures and structure
    - Syntax error detection before import
    - Hot reload support for development mode
    
    The loader watches for file modifications and automatically invalidates
    the cache when files change, allowing handlers to be updated without
    restarting the server in development mode.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the custom handler loader.
        
        Args:
            project_root: Root directory of the project (where handlers are located)
        """
        self.project_root = project_root
        self.validator = CustomHandlerValidator()
        self._not_found_last_mtime = None
        self._docs_last_mtime = None
        self._cached_not_found_handler = None
        self._cached_docs_handler = None
        self._last_error = None
    
    def load_not_found_handler(self, force_reload: bool = False) -> Optional[Any]:
        """
        Load custom 404 handler from not-found.py with hot reload support.
        
        The handler can be defined as either:
        - `handler(request, context)` - Recommended, full control
        - `GET(request, context)` - Alternative name for compatibility
        
        Args:
            force_reload: If True, bypass cache and force reload the file
            
        Returns:
            The handler function if found and valid, None otherwise
        """
        not_found_path = self.project_root / "not-found.py"
        
        # File doesn't exist - clear cache and return None
        if not not_found_path.exists():
            if self._cached_not_found_handler is not None:
                logger.debug("not-found.py removed, clearing cache")
                self._cached_not_found_handler = None
                self._not_found_last_mtime = None
            return None
        
        # Check if file has been modified
        current_mtime = not_found_path.stat().st_mtime
        
        # Return cached version if file hasn't changed
        if not force_reload and self._cached_not_found_handler is not None and self._not_found_last_mtime == current_mtime:
            logger.debug("Using cached not-found handler")
            return self._cached_not_found_handler
        
        # File changed or first load - process it
        logger.info(f"Loading/Reloading not-found.py (modified at {datetime.fromtimestamp(current_mtime)})")
        
        # Validate the file structure first
        is_valid, errors = self.validator.validate_not_found_file(not_found_path)
        
        if not is_valid:
            error_msg = "\n".join(errors)
            logger.error(f"Invalid not-found.py file: {error_msg}")
            self._last_error = error_msg
            self._cached_not_found_handler = None
            self._not_found_last_mtime = None
            return None
        
        # Import the module
        module, error = self._import_custom_module(not_found_path, "not_found_handler", force_reload)
        
        if module is None:
            logger.error(f"Failed to load not-found.py: {error}")
            self._last_error = error
            self._cached_not_found_handler = None
            self._not_found_last_mtime = None
            return None
        
        # Find the handler function
        handler = None
        if hasattr(module, 'handler'):
            handler = module.handler
            logger.info("Loaded custom 404 handler from not-found.py (using 'handler' function)")
        elif hasattr(module, 'GET'):
            handler = module.GET
            logger.info("Loaded custom 404 handler from not-found.py (using 'GET' function)")
        else:
            error_msg = "not-found.py must define 'handler' or 'GET' function"
            logger.error(error_msg)
            self._last_error = error_msg
            self._cached_not_found_handler = None
            self._not_found_last_mtime = None
            return None
        
        # Cache the handler
        self._cached_not_found_handler = handler
        self._not_found_last_mtime = current_mtime
        self._last_error = None
        
        return handler
    
    def load_docs_handler(self, force_reload: bool = False) -> Optional[Any]:
        """
        Load custom documentation handler from docs.py with hot reload support.
        
        The handler can be defined as either:
        - `handler(request, context)` - Recommended, full control
        - `GET(request, context)` - Alternative name for compatibility
        
        Args:
            force_reload: If True, bypass cache and force reload the file
            
        Returns:
            The handler function if found and valid, None otherwise
        """
        docs_path = self.project_root / "docs.py"
        
        # File doesn't exist - clear cache and return None
        if not docs_path.exists():
            if self._cached_docs_handler is not None:
                logger.debug("docs.py removed, clearing cache")
                self._cached_docs_handler = None
                self._docs_last_mtime = None
            return None
        
        # Check if file has been modified
        current_mtime = docs_path.stat().st_mtime
        
        # Return cached version if file hasn't changed
        if not force_reload and self._cached_docs_handler is not None and self._docs_last_mtime == current_mtime:
            logger.debug("Using cached docs handler")
            return self._cached_docs_handler
        
        # File changed or first load - process it
        logger.info(f"Loading/Reloading docs.py (modified at {datetime.fromtimestamp(current_mtime)})")
        
        # Validate the file structure first
        is_valid, errors = self.validator.validate_docs_file(docs_path)
        
        if not is_valid:
            error_msg = "\n".join(errors)
            logger.error(f"Invalid docs.py file: {error_msg}")
            self._last_error = error_msg
            self._cached_docs_handler = None
            self._docs_last_mtime = None
            return None
        
        # Import the module
        module, error = self._import_custom_module(docs_path, "docs_handler", force_reload)
        
        if module is None:
            logger.error(f"Failed to load docs.py: {error}")
            self._last_error = error
            self._cached_docs_handler = None
            self._docs_last_mtime = None
            return None
        
        # Find the handler function
        handler = None
        if hasattr(module, 'handler'):
            handler = module.handler
            logger.info("Loaded custom docs handler from docs.py (using 'handler' function)")
        elif hasattr(module, 'GET'):
            handler = module.GET
            logger.info("Loaded custom docs handler from docs.py (using 'GET' function)")
        else:
            error_msg = "docs.py must define 'handler' or 'GET' function"
            logger.error(error_msg)
            self._last_error = error_msg
            self._cached_docs_handler = None
            self._docs_last_mtime = None
            return None
        
        # Cache the handler
        self._cached_docs_handler = handler
        self._docs_last_mtime = current_mtime
        self._last_error = None
        
        return handler
    
    def reload_all(self) -> None:
        """Force reload all custom handlers (both not-found and docs)."""
        logger.info("Forcing reload of all custom handlers")
        self.load_not_found_handler(force_reload=True)
        self.load_docs_handler(force_reload=True)
    
    def _import_custom_module(self, file_path: Path, module_name: str, force_reload: bool = False) -> Tuple[Optional[Any], Optional[str]]:
        """
        Import a custom module from file path with cache clearing.
        
        This method handles the actual import logic:
        1. Read and syntax-check the file
        2. Clear any existing cached module
        3. Load the module using importlib
        4. Return the module object
        
        Args:
            file_path: Path to the Python file to import
            module_name: Base name for the module (will be prefixed)
            force_reload: If True, force reload even if cached
            
        Returns:
            Tuple of (module, error_message). If successful, module is set
            and error_message is None. If failed, module is None and
            error_message contains the error details.
        """
        try:
            # Read and syntax-check the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                return None, f"Syntax error at line {e.lineno}: {e.msg}"
            
            # Create unique module name to avoid collisions
            full_module_name = f"custom_{module_name}_{file_path.stem}"
            
            # Clear any existing cached version
            if full_module_name in sys.modules:
                logger.debug(f"Removing cached module: {full_module_name}")
                del sys.modules[full_module_name]
            
            # Load the module
            spec = importlib.util.spec_from_file_location(full_module_name, file_path)
            if spec is None or spec.loader is None:
                return None, "Failed to create module spec"
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_module_name] = module
            spec.loader.exec_module(module)
            
            return module, None
            
        except Exception as e:
            import traceback
            return None, f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
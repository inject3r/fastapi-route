"""
Python configuration file loader with caching and hot reload support.

This module handles loading configuration from config.py files with
automatic file watching, caching, and validation. It supports both
synchronous loading and hot reloading when the file changes.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from ..types import Config
from ..utils.logger import logger
from .validator import ConfigValidator


class PyConfigLoader:
    """
    Loads configuration from Python files with intelligent caching.
    
    Features:
    - Automatically detects file changes and invalidates cache
    - Validates configuration structure and types before loading
    - Returns rich error messages for syntax or validation failures
    - Thread-safe caching for concurrent access
    - Supports custom config file paths
    
    The loader treats config.py as a Python module, allowing users to write
    actual code with logic, imports, and computed values - not just static JSON.
    """
    
    _cached_config: Optional[Config] = None
    _cached_path: Optional[Path] = None
    _cached_mtime: Optional[float] = None
    _last_error: Optional[str] = None
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> Tuple[Optional[Config], Optional[str]]:
        """
        Load configuration from config.py with automatic caching.
        
        This method handles:
        - Reading and parsing the Python file
        - Validating the configuration structure
        - Detecting file modifications for cache invalidation
        - Returning both the config object and any error that occurred
        
        Args:
            config_path: Optional explicit path to config file.
                        If None, looks for config.py in current directory.
        
        Returns:
            Tuple of (config, error_message). If successful, config is the
            Config object and error_message is None. If failed, config is
            None and error_message contains the error details.
        """
        # Determine which config file to load
        if config_path:
            path = Path(config_path)
        else:
            path = Path.cwd() / "config.py"
        
        # No config file exists - return defaults
        if not path.exists():
            logger.info("No config.py found, using default configuration")
            default_config = Config()
            default_config.config_file = None
            cls._cached_config = default_config
            cls._cached_path = None
            cls._cached_mtime = None
            cls._last_error = None
            return default_config, None
        
        # Check if cached version is still valid (file hasn't changed)
        if cls._cached_config is not None and cls._cached_path == path:
            current_mtime = path.stat().st_mtime
            if cls._cached_mtime == current_mtime:
                logger.debug("Using cached config from config.py")
                return cls._cached_config, cls._last_error
        
        # File changed or first load - process fresh
        logger.info(f"Loading config from {path}")
        
        try:
            # Import and extract configuration variables
            config_dict = cls._import_config_module(path)
            
            # Validate the configuration structure
            validator = ConfigValidator()
            is_valid, errors = validator.validate_config_dict(config_dict)
            
            if not is_valid:
                error_msg = "\n".join(errors)
                cls._last_error = error_msg
                logger.error(f"Config validation failed:\n{error_msg}")
                return None, error_msg
            
            # Create strongly-typed Config object
            config = Config(**config_dict)
            config.config_file = str(path)
            
            # Update cache for future requests
            cls._cached_config = config
            cls._cached_path = path
            cls._cached_mtime = path.stat().st_mtime
            cls._last_error = None
            
            logger.info("Config loaded successfully from config.py")
            return config, None
            
        except Exception as e:
            # Cache any unexpected errors during loading
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            cls._last_error = error_msg
            logger.error(f"Failed to load config.py: {error_msg}")
            return None, error_msg
    
    @classmethod
    def reload(cls, config_path: Optional[str] = None) -> Tuple[Optional[Config], Optional[str]]:
        """
        Force reload configuration, bypassing cache completely.
        
        This is useful when the config file has been modified and you need
        to pick up changes immediately without waiting for cache expiration.
        
        Args:
            config_path: Optional explicit path to config file
            
        Returns:
            Same as load() method - (config, error_message) tuple
        """
        cls._cached_config = None
        cls._cached_path = None
        cls._cached_mtime = None
        return cls.load(config_path)
    
    @classmethod
    def _import_config_module(cls, file_path: Path) -> Dict[str, Any]:
        """
        Dynamically import a Python file and extract configuration variables.
        
        This method:
        1. Reads and compiles the Python file to check syntax
        2. Loads the file as a Python module
        3. Extracts known configuration variable names
        
        Args:
            file_path: Path to the Python configuration file
            
        Returns:
            Dictionary of extracted configuration variables
            
        Raises:
            Exception: If file has syntax errors, cannot be imported, or
                      required modules are missing
        """
        # Read raw file content for syntax checking
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate Python syntax before attempting import
        try:
            compile(content, str(file_path), 'exec')
        except SyntaxError as e:
            raise Exception(f"Syntax error at line {e.lineno}: {e.msg}")
        
        # Create unique module name to avoid collisions
        module_name = f"user_config_{file_path.stem}"
        
        # Remove any previously cached version
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Load as a proper Python module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise Exception("Failed to create module spec")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Extract known configuration keys
        config_dict = {}
        config_keys = [
            'app_name', 'debug', 'cors_enabled', 'cors_origins',
            'middlewares', 'plugins', 'route_dir', 'docs_enabled',
            'custom_docs_template'
        ]
        
        for key in config_keys:
            if hasattr(module, key):
                config_dict[key] = getattr(module, key)
        
        return config_dict
    
    @classmethod
    def get_last_error(cls) -> Optional[str]:
        """
        Retrieve the most recent error message from config loading.
        
        Returns:
            The last error message as a string, or None if no error occurred.
            Useful for debugging configuration issues.
        """
        return cls._last_error
    
    @classmethod
    def create_default_config(cls, path: Path) -> None:
        """
        Generate a default config.py file with commented examples.
        
        Creates a starter configuration file with all available options
        documented. Does nothing if the file already exists to prevent
        overwriting existing configuration.
        
        Args:
            path: Where to create the config.py file
        """
        default_config = '''# FastAPI Route Configuration
# Edit this file to configure your application

# Application name (shown in documentation)
app_name = "My FastAPI Route App"

# Debug mode - detailed errors (disable in production)
debug = True

# CORS (Cross-Origin Resource Sharing) settings
cors_enabled = True
cors_origins = ["*"]  # List of allowed origins: ["https://example.com", "http://localhost:3000"]

# Custom middleware (import paths to Python classes or functions)
# Example: "myapp.middleware.AuthMiddleware"
middlewares = []

# Custom plugins (import paths)
plugins = []

# Directory containing route files (relative to project root)
route_dir = "routes"

# Documentation settings
docs_enabled = True

# Path to custom HTML template for documentation (None = use default)
custom_docs_template = None

# Example: Custom HTML template location
# custom_docs_template = "templates/docs.html"
'''
        
        # Don't overwrite existing configuration
        if path.exists():
            logger.debug(f"Config file already exists at {path}, skipping creation")
            return
        
        path.write_text(default_config, encoding='utf-8')
        logger.info(f"Created default config.py at {path}")
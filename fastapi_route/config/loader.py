"""
Configuration loader with advanced settings support.

This module handles loading application configuration from either Python
or JSON files. It supports hot-reloading, caching, and automatic type
conversion from configuration dictionaries to typed dataclass objects.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..types import Config, ServerConfig, LoggingConfig, BuildConfig, RoutesConfig
from ..constants import DEFAULT_CONFIG_NAME
from ..utils.logger import logger


class ConfigLoader:
    """
    Advanced configuration loader with caching and hot-reload support.
    
    Features:
    - Prefers config.py over fastapi-route.json (legacy)
    - Automatically caches loaded config for performance
    - Detects file changes and invalidates cache
    - Converts nested dictionaries to typed dataclasses
    - Supports Python file format with actual code, not just JSON
    """
    
    _cached_config: Optional[Config] = None
    _cached_path: Optional[Path] = None
    _cached_mtime: Optional[float] = None
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> Config:
        """
        Load configuration from file with automatic fallback.
        
        Priority order:
        1. Explicit config_path argument if provided
        2. config.py in current working directory
        3. fastapi-route.json in current working directory (legacy)
        4. Default configuration values
        
        Args:
            config_path: Optional explicit path to config file
            
        Returns:
            Fully populated Config object with all settings
        """
        # Determine which config file to load
        py_config_path = Path.cwd() / "config.py"
        json_config_path = Path.cwd() / DEFAULT_CONFIG_NAME
        
        if config_path:
            path = Path(config_path)
        elif py_config_path.exists():
            path = py_config_path
        else:
            path = json_config_path if json_config_path.exists() else None
        
        # No config file found - return defaults
        if not path or not path.exists():
            logger.info("No config file found, using defaults")
            return Config()
        
        # Check cache for unchanged file
        current_mtime = path.stat().st_mtime
        if (cls._cached_config is not None and 
            cls._cached_path == path and 
            cls._cached_mtime == current_mtime):
            return cls._cached_config
        
        # Load based on file extension
        if path.suffix == '.py':
            config_dict = cls._load_from_py(path)
        else:
            config_dict = cls._load_from_json(path)
        
        # Convert dictionary to strongly-typed Config object
        config = cls._create_config(config_dict)
        
        # Cache for future requests
        cls._cached_config = config
        cls._cached_path = path
        cls._cached_mtime = current_mtime
        
        logger.info(f"Config loaded from {path}")
        return config
    
    @classmethod
    def _load_from_py(cls, path: Path) -> Dict[str, Any]:
        """
        Dynamically import and load configuration from Python file.
        
        This allows users to write actual Python code in config.py,
        enabling logic, conditionals, and computed values.
        
        Args:
            path: Path to config.py file
            
        Returns:
            Dictionary of configuration variables
            
        Raises:
            ValueError: If module cannot be loaded or parsed
        """
        import importlib.util
        
        module_name = "user_config"
        
        # Remove any cached version to force fresh import
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Create module spec from file path
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Failed to load config from {path}")
        
        # Execute the module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Extract known configuration variables
        config_dict = {}
        config_keys = [
            'app_name', 'debug', 'cors_enabled', 'cors_origins',
            'cors_allow_credentials', 'cors_allow_methods', 'cors_allow_headers',
            'docs_enabled', 'redoc_enabled', 'openapi_url', 'openapi_prefix',
            'title', 'description', 'version', 'terms_of_service', 
            'contact', 'license_info',
            'route_dir', 'static_dir', 'static_directory_listing',
            'middlewares', 'plugins', 'server', 'logging', 'build', 
            'routes', 'commands'
        ]
        
        for key in config_keys:
            if hasattr(module, key):
                config_dict[key] = getattr(module, key)
        
        return config_dict
    
    @classmethod
    def _load_from_json(cls, path: Path) -> Dict[str, Any]:
        """
        Load configuration from legacy JSON file.
        
        This exists for backward compatibility with older projects.
        New projects should use config.py for full features.
        
        Args:
            path: Path to fastapi-route.json file
            
        Returns:
            Dictionary parsed from JSON
        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def _create_config(cls, config_dict: Dict[str, Any]) -> Config:
        """
        Convert raw dictionary to typed Config object.
        
        Handles nested configuration sections (server, logging, build, routes)
        and creates appropriate dataclass instances for each.
        
        Args:
            config_dict: Raw configuration dictionary
            
        Returns:
            Fully typed Config instance
        """
        # Extract nested configuration sections
        server_dict = config_dict.pop('server', {})
        logging_dict = config_dict.pop('logging', {})
        build_dict = config_dict.pop('build', {})
        routes_dict = config_dict.pop('routes', {})
        commands_dict = config_dict.pop('commands', {})
        
        # Create strongly-typed nested configs
        server = ServerConfig(**server_dict) if server_dict else ServerConfig()
        logging = LoggingConfig(**logging_dict) if logging_dict else LoggingConfig()
        build = BuildConfig(**build_dict) if build_dict else BuildConfig()
        routes = RoutesConfig(**routes_dict) if routes_dict else RoutesConfig()
        
        # Assemble main configuration object
        return Config(
            server=server,
            logging=logging,
            build=build,
            routes=routes,
            commands=commands_dict,
            **config_dict
        )
    
    @classmethod
    def reload(cls) -> Config:
        """
        Force reload configuration, bypassing cache.
        
        Useful when config file has been modified externally and
        you need to pick up changes immediately.
        
        Returns:
            Freshly loaded Config instance
        """
        cls._cached_config = None
        cls._cached_path = None
        cls._cached_mtime = None
        return cls.load()
    
    @classmethod
    def create_default_config(cls) -> None:
        """
        Generate a default config.py file with comprehensive examples.
        
        Creates a fully commented configuration file showing all
        available options with sensible defaults. Does nothing if
        config.py already exists to prevent overwriting user changes.
        """
        config_path = Path.cwd() / "config.py"
        
        # Don't overwrite existing configuration
        if config_path.exists():
            return
        
        default_config = '''# FastAPI Route Advanced Configuration
# Edit this file to configure your application

# ============================================================
# Application Settings
# ============================================================

# Application name (shown in documentation and logs)
app_name = "My FastAPI App"

# Debug mode - enables detailed error pages (disable in production)
debug = False

# API version (appears in OpenAPI docs)
version = "1.0.0"

# API description (appears in OpenAPI docs)
description = "My FastAPI Route Application"

# ============================================================
# CORS Settings
# ============================================================

# Enable Cross-Origin Resource Sharing
cors_enabled = True

# Allowed origins (use ["*"] for all, or specific domains)
cors_origins = ["*"]

# Allow credentials (cookies, authorization headers)
cors_allow_credentials = True

# Allowed HTTP methods
cors_allow_methods = ["*"]

# Allowed request headers
cors_allow_headers = ["*"]

# ============================================================
# Documentation Settings
# ============================================================

# Enable built-in documentation at /docs
docs_enabled = True

# Enable ReDoc documentation at /redoc
redoc_enabled = False

# OpenAPI JSON endpoint URL
openapi_url = "/openapi.json"

# OpenAPI URL prefix
openapi_prefix = ""

# ============================================================
# Directory Settings
# ============================================================

# Directory containing route files
route_dir = "routes"

# Directory for static assets (served under /)
static_dir = "public"

# Show directory listings for static assets (security risk in production)
static_directory_listing = False

# ============================================================
# Server Settings
# ============================================================

server = {
    "host": "127.0.0.1",           # Bind address
    "port": 8000,                   # Bind port
    "reload": False,                # Auto-reload on code changes
    "workers": 1,                   # Number of worker processes
    "timeout_keep_alive": 5,        # Keep-alive timeout in seconds
    "limit_concurrency": None,      # Maximum concurrent connections
    "limit_max_requests": None,     # Maximum requests before worker restart
    "backlog": 2048,                # TCP listen backlog
    "h11_max_incomplete_event_size": None,
    "uds": None,                    # Unix domain socket path
    "fd": None,                     # File descriptor for socket
    "interface": "auto",            # ASGI interface (auto, asgi, wsgi)
    "ws_max_size": 16777216,        # WebSocket max message size
    "ws_ping_interval": 20.0,       # WebSocket ping interval
    "ws_ping_timeout": 20.0,        # WebSocket ping timeout
    "ws_per_message_deflate": True, # WebSocket compression
    "lifespan": "auto",             # Lifespan protocol (auto, on, off)
    "loop": "auto",                 # Event loop implementation
    "http": "auto"                  # HTTP protocol implementation
}

# ============================================================
# Logging Settings
# ============================================================

logging = {
    "level": "INFO",                # Log level (DEBUG, INFO, WARNING, ERROR)
    "format": "[%Y-%m-%d %H:%M:%S]", # Timestamp format
    "color": True,                  # Enable colored output
    "production_level": "WARNING"   # Log level in production mode
}

# ============================================================
# Build Settings
# ============================================================

build = {
    "cache_dir": ".cache",          # Cache directory name
    "compression_level": 6,         # Zlib compression (1-9, higher = smaller)
    "force_rebuild": False,         # Always rebuild cache
    "exclude_patterns": [],         # Files to exclude from build
    "include_patterns": []          # Files to include (overrides exclude)
}

# ============================================================
# Routes Settings
# ============================================================

routes = {
    "routes_dir": "routes",         # Routes directory
    "route_files": ["route.py", "index.py", "__init__.py"],
    "param_prefix": "[",            # Dynamic param prefix (e.g., [user_id])
    "param_suffix": "]",            # Dynamic param suffix
    "group_prefix": "(",            # Route group prefix (ignored in URL)
    "group_suffix": ")"             # Route group suffix
}

# ============================================================
# Custom Commands
# ============================================================

commands = {
    "dev": "fastapi-route dev --host {server.host} --port {server.port}",
    "build": "fastapi-route build",
    "run": "fastapi-route run --host {server.host} --port {server.port}",
    "clean": "fastapi-route clean",
    "status": "fastapi-route status",
}

# ============================================================
# Middlewares (import paths)
# ============================================================

middlewares = []

# ============================================================
# Plugins (import paths)
# ============================================================

plugins = []

# ============================================================
# Contact Information (optional)
# ============================================================

# contact = {
#     "name": "API Support",
#     "url": "https://example.com/support",
#     "email": "support@example.com"
# }

# ============================================================
# License Information (optional)
# ============================================================

# license_info = {
#     "name": "MIT",
#     "url": "https://opensource.org/licenses/MIT"
# }
'''
        
        config_path.write_text(default_config, encoding='utf-8')
        logger.info(f"Created default config.py at {config_path}")
    
    @classmethod
    def get_server_config(cls) -> ServerConfig:
        """
        Convenience method to get only server configuration.
        
        Returns:
            ServerConfig object with host, port, workers, etc.
        """
        config = cls.load()
        return config.server
    
    @classmethod
    def get_logging_config(cls) -> LoggingConfig:
        """
        Convenience method to get only logging configuration.
        
        Returns:
            LoggingConfig object with level, format, color settings
        """
        config = cls.load()
        return config.logging
    
    @classmethod
    def get_build_config(cls) -> BuildConfig:
        """
        Convenience method to get only build configuration.
        
        Returns:
            BuildConfig object with cache_dir, compression_level, etc.
        """
        config = cls.load()
        return config.build
    
    @classmethod
    def get_command(cls, name: str, **kwargs) -> Optional[str]:
        """
        Retrieve a custom command with variable substitution.
        
        Args:
            name: Command name (e.g., 'deploy', 'test')
            **kwargs: Variables to substitute in command template
            
        Returns:
            Formatted command string or None if command not found
        """
        config = cls.load()
        command_template = config.commands.get(name)
        
        if command_template:
            return command_template.format(
                server=config.server,
                **kwargs
            )
        
        return None
"""
Type hints and shared data types for FastAPI Route.

This module defines all the core data structures used throughout the
framework, including route information, configuration objects, and
type aliases for common callables.

Centralizing types here ensures consistency across the codebase and
provides IDE support for autocompletion and type checking.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# Type Aliases
# ============================================================

# Handler function type - accepts request and optional context/params
RouteHandler = Callable[..., Any]

# Middleware function type - accepts request and call_next
Middleware = Callable[[Any, Callable], Any]


# ============================================================
# Core Data Types
# ============================================================

@dataclass
class RouteInfo:
    """
    Information about a discovered route.
    
    This dataclass holds all metadata for a single route, including
    its URL pattern, HTTP method, handler function, and source file.
    
    Attributes:
        path: URL path pattern (may contain {param} placeholders)
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        handler: The callable function that handles the request
        file_path: Source file where the route is defined
        is_dynamic: Whether the path contains dynamic parameters
        param_names: List of dynamic parameter names from the path
    """
    path: str
    method: str
    handler: RouteHandler
    file_path: Path
    is_dynamic: bool = False
    param_names: List[str] = field(default_factory=list)


# ============================================================
# Configuration Data Types
# ============================================================

@dataclass
class LoggingConfig:
    """
    Logging configuration settings.
    
    Controls log output format, verbosity, and behavior in
    development vs production environments.
    
    Attributes:
        level: Log level for development (DEBUG, INFO, WARNING, ERROR)
        format: Timestamp format string (strftime format)
        color: Enable ANSI color codes in terminal output
        production_level: Log level for production mode (usually higher)
    """
    level: str = "INFO"
    format: str = "[%Y-%m-%d %H:%M:%S]"
    color: bool = True
    production_level: str = "WARNING"


@dataclass
class ServerConfig:
    """
    Uvicorn server configuration settings.
    
    These settings control how the ASGI server behaves, including
    networking, concurrency, and WebSocket parameters.
    
    Most settings are passed directly to uvicorn.run().
    """
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    timeout_keep_alive: int = 5
    limit_concurrency: Optional[int] = None
    limit_max_requests: Optional[int] = None
    backlog: int = 2048
    h11_max_incomplete_event_size: Optional[int] = None
    factory: bool = False
    uds: Optional[str] = None
    fd: Optional[int] = None
    interface: str = "auto"          # auto, asgi, wsgi
    ws_max_size: int = 16777216
    ws_ping_interval: float = 20.0
    ws_ping_timeout: float = 20.0
    ws_per_message_deflate: bool = True
    lifespan: str = "auto"           # auto, on, off
    loop: str = "auto"               # auto, asyncio, uvloop
    http: str = "auto"               # auto, h11, httptools


@dataclass
class BuildConfig:
    """
    Build cache configuration settings.
    
    Controls how routes are compiled and cached for production use.
    
    Attributes:
        cache_dir: Directory name for build cache (relative to project root)
        compression_level: Zlib compression level (1-9, higher = smaller)
        force_rebuild: Always rebuild cache even if it exists
        exclude_patterns: File patterns to exclude from build
        include_patterns: File patterns to include (overrides exclude)
    """
    cache_dir: str = ".cache"
    compression_level: int = 6
    force_rebuild: bool = False
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)


@dataclass
class RoutesConfig:
    """
    Routes directory configuration.
    
    Controls how route files are discovered and interpreted.
    
    Attributes:
        routes_dir: Directory containing route files
        route_files: Filenames recognized as route files (in priority order)
        param_prefix: Character marking start of dynamic parameter folders
        param_suffix: Character marking end of dynamic parameter folders
        group_prefix: Character marking start of route group folders
        group_suffix: Character marking end of route group folders
    """
    routes_dir: str = "routes"
    route_files: List[str] = field(default_factory=lambda: ["route.py", "index.py", "__init__.py"])
    param_prefix: str = "["
    param_suffix: str = "]"
    group_prefix: str = "("
    group_suffix: str = ")"


@dataclass
class Config:
    """
    Main application configuration.
    
    This is the root configuration object that aggregates all settings
    from config.py. It includes:
    - Application metadata (name, version, description)
    - CORS settings
    - Documentation settings
    - Directory paths
    - Server, logging, build, and routes configurations
    - Custom CLI commands
    
    Most fields have sensible defaults and can be overridden in config.py.
    """
    # Application settings
    app_name: str = "FastAPI Route App"
    debug: bool = False
    
    # CORS settings
    cors_enabled: bool = True
    cors_origins: List[str] = None
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = None
    cors_allow_headers: List[str] = None
    
    # FastAPI specific settings (for OpenAPI docs)
    docs_enabled: bool = True
    redoc_enabled: bool = False
    openapi_url: Optional[str] = "/openapi.json"
    openapi_prefix: str = ""
    title: Optional[str] = None
    description: Optional[str] = None
    version: str = "0.1.2"
    terms_of_service: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    license_info: Optional[Dict[str, str]] = None
    
    # Directory settings
    route_dir: str = "routes"
    static_dir: Optional[str] = "public"
    static_directory_listing: bool = False
    
    # Advanced settings
    middlewares: List[str] = None
    plugins: List[str] = None
    
    # Nested configuration sections
    server: ServerConfig = field(default_factory=ServerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    routes: RoutesConfig = field(default_factory=RoutesConfig)
    
    # Custom CLI commands (key = command name, value = shell command)
    commands: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        if self.cors_allow_methods is None:
            self.cors_allow_methods = ["*"]
        if self.cors_allow_headers is None:
            self.cors_allow_headers = ["*"]
        if self.middlewares is None:
            self.middlewares = []
        if self.plugins is None:
            self.plugins = []
        
        # Default CLI commands if none provided
        if not self.commands:
            self.commands = {
                "dev": "fastapi-route dev --host {server.host} --port {server.port}",
                "build": "fastapi-route build",
                "run": "fastapi-route run --host {server.host} --port {server.port}",
                "clean": "fastapi-route clean",
                "status": "fastapi-route status",
            }
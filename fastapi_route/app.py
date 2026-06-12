"""
Main application factory for FastAPI Route.

This module provides the core application class that builds and runs the
FastAPI application. It handles route discovery, caching, configuration,
and lifecycle management.

The application can run in two modes:
- Development: Routes are scanned from filesystem on each build
- Production: Routes are loaded from build cache for faster startup

Features:
- Automatic route discovery from filesystem
- Build cache support for production
- Custom documentation endpoint
- Lifecycle hooks for startup/shutdown
- Configurable logging levels
"""

import sys
from pathlib import Path
from typing import Optional, Any, Dict, List

from .config.loader import ConfigLoader
from .core.registry import RouteRegistry
from .core.builder import AppBuilder
from .core.lifecycle import LifecycleManager
from .routing.filesystem import FileSystemRouter
from .build import CacheLoader
from .types import RouteInfo
from .utils.logger import logger, Logger


class FastAPIRouterApp:
    """
    Main application class for FastAPI Route.
    
    This class orchestrates the entire application lifecycle:
    1. Load configuration
    2. Discover routes (from filesystem or cache)
    3. Build the FastAPI application
    4. Set up middleware and handlers
    5. Run the server
    
    The application can be used in two ways:
    - Direct execution: app = FastAPIRouterApp(); app.run()
    - As ASGI app: app = FastAPIRouterApp(); app = app.build()
    
    Args:
        config_path: Optional path to configuration file
        enable_docs: Whether to enable the /docs endpoint
        custom_docs_template: Custom HTML template for documentation
        use_cache: Use build cache for routes (production mode)
        is_production: Run in production mode (reduced logging)
    """
    
    def __init__(self, config_path: Optional[str] = None, enable_docs: bool = True, 
                 custom_docs_template: Optional[str] = None, use_cache: bool = False, 
                 is_production: bool = False):
        self.config_path = config_path
        self.config = ConfigLoader.load(config_path)
        
        # Apply settings from config or constructor args
        self.enable_docs = enable_docs if hasattr(self.config, 'docs_enabled') else enable_docs
        self.custom_docs_template = custom_docs_template or getattr(self.config, 'custom_docs_template', None)
        self.use_cache = use_cache
        self.is_production = is_production
        
        # Configure logger based on mode
        Logger.set_production_mode(is_production)
        
        # Initialize core components
        self.registry = RouteRegistry()
        self.lifecycle = LifecycleManager()
        self._fastapi_app = None
        self._is_built = False
    
    def _load_handler_from_file(self, file_path: Path, handler_name: str):
        """
        Dynamically load a handler function from a Python file.
        
        This is used in production mode to load route handlers from the
        original source files when using build cache.
        
        Args:
            file_path: Path to the route file
            handler_name: Name of the handler function (e.g., "GET")
            
        Returns:
            Handler function if found, None otherwise
        """
        import importlib.util
        import sys
        
        try:
            # Convert file path to module name
            module_name = str(file_path).replace("/", ".").replace("\\", ".").replace(".py", "")
            
            # Use cached module if available
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    return None
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            
            return getattr(module, handler_name, None)
        except Exception as e:
            if not self.is_production:
                logger.error(f"Failed to load handler {handler_name} from {file_path}: {e}")
            return None
    
    def build(self) -> Any:
        """
        Build and return the FastAPI application.
        
        This method performs the actual application construction:
        1. Discover routes (filesystem or cache)
        2. Register routes in the registry
        3. Build the FastAPI app with all middleware and handlers
        4. Set up lifecycle events
        
        Returns:
            Configured FastAPI application instance
        """
        if self._is_built and self._fastapi_app:
            return self._fastapi_app
        
        if not self.is_production:
            logger.info("Building FastAPI Route application...")
        
        try:
            routes: List[RouteInfo] = []
            routes_metadata: List[Dict[str, Any]] = []
            
            # Try to load from cache if production mode
            if self.use_cache:
                cache_loader = CacheLoader(Path.cwd())
                routes_metadata = cache_loader.load_routes_metadata()
                if routes_metadata:
                    if not self.is_production:
                        logger.info(f"Loading {len(routes_metadata)} routes from cache")
                else:
                    if not self.is_production:
                        logger.warning("Cache invalid or missing, falling back to filesystem scan")
                    self.use_cache = False
            
            # Fall back to filesystem scan if cache not available
            if not self.use_cache:
                router = FileSystemRouter(self.config.route_dir)
                routes = router.scan()
                if not self.is_production:
                    logger.info(f"Discovered {len(routes)} routes via filesystem scan")
            else:
                # Load handlers from source files for cached routes
                for meta in routes_metadata:
                    handler = self._load_handler_from_file(
                        Path(meta['file_path']), 
                        meta['method']
                    )
                    if handler is None:
                        if not self.is_production:
                            logger.error(f"Failed to load handler for {meta['method']} {meta['path']}")
                        continue
                    
                    route = RouteInfo(
                        path=meta['path'],
                        method=meta['method'],
                        handler=handler,
                        file_path=Path(meta['file_path']),
                        is_dynamic=meta['is_dynamic'],
                        param_names=meta['param_names']
                    )
                    routes.append(route)
                
                if not self.is_production:
                    logger.info(f"Loaded {len(routes)} routes from cache")
            
            # No routes found - cannot start
            if not routes:
                logger.warning("No routes found")
                return None
            
            # Register all routes
            for route in routes:
                self.registry.register(route)
            
            # Build the FastAPI application
            builder = AppBuilder(self.config, self.registry, self.enable_docs, self.custom_docs_template)
            self._fastapi_app = builder.build()
            
            # Set up lifecycle hooks
            self.lifecycle.setup(self._fastapi_app)
            
            self._is_built = True
            
            # Log success
            if not self.is_production:
                logger.info(f"Application built with {len(routes)} routes")
                if self.enable_docs:
                    logger.info(f"Documentation available at /docs")
            
            return self._fastapi_app
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            if not self.is_production:
                import traceback
                traceback.print_exc()
            raise
    
    def run(self, host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
        """
        Run the application using uvicorn server.
        
        Args:
            host: Host address to bind to
            port: Port number to listen on
            reload: Enable auto-reload (development mode)
        """
        try:
            import uvicorn
        except ImportError:
            logger.error("uvicorn not installed. Please install it: pip install uvicorn")
            return
        
        app = self.build()
        
        if app is None:
            logger.error("No routes found, cannot start server")
            return
        
        mode = "development" if reload else "production"
        logger.info(f"Starting {mode} server on http://{host}:{port}")
        
        if not reload and self.use_cache:
            logger.info("Running in production mode with build cache")
        
        # Reduce uvicorn log noise in production
        if self.is_production:
            import logging
            log_config = uvicorn.config.LOGGING_CONFIG
            log_config["loggers"]["uvicorn"]["level"] = "WARNING"
            log_config["loggers"]["uvicorn.access"]["level"] = "WARNING"
            log_config["loggers"]["uvicorn.error"]["level"] = "WARNING"
            uvicorn.run(app, host=host, port=port, reload=reload, 
                       log_config=log_config, access_log=False)
        else:
            uvicorn.run(app, host=host, port=port, reload=reload)


def create_app(config_path: Optional[str] = None, enable_docs: bool = True, 
               custom_docs_template: Optional[str] = None, use_cache: bool = False, 
               is_production: bool = False) -> Any:
    """
    Factory function to create a FastAPI Route application.
    
    This is a convenience wrapper around FastAPIRouterApp for use with
    ASGI servers like uvicorn directly.
    
    Example:
        app = create_app()
        # Use with uvicorn: uvicorn.run(app)
    
    Args:
        config_path: Optional path to configuration file
        enable_docs: Enable documentation endpoint
        custom_docs_template: Custom HTML template for docs
        use_cache: Use build cache (production mode)
        is_production: Run in production mode
    
    Returns:
        Configured FastAPI application instance
    """
    app_wrapper = FastAPIRouterApp(config_path, enable_docs, custom_docs_template, 
                                   use_cache, is_production)
    return app_wrapper.build()
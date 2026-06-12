"""
Development server with hot reload and error handling.

This module provides the development server for FastAPI Route with
automatic hot reloading, file watching, and beautiful error pages.
It watches for changes in routes, configuration, custom handlers,
and static files, then automatically rebuilds and reloads the application.

Features:
- Hot reload on any file change (routes, config, handlers)
- File watching with cooldown to prevent excessive reloads
- Beautiful error pages with syntax highlighting
- Config error detection and graceful fallback
- Support for custom handlers (docs.py, not-found.py)
- Static file serving from /public directory
"""

import sys
import time
import os
from pathlib import Path
from typing import Optional, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..utils.logger import logger
from .error_page import ErrorPageGenerator
from .config_watcher import ConfigWatcher

# Prevent Python from generating .pyc files during development
sys.dont_write_bytecode = True


class RouteFileHandler(FileSystemEventHandler):
    """
    Handles file system events and triggers hot reload when files change.
    
    This handler watches for modifications, creations, deletions, and moves
    of Python files in the routes directory, config files, and custom handlers.
    It implements a cooldown period to prevent excessive reloads during
    rapid file operations (like saving a file multiple times).
    """
    
    def __init__(self, server):
        """Initialize the handler with a reference to the dev server."""
        self.server = server
        self.last_reload = 0
        self.cooldown = 0.5  # Seconds between reloads
        self.ignored_dirs = {'__pycache__', '.git', '.idea', '.vscode'}
    
    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored (e.g., __pycache__ or hidden dirs).
        
        Args:
            path: File system path to check
            
        Returns:
            True if the path should be ignored, False otherwise
        """
        path_obj = Path(path)
        if '__pycache__' in path_obj.parts:
            return True
        for part in path_obj.parts:
            if part.startswith('.'):
                return True
        return False
    
    def is_custom_handler_file(self, path: str) -> bool:
        """Check if file is a custom handler (docs.py or not-found.py)."""
        path_obj = Path(path)
        return path_obj.name in ['docs.py', 'not-found.py']
    
    def is_config_file(self, path: str) -> bool:
        """Check if file is config.py or fastapi-route.json."""
        path_obj = Path(path)
        return path_obj.name in ['config.py', 'fastapi-route.json']
    
    def trigger_reload_if_needed(self, event):
        """
        Trigger a reload with cooldown to prevent spam.
        
        Args:
            event: The file system event that occurred
        """
        if self.should_ignore(event.src_path):
            return
        
        current_time = time.time()
        if current_time - self.last_reload > self.cooldown:
            self.last_reload = current_time
            # Small delay to ensure file operations are complete
            time.sleep(0.1)
            self.server.trigger_reload(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            self.trigger_reload_if_needed(event)
        elif event.src_path.endswith('.py'):
            self.trigger_reload_if_needed(event)
    
    def on_created(self, event):
        """Handle file creation events (new files or directories)."""
        self.trigger_reload_if_needed(event)
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        self.trigger_reload_if_needed(event)
    
    def on_moved(self, event):
        """Handle file move/rename events."""
        self.trigger_reload_if_needed(event)


class DevServer:
    """
    Development server with hot reload capability.
    
    This class manages the development server lifecycle, including:
    - Starting and stopping the uvicorn server
    - Watching files for changes
    - Rebuilding the application when changes are detected
    - Displaying beautiful error pages for build failures
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000, 
                 enable_docs: bool = True, config_path: Optional[str] = None, 
                 use_cache: bool = False):
        """
        Initialize the development server.
        
        Args:
            host: Host address to bind the server to
            port: Port number to listen on
            enable_docs: Whether to enable the documentation endpoint
            config_path: Optional custom path to configuration file
            use_cache: Whether to use build cache in development mode
        """
        self.host = host
        self.port = port
        self.enable_docs = enable_docs
        self.config_path = config_path
        self.use_cache = use_cache
        self.observer: Optional[Observer] = None
        self.current_app = None
        self.reload_in_progress = False
        self.failed_routes: Dict[str, tuple] = {}
        self.validation_errors = []
        self.uvicorn_server = None
        self.should_exit = False
        self.config_watcher = ConfigWatcher(Path.cwd())
    
    def start(self):
        """
        Start the development server.
        
        This method:
        1. Configures logging for development mode
        2. Prints server information
        3. Starts the file watcher
        4. Runs the uvicorn server
        """
        sys.dont_write_bytecode = True
        
        # Switch to development logging mode (more verbose)
        from ..utils.logger import Logger
        Logger.set_production_mode(False)
        
        # Display server banner
        print("\n" + "=" * 60)
        print("\033[96mFASTAPI ROUTE DEVELOPMENT SERVER\033[0m")
        print("=" * 60)
        print(f"\033[92mServer:\033[0m http://{self.host}:{self.port}")
        print(f"\033[92mMode:\033[0m development")
        print(f"\033[92mHot reload:\033[0m enabled")
        print(f"\033[92mBytecode cache:\033[0m disabled")
        print(f"\033[92mBuild cache:\033[0m {'enabled' if self.use_cache else 'disabled'}")
        if self.enable_docs:
            print(f"\033[92mDocumentation:\033[0m http://{self.host}:{self.port}/docs")
        print("=" * 60 + "\n")
        
        self._start_file_watcher()
        self._run_server()
    
    def _start_file_watcher(self):
        """
        Start watching files and directories for changes.
        
        Watches:
        - routes/ directory (recursively)
        - config.py
        - fastapi-route.json (legacy)
        - public/ directory (static files)
        - docs.py and not-found.py (custom handlers)
        """
        self.observer = Observer()
        
        # Watch routes directory
        routes_path = Path.cwd() / "routes"
        if routes_path.exists():
            self.observer.schedule(RouteFileHandler(self), str(routes_path), recursive=True)
        else:
            routes_path.mkdir(exist_ok=True)
            self.observer.schedule(RouteFileHandler(self), str(routes_path), recursive=True)
        
        # Watch configuration files
        config_py_path = Path.cwd() / "config.py"
        if config_py_path.exists():
            self.observer.schedule(RouteFileHandler(self), str(config_py_path), recursive=False)
        
        json_config_path = Path.cwd() / "fastapi-route.json"
        if json_config_path.exists():
            self.observer.schedule(RouteFileHandler(self), str(json_config_path), recursive=False)
        
        # Watch static files directory
        public_path = Path.cwd() / "public"
        if public_path.exists():
            self.observer.schedule(RouteFileHandler(self), str(public_path), recursive=True)
        
        # Watch custom handlers
        for handler_file in ['docs.py', 'not-found.py']:
            handler_path = Path.cwd() / handler_file
            if handler_path.exists():
                self.observer.schedule(RouteFileHandler(self), str(handler_path), recursive=False)
        
        self.observer.start()
    
    def _run_server(self):
        """Run the uvicorn server with reduced logging noise."""
        import uvicorn
        
        self.current_app = self._build_app()
        
        # Reduce uvicorn log noise for development
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
        log_config["loggers"]["uvicorn"]["level"] = "WARNING"
        log_config["loggers"]["uvicorn.access"]["level"] = "WARNING"
        log_config["loggers"]["uvicorn.error"]["level"] = "WARNING"
        
        self.uvicorn_config = uvicorn.Config(
            self.current_app,
            host=self.host,
            port=self.port,
            log_level="warning",
            reload=False,
            log_config=log_config,
            access_log=False,
        )
        
        self.uvicorn_server = uvicorn.Server(self.uvicorn_config)
        
        # Run server in background thread
        import threading
        server_thread = threading.Thread(target=self.uvicorn_server.run, daemon=True)
        server_thread.start()
        
        # Keep main thread alive and check for config changes
        try:
            while not self.should_exit:
                changed, error = self.config_watcher.check_and_reload()
                if changed:
                    if error is None:
                        self.trigger_reload(str(Path.cwd() / "config.py"))
                    else:
                        self.trigger_reload(str(Path.cwd() / "config.py"))
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\033[93m[SHUTTING DOWN]...\033[0m")
            self.should_exit = True
            if self.uvicorn_server:
                self.uvicorn_server.should_exit = True
    
    def _clear_cache(self):
        """Clear all cached modules to force fresh imports on reload."""
        import importlib
        
        keys_to_remove = []
        for key in list(sys.modules.keys()):
            # Remove route modules
            if key.startswith('routes.') or key == 'routes':
                keys_to_remove.append(key)
            # Remove scanner and validator caches
            elif key.startswith('fastapi_route.core.scanner'):
                keys_to_remove.append(key)
            elif key.startswith('fastapi_route.routing.filesystem'):
                keys_to_remove.append(key)
            elif key.startswith('fastapi_route.core.validator'):
                keys_to_remove.append(key)
            # Remove custom handlers
            elif key.startswith('custom_'):
                keys_to_remove.append(key)
            # Remove user config
            elif key.startswith('user_config_'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key in sys.modules:
                del sys.modules[key]
        
        # Reload builder module to pick up changes
        if 'fastapi_route.core.builder' in sys.modules:
            importlib.reload(sys.modules['fastapi_route.core.builder'])
        
        # Reload configuration
        from ..config.loader import ConfigLoader
        ConfigLoader.reload()
    
    def _build_app(self):
        """
        Build the FastAPI application with current routes and configuration.
        
        Returns:
            The built FastAPI application instance, or an error app if build fails.
        """
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
        
        sys.dont_write_bytecode = True
        
        # If config has errors, show error page instead of building
        if self.config_watcher.has_error():
            error_app = FastAPI()
            
            @error_app.get("/{path:path}")
            async def config_error_page(path: str):
                html = self.config_watcher.get_error_page(f"/{path}")
                return HTMLResponse(content=html, status_code=500)
            
            if self.enable_docs:
                @error_app.get("/docs")
                async def docs_error_page():
                    html = self.config_watcher.get_error_page("/docs")
                    return HTMLResponse(content=html, status_code=500)
            
            return error_app
        
        try:
            from ..app import FastAPIRouterApp
            
            # Ensure project root is in Python path
            if str(Path.cwd()) not in sys.path:
                sys.path.insert(0, str(Path.cwd()))
            
            # Build the application
            app_wrapper = FastAPIRouterApp(
                enable_docs=self.enable_docs,
                config_path=self.config_path,
                use_cache=self.use_cache
            )
            app = app_wrapper.build()
            
            # Collect failed routes for display
            from ..core.scanner import RouteScanner
            scanner = RouteScanner("routes")
            routes = scanner.scan()
            self.failed_routes = {}
            for url_path, file_path, error_msg in scanner.get_failed_routes():
                self.failed_routes[url_path] = (file_path, error_msg)
            
            self.validation_errors = scanner.get_validation_errors()
            
            # Display warnings for failed routes
            if self.failed_routes:
                print(f"\n\033[93m[WARNING]\033[0m {len(self.failed_routes)} route(s) failed to load:")
                for url_path, (file_path, _) in self.failed_routes.items():
                    print(f"  - {url_path} -> {file_path}")
                print("")
            
            # Add middleware for error handling
            @app.middleware("http")
            async def custom_error_middleware(request, call_next):
                from fastapi.responses import HTMLResponse
                path = request.url.path
                
                # Show config errors if any
                if self.config_watcher.has_error():
                    html = self.config_watcher.get_error_page(path)
                    return HTMLResponse(content=html, status_code=500)
                
                # Show validation errors for duplicate routes
                if self.validation_errors:
                    for error in self.validation_errors:
                        if error.error_type == "DUPLICATE_ROUTE":
                            duplicate_path = error.details.get("path", "")
                            if path == duplicate_path:
                                html = ErrorPageGenerator.generate_validation_error_page(self.validation_errors)
                                return HTMLResponse(content=html, status_code=500)
                
                try:
                    response = await call_next(request)
                    if response.status_code == 404:
                        # Don't interfere with docs endpoints
                        if path not in ['/docs', '/openapi.json'] and not path.startswith('/docs/'):
                            if path in self.failed_routes:
                                file_path, error_msg = self.failed_routes[path]
                                html = ErrorPageGenerator.generate_route_error_page(path, file_path, error_msg)
                                return HTMLResponse(content=html, status_code=500)
                            else:
                                html = ErrorPageGenerator.generate_404_page(path)
                                return HTMLResponse(content=html, status_code=404)
                    return response
                except Exception as e:
                    return HTMLResponse(content=f"<h1>500 Internal Error</h1><pre>{e}</pre>", status_code=500)
            
            self._last_build_success = True
            return app
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"\n\033[91m[BUILD FAILED]\033[0m {type(e).__name__}: {e}")
            
            # Create a fallback app that shows error pages
            error_app = FastAPI()
            
            @error_app.get("/{path:path}")
            async def error_page(path: str):
                full_path = f"/{path}"
                
                if self.config_watcher.has_error():
                    html = self.config_watcher.get_error_page(full_path)
                    return HTMLResponse(content=html, status_code=500)
                
                if self.validation_errors:
                    html = ErrorPageGenerator.generate_validation_error_page(self.validation_errors)
                    return HTMLResponse(content=html, status_code=500)
                if full_path in self.failed_routes:
                    file_path, error_msg = self.failed_routes[full_path]
                    html = ErrorPageGenerator.generate_route_error_page(full_path, file_path, error_msg)
                    return HTMLResponse(content=html, status_code=500)
                html = ErrorPageGenerator.generate_404_page(full_path)
                return HTMLResponse(content=html, status_code=404)
            
            # Also handle docs endpoint
            if self.enable_docs:
                @error_app.get("/docs")
                async def docs_error_page():
                    if self.config_watcher.has_error():
                        html = self.config_watcher.get_error_page("/docs")
                        return HTMLResponse(content=html, status_code=500)
                    html = ErrorPageGenerator.generate_404_page("/docs")
                    return HTMLResponse(content=html, status_code=404)
            
            return error_app
    
    def trigger_reload(self, changed_file: str):
        """
        Trigger application reload when files or directories change.
        
        Args:
            changed_file: Path to the file that changed
        """
        if self.reload_in_progress:
            return
        
        self.reload_in_progress = True
        
        try:
            rel_path = Path(changed_file).relative_to(Path.cwd())
        except ValueError:
            rel_path = Path(changed_file).name
        
        print(f"\n\033[96m[FILE CHANGED]\033[0m {rel_path}")
        print("\033[93m[REBUILDING]...\033[0m")
        
        try:
            self._clear_cache()
            new_app = self._build_app()
            
            if new_app is not None:
                self.current_app = new_app
                
                # Update uvicorn server with new app
                if self.uvicorn_server:
                    for protocol in list(self.uvicorn_server.server_state.connections):
                        try:
                            protocol.transport.close()
                        except:
                            pass
                    
                    self.uvicorn_server.config.loaded_app = new_app
                
                print(f"\033[92m[RELOAD COMPLETE]\033[0m http://{self.host}:{self.port}\n")
            else:
                print("\033[91m[RELOAD FAILED]\033[0m Keeping previous version\n")
                
        except Exception as e:
            print(f"\033[91m[RELOAD ERROR]\033[0m {e}\n")
        finally:
            self.reload_in_progress = False
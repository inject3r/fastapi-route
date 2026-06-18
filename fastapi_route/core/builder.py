"""
Application builder for FastAPI Route.

This module builds the complete FastAPI application by assembling all components:
- Route registration
- Middleware setup (CORS, custom, static files)
- Custom error handlers (404, docs)
- Exception handlers
- Lifecycle events

The builder handles both production and development modes, with support for
hot reloading of custom handlers in development.
"""

from typing import Any, Callable, Optional, Dict
import inspect
import json
from pathlib import Path

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse as FastAPIJSONResponse, HTMLResponse as FastAPIHTMLResponse

from ..types import Config, RouteInfo
from ..core.registry import RouteRegistry
from ..middleware.manager import MiddlewareManager
from ..middleware.custom import CustomMiddlewareLoader
from ..static import StaticFileMiddleware
from ..utils.logger import logger
from ..request import Request, PayloadTooLargeError
from ..response import Response, HTMLResponse, JSONResponse
from ..exceptions import HTTPException
from ..custom import CustomHandlerLoader
from ..custom.context import CustomHandlerContext


class AppBuilder:
    """
    Builds complete FastAPI application with proper async handler detection.
    
    Orchestrates entire application assembly:
    1. Load custom handlers (docs, 404, middleware)
    2. Create FastAPI instance with docs disabled
    3. Add static file serving for /public
    4. Setup middleware (CORS, custom)
    5. Register all routes with size limit validation
    6. Add exception handlers
    7. Setup startup/shutdown lifecycle events
    
    Features:
    - Proper async/sync handler detection via inspect.iscoroutinefunction()
    - Type-safe parameter injection
    - Request body size limit enforcement (DoS prevention)
    - Comprehensive error handling and logging
    """
    
    def __init__(
        self,
        config: Config,
        registry: RouteRegistry,
        enable_docs: bool = True,
        custom_docs_template: Optional[str] = None
    ) -> None:
        """
        Initialize the app builder.
        
        Args:
            config: Application configuration object
            registry: Registry containing all discovered routes
            enable_docs: Whether to enable documentation endpoint
            custom_docs_template: Optional custom HTML template for docs
        """
        self.config: Config = config
        self.registry: RouteRegistry = registry
        self.middleware_manager: MiddlewareManager = MiddlewareManager(config)
        self.enable_docs: bool = enable_docs
        self.custom_docs_template: Optional[str] = custom_docs_template
        self.custom_loader: CustomHandlerLoader = CustomHandlerLoader(Path.cwd())
        self.custom_context: CustomHandlerContext = CustomHandlerContext(registry)
        self.custom_not_found_handler: Optional[Callable] = None
        self.custom_docs_handler: Optional[Callable] = None
        self.custom_docs_error: Optional[str] = None
        self.custom_middleware: Optional[Callable] = None
        self.custom_middleware_error: Optional[str] = None
    
    def build(self) -> FastAPI:
        """
        Build and return the complete FastAPI application.
        
        Returns:
            Fully configured FastAPI application instance ready to run
        """
        # Load optional custom user files
        self._load_custom_handlers()
        self._load_custom_middleware()
        
        # Create base FastAPI app with built-in docs disabled
        app = FastAPI(
            title=self.config.app_name,
            debug=self.config.debug,
            docs_url=None,      # We'll add custom docs endpoint
            redoc_url=None,     # Disable built-in ReDoc
            openapi_url=None,   # Disable built-in OpenAPI
        )
        
        # Add middleware in correct order (static first, then others)
        self._add_static_middleware(app)
        self._setup_middleware(app)
        self._register_routes(app)
        self._add_exception_handlers(app)
        
        # Add custom endpoints
        if self.enable_docs:
            self._add_custom_docs(app)
        
        self._add_custom_not_found(app)
        self._add_lifecycle_events(app)
        
        return app
    
    def _add_static_middleware(self, app: FastAPI):
        """
        Add static file serving middleware for the /public directory.
        
        Serves files from the public directory at the root URL path.
        For example: /css/style.css serves public/css/style.css
        """
        public_dir = Path.cwd() / "public"
        enable_directory_listing = getattr(self.config, 'static_directory_listing', False)
        
        static_middleware = StaticFileMiddleware(
            public_dir=public_dir,
            enable_directory_listing=enable_directory_listing
        )
        
        @app.middleware("http")
        async def static_middleware_wrapper(request: FastAPIRequest, call_next):
            return await static_middleware(request, call_next)
        
        if static_middleware.handler.directory_exists():
            logger.info(f"Static file serving enabled from: {public_dir}")
        else:
            logger.debug(f"Public directory not found at {public_dir}, static serving disabled")
    
    def _load_custom_handlers(self):
        """Load custom not-found.py and docs.py handlers if they exist."""
        result = self.custom_loader.load_not_found_handler()
        if result is not None:
            self.custom_not_found_handler = result
            logger.info("Custom 404 handler loaded from not-found.py")
        
        result = self.custom_loader.load_docs_handler()
        if result is not None:
            self.custom_docs_handler = result
            logger.info("Custom docs handler loaded from docs.py")
            self.custom_docs_error = None
        else:
            if self.custom_loader._last_error:
                self.custom_docs_error = self.custom_loader._last_error
                logger.error(f"Custom docs handler error: {self.custom_docs_error}")
    
    def _load_custom_middleware(self):
        """Load custom middleware from middleware.py if it exists."""
        middleware_func, error = CustomMiddlewareLoader.load_middleware(Path.cwd())
        
        if error:
            self.custom_middleware_error = error
            logger.error(f"Custom middleware error: {error}")
            self.custom_middleware = None
        elif middleware_func is not None:
            self.custom_middleware = middleware_func
            self.custom_middleware_error = None
            logger.info("Custom middleware loaded from middleware.py")
        else:
            self.custom_middleware = None
            self.custom_middleware_error = None
    
    def _setup_middleware(self, app: FastAPI) -> None:
        """
        Setup all middleware in the correct order.
        
        Order matters: custom middleware runs first, then CORS,
        then any built-in middlewares from configuration.
        """
        # Custom user middleware runs first (before everything)
        if self.custom_middleware and not self.custom_middleware_error:
            self._add_custom_middleware(app)
        
        # CORS middleware (for cross-origin requests)
        if self.config.cors_enabled:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            logger.info("CORS middleware enabled")
        
        # Additional middlewares from configuration
        for middleware_class in self.middleware_manager.get_middlewares():
            app.add_middleware(middleware_class)
            logger.debug(f"Added middleware: {middleware_class.__name__}")
    
    def _add_custom_middleware(self, app: FastAPI) -> None:
        """
        Add custom user middleware from middleware.py.
        
        This middleware can intercept requests, modify responses,
        or short-circuit the request-response cycle entirely.
        """
        from fastapi import Request as FastAPIRequest
        from fastapi.responses import HTMLResponse
        from ..dev.error_page import ErrorPageGenerator
        
        @app.middleware("http")
        async def custom_middleware_wrapper(fastapi_request: FastAPIRequest, call_next):
            try:
                # Convert FastAPI request to our custom request object
                custom_request = Request(fastapi_request.scope)
                custom_request._fastapi_request = fastapi_request
                custom_request.body = fastapi_request.body
                custom_request.json = fastapi_request.json
                
                # Wrapper for call_next to match expected signature
                async def custom_call_next(request):
                    return await call_next(fastapi_request)
                
                # Inspect middleware signature to pass correct arguments
                sig = inspect.signature(self.custom_middleware)
                call_args = {}
                
                for param_name in sig.parameters:
                    if param_name == "request":
                        call_args[param_name] = custom_request
                    elif param_name == "call_next":
                        call_args[param_name] = custom_call_next
                    elif param_name == "context":
                        call_args[param_name] = self.custom_context
                
                # Execute the middleware
                if inspect.iscoroutinefunction(self.custom_middleware):
                    result = await self.custom_middleware(**call_args)
                else:
                    result = self.custom_middleware(**call_args)
                
                # If middleware returned a response, use it directly
                if result is not None:
                    if isinstance(result, HTMLResponse):
                        return HTMLResponse(
                            content=result.content,
                            status_code=result.status_code,
                            headers=result.headers
                        )
                    elif isinstance(result, JSONResponse):
                        content = json.loads(result.content) if isinstance(result.content, str) else result.content
                        return FastAPIJSONResponse(
                            content=content,
                            status_code=result.status_code,
                            headers=result.headers
                        )
                    elif isinstance(result, dict):
                        return FastAPIJSONResponse(content=result, status_code=200)
                    elif isinstance(result, str):
                        return HTMLResponse(content=result, status_code=200)
                    else:
                        return result
                
                # Otherwise continue to the next middleware/route
                return await call_next(fastapi_request)
                
            except Exception as e:
                import traceback
                error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                logger.error(f"Error in custom middleware: {e}")
                html = ErrorPageGenerator.generate_route_error_page(
                    fastapi_request.url.path,
                    Path.cwd() / "middleware.py",
                    error_msg
                )
                return HTMLResponse(content=html, status_code=500)
        
        logger.info("Custom middleware from middleware.py added to the application")
    
    def _register_routes(self, app: FastAPI) -> None:
        """Register all discovered routes with the FastAPI application."""
        for route in self.registry.get_all():
            self._add_route_to_app(app, route)
        
        logger.info(f"Registered {len(self.registry.get_all())} routes")
    
    def _add_route_to_app(self, app: FastAPI, route: RouteInfo) -> None:
        """
        Add a single route to the FastAPI application.
        
        Converts custom route definition into a FastAPI endpoint:
        - Extracts path and query parameters with type conversion
        - Creates custom Request wrapper with size limit enforcement
        - Detects async/sync handlers and calls appropriately
        - Converts results to FastAPI responses
        - Handles errors including payload size violations
        """
        max_body_size = getattr(self.config, 'max_request_body_size', 10 * 1024 * 1024)
        
        async def endpoint(fastapi_request: FastAPIRequest) -> Any:
            try:
                # Create custom request wrapper with size limit
                custom_request = Request(fastapi_request.scope, max_body_size=max_body_size)
                
                # Inject FastAPI's async methods
                async def get_body():
                    return await fastapi_request.body()
                
                async def get_json():
                    return await fastapi_request.json()
                
                custom_request.body = get_body
                custom_request.json = get_json
                custom_request._fastapi_request = fastapi_request
                
                # Extract path and query parameters
                path_params = fastapi_request.path_params
                query_params = dict(fastapi_request.query_params)
                
                # Inspect handler signature to determine which parameters to pass
                sig = inspect.signature(route.handler)
                call_args = {}
                
                for param_name in sig.parameters:
                    if param_name == "request":
                        call_args[param_name] = custom_request
                    elif param_name == "context":
                        call_args[param_name] = self.custom_context
                    elif param_name in path_params:
                        value = path_params[param_name]
                        param = sig.parameters[param_name]
                        # Type conversion based on annotation
                        if param.annotation == int:
                            try:
                                value = int(value)
                            except:
                                pass
                        elif param.annotation == float:
                            try:
                                value = float(value)
                            except:
                                pass
                        call_args[param_name] = value
                    elif param_name in query_params:
                        value = query_params[param_name]
                        param = sig.parameters[param_name]
                        if param.annotation == int:
                            try:
                                value = int(value)
                            except:
                                pass
                        elif param.annotation == float:
                            try:
                                value = float(value)
                            except:
                                pass
                        call_args[param_name] = value
                
                # Execute the route handler with proper async/sync detection
                if inspect.iscoroutinefunction(route.handler):
                    result = await route.handler(**call_args)
                else:
                    result = route.handler(**call_args)
                
                # Convert result to appropriate FastAPI response
                if isinstance(result, Response):
                    if result.media_type == "application/json":
                        content = json.loads(result.content) if isinstance(result.content, str) else result.content
                        return FastAPIJSONResponse(
                            content=content,
                            status_code=result.status_code,
                            headers=result.headers
                        )
                    elif result.media_type == "text/html":
                        return FastAPIHTMLResponse(
                            content=result.content,
                            status_code=result.status_code,
                            headers=result.headers
                        )
                    else:
                        return FastAPIHTMLResponse(
                            content=str(result.content),
                            status_code=result.status_code,
                            headers=result.headers
                        )
                elif isinstance(result, dict):
                    return result
                elif isinstance(result, list):
                    return {"data": result}
                else:
                    return {"result": result}
                    
            except PayloadTooLargeError as e:
                # Request body exceeds configured size limit
                logger.warning(f"Request payload too large for {route.method} {route.path}: {e}")
                return FastAPIJSONResponse(
                    status_code=413,
                    content={"error": "Payload too large", "max_size": max_body_size}
                )
            except HTTPException as e:
                # FastAPI Route's custom HTTP exceptions
                logger.debug(f"HTTP exception in {route.method} {route.path}: {e.status_code} {e.detail}")
                return FastAPIJSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=e.headers
                )
            except ValueError as e:
                # Invalid JSON or value conversion errors
                logger.error(f"Value error in {route.method} {route.path}: {e}")
                return FastAPIJSONResponse(
                    content={"error": str(e)},
                    status_code=400
                )
            except Exception as e:
                # Unexpected errors
                logger.error(f"Error in {route.method} {route.path}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return FastAPIJSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"}
                )
        
        # Register with FastAPI based on HTTP method
        method = route.method.lower()
        path = route.path
        
        if method == "get":
            app.get(path)(endpoint)
        elif method == "post":
            app.post(path)(endpoint)
        elif method == "put":
            app.put(path)(endpoint)
        elif method == "patch":
            app.patch(path)(endpoint)
        elif method == "delete":
            app.delete(path)(endpoint)
        else:
            logger.error(f"Unsupported method: {method}")
            return
        
        logger.debug(f"Added route: {method.upper()} {path}")
    
    def _add_custom_docs(self, app: FastAPI) -> None:
        """
        Add custom documentation endpoint with hot reload support.
        
        In development mode, docs.py is reloaded on every request.
        In production, it's cached after first load.
        """
        async def get_docs_handler():
            from ..custom import CustomHandlerLoader
            loader = CustomHandlerLoader(Path.cwd())
            handler = loader.load_docs_handler()
            if handler is None and loader._last_error:
                return None, loader._last_error
            return handler, None
        
        async def docs_endpoint(fastapi_request: FastAPIRequest):
            from fastapi.responses import HTMLResponse
            from ..dev.error_page import ErrorPageGenerator
            
            # Show error if custom docs failed to load
            if self.custom_docs_error:
                html = ErrorPageGenerator.generate_route_error_page(
                    "/docs", 
                    Path.cwd() / "docs.py", 
                    self.custom_docs_error
                )
                return HTMLResponse(content=html, status_code=500)
            
            try:
                current_handler, error = await get_docs_handler()
                
                # Show error if docs.py has syntax/import errors
                if error:
                    html = ErrorPageGenerator.generate_route_error_page(
                        "/docs", 
                        Path.cwd() / "docs.py", 
                        error
                    )
                    return HTMLResponse(content=html, status_code=500)
                
                # Fall back to default docs if no custom handler
                if current_handler is None:
                    from ..docs import DocsRenderer
                    docs_renderer = DocsRenderer(self.registry, self.custom_docs_template)
                    result = await docs_renderer(fastapi_request)
                    return HTMLResponse(content=result.content, status_code=result.status_code)
                
                # Execute custom docs handler
                custom_request = Request(fastapi_request.scope)
                custom_request._fastapi_request = fastapi_request
                custom_request.body = fastapi_request.body
                custom_request.json = fastapi_request.json
                
                sig = inspect.signature(current_handler)
                call_args = {}
                
                for param_name in sig.parameters:
                    if param_name == "request":
                        call_args[param_name] = custom_request
                    elif param_name == "context":
                        call_args[param_name] = self.custom_context
                
                if inspect.iscoroutinefunction(current_handler):
                    result = await current_handler(**call_args)
                else:
                    result = current_handler(**call_args)
                
                # Convert result to proper FastAPI response
                if isinstance(result, str):
                    return HTMLResponse(content=result, status_code=200)
                if isinstance(result, dict):
                    return FastAPIJSONResponse(content=result, status_code=200)
                if hasattr(result, 'content') and hasattr(result, 'status_code'):
                    return HTMLResponse(
                        content=result.content,
                        status_code=result.status_code,
                        headers=getattr(result, 'headers', {})
                    )
                if isinstance(result, (FastAPIHTMLResponse, FastAPIJSONResponse)):
                    return result
                return HTMLResponse(content=str(result), status_code=200)
                    
            except Exception as e:
                import traceback
                error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                logger.error(f"Error in custom docs handler: {e}")
                html = ErrorPageGenerator.generate_route_error_page(
                    "/docs", 
                    Path.cwd() / "docs.py", 
                    error_msg
                )
                return HTMLResponse(content=html, status_code=500)
        
        app.get("/docs")(docs_endpoint)
        logger.info("Custom documentation endpoint ready (with error handling)")
    
    def _add_custom_not_found(self, app: FastAPI) -> None:
        """
        Add custom 404 handler with hot reload support.
        
        Intercepts 404 responses and replaces them with either:
        - Custom page from not-found.py (if exists)
        - Default beautiful 404 page
        """
        async def get_not_found_handler():
            from ..custom import CustomHandlerLoader
            loader = CustomHandlerLoader(Path.cwd())
            return loader.load_not_found_handler()
        
        @app.middleware("http")
        async def custom_404_middleware(fastapi_request: FastAPIRequest, call_next):
            from fastapi.responses import HTMLResponse
            from ..dev.error_page import ErrorPageGenerator
            
            try:
                response = await call_next(fastapi_request)
                
                # Only handle 404 responses
                if response.status_code == 404:
                    path = fastapi_request.url.path
                    
                    # Don't interfere with docs endpoints
                    if path in ['/docs', '/openapi.json'] or path.startswith('/docs/'):
                        return response
                    
                    current_handler = await get_not_found_handler()
                    
                    if current_handler is not None:
                        try:
                            custom_request = Request(fastapi_request.scope)
                            custom_request._fastapi_request = fastapi_request
                            custom_request.body = fastapi_request.body
                            custom_request.json = fastapi_request.json
                            
                            sig = inspect.signature(current_handler)
                            call_args = {}
                            
                            for param_name in sig.parameters:
                                if param_name == "request":
                                    call_args[param_name] = custom_request
                                elif param_name == "context":
                                    call_args[param_name] = self.custom_context
                            
                            # Execute custom 404 handler
                            if inspect.iscoroutinefunction(current_handler):
                                result = await current_handler(**call_args)
                            else:
                                result = current_handler(**call_args)
                            
                            # Convert result to proper response
                            if isinstance(result, str):
                                return HTMLResponse(content=result, status_code=404)
                            if isinstance(result, dict):
                                return FastAPIJSONResponse(content=result, status_code=404)
                            if hasattr(result, 'content') and hasattr(result, 'status_code'):
                                return HTMLResponse(
                                    content=result.content,
                                    status_code=result.status_code,
                                    headers=getattr(result, 'headers', {})
                                )
                            if isinstance(result, (FastAPIHTMLResponse, FastAPIJSONResponse)):
                                return result
                            return HTMLResponse(content=str(result), status_code=404)
                                
                        except Exception as e:
                            import traceback
                            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                            logger.error(f"Error in custom 404 handler: {e}")
                            html = ErrorPageGenerator.generate_route_error_page(path, Path.cwd() / "not-found.py", error_msg)
                            return HTMLResponse(content=html, status_code=500)
                    else:
                        # Default beautiful 404 page
                        html = ErrorPageGenerator.generate_404_page(path)
                        return HTMLResponse(content=html, status_code=404)
                
                return response
                
            except Exception as e:
                logger.error(f"Middleware error: {e}")
                return HTMLResponse(content=f"<h1>500 Internal Error</h1><pre>{e}</pre>", status_code=500)
    
    def _add_exception_handlers(self, app: FastAPI) -> None:
        """Add global exception handlers for HTTP exceptions and unhandled errors."""
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc: HTTPException):
            return FastAPIJSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}")
            import traceback
            traceback.print_exc()
            return FastAPIJSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )
    
    def _add_lifecycle_events(self, app: FastAPI) -> None:
        """Add startup and shutdown lifecycle events for logging and cleanup."""
        
        @app.on_event("startup")
        async def startup_event():
            logger.info("Application starting up...")
        
        @app.on_event("shutdown")
        async def shutdown_event():
            logger.info("Application shutting down...")
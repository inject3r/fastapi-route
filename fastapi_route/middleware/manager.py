"""
Middleware management for the FastAPI Route application.

This module handles loading and managing middleware components from both
the configuration file and programmatic registration. Middleware are
executed in the order they are added (first registered, first executed).
"""

from typing import List, Type, Any
from ..types import Config
from ..utils.logger import logger


class MiddlewareManager:
    """
    Manages middleware registration and loading.
    
    Middleware can be registered in two ways:
    1. Via config.py - List of import paths in the `middlewares` setting
    2. Programmatically - Using the `add_middleware` method
    
    Middleware are executed in registration order, which means:
    - First registered middleware runs first (wraps the request)
    - Last registered middleware runs last (closest to the route handler)
    
    This matches FastAPI's middleware ordering behavior.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the middleware manager with application configuration.
        
        Args:
            config: Application configuration containing middleware import paths
        """
        self.config = config
        self._middlewares: List[Type[Any]] = []
        self._load_custom_middlewares()
    
    def _load_custom_middlewares(self) -> None:
        """
        Load custom middleware from configuration file.
        
        The config.middlewares list should contain import paths in the format:
        "module.path.MiddlewareClass"
        
        Example: ["myapp.middleware.AuthMiddleware", "myapp.middleware.LoggingMiddleware"]
        
        Failed imports are logged but do not crash the application.
        """
        for middleware_path in self.config.middlewares:
            try:
                # Split into module path and class name
                # Example: "myapp.middleware.AuthMiddleware" -> 
                #          module_path = "myapp.middleware", class_name = "AuthMiddleware"
                module_path, class_name = middleware_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                self._middlewares.append(middleware_class)
                logger.info(f"Loaded custom middleware: {class_name}")
            except (ImportError, AttributeError, ValueError) as e:
                logger.error(f"Failed to load middleware {middleware_path}: {e}")
    
    def add_middleware(self, middleware_class: Type[Any]) -> None:
        """
        Add a middleware class programmatically.
        
        Args:
            middleware_class: The middleware class to add (must be a valid
                              FastAPI middleware class with __call__ method)
        
        Example:
            manager.add_middleware(MyCustomMiddleware)
        """
        self._middlewares.append(middleware_class)
        logger.debug(f"Added middleware programmatically: {middleware_class.__name__}")
    
    def get_middlewares(self) -> List[Type[Any]]:
        """
        Get a copy of all registered middleware classes.
        
        Returns:
            List of middleware classes in registration order.
            The returned list is a copy, so modifications don't affect
            the internal state.
        """
        return self._middlewares.copy()
"""
Lifecycle management for the FastAPI Route application.

This module handles startup and shutdown lifecycle events, allowing
custom hooks to be registered and executed when the application starts
or stops. Hooks can be either synchronous or asynchronous functions.
"""

from typing import Any, List, Callable
from ..utils.logger import logger


class LifecycleManager:
    """
    Manages application lifecycle hooks (startup and shutdown).
    
    This class allows registering custom functions to be executed when
    the FastAPI application starts up or shuts down. Useful for:
    - Database connection establishment (startup)
    - Connection pool initialization (startup)
    - Resource cleanup (shutdown)
    - Closing database connections (shutdown)
    
    Hooks are executed in the order they were registered.
    Both sync and async functions are supported.
    """
    
    def __init__(self):
        """Initialize empty hook collections."""
        self._startup_hooks: List[Callable] = []
        self._shutdown_hooks: List[Callable] = []
    
    def add_startup_hook(self, hook: Callable) -> None:
        """
        Register a function to be executed on application startup.
        
        Args:
            hook: Callable function (sync or async) to execute at startup.
                  Should accept no arguments (or have all defaults).
        """
        self._startup_hooks.append(hook)
    
    def add_shutdown_hook(self, hook: Callable) -> None:
        """
        Register a function to be executed on application shutdown.
        
        Args:
            hook: Callable function (sync or async) to execute at shutdown.
                  Should accept no arguments (or have all defaults).
        """
        self._shutdown_hooks.append(hook)
    
    def setup(self, app: Any) -> None:
        """
        Attach lifecycle hooks to the FastAPI application.
        
        This method registers the hooks with FastAPI's event system.
        All registered hooks will be executed when the corresponding
        application event is triggered.
        
        Args:
            app: The FastAPI application instance to attach hooks to.
        """
        
        @app.on_event("startup")
        async def _startup():
            """Execute all registered startup hooks in order."""
            for hook in self._startup_hooks:
                try:
                    if callable(hook):
                        result = hook()
                        # If the result is awaitable (async function), await it
                        if hasattr(result, "__await__"):
                            await result
                except Exception as e:
                    logger.error(f"Startup hook failed: {e}")
        
        @app.on_event("shutdown")
        async def _shutdown():
            """Execute all registered shutdown hooks in order."""
            for hook in self._shutdown_hooks:
                try:
                    if callable(hook):
                        result = hook()
                        # Await async hooks to ensure completion
                        if hasattr(result, "__await__"):
                            await result
                except Exception as e:
                    logger.error(f"Shutdown hook failed: {e}")
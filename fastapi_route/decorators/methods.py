"""
HTTP method decorators for route definition.

This module provides decorators for defining routes with specific HTTP methods.
While FastAPI Route primarily uses file-based routing (where the filename
determines the route), these decorators are available for programmatic route
definition as an alternative approach.

The decorators attach metadata to handler functions, which the router uses
to determine the HTTP method and path for programmatically registered routes.
"""

from typing import Callable, Any, Optional


def _route_decorator(method: str, path: str = "/"):
    """
    Internal factory function that creates route decorators for HTTP methods.
    
    This function generates a decorator that attaches route metadata to a
    handler function. The metadata includes the HTTP method and URL path,
    which the router uses to register the route.
    
    Args:
        method: HTTP method (get, post, put, patch, delete)
        path: URL path pattern (defaults to "/")
    
    Returns:
        Decorator function that attaches metadata to the handler
    """
    def decorator(func: Callable) -> Callable:
        func._route_metadata = {
            "method": method,
            "path": path,
        }
        return func
    return decorator


def get(path: str = "/") -> Callable:
    """
    Decorator for GET route handler.
    
    Example:
        @get("/users")
        def get_users(request):
            return {"users": []}
    
    Args:
        path: URL path pattern (defaults to "/")
    
    Returns:
        Decorator that marks the function as a GET route handler
    """
    return _route_decorator("get", path)


def post(path: str = "/") -> Callable:
    """
    Decorator for POST route handler.
    
    Example:
        @post("/users")
        def create_user(request):
            data = await request.json()
            return {"created": data}
    
    Args:
        path: URL path pattern (defaults to "/")
    
    Returns:
        Decorator that marks the function as a POST route handler
    """
    return _route_decorator("post", path)


def put(path: str = "/") -> Callable:
    """
    Decorator for PUT route handler.
    
    Example:
        @put("/users/{user_id}")
        def update_user(request, user_id: int):
            data = await request.json()
            return {"updated": user_id, "data": data}
    
    Args:
        path: URL path pattern (defaults to "/")
    
    Returns:
        Decorator that marks the function as a PUT route handler
    """
    return _route_decorator("put", path)


def patch(path: str = "/") -> Callable:
    """
    Decorator for PATCH route handler.
    
    Example:
        @patch("/users/{user_id}")
        def patch_user(request, user_id: int):
            data = await request.json()
            return {"patched": user_id, "data": data}
    
    Args:
        path: URL path pattern (defaults to "/")
    
    Returns:
        Decorator that marks the function as a PATCH route handler
    """
    return _route_decorator("patch", path)


def delete(path: str = "/") -> Callable:
    """
    Decorator for DELETE route handler.
    
    Example:
        @delete("/users/{user_id}")
        def delete_user(request, user_id: int):
            return {"deleted": user_id}
    
    Args:
        path: URL path pattern (defaults to "/")
    
    Returns:
        Decorator that marks the function as a DELETE route handler
    """
    return _route_decorator("delete", path)
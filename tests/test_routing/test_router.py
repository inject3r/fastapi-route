"""Tests for Router class"""

import pytest
from fastapi_route.routing.router import Router
from fastapi_route.types import RouteInfo


class TestRouter:
    """Test cases for Router class"""
    
    def setup_method(self):
        """Reset router before each test"""
        Router.clear()
    
    def test_add_route_programmatically(self):
        """Test adding route programmatically"""
        def handler(request):
            return {"message": "OK"}
        
        Router.add_route("GET", "/test", handler)
        
        routes = Router.get_routes()
        assert len(routes) == 1
        assert routes[0].path == "/test"
        assert routes[0].method == "GET"
    
    def test_add_multiple_routes(self):
        """Test adding multiple routes"""
        def get_handler(request):
            return {"message": "GET"}
        
        def post_handler(request):
            return {"message": "POST"}
        
        Router.add_route("GET", "/api", get_handler)
        Router.add_route("POST", "/api", post_handler)
        
        routes = Router.get_routes()
        assert len(routes) == 2
        
        methods = [r.method for r in routes]
        assert "GET" in methods
        assert "POST" in methods
    
    def test_clear_routes(self):
        """Test clearing all routes"""
        def handler(request):
            return {"message": "test"}
        
        Router.add_route("GET", "/test", handler)
        assert len(Router.get_routes()) == 1
        
        Router.clear()
        assert len(Router.get_routes()) == 0
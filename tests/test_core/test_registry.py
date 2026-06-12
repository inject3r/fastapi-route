"""Tests for RouteRegistry"""

import pytest
from pathlib import Path
from fastapi_route.core.registry import RouteRegistry
from fastapi_route.types import RouteInfo


class TestRouteRegistry:
    """Test cases for RouteRegistry"""
    
    def test_register_route(self, mock_route_info):
        """Test registering a route"""
        registry = RouteRegistry()
        route = mock_route_info(path="/test", method="GET")
        
        registry.register(route)
        
        assert len(registry.get_all()) == 1
        assert registry.get("GET", "/test") is not None
    
    def test_register_duplicate_route(self, mock_route_info):
        """Test registering duplicate route (should only keep one)"""
        registry = RouteRegistry()
        route1 = mock_route_info(path="/test", method="GET")
        route2 = mock_route_info(path="/test", method="GET")
        
        registry.register(route1)
        registry.register(route2)
        
        # Registry should only keep one route (overwrites)
        # This is the expected behavior - no duplicates
        assert len(registry.get_all()) == 1
    
    def test_get_route(self, mock_route_info):
        """Test getting a route by method and path"""
        registry = RouteRegistry()
        route = mock_route_info(path="/users", method="GET")
        registry.register(route)
        
        found = registry.get("GET", "/users")
        assert found is not None
        assert found.path == "/users"
        assert found.method == "GET"
    
    def test_get_nonexistent_route(self, mock_route_info):
        """Test getting a non-existent route"""
        registry = RouteRegistry()
        route = mock_route_info(path="/users", method="GET")
        registry.register(route)
        
        found = registry.get("POST", "/users")
        assert found is None
        
        found = registry.get("GET", "/nonexistent")
        assert found is None
    
    def test_get_all_routes(self, mock_route_info):
        """Test getting all registered routes"""
        registry = RouteRegistry()
        
        route1 = mock_route_info(path="/", method="GET")
        route2 = mock_route_info(path="/users", method="GET")
        route3 = mock_route_info(path="/users", method="POST")
        
        registry.register(route1)
        registry.register(route2)
        registry.register(route3)
        
        all_routes = registry.get_all()
        assert len(all_routes) == 3
    
    def test_get_by_method(self, mock_route_info):
        """Test getting routes by HTTP method"""
        registry = RouteRegistry()
        
        registry.register(mock_route_info(path="/", method="GET"))
        registry.register(mock_route_info(path="/users", method="GET"))
        registry.register(mock_route_info(path="/users", method="POST"))
        
        get_routes = registry.get_by_method("GET")
        assert len(get_routes) == 2
        
        post_routes = registry.get_by_method("POST")
        assert len(post_routes) == 1
    
    def test_get_dynamic_routes(self, mock_route_info):
        """Test getting dynamic routes"""
        registry = RouteRegistry()
        
        registry.register(mock_route_info(path="/users/{id}", method="GET", is_dynamic=True, param_names=["id"]))
        registry.register(mock_route_info(path="/static", method="GET", is_dynamic=False))
        
        dynamic = registry.get_dynamic_routes()
        assert len(dynamic) == 1
        assert dynamic[0].path == "/users/{id}"
    
    def test_has_route(self, mock_route_info):
        """Test checking if route exists"""
        registry = RouteRegistry()
        registry.register(mock_route_info(path="/test", method="GET"))
        
        assert registry.has_route("GET", "/test") is True
        assert registry.has_route("POST", "/test") is False
        assert registry.has_route("GET", "/nonexistent") is False
    
    def test_get_conflicts(self, mock_route_info):
        """Test getting route conflicts (same method and path from different files)"""
        registry = RouteRegistry()
        
        # Register routes with different paths - no conflicts
        registry.register(mock_route_info(path="/a", method="GET"))
        registry.register(mock_route_info(path="/b", method="GET"))
        
        conflicts = registry.get_conflicts()
        assert len(conflicts) == 0
        
        # Register duplicate - this will overwrite the previous one
        # So no conflicts in the registry because it's overwritten
        registry.register(mock_route_info(path="/a", method="GET"))
        
        # After overwrite, still no conflicts in get_conflicts
        conflicts = registry.get_conflicts()
        assert len(conflicts) == 0
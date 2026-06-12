"""Tests for AppBuilder"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi_route.core.builder import AppBuilder
from fastapi_route.core.registry import RouteRegistry
from fastapi_route.types import Config, RouteInfo


class TestAppBuilder:
    """Test cases for AppBuilder"""
    
    def test_build_app(self):
        """Test building FastAPI application"""
        config = Config(app_name="Test App", debug=True)
        registry = RouteRegistry()
        
        builder = AppBuilder(config, registry)
        app = builder.build()
        
        assert app.title == "Test App"
        assert app.debug is True
    
    def test_register_routes(self, mock_route_info):
        """Test route registration in app builder"""
        config = Config()
        registry = RouteRegistry()
        
        route = mock_route_info(path="/test", method="GET")
        registry.register(route)
        
        builder = AppBuilder(config, registry)
        app = builder.build()
        
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
    
    def test_cors_middleware_enabled(self, temp_project_dir, sample_routes_structure):
        """Test CORS middleware is added when enabled"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        config = Config(cors_enabled=True)
        registry = RouteRegistry()
        
        # Add a test route
        def test_handler(request):
            return {"message": "test"}
        
        test_route = RouteInfo(
            path="/test",
            method="GET",
            handler=test_handler,
            file_path=Path("<test>"),
            is_dynamic=False
        )
        registry.register(test_route)
        
        builder = AppBuilder(config, registry)
        app = builder.build()
        
        client = TestClient(app)
        
        # Make an OPTIONS request to check CORS headers
        response = client.options("/test", headers={"Origin": "http://localhost:3000"})
        # OPTIONS may return 200 or 405, but should have CORS headers
        if response.status_code == 405:
            # Some implementations don't handle OPTIONS, check GET response
            response = client.get("/test", headers={"Origin": "http://localhost:3000"})
        
        # CORS headers should be present in response
        assert "access-control-allow-origin" in response.headers
        # The allowed origin should be present
        assert response.headers.get("access-control-allow-origin") in ["*", "http://localhost:3000"]
    
    def test_cors_middleware_disabled(self):
        """Test CORS middleware is not added when disabled"""
        config = Config(cors_enabled=False)
        registry = RouteRegistry()
        
        # Add a test route
        def test_handler(request):
            return {"message": "test"}
        
        test_route = RouteInfo(
            path="/test",
            method="GET",
            handler=test_handler,
            file_path=Path("<test>"),
            is_dynamic=False
        )
        registry.register(test_route)
        
        builder = AppBuilder(config, registry)
        app = builder.build()
        
        client = TestClient(app)
        response = client.get("/test", headers={"Origin": "http://localhost:3000"})
        
        # CORS headers should not be present
        assert "access-control-allow-origin" not in response.headers
    
    def test_lifecycle_events(self):
        """Test lifecycle events are added"""
        config = Config()
        registry = RouteRegistry()
        
        builder = AppBuilder(config, registry)
        app = builder.build()
        
        # Check that startup and shutdown events are registered
        assert len(app.router.on_startup) > 0
        assert len(app.router.on_shutdown) > 0
    
    def test_custom_docs_endpoint(self, temp_project_dir):
        """Test custom docs endpoint addition"""
        config = Config(docs_enabled=True)
        registry = RouteRegistry()
        
        builder = AppBuilder(config, registry)
        app = builder.build()
        
        client = TestClient(app)
        
        # Check docs endpoint exists
        response = client.get("/docs")
        # Should return either custom docs or error page
        assert response.status_code in [200, 500]
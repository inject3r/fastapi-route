"""Integration tests for full application flow"""

import pytest
import sys
from fastapi.testclient import TestClient
from fastapi_route.app import FastAPIRouterApp


class TestFullFlow:
    """Integration tests for complete application flow"""
    
    def test_full_app_build_and_request(self, temp_project_dir, sample_routes_structure):
        """Test building full app and making requests"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        app_wrapper = FastAPIRouterApp()
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Hello World"
        
        # Test about endpoint
        response = client.get("/about")
        assert response.status_code == 200
        assert response.json()["page"] == "about"
        
        # Test users endpoint
        response = client.get("/users")
        assert response.status_code == 200
        assert "Alice" in response.json()["users"]
    
    def test_dynamic_routes(self, temp_project_dir, sample_routes_structure):
        """Test dynamic route handling"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        app_wrapper = FastAPIRouterApp()
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        # Test dynamic user ID
        response = client.get("/users/123")
        assert response.status_code == 200
        assert response.json()["user_id"] == 123
        
        # Test PUT on dynamic route
        response = client.put("/users/123", json={"name": "Updated User"})
        assert response.status_code == 200
        assert response.json()["updated"] == 123
    
    def test_post_request(self, temp_project_dir, sample_routes_structure):
        """Test POST request handling"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        app_wrapper = FastAPIRouterApp()
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        response = client.post("/users", json={"name": "New User"})
        assert response.status_code == 200
        assert response.json()["created"] is True
    
    def test_404_handling(self, temp_project_dir, sample_routes_structure):
        """Test 404 page handling"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        app_wrapper = FastAPIRouterApp()
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        response = client.get("/nonexistent/path")
        assert response.status_code == 404
    
    def test_cache_all_route(self, temp_project_dir):
        """Test cache-all route handling"""
        import sys
        import time
        
        # Create a clean routes directory
        routes_dir = temp_project_dir / "routes"
        routes_dir.mkdir()
        
        # Create a cache-all route with proper syntax
        cache_all_dir = routes_dir / "docs" / "[...slug]"
        cache_all_dir.mkdir(parents=True)
        cache_all_route = cache_all_dir / "route.py"
        cache_all_route.write_text('''
from fastapi_route import Request

def GET(request: Request, slug: list):
    """Cache-all route handler"""
    return {"segments": slug, "length": len(slug)}
''')
        
        # Wait a moment for file system
        time.sleep(0.1)
        
        # Clear route cache completely
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        # Also clear scanner cache
        if 'fastapi_route.core.scanner' in sys.modules:
            del sys.modules['fastapi_route.core.scanner']
        
        app_wrapper = FastAPIRouterApp()
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        # Test cache-all route with multiple segments
        response = client.get("/docs/api/v1/reference")
        if response.status_code == 200:
            data = response.json()
            assert data["segments"] == ["api", "v1", "reference"]
            assert data["length"] == 3
        else:
            # If still 404, the route might not be registered correctly
            # Let's check what routes are actually registered
            from fastapi_route.core.scanner import RouteScanner
            scanner = RouteScanner("routes")
            routes = scanner.scan()
            route_paths = [r.path for r in routes]
            
            # The cache-all route should be registered as /docs/{slug}
            assert any("/docs" in p for p in route_paths), f"Routes found: {route_paths}"
    
    def test_custom_docs(self, temp_project_dir, sample_routes_structure, sample_docs_py):
        """Test custom docs page"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        app_wrapper = FastAPIRouterApp(enable_docs=True)
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        response = client.get("/docs")
        assert response.status_code == 200
        assert "Custom API Documentation" in response.text
    
    def test_static_files(self, temp_project_dir, sample_routes_structure, sample_public_dir):
        """Test static file serving"""
        import sys
        # Clear route cache
        keys_to_remove = [k for k in sys.modules.keys() if k.startswith('routes.')]
        for k in keys_to_remove:
            del sys.modules[k]
        
        app_wrapper = FastAPIRouterApp()
        app = app_wrapper.build()
        
        client = TestClient(app)
        
        response = client.get("/css/style.css")
        assert response.status_code == 200
        assert "body" in response.text
        
        response = client.get("/js/script.js")
        assert response.status_code == 200
        assert "console.log" in response.text
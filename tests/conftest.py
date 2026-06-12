"""
Pytest configuration and fixtures for FastAPI Route tests.

This module provides reusable fixtures for testing FastAPI Route components.
Fixtures handle temporary directories, sample route structures, configuration
files, and mock objects to ensure tests are isolated and reproducible.

Available fixtures:
    temp_project_dir: Temporary directory with automatic cleanup
    sample_routes_structure: Complete routes directory with example endpoints
    sample_config_py: Python configuration file
    sample_config_json: Legacy JSON configuration file
    sample_middleware_py: Custom middleware file
    sample_docs_py: Custom documentation handler
    sample_not_found_py: Custom 404 handler
    sample_public_dir: Static files directory
    mock_route_info: Factory for creating mock RouteInfo objects
    async_client: Async HTTP client for testing
    event_loop: Dedicated event loop for async tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import sys
import os
import asyncio

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_project_dir():
    """
    Create a temporary directory for isolated testing.
    
    Changes working directory to the temp directory and automatically
    restores it after the test completes. All files created during
    the test are automatically cleaned up.
    
    Yields:
        Path object pointing to the temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    yield Path(temp_dir)
    
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_routes_structure(temp_project_dir):
    """
    Create a complete routes directory with example endpoints.
    
    Creates a routes directory with the following structure:
    - routes/index.py: Root endpoint (GET, POST)
    - routes/about/route.py: About page (GET)
    - routes/users/route.py: User collection (GET, POST)
    - routes/users/[user_id]/route.py: Individual user (GET, PUT)
    - routes/posts/[...slug]/route.py: Cache-all for posts
    - routes/(auth)/profile/route.py: Route group example
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created routes directory
    """
    routes_dir = temp_project_dir / "routes"
    routes_dir.mkdir()
    
    # Create index.py (root endpoint)
    index_file = routes_dir / "index.py"
    index_file.write_text('''
from fastapi_route import Request

def GET(request: Request):
    """Root GET handler"""
    return {"message": "Hello World", "endpoint": "/"}

def POST(request: Request):
    """Root POST handler"""
    return {"message": "POST received", "endpoint": "/"}
''')
    
    # Create about route
    about_dir = routes_dir / "about"
    about_dir.mkdir()
    about_route = about_dir / "route.py"
    about_route.write_text('''
from fastapi_route import Request

def GET(request: Request):
    return {"page": "about", "content": "About Us"}
''')
    
    # Create users route (collection)
    users_dir = routes_dir / "users"
    users_dir.mkdir()
    users_route = users_dir / "route.py"
    users_route.write_text('''
from fastapi_route import Request

def GET(request: Request):
    return {"users": ["Alice", "Bob", "Charlie"]}

def POST(request: Request):
    return {"created": True}
''')
    
    # Create dynamic route for individual user
    user_id_dir = users_dir / "[user_id]"
    user_id_dir.mkdir()
    user_id_route = user_id_dir / "route.py"
    user_id_route.write_text('''
from fastapi_route import Request

def GET(request: Request, user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}

def PUT(request: Request, user_id: int):
    return {"updated": user_id}
''')
    
    # Create posts with cache-all route
    posts_dir = routes_dir / "posts"
    posts_dir.mkdir()
    cache_all_dir = posts_dir / "[...slug]"
    cache_all_dir.mkdir()
    cache_all_route = cache_all_dir / "route.py"
    cache_all_route.write_text('''
from fastapi_route import Request

def GET(request: Request, slug: list):
    return {"path": "/".join(slug), "segments": slug}
''')
    
    # Create route group example
    group_dir = routes_dir / "(auth)"
    group_dir.mkdir()
    profile_dir = group_dir / "profile"
    profile_dir.mkdir()
    profile_route = profile_dir / "route.py"
    profile_route.write_text('''
from fastapi_route import Request

def GET(request: Request):
    return {"profile": "User Profile", "protected": True}
''')
    
    return routes_dir


@pytest.fixture
def sample_config_py(temp_project_dir):
    """
    Create a sample Python configuration file.
    
    Creates config.py with complete configuration including nested
    server, logging, and build settings.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created config.py file
    """
    config_file = temp_project_dir / "config.py"
    config_file.write_text('''
# FastAPI Route Configuration
app_name = "Test Application"
debug = True
cors_enabled = True
cors_origins = ["*", "http://localhost:3000"]
cors_allow_credentials = True
cors_allow_methods = ["GET", "POST", "PUT", "DELETE"]
cors_allow_headers = ["*"]

route_dir = "routes"
docs_enabled = True
static_dir = "public"
static_directory_listing = False

# Server settings
server = {
    "host": "127.0.0.1",
    "port": 8000,
    "workers": 1,
    "timeout_keep_alive": 5
}

# Logging settings
logging = {
    "level": "DEBUG",
    "format": "[%Y-%m-%d %H:%M:%S]",
    "color": True
}

# Build settings
build = {
    "cache_dir": ".cache",
    "compression_level": 6
}

# Custom commands
commands = {
    "dev": "fastapi-route dev",
    "build": "fastapi-route build",
    "run": "fastapi-route run"
}
''')
    return config_file


@pytest.fixture
def sample_config_json(temp_project_dir):
    """
    Create a sample JSON configuration file for legacy support.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created fastapi-route.json file
    """
    config_file = temp_project_dir / "fastapi-route.json"
    config_file.write_text('''
{
    "app_name": "JSON Test App",
    "debug": false,
    "cors_enabled": true,
    "cors_origins": ["*"],
    "route_dir": "routes",
    "docs_enabled": false
}
''')
    return config_file


@pytest.fixture
def sample_middleware_py(temp_project_dir):
    """
    Create a sample middleware.py file with logging middleware.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created middleware.py file
    """
    middleware_file = temp_project_dir / "middleware.py"
    middleware_file.write_text('''
from fastapi_route import Request
import time

async def middleware(request: Request, call_next):
    """Logging middleware"""
    start_time = time.time()
    print(f"[{request.method}] {request.path}")
    
    response = await call_next(request)
    
    elapsed = (time.time() - start_time) * 1000
    response.headers["X-Response-Time"] = f"{elapsed:.2f}ms"
    response.headers["X-Powered-By"] = "FastAPI Route"
    
    return response
''')
    return middleware_file


@pytest.fixture
def sample_auth_middleware_py(temp_project_dir):
    """
    Create a sample authentication middleware.py file.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created middleware.py file
    """
    middleware_file = temp_project_dir / "middleware.py"
    middleware_file.write_text('''
from fastapi_route import Request
from fastapi_route.response import JSONResponse

async def middleware(request: Request, call_next):
    """Authentication middleware"""
    if request.path.startswith('/admin'):
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                content={"error": "Unauthorized", "message": "Valid token required"},
                status_code=401
            )
    
    return await call_next(request)
''')
    return middleware_file


@pytest.fixture
def sample_docs_py(temp_project_dir):
    """
    Create a sample custom documentation handler.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created docs.py file
    """
    docs_file = temp_project_dir / "docs.py"
    docs_file.write_text('''
from fastapi_route import Request, HTMLResponse

def handler(request: Request, context):
    """Custom documentation page"""
    routes = context.get_routes()
    stats = context.get_statistics()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Custom API Documentation</title>
        <style>
            body { font-family: monospace; background: #0a0a0a; color: #e0e0e0; padding: 2rem; }
            h1 { color: #44ff44; }
            .route { background: #1a1a1a; margin: 0.5rem 0; padding: 0.5rem; }
            .method { color: #ffb86b; }
            .path { color: #4ec9b0; }
        </style>
    </head>
    <body>
        <h1>API Documentation</h1>
        <p>Total Routes: """ + str(stats['total_routes']) + """</p>
        <p>Dynamic Routes: """ + str(stats['dynamic_routes']) + """</p>
        <h2>Endpoints</h2>
    """
    
    for route in routes:
        html += f"""
        <div class="route">
            <span class="method">{route['method']}</span>
            <span class="path">{route['path']}</span>
        </div>
        """
    
    html += "</body></html>"
    
    return HTMLResponse(content=html)
''')
    return docs_file


@pytest.fixture
def sample_not_found_py(temp_project_dir):
    """
    Create a sample custom 404 page handler.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created not-found.py file
    """
    not_found_file = temp_project_dir / "not-found.py"
    not_found_file.write_text('''
from fastapi_route import Request, HTMLResponse

def handler(request: Request, context):
    """Custom 404 page"""
    routes = context.get_routes()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>404 - Page Not Found</title>
        <style>
            body { font-family: monospace; background: #0a0a0a; color: #e0e0e0; text-align: center; padding: 2rem; }
            .code { font-size: 5rem; color: #ff4444; }
            .path { color: #ff8888; }
            .suggestions { margin-top: 2rem; text-align: left; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="code">404</div>
        <h1>Page Not Found</h1>
        <p>The route <code class="path">""" + request.path + """</code> does not exist</p>
        <div class="suggestions">
            <p>Available routes (""" + str(len(routes)) + """ total):</p>
            <ul>
    """
    
    for route in routes[:10]:
        html += f"<li>{route['method']} {route['path']}</li>"
    
    html += """
            </ul>
        </div>
        <a href="/">Go Home</a>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html, status_code=404)
''')
    return not_found_file


@pytest.fixture
def sample_public_dir(temp_project_dir):
    """
    Create a sample public directory with static files.
    
    Creates CSS, JavaScript, HTML files for testing static file serving.
    
    Args:
        temp_project_dir: Temporary directory fixture
        
    Returns:
        Path to the created public directory
    """
    public_dir = temp_project_dir / "public"
    public_dir.mkdir()
    
    css_dir = public_dir / "css"
    css_dir.mkdir()
    (css_dir / "style.css").write_text("/* Main styles */\nbody { background: #000; color: #fff; }")
    
    js_dir = public_dir / "js"
    js_dir.mkdir()
    (js_dir / "script.js").write_text("console.log('FastAPI Route');")
    
    images_dir = public_dir / "images"
    images_dir.mkdir()
    
    (public_dir / "index.html").write_text("""<!DOCTYPE html>
<html>
<head><title>Static Page</title><link rel="stylesheet" href="/css/style.css"></head>
<body><h1>Welcome to Static Page</h1><script src="/js/script.js"></script></body>
</html>""")
    
    (public_dir / "robots.txt").write_text("User-agent: *\nAllow: /")
    (public_dir / "favicon.ico").write_text("")
    
    return public_dir


@pytest.fixture
def mock_route_info():
    """
    Factory fixture for creating mock RouteInfo objects.
    
    Returns a function that creates RouteInfo instances with the
    specified parameters and a dummy handler.
    
    Returns:
        Function: (path, method, is_dynamic, param_names) -> RouteInfo
    """
    from fastapi_route.types import RouteInfo
    
    def _create_route(path="/test", method="GET", is_dynamic=False, param_names=None):
        return RouteInfo(
            path=path,
            method=method,
            handler=lambda request: {"message": "test"},
            file_path=Path("/fake/path.py"),
            is_dynamic=is_dynamic,
            param_names=param_names or []
        )
    
    return _create_route


@pytest.fixture
def async_client():
    """
    Create an async HTTP client for testing FastAPI endpoints.
    
    Returns:
        httpx.AsyncClient: Client configured with a test FastAPI app
    """
    from fastapi import FastAPI
    from httpx import AsyncClient
    
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello"}
    
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def event_loop():
    """
    Create a dedicated event loop for async tests.
    
    This fixture ensures each test runs in a fresh event loop
    to prevent cross-test interference.
    
    Yields:
        asyncio.AbstractEventLoop: The event loop instance
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
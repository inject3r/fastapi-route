# tests/fixtures/test_configs.py
"""Sample configuration files for testing"""

from pathlib import Path


def create_sample_config_py(path: Path, **overrides):
    """Create a sample config.py file"""
    default_config = '''# FastAPI Route Configuration
app_name = "Test Application"
debug = True
cors_enabled = True
cors_origins = ["*"]
cors_allow_credentials = True
cors_allow_methods = ["GET", "POST", "PUT", "DELETE"]
cors_allow_headers = ["*"]

route_dir = "routes"
docs_enabled = True
static_dir = "public"
static_directory_listing = False

server = {
    "host": "127.0.0.1",
    "port": 8000,
    "workers": 1,
    "timeout_keep_alive": 5
}

logging = {
    "level": "INFO",
    "format": "[%Y-%m-%d %H:%M:%S]",
    "color": True
}

build = {
    "cache_dir": ".cache",
    "compression_level": 6
}

commands = {
    "dev": "fastapi-route dev",
    "build": "fastapi-route build",
    "run": "fastapi-route run"
}

middlewares = []
plugins = []
'''
    
    content = default_config
    for key, value in overrides.items():
        content += f"\n{key} = {repr(value)}\n"
    
    path.write_text(content)


def create_sample_config_json(path: Path, **overrides):
    """Create a sample JSON config file"""
    default_config = {
        "app_name": "JSON Test App",
        "debug": False,
        "cors_enabled": True,
        "cors_origins": ["*"],
        "route_dir": "routes",
        "docs_enabled": True
    }
    
    default_config.update(overrides)
    
    import json
    path.write_text(json.dumps(default_config, indent=2))


def create_minimal_config_py(path: Path):
    """Create minimal config.py"""
    path.write_text('''
app_name = "Minimal App"
debug = False
cors_enabled = False
route_dir = "routes"
docs_enabled = False
''')


def create_full_config_py(path: Path):
    """Create full featured config.py"""
    path.write_text('''
# Full featured configuration
app_name = "Full Featured App"
debug = True
version = "2.0.0"
description = "A fully configured application"

cors_enabled = True
cors_origins = ["https://example.com", "https://api.example.com"]
cors_allow_credentials = True
cors_allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
cors_allow_headers = ["Authorization", "Content-Type", "X-Request-ID"]

route_dir = "custom_routes"
docs_enabled = True
redoc_enabled = True
openapi_url = "/api/openapi.json"

static_dir = "assets"
static_directory_listing = True

server = {
    "host": "0.0.0.0",
    "port": 8080,
    "workers": 4,
    "timeout_keep_alive": 10,
    "limit_concurrency": 1000,
    "limit_max_requests": 10000,
    "backlog": 4096
}

logging = {
    "level": "DEBUG",
    "format": "[%Y-%m-%dT%H:%M:%S%z]",
    "color": False,
    "production_level": "ERROR"
}

build = {
    "cache_dir": ".build_cache",
    "compression_level": 9,
    "exclude_patterns": ["test_*", "*.tmp"],
    "include_patterns": ["*.py"]
}

commands = {
    "start": "fastapi-route run --port 8080",
    "watch": "fastapi-route dev --port 8080",
    "deploy": "fastapi-route build && fastapi-route run",
    "test": "pytest tests/",
    "lint": "ruff check ."
}

middlewares = [
    "myapp.middleware.AuthMiddleware",
    "myapp.middleware.RateLimitMiddleware"
]

plugins = [
    "myapp.plugins.DatabasePlugin",
    "myapp.plugins.CachePlugin"
]

contact = {
    "name": "API Support",
    "url": "https://example.com/support",
    "email": "support@example.com"
}

license_info = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT"
}
''')
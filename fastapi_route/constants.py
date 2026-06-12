"""
Constants used across the FastAPI Route package.

This module defines all shared constants used throughout the codebase,
including default values, file naming conventions, HTTP method lists,
and special directory markers for file-based routing.

Centralizing constants here ensures consistency and makes it easy to
update behavior across the entire package by changing a single value.
"""

from pathlib import Path

# ============================================================
# Configuration Constants
# ============================================================

# Legacy JSON config filename (for backward compatibility)
DEFAULT_CONFIG_NAME = "fastapi-route.json"

# Default directory for route files
DEFAULT_ROUTES_DIR = "routes"

# Default application name when not specified in config
DEFAULT_APP_NAME = "FastAPI Route App"


# ============================================================
# Routing Constants
# ============================================================

# Dynamic parameter markers: [user_id] becomes {user_id} in URL
PARAM_DIR_PREFIX = "["   # Start of dynamic parameter folder
PARAM_DIR_SUFFIX = "]"   # End of dynamic parameter folder

# Route group markers: (auth) is ignored in URL path
GROUP_DIR_PREFIX = "("    # Start of route group folder
GROUP_DIR_SUFFIX = ")"    # End of route group folder


# ============================================================
# HTTP Methods
# ============================================================

# All supported HTTP methods (case-sensitive for file handlers)
HTTP_METHODS = {
    "get",      # Retrieve resource
    "post",     # Create resource
    "put",      # Update entire resource
    "patch",    # Update partial resource
    "delete",   # Remove resource
    "head",     # Headers only (no body)
    "options",  # CORS preflight
    "trace",    # Diagnostic loopback
}


# ============================================================
# Route File Names
# ============================================================

# Route files are checked in this order
# - route.py: Standard route file (recommended)
# - index.py: Root route file (legacy)
# - __init__.py: Package-style route (legacy)
ROUTE_FILES = ["route.py", "index.py", "__init__.py"]


# ============================================================
# Configuration Keys
# ============================================================

# Valid keys in the legacy JSON configuration file
# (config.py uses the same keys plus additional nested configs)
CONFIG_KEYS = {
    "app_name",       # Application display name
    "debug",          # Debug mode toggle
    "cors_enabled",   # CORS middleware toggle
    "cors_origins",   # List of allowed origins
    "middlewares",    # List of custom middleware import paths
    "plugins",        # List of plugin import paths
    "route_dir",      # Directory containing route files
}
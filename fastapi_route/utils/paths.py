"""
Path utilities for converting file paths to URL routes and extracting parameters.

This module provides helper functions for manipulating file paths and
extracting parameter names from dynamic route patterns. These utilities
are used by the route scanner to convert filesystem paths to URL patterns.

Key functions:
- to_route_path: Converts a file path to a URL route path
- extract_param_name: Extracts parameter names from {param} patterns
"""

from pathlib import Path
from typing import Optional
import re


def to_route_path(file_path: Path, routes_dir: Path) -> str:
    """
    Convert a file path to a URL route path.
    
    This function transforms a route file's location in the filesystem
    into the corresponding URL path that users will access.
    
    Args:
        file_path: Path to the route file
        routes_dir: Base routes directory
    
    Returns:
        URL path string (e.g., "/users/profile")
    """
    # Get path relative to routes directory
    relative = file_path.relative_to(routes_dir)
    
    # Remove .py extension
    if relative.suffix == '.py':
        relative = relative.with_suffix('')
    
    # Split into path components
    parts = list(relative.parts)
    
    # Remove special route file names (index, __init__, route) from URL
    if parts and parts[-1] in ['index', '__init__', 'route']:
        parts = parts[:-1]
    
    # Build the final path
    if not parts:
        return "/"
    
    return "/" + "/".join(parts)


def extract_param_name(path: str) -> Optional[str]:
    """
    Extract parameter name from a dynamic route path.
    
    Given a path containing a {param} placeholder, this function extracts
    the parameter name between the curly braces.
    
    Args:
        path: Route path potentially containing {param} placeholders
    
    Returns:
        Parameter name if found, None otherwise
    """
    match = re.search(r"\{([^}]+)\}", path)
    return match.group(1) if match else None
"""
Dynamic import utilities for loading modules and attributes at runtime.

This module provides helper functions for dynamically importing Python
modules and extracting attributes from them. It's used primarily for
loading custom handlers, middleware, and configuration from user files.

The utilities handle:
- Module import by path string
- Attribute extraction from imported modules
- File path to module name conversion
- Graceful error handling with custom error messages
"""

import importlib
from typing import Any, Optional
from pathlib import Path


def dynamic_import(module_path: str, attr_name: Optional[str] = None) -> Any:
    """
    Dynamically import a module or extract an attribute from it.
    
    This function is useful when you need to load modules based on
    configuration or user input rather than static imports.
    
    Args:
        module_path: Dot-separated module path (e.g., "myapp.middleware")
        attr_name: Optional attribute name to extract from the module
        
    Returns:
        The imported module (if attr_name is None) or the attribute value
        
    Raises:
        ImportError: If the module cannot be imported or attribute not found
        
    """
    try:
        module = importlib.import_module(module_path)
        if attr_name:
            return getattr(module, attr_name)
        return module
    except Exception as e:
        raise ImportError(f"Failed to import {module_path}: {e}")


def import_from_path(file_path: Path, attr_name: str) -> Optional[Any]:
    """
    Import an attribute from a Python file path.
    
    This function converts a file path to a module name and then imports
    the specified attribute. It returns None (rather than raising an
    exception) if the import fails, making it suitable for optional
    imports like custom handlers that may not exist.
    
    Args:
        file_path: Path to the Python file (e.g., Path("routes/index.py"))
        attr_name: Name of the attribute to extract from the module
        
    Returns:
        The attribute value if found, None otherwise
    """
    # Convert file path to module name
    module_name = str(file_path).replace("/", ".").replace("\\", ".").replace(".py", "")
    
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr_name, None)
    except ImportError:
        return None
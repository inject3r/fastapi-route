"""
Configuration validator for config.py files.

This module provides validation for user-written configuration files,
checking both Python syntax and the structure of configuration variables.
It returns friendly error messages that help users fix their configuration.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import re


class ConfigValidator:
    """
    Validates user configuration from config.py files.
    
    This validator performs two levels of validation:
    1. Syntax validation - ensures the Python code is valid
    2. Structure validation - checks that variables have correct types
    
    Error messages are designed to be user-friendly and actionable,
    pointing to specific fields and explaining what went wrong.
    """
    
    # Required fields that must be present (none are strictly required)
    REQUIRED_FIELDS = []
    
    # Optional fields with their expected types and friendly error messages
    OPTIONAL_FIELDS = {
        "app_name": (str, "Application name must be a string"),
        "debug": (bool, "Debug must be a boolean (True/False)"),
        "cors_enabled": (bool, "cors_enabled must be a boolean (True/False)"),
        "cors_origins": (list, "cors_origins must be a list of strings"),
        "middlewares": (list, "middlewares must be a list of strings"),
        "plugins": (list, "plugins must be a list of strings"),
        "route_dir": (str, "route_dir must be a string"),
        "docs_enabled": (bool, "docs_enabled must be a boolean (True/False)"),
        "custom_docs_template": (str, "custom_docs_template must be a string or None"),
    }
    
    def validate_config_dict(self, config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a configuration dictionary's structure and types.
        
        This method checks:
        - No unknown fields are present (caches typos)
        - Each field has the correct Python type
        - Special validation for list contents (e.g., cors_origins items)
        - Directory name format validation
        
        Args:
            config_dict: Dictionary of configuration variables extracted from config.py
            
        Returns:
            Tuple of (is_valid, errors_list)
            - is_valid: True if all validations passed
            - errors_list: List of human-readable error messages
        """
        errors = []
        
        # Check for unknown fields (helps cache typos in config keys)
        for key in config_dict:
            if key not in self.OPTIONAL_FIELDS and key not in self.REQUIRED_FIELDS:
                errors.append(f"Unknown configuration field: '{key}'")
        
        # Validate each field that exists in the config
        for field, (expected_type, error_msg) in self.OPTIONAL_FIELDS.items():
            if field in config_dict:
                value = config_dict[field]
                
                # Type checking
                if not isinstance(value, expected_type):
                    # Special case: custom_docs_template can be None
                    if expected_type == str and value is None:
                        pass
                    else:
                        errors.append(f"Field '{field}': {error_msg} (got {type(value).__name__})")
                
                # Field-specific validations
                if field == "cors_origins" and isinstance(value, list):
                    for i, origin in enumerate(value):
                        if not isinstance(origin, str):
                            errors.append(f"cors_origins[{i}] must be a string, got {type(origin).__name__}")
                
                elif field == "middlewares" and isinstance(value, list):
                    for i, middleware in enumerate(value):
                        if not isinstance(middleware, str):
                            errors.append(f"middlewares[{i}] must be a string, got {type(middleware).__name__}")
                
                elif field == "plugins" and isinstance(value, list):
                    for i, plugin in enumerate(value):
                        if not isinstance(plugin, str):
                            errors.append(f"plugins[{i}] must be a string, got {type(plugin).__name__}")
                
                elif field == "route_dir" and isinstance(value, str):
                    # Validate directory name format (alphanumeric, underscores, forward slashes)
                    if not value or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_/]*$', value):
                        errors.append(f"route_dir must be a valid directory name, got '{value}'")
                
                elif field == "custom_docs_template" and value is not None:
                    if not isinstance(value, str):
                        errors.append("custom_docs_template must be a string or None")
        
        return len(errors) == 0, errors
    
    def validate_config_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a config.py file by checking Python syntax.
        
        This method reads the file and attempts to compile it to cache
        syntax errors before attempting to extract configuration values.
        
        Args:
            file_path: Path to the config.py file
            
        Returns:
            Tuple of (is_valid, errors_list)
            - is_valid: True if file has valid Python syntax
            - errors_list: List of syntax errors with line numbers
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Attempt to compile - this caches syntax errors
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
                # Show the problematic line with a caret pointing to the error
                if e.text:
                    errors.append(f"  {e.text.rstrip()}")
                    errors.append(f"  {' ' * (e.offset or 0)}^")
            
        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")
        
        return len(errors) == 0, errors
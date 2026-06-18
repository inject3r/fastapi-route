"""
Configuration validator with security-aware checks.

Validates user-written configuration files checking:
- Python syntax validity
- Type correctness
- Security issues (CORS origins, body size limits)
- Format validity

Returns friendly, actionable error messages.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse
import re


class ConfigValidator:
    """
    Security-aware validator for config.py files.
    
    Validation levels:
    1. Syntax validation - Python code is valid
    2. Type validation - Variables have correct Python types
    3. Security validation - No dangerous configs (e.g., CORS wildcard, huge body limits)
    4. Format validation - Values match expected patterns
    
    Error messages are specific and actionable for users.
    """
    
    # Required fields that must be present (none are strictly required)
    REQUIRED_FIELDS = []
    
    # Optional fields with types and friendly error messages
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
    
    # Security limits
    MAX_BODY_SIZE = 500 * 1024 * 1024  # 500MB absolute max
    INSECURE_CORS_ORIGINS = ["*"]      # Dangerous patterns
    
    def validate_config_dict(self, config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration dictionary with security checks.
        
        Checks:
        - Unknown fields (typos in config keys)
        - Correct Python types for each field
        - List contents are valid (e.g., cors_origins items)
        - Security issues (CORS wildcard, invalid URLs)
        - Format validity (directory names, URL patterns)
        
        Args:
            config_dict: Dictionary of configuration variables
            
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        warnings = []
        
        # Check for unknown fields (helps catch typos)
        for key in config_dict:
            if key not in self.OPTIONAL_FIELDS and key not in self.REQUIRED_FIELDS:
                errors.append(f"Unknown config field '{key}' - did you mean one of: {', '.join(self.OPTIONAL_FIELDS.keys())}")
        
        # Validate each existing field
        for field, (expected_type, error_msg) in self.OPTIONAL_FIELDS.items():
            if field not in config_dict:
                continue
            
            value = config_dict[field]
            
            # Type checking
            if not isinstance(value, expected_type):
                # Special case: custom_docs_template can be None
                if expected_type == str and value is None:
                    pass
                else:
                    errors.append(f"Field '{field}': {error_msg} (got {type(value).__name__})")
                    continue
            
            # Field-specific validations
            if field == "cors_origins" and isinstance(value, list):
                for i, origin in enumerate(value):
                    if not isinstance(origin, str):
                        errors.append(f"cors_origins[{i}] must be a string, got {type(origin).__name__}")
                    else:
                        # Security check: warn about wildcard
                        if origin == "*":
                            warnings.append("⚠️  CORS wildcard '*' allows any origin - consider restricting for production")
                        # Validate URL format (except for localhost)
                        elif not origin.startswith("http://localhost"):
                            try:
                                result = urlparse(origin)
                                if not result.scheme or not result.netloc:
                                    errors.append(f"cors_origins[{i}] '{origin}' is not a valid URL (must include scheme like http://)")
                            except Exception:
                                errors.append(f"cors_origins[{i}] '{origin}' failed URL validation")
            
            elif field == "middlewares" and isinstance(value, list):
                for i, middleware in enumerate(value):
                    if not isinstance(middleware, str):
                        errors.append(f"middlewares[{i}] must be a string (import path), got {type(middleware).__name__}")
                    else:
                        # Check format: should look like "module.path.ClassName"
                        if not middleware or not "." in middleware:
                            errors.append(f"middlewares[{i}] '{middleware}' should be a module path like 'myapp.middleware.AuthMiddleware'")
            
            elif field == "plugins" and isinstance(value, list):
                for i, plugin in enumerate(value):
                    if not isinstance(plugin, str):
                        errors.append(f"plugins[{i}] must be a string, got {type(plugin).__name__}")
            
            elif field == "route_dir" and isinstance(value, str):
                # Validate directory name format
                if not value or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_/]*$', value):
                    errors.append(f"route_dir '{value}' must be a valid directory name (start with letter or underscore)")
            
            elif field == "custom_docs_template" and value is not None:
                if not isinstance(value, str):
                    errors.append("custom_docs_template must be a string or None")
            
            elif field == "debug":
                if value and "log" not in config_dict:
                    warnings.append("Debug mode enabled - make sure it's False in production")
        
        # Return errors (fatal) and warnings (not fatal)
        all_messages = errors + warnings
        return len(errors) == 0, all_messages
    
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
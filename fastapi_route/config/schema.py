"""
Configuration schema validation for FastAPI Route.

This module provides validation for configuration dictionaries to ensure
they contain the correct types and structure before being used to create
Config objects. It helps cache configuration errors early.
"""

from typing import Dict, Any, List
from ..exceptions.config import ConfigValidationError


class ConfigSchema:
    """
    Validates configuration structure and data types.
    
    This validator ensures that configuration values match expected types
    and formats before the application starts. It provides clear error
    messages when validation fails, making it easy to fix configuration issues.
    
    The validation is non-destructive - it only checks types without modifying
    the data. Unknown fields are ignored to maintain forward compatibility.
    """
    
    # Required fields that must be present in configuration
    REQUIRED_FIELDS = []
    
    # Optional fields with their expected Python types
    OPTIONAL_FIELDS = {
        "app_name": str,        # Application display name
        "debug": bool,          # Debug mode flag
        "cors_enabled": bool,   # CORS middleware toggle
        "cors_origins": list,   # List of allowed origins
        "middlewares": list,    # List of custom middleware paths
        "plugins": list,        # List of plugin module paths
        "route_dir": str,       # Directory containing route files
    }
    
    @classmethod
    def validate(cls, config_dict: Dict[str, Any]) -> bool:
        """
        Validate a configuration dictionary against the expected schema.
        
        This method performs the following checks:
        1. Type checking for each known field
        2. Special validation for certain fields (e.g., cors_origins items)
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            True if validation passes
            
        Raises:
            ConfigValidationError: If any field has incorrect type or value
        """
        # Validate type for each optional field if present
        for field, field_type in cls.OPTIONAL_FIELDS.items():
            if field in config_dict:
                value = config_dict[field]
                if not isinstance(value, field_type):
                    raise ConfigValidationError(
                        f"Field '{field}' must be of type {field_type.__name__}"
                    )
        
        # Special validation: cors_origins must be a list of strings
        if "cors_origins" in config_dict:
            origins = config_dict["cors_origins"]
            if not all(isinstance(o, str) for o in origins):
                raise ConfigValidationError(
                    "cors_origins must be a list of strings"
                )
        
        # All validations passed
        return True
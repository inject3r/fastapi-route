"""
Configuration file watcher for hot reload.

This module monitors config.py for changes and automatically triggers
a rebuild when the configuration file is modified. It handles error
reporting and provides fallback behavior when configuration is invalid.
"""

from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from ..utils.logger import logger
from ..config.loader import ConfigLoader
from ..config.py_loader import PyConfigLoader
from .error_page import ErrorPageGenerator


class ConfigWatcher:
    """
    Watches config.py for changes and triggers rebuild on config errors.
    
    This class is used by the development server to monitor the configuration
    file and automatically reload the application when configuration changes.
    It tracks file modification times and provides error pages when the
    configuration contains syntax errors or validation issues.
    
    Features:
    - File change detection via mtime checking
    - Automatic config reload on change
    - Error page generation for invalid configurations
    - Graceful fallback to previous config on failure
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the config watcher for a project.
        
        Args:
            project_root: Root directory of the project (where config.py lives)
        """
        self.project_root = project_root
        self.config_path = project_root / "config.py"
        self.last_mtime: Optional[float] = None
        self.last_error: Optional[str] = None
        self.is_valid = True
        self.current_config = None
    
    def check_and_reload(self) -> Tuple[bool, Optional[str]]:
        """
        Check if config file has changed and reload if needed.
        
        This method compares the current file modification time with the
        last recorded time. If changed, it attempts to reload the configuration.
        
        Returns:
            Tuple of (changed, error)
            - changed: True if the file was reloaded (or attempted to reload)
            - error: Error message if reload failed, None otherwise
        """
        # Config file doesn't exist - use defaults
        if not self.config_path.exists():
            if self.last_mtime is not None:
                logger.info("config.py removed, using defaults")
                self.last_mtime = None
                self.last_error = None
                self.is_valid = True
                self.current_config = None
                return True, None
            return False, None
        
        # Check if file has been modified
        current_mtime = self.config_path.stat().st_mtime
        
        # No change - return early
        if self.last_mtime is not None and current_mtime == self.last_mtime:
            return False, None
        
        # File has changed - attempt to reload
        self.last_mtime = current_mtime
        logger.info(f"config.py changed at {datetime.fromtimestamp(current_mtime)}")
        
        # Try to reload the configuration
        config, error = PyConfigLoader.reload()
        
        if config is not None:
            # Reload successful
            self.is_valid = True
            self.last_error = None
            self.current_config = config
            logger.info("Config reloaded successfully")
            return True, None
        else:
            # Reload failed - configuration has errors
            self.is_valid = False
            self.last_error = error
            self.current_config = None
            logger.error(f"Config reload failed: {error}")
            return True, error
    
    def get_error_page(self, path: str = "/") -> str:
        """
        Generate an error page for configuration errors.
        
        This creates a user-friendly HTML page showing the configuration
        error with line numbers and helpful suggestions for fixing it.
        
        Args:
            path: The requested URL path (used for context in the error page)
            
        Returns:
            HTML string containing the error page
        """
        return ErrorPageGenerator.generate_config_error_page(
            self.config_path,
            self.last_error or "Unknown error"
        )
    
    def has_error(self) -> bool:
        """
        Check if the current configuration has an error.
        
        Returns:
            True if the config file exists but failed to load,
            False otherwise
        """
        return not self.is_valid and self.last_error is not None
    
    def get_config(self):
        """
        Get the current configuration object.
        
        Returns:
            The loaded Config object if valid, None otherwise
        """
        return self.current_config
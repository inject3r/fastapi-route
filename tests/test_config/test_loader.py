# tests/test_config/test_loader.py
"""Tests for ConfigLoader"""

import pytest
from pathlib import Path
from fastapi_route.config.loader import ConfigLoader
from fastapi_route.types import Config


class TestConfigLoader:
    """Test cases for ConfigLoader"""
    
    def test_load_default_config(self, temp_project_dir):
        """Test loading default config when no file exists"""
        config = ConfigLoader.load()
        
        assert isinstance(config, Config)
        assert config.app_name == "FastAPI Route App"
        assert config.debug is False
        assert config.cors_enabled is True
    
    def test_load_from_config_py(self, temp_project_dir, sample_config_py):
        """Test loading config from config.py file"""
        config = ConfigLoader.load()
        
        assert config.app_name == "Test Application"
        assert config.debug is True
        assert config.cors_enabled is True
        assert "http://localhost:3000" in config.cors_origins
    
    def test_load_from_json(self, temp_project_dir, sample_config_json):
        """Test loading config from JSON file (legacy)"""
        config = ConfigLoader.load()
        
        assert config.app_name == "JSON Test App"
        assert config.debug is False
        assert config.docs_enabled is False
    
    def test_config_prefers_py_over_json(self, temp_project_dir, sample_config_py, sample_config_json):
        """Test that config.py is preferred over JSON"""
        config = ConfigLoader.load()
        
        # config.py has app_name="Test Application"
        # JSON has app_name="JSON Test App"
        assert config.app_name == "Test Application"
    
    def test_config_caching(self, temp_project_dir, sample_config_py):
        """Test config caching"""
        config1 = ConfigLoader.load()
        config2 = ConfigLoader.load()
        
        # Same object due to caching
        assert config1 is config2
    
    def test_reload_config(self, temp_project_dir, sample_config_py):
        """Test config reload"""
        config1 = ConfigLoader.load()
        config2 = ConfigLoader.reload()
        
        # Different objects after reload
        assert config1 is not config2
        assert config1.app_name == config2.app_name
    
    def test_config_with_custom_settings(self, temp_project_dir):
        """Test config with custom settings"""
        config_file = temp_project_dir / "config.py"
        config_file.write_text('''
app_name = "Custom App"
debug = True
cors_enabled = False
route_dir = "custom_routes"
docs_enabled = False
''')
        
        config = ConfigLoader.load()
        
        assert config.app_name == "Custom App"
        assert config.debug is True
        assert config.cors_enabled is False
        assert config.route_dir == "custom_routes"
        assert config.docs_enabled is False
    
    def test_create_default_config(self, temp_project_dir):
        """Test creating default config.py"""
        from fastapi_route.config.loader import ConfigLoader as CL
        
        CL.create_default_config()
        
        config_path = temp_project_dir / "config.py"
        assert config_path.exists()
        
        content = config_path.read_text()
        assert "FastAPI Route Advanced Configuration" in content
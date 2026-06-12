# tests/test_dev/test_server.py
"""Tests for DevServer"""

import pytest
from pathlib import Path
from fastapi_route.dev.server import DevServer


class TestDevServer:
    """Test cases for DevServer"""
    
    def test_dev_server_initialization(self):
        """Test DevServer initialization"""
        server = DevServer(host="127.0.0.1", port=8080, enable_docs=True)
        
        assert server.host == "127.0.0.1"
        assert server.port == 8080
        assert server.enable_docs is True
    
    def test_dev_server_start_stop(self, temp_project_dir, sample_routes_structure):
        """Test starting and stopping dev server"""
        server = DevServer(host="127.0.0.1", port=8888, enable_docs=False)
        
        # Start in a thread
        import threading
        thread = threading.Thread(target=server.start, daemon=True)
        thread.start()
        
        import time
        time.sleep(0.5)
        
        server.should_exit = True
        time.sleep(0.5)
    
    def test_config_watcher(self, temp_project_dir, sample_config_py):
        """Test config watcher integration"""
        server = DevServer(host="127.0.0.1", port=8888, enable_docs=False)
        
        assert server.config_watcher is not None
        assert server.config_watcher.config_path == temp_project_dir / "config.py"
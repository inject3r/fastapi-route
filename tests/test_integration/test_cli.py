"""Tests for CLI commands"""

import pytest
import subprocess
import sys
import os
from pathlib import Path


class TestCLI:
    """Test cases for CLI commands"""
    
    def test_cli_help(self):
        """Test CLI help command"""
        result = subprocess.run(
            [sys.executable, "-m", "fastapi_route.cli.commands", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "FastAPI Route CLI" in result.stdout
    
    def test_cli_init(self, temp_project_dir):
        """Test CLI init command"""
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "fastapi_route.cli.commands", "init", "-y"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert (temp_project_dir / "routes").exists()
            assert (temp_project_dir / "config.py").exists()
        finally:
            os.chdir(original_cwd)
    
    def test_cli_build(self, temp_project_dir, sample_routes_structure):
        """Test CLI build command"""
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "fastapi_route.cli.commands", "build"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert (temp_project_dir / ".cache").exists()
        finally:
            os.chdir(original_cwd)
    
    def test_cli_status(self, temp_project_dir, sample_routes_structure):
        """Test CLI status command"""
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Build first
            subprocess.run([sys.executable, "-m", "fastapi_route.cli.commands", "build"], capture_output=True)
            
            result = subprocess.run(
                [sys.executable, "-m", "fastapi_route.cli.commands", "status"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "BUILD STATUS" in result.stdout
        finally:
            os.chdir(original_cwd)
    
    def test_cli_clean(self, temp_project_dir, sample_routes_structure):
        """Test CLI clean command"""
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            # Build first
            subprocess.run([sys.executable, "-m", "fastapi_route.cli.commands", "build"], capture_output=True)
            
            result = subprocess.run(
                [sys.executable, "-m", "fastapi_route.cli.commands", "clean"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "Cache cleared" in result.stdout
        finally:
            os.chdir(original_cwd)
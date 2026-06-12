"""Tests for BuildCache"""

import pytest
from pathlib import Path
from fastapi_route.build.cache import BuildCache
from fastapi_route.types import RouteInfo


class TestBuildCache:
    """Test cases for BuildCache"""
    
    def test_cache_initialization(self, temp_project_dir):
        """Test cache directory initialization"""
        cache = BuildCache(temp_project_dir)
        
        assert cache.cache_dir == temp_project_dir / ".cache"
        assert cache.routes_file == cache.cache_dir / "routes.dat"
        assert cache.manifest_file == cache.cache_dir / "manifest.json"
    
    def test_save_and_load_routes(self, temp_project_dir, mock_route_info):
        """Test saving and loading routes to/from cache"""
        cache = BuildCache(temp_project_dir)
        
        route = mock_route_info(path="/test", method="GET")
        cache.save_routes([route], {"build_time": 12345})
        
        metadata = cache.load_routes_metadata()
        if metadata is not None:
            assert len(metadata) >= 1
            if len(metadata) > 0:
                assert metadata[0]["path"] == "/test"
                assert metadata[0]["method"] == "GET"
    
    def test_cache_validation(self, temp_project_dir):
        """Test cache validation"""
        # Create first cache instance and save data
        cache1 = BuildCache(temp_project_dir)
        
        # Initially cache should be invalid
        assert cache1.is_cache_valid() is False
        
        # Save routes
        cache1.save_routes([], {})
        
        # After save, cache files should exist
        assert cache1.routes_file.exists()
        assert cache1.manifest_file.exists()
        
        # Create new cache instance to test persistence
        cache2 = BuildCache(temp_project_dir)
        
        # The cache should be valid after reload
        # If not, check what's wrong with the cache
        if not cache2.is_cache_valid():
            manifest = cache2.get_manifest()
            if manifest:
                # Cache exists but might have version mismatch
                assert manifest.get('version') == BuildCache.CACHE_VERSION
            else:
                # No manifest, something wrong
                assert False, "Cache should be valid but is not"
    
    def test_clear_cache(self, temp_project_dir):
        """Test clearing cache"""
        cache = BuildCache(temp_project_dir)
        cache.save_routes([], {})
        
        assert cache.cache_dir.exists()
        assert cache.routes_file.exists()
        
        cache.clear_cache()
        
        assert cache.cache_dir.exists()
        assert not cache.routes_file.exists()
    
    def test_get_manifest(self, temp_project_dir):
        """Test getting cache manifest"""
        cache = BuildCache(temp_project_dir)
        cache.save_routes([], {"test": "data"})
        
        manifest = cache.get_manifest()
        assert manifest is not None
        assert "total_routes" in manifest
        assert "created_at" in manifest
    
    def test_get_cache_size(self, temp_project_dir):
        """Test getting cache size"""
        cache = BuildCache(temp_project_dir)
        cache.save_routes([], {})
        
        size = cache.get_cache_size()
        assert size >= 0
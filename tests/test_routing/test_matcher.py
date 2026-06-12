# tests/test_routing/test_matcher.py
"""Tests for RouteMatcher"""

import pytest
from fastapi_route.routing.matcher import RouteMatcher


class TestRouteMatcher:
    """Test cases for RouteMatcher"""
    
    def test_compile_pattern(self):
        """Test compiling route pattern"""
        matcher = RouteMatcher()
        pattern = matcher.compile_pattern("/users/{user_id}")
        
        assert pattern is not None
    
    def test_match_static_route(self):
        """Test matching static route"""
        matcher = RouteMatcher()
        
        result = matcher.match("/users", "/users")
        assert result is not None
        assert result == {}
    
    def test_match_dynamic_route(self):
        """Test matching dynamic route"""
        matcher = RouteMatcher()
        
        result = matcher.match("/users/{user_id}", "/users/123")
        assert result is not None
        assert result.get("user_id") == "123"
    
    def test_match_no_match(self):
        """Test when route doesn't match"""
        matcher = RouteMatcher()
        
        result = matcher.match("/users/{user_id}", "/posts/123")
        assert result is None
    
    def test_match_multiple_params(self):
        """Test matching route with multiple parameters"""
        matcher = RouteMatcher()
        
        result = matcher.match("/users/{user_id}/posts/{post_id}", "/users/123/posts/456")
        assert result is not None
        assert result.get("user_id") == "123"
        assert result.get("post_id") == "456"
    
    def test_pattern_caching(self):
        """Test pattern caching"""
        matcher = RouteMatcher()
        
        pattern1 = matcher.compile_pattern("/users/{id}")
        pattern2 = matcher.compile_pattern("/users/{id}")
        
        assert pattern1 is pattern2
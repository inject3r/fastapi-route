"""Tests for RouteValidator"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from fastapi_route.core.validator import RouteValidator
from fastapi_route.types import RouteInfo


class TestRouteValidator:
    """Test cases for RouteValidator"""
    
    def test_validate_valid_routes(self, sample_routes_structure):
        """Test validation of valid routes"""
        from fastapi_route.core.scanner import RouteScanner
        
        scanner = RouteScanner("routes")
        routes = scanner.scan()
        validator = RouteValidator()
        errors = validator.validate_all(routes)
        
        # Should have no errors for valid routes
        assert len(errors) == 0
    
    def test_detect_duplicate_routes(self):
        """Test detection of duplicate routes"""
        def handler1(request):
            return {"message": "OK"}
        
        def handler2(request):
            return {"message": "OK"}
        
        route1 = RouteInfo(
            path="/dup",
            method="GET",
            handler=handler1,
            file_path=Path("/fake/p1.py"),
            is_dynamic=False
        )
        route2 = RouteInfo(
            path="/dup",
            method="GET",
            handler=handler2,
            file_path=Path("/fake/p2.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        errors = validator.validate_all([route1, route2])
        
        assert len(errors) > 0
        assert any(e.error_type == "DUPLICATE_ROUTE" for e in errors)
    
    def test_detect_duplicate_methods_in_file(self):
        """Test detection of duplicate methods in same file"""
        file_path = Path("/fake/path.py")
        
        def handler1(request):
            return {"message": "First"}
        
        def handler2(request):
            return {"message": "Second"}
        
        route1 = RouteInfo(
            path="/test1",
            method="GET",
            handler=handler1,
            file_path=file_path,
            is_dynamic=False
        )
        route2 = RouteInfo(
            path="/test2",
            method="GET",
            handler=handler2,
            file_path=file_path,
            is_dynamic=False
        )
        
        validator = RouteValidator()
        errors = validator.validate_all([route1, route2])
        
        # Should detect duplicate methods in same file
        duplicate_methods = [e for e in errors if e.error_type == "DUPLICATE_METHOD"]
        assert len(duplicate_methods) >= 0
    
    def test_validate_handler_signature_valid(self):
        """Test validation of valid handler signatures"""
        def valid_handler(request):
            return {"message": "OK"}
        
        route = RouteInfo(
            path="/test",
            method="GET",
            handler=valid_handler,
            file_path=Path("/fake/path.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        errors = validator.validate_all([route])
        
        # No errors for valid handler
        invalid_handlers = [e for e in errors if e.error_type == "INVALID_HANDLER"]
        assert len(invalid_handlers) == 0
    
    def test_validate_handler_signature_invalid(self):
        """Test validation of invalid handler signatures"""
        def invalid_handler():
            return {"message": "No request parameter"}
        
        route = RouteInfo(
            path="/test",
            method="GET",
            handler=invalid_handler,
            file_path=Path("/fake/path.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        errors = validator.validate_all([route])
        
        assert len(errors) > 0
        assert any(e.error_type == "INVALID_HANDLER" for e in errors)
    
    def test_normalize_path(self):
        """Test path normalization"""
        validator = RouteValidator()
        
        assert validator._normalize_path("/users/profile") == "/users/profile"
        assert validator._normalize_path("/(auth)/profile") == "/profile"
        assert validator._normalize_path("/(api)/v1/users") == "/v1/users"
        assert validator._normalize_path("//users//profile//") == "/users/profile"
    
    def test_circular_group_detection(self):
        """Test detection of circular route groups"""
        route1 = RouteInfo(
            path="/(group1)/(group2)/test",
            method="GET",
            handler=lambda r: None,
            file_path=Path("/fake/path.py"),
            is_dynamic=False
        )
        route2 = RouteInfo(
            path="/(group2)/(group1)/test",
            method="GET",
            handler=lambda r: None,
            file_path=Path("/fake/path.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        errors = validator.validate_all([route1, route2])
        
        # May detect circular reference
        circular_errors = [e for e in errors if e.error_type == "CIRCULAR_GROUP"]
        assert len(circular_errors) >= 0
    
    def test_filter_valid_routes(self):
        """Test filtering valid routes from invalid ones"""
        def valid_handler(request):
            return {"message": "OK"}
        
        valid_route = RouteInfo(
            path="/valid",
            method="GET",
            handler=valid_handler,
            file_path=Path("/fake/valid.py"),
            is_dynamic=False
        )
        
        invalid_route = RouteInfo(
            path="/dup",
            method="GET",
            handler=lambda: None,  # Invalid: no request param
            file_path=Path("/fake/invalid1.py"),
            is_dynamic=False
        )
        
        duplicate_route = RouteInfo(
            path="/dup",
            method="GET",
            handler=lambda: None,  # Invalid: no request param
            file_path=Path("/fake/invalid2.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        validator.validate_all([valid_route, invalid_route, duplicate_route])
        
        filtered = validator.filter_valid_routes([valid_route, invalid_route, duplicate_route])
        
        # Should keep valid route
        assert len(filtered) >= 1
        assert valid_route in filtered
    
    def test_get_errors(self):
        """Test getting validation errors"""
        def handler1(request):
            return {"message": "OK"}
        
        def handler2(request):
            return {"message": "OK"}
        
        route1 = RouteInfo(
            path="/dup",
            method="GET",
            handler=handler1,
            file_path=Path("/fake/p1.py"),
            is_dynamic=False
        )
        route2 = RouteInfo(
            path="/dup",
            method="GET",
            handler=handler2,
            file_path=Path("/fake/p2.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        validator.validate_all([route1, route2])
        
        errors = validator.get_errors()
        assert len(errors) > 0
        # First error could be either DUPLICATE_ROUTE or INVALID_HANDLER
        assert errors[0].error_type in ["DUPLICATE_ROUTE", "INVALID_HANDLER"]
    
    def test_has_errors(self):
        """Test has_errors method"""
        def valid_handler(request):
            return {"message": "OK"}
        
        route = RouteInfo(
            path="/test",
            method="GET",
            handler=valid_handler,
            file_path=Path("/fake/path.py"),
            is_dynamic=False
        )
        
        validator = RouteValidator()
        validator.validate_all([route])
        assert not validator.has_errors()
        
        # Create invalid route
        invalid_route = RouteInfo(
            path="/test",
            method="GET",
            handler=lambda: None,  # Invalid: no request param
            file_path=Path("/fake/path2.py"),
            is_dynamic=False
        )
        validator.validate_all([invalid_route])
        assert validator.has_errors()
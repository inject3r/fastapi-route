"""
URL pattern matching for dynamic routes.

This module provides pattern matching functionality for dynamic route
parameters. It converts route patterns like "/users/{user_id}" into
regular expressions and extracts parameter values from URLs.

Features:
- Converts {param} syntax to regex capture groups
- Supports cache-all parameters (multiple path segments)
- Caches compiled patterns for performance
"""

import re
from typing import Optional, Dict, Tuple, Pattern, Union, List


class RouteMatcher:
    """
    Matches URLs against route patterns with parameter extraction.
    
    This class converts route pattern strings into regular expressions
    and provides URL matching with parameter extraction.
    
    Pattern syntax:
    - {param} - Captures a single path segment as parameter 'param'
    - [...slug] - Captures all remaining path segments as a list
    """
    
    def __init__(self):
        """Initialize empty pattern cache."""
        self._patterns: Dict[str, Pattern] = {}
    
    def compile_pattern(self, route_path: str) -> Pattern:
        """
        Compile a route pattern into a compiled regular expression.
        
        This method converts FastAPI-style {param} placeholders into
        regex capture groups. Results are cached to avoid recompiling
        the same pattern multiple times.
        
        Args:
            route_path: Route pattern with {param} placeholders
            
        Returns:
            Compiled regular expression pattern object
        """
        if route_path in self._patterns:
            return self._patterns[route_path]
        
        # Convert {param} to regex named capture group: (?P<param>[^/]+)
        # This captures a single path segment until the next slash
        pattern_str = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"(?P<\1>[^/]+)", route_path)
        pattern_str = f"^{pattern_str}$"
        
        pattern = re.compile(pattern_str)
        self._patterns[route_path] = pattern
        return pattern
    
    def match(self, route_path: str, url_path: str) -> Optional[Dict[str, Union[str, List[str]]]]:
        """
        Match a URL against a route pattern and extract parameters.
        
        Args:
            route_path: Route pattern with {param} placeholders
            url_path: Actual URL path to match
            
        Returns:
            Dictionary of extracted parameters if match succeeds,
            None if the URL does not match the pattern.
            
        Example:
            matcher.match("/users/{user_id}", "/users/123")
            Returns {"user_id": "123"}
            
            matcher.match("/docs/{slug}", "/docs/api/v1/reference")
            Returns {"slug": ["api", "v1", "reference"]}
        """
        pattern = self.compile_pattern(route_path)
        match = pattern.match(url_path)
        
        if match:
            result = match.groupdict()
            # Check for cache-all parameters (contain slashes)
            for key, value in result.items():
                if isinstance(value, str) and '/' in value:
                    result[key] = value.split('/')
            return result
        return None
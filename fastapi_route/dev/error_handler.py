"""
Error handling system for development mode.

This module provides comprehensive error handling and display for
development mode, including formatted tracebacks, syntax highlighting,
and helpful suggestions for fixing common errors.
"""

import traceback
import sys
from typing import Dict, Any, Optional


class ErrorHandler:
    """
    Handles and formats errors for development display.
    
    This class processes exceptions and formats them into structured
    error information suitable for display in the development server's
    error pages. It extracts relevant information like file paths,
    line numbers, and traceback details.
    """
    
    def __init__(self):
        """Initialize empty error collector."""
        self.errors = []
    
    def format_error(self, error: Exception, file_path: str = None) -> Dict[str, Any]:
        """
        Format an exception for display in the error page.
        
        Args:
            error: The exception to format
            file_path: Optional explicit file path (overrides traceback)
            
        Returns:
            Dictionary containing formatted error information:
            - type: Exception class name
            - message: Exception message
            - traceback: Full traceback string
            - location: Dict with file and line number
            - file: Source file path
            - line: Line number where error occurred
        """
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # Parse traceback to find the actual error location
        tb_lines = error_traceback.split('\n')
        error_location = self._extract_error_location(tb_lines)
        
        return {
            "type": error_type,
            "message": error_message,
            "traceback": error_traceback,
            "location": error_location,
            "file": file_path or error_location.get('file', 'unknown'),
            "line": error_location.get('line', 0)
        }
    
    def _extract_error_location(self, tb_lines: list) -> Dict[str, Any]:
        """
        Extract file path and line number from traceback lines.
        
        Args:
            tb_lines: List of traceback lines
            
        Returns:
            Dictionary with 'file' and 'line' keys
        """
        for line in tb_lines:
            if 'File "' in line and 'route.py' in line:
                import re
                match = re.search(r'File "([^"]+)", line (\d+)', line)
                if match:
                    return {
                        "file": match.group(1),
                        "line": int(match.group(2))
                    }
        return {"file": "unknown", "line": 0}
    
    def format_syntax_error(self, error: SyntaxError, file_path: str) -> Dict[str, Any]:
        """
        Format a syntax error specially with detailed location information.
        
        Args:
            error: The SyntaxError exception
            file_path: Path to the file containing the error
            
        Returns:
            Dictionary with syntax error details including column position
            and the problematic line of code.
        """
        return {
            "type": "SyntaxError",
            "message": error.msg,
            "file": file_path,
            "line": error.lineno or 0,
            "column": error.offset or 0,
            "text": error.text or ""
        }


class DevErrorPage:
    """
    Generate beautiful error pages for development mode.
    
    This class creates HTML error pages with:
    - Syntax highlighting for code snippets
    - Line numbers pointing to error locations
    - Helpful suggestions for fixing common errors
    - Clean, modern dark-themed design
    """
    
    @staticmethod
    def render(error_info: Dict[str, Any]) -> str:
        """
        Render a complete HTML error page from error information.
        
        Args:
            error_info: Dictionary containing error details from ErrorHandler
            
        Returns:
            Complete HTML string for the error page
        """
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FastAPI Route - Build Error</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 2rem;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            border-bottom: 2px solid #f48771;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        
        .error-title {{
            font-size: 2rem;
            font-weight: bold;
            color: #f48771;
            margin-bottom: 0.5rem;
        }}
        
        .error-message {{
            font-size: 1.2rem;
            color: #ce9178;
            margin-bottom: 1rem;
        }}
        
        .error-location {{
            background: #2d2d2d;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 2rem;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }}
        
        .section-title {{
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #9cdcfe;
        }}
        
        .traceback {{
            background: #252526;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.4;
            margin-bottom: 2rem;
        }}
        
        .traceback-line {{
            padding: 0.2rem 0;
            border-left: 3px solid transparent;
        }}
        
        .traceback-line.error {{
            background: #4d2b2b;
            border-left-color: #f48771;
        }}
        
        .file-info {{
            color: #6a9955;
        }}
        
        .line-number {{
            color: #858585;
            display: inline-block;
            width: 40px;
            text-align: right;
            margin-right: 1rem;
        }}
        
        .suggestion {{
            background: #2d2d2d;
            padding: 1rem;
            border-radius: 6px;
            border-left: 3px solid #f48771;
            margin-top: 2rem;
        }}
        
        .suggestion-title {{
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #f48771;
        }}
        
        code {{
            background: #252526;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
        }}
        
        .refresh-info {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #3e3e42;
            color: #858585;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="error-title">FastAPI Route - Build Error</div>
            <div class="error-message">{error_info['type']}: {error_info['message']}</div>
        </div>
        
        <div class="error-location">
            <div class="file-info">
                File: {error_info['location'].get('file', 'unknown')}
                {f", Line: {error_info['location'].get('line', 0)}" if error_info['location'].get('line') else ''}
            </div>
        </div>
        
        <div class="section-title">Source</div>
        <div class="traceback">
            {DevErrorPage._format_traceback(error_info['traceback'])}
        </div>
        
        <div class="suggestion">
            <div class="suggestion-title">Quick Fix Suggestions</div>
            <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                {DevErrorPage._get_suggestions(error_info)}
            </ul>
        </div>
        
        <div class="refresh-info">
            Fix the error and save the file. The server will automatically reload.
        </div>
    </div>
</body>
</html>
'''
    
    @staticmethod
    def _format_traceback(traceback_str: str) -> str:
        """
        Format traceback string for HTML display with highlighting.
        
        Args:
            traceback_str: Raw traceback string
            
        Returns:
            HTML formatted traceback with highlighted error lines
        """
        lines = traceback_str.split('\n')
        formatted = []
        
        for line in lines:
            if 'File "' in line and 'route.py' in line:
                formatted.append(f'<div class="traceback-line error">{line}</div>')
            elif line.strip():
                formatted.append(f'<div class="traceback-line">{line}</div>')
            else:
                formatted.append('<div class="traceback-line"> </div>')
        
        return '\n'.join(formatted)
    
    @staticmethod
    def _get_suggestions(error_info: Dict[str, Any]) -> str:
        """
        Generate helpful suggestions based on error type.
        
        Args:
            error_info: Dictionary containing error details
            
        Returns:
            HTML list items with actionable suggestions
        """
        error_type = error_info['type']
        
        suggestions = []
        
        if error_type == 'SyntaxError':
            suggestions.append('Check for missing colons, parentheses, or quotes')
            suggestions.append('Make sure indentation is consistent (spaces vs tabs)')
        elif error_type == 'ImportError':
            suggestions.append('Make sure all required packages are installed')
            suggestions.append('Check for circular imports')
        elif error_type == 'AttributeError':
            suggestions.append('Check if the function or variable exists')
            suggestions.append('Verify the spelling of the attribute name')
        elif 'route' in error_info.get('file', '').lower():
            suggestions.append('Ensure your route file contains GET, POST, etc. functions')
            suggestions.append('Each handler function must accept at least "request" parameter')
            suggestions.append('Example: def GET(request: Request): return {"key": "value"}')
        else:
            suggestions.append('Review the error message above for details')
            suggestions.append('Check the file syntax and imports')
        
        html_items = []
        for suggestion in suggestions:
            html_items.append(f'<li>{suggestion}</li>')
        
        return '\n'.join(html_items)
"""Error page generator for development mode"""

from pathlib import Path
import re
from ..project import __LOGO__

class ErrorPageGenerator:
    """Generate beautiful error pages for route errors"""
    
    @staticmethod
    def extract_user_code_error(error_msg: str, file_path: Path) -> tuple:
        """Extract only the relevant part of error that comes from user code"""
        lines = error_msg.split('\n')
        user_error_lines = []
        user_traceback = []
        in_user_code = False
        error_line_content = ""
        error_line_num = 0
        
        # Find the user's file in traceback
        for i, line in enumerate(lines):
            # Look for user's route file
            if str(file_path) in line:
                in_user_code = True
                # Extract line number
                match = re.search(r'line (\d+)', line)
                if match:
                    error_line_num = int(match.group(1))
                # Get the actual error line from next lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('  File'):
                        error_line_content = lines[j].strip()
                        break
                user_traceback.append(line)
            elif in_user_code and line.strip():
                user_traceback.append(line)
                if not line.startswith('  File') and not line.startswith('    '):
                    in_user_code = False
        
        # Get error type and message (first line of error)
        error_type = "Error"
        error_message = error_msg
        for line in lines:
            if 'Error:' in line or 'Exception:' in line:
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    error_type = parts[0].strip()
                    error_message = parts[1].strip()
                break
        
        # Build user-friendly error message
        if error_line_num > 0 and error_line_content:
            user_error_lines.append(f"Line {error_line_num}: {error_line_content}")
            user_error_lines.append(f"^")
            user_error_lines.append(f"Error: {error_message}")
        
        return error_type, error_message, user_traceback, error_line_num, error_line_content
    
    @staticmethod
    def generate_validation_error_page(errors: list) -> str:
        """Generate page for validation errors"""
        errors_html = ""
        for error in errors:
            errors_html += f'''
            <div class="validation-error">
                <div class="error-badge">{error.error_type}</div>
                <div class="error-text">{error.message}</div>
                {f'<div class="error-file">File: {error.file_path}</div>' if error.file_path else ''}
                {f'<div class="error-details">Details: {error.details}</div>' if error.details else ''}
            </div>
            '''
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FastAPI Route - Validation Errors</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            background: #000000;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        
        .navbar {{
            background: #0a0a0a;
            border-bottom: 1px solid #1a1a1a;
            padding: 1rem 2rem;
            display: flex;
            gap: 10px;
        }}
        
        .navbar a {{
            color: #ffffff;
            text-decoration: none;
            border-bottom: 1px solid #333;
        }}
        
        .navbar a:hover {{
            border-bottom-color: #fff;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .header {{
            border-left: 3px solid #ff4444;
            padding: 1.5rem;
            margin-bottom: 2rem;
            background: #050505;
        }}
        
        .title {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #ff4444;
            margin-bottom: 0.5rem;
        }}
        
        .count {{
            color: #ff8888;
            font-size: 0.9rem;
        }}
        
        .validation-error {{
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            margin-bottom: 1rem;
            padding: 1rem;
        }}
        
        .error-badge {{
            display: inline-block;
            background: #ff4444;
            color: #000000;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        
        .error-text {{
            color: #ff8888;
            margin: 0.5rem 0;
        }}
        
        .error-file {{
            color: #44ff44;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }}
        
        .error-details {{
            color: #ffb86b;
            font-size: 0.75rem;
            margin-top: 0.25rem;
        }}
        
        .suggestions {{
            background: #050505;
            border-left: 3px solid #6bcbff;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        
        .suggestions-title {{
            color: #6bcbff;
            margin-bottom: 0.75rem;
        }}
        
        .suggestions-list {{
            margin-left: 1.5rem;
        }}
        
        .suggestions-list li {{
            margin: 0.5rem 0;
        }}
        
        code {{
            background: #1a1a1a;
            padding: 0.2rem 0.4rem;
        }}
        
        .file-content {{
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 1rem;
            margin-top: 1rem;
            overflow-x: auto;
            font-family: monospace;
            font-size: 0.8rem;
        }}
        
        .line-number {{
            color: #555;
            display: inline-block;
            width: 40px;
            text-align: right;
            margin-right: 1rem;
        }}
        
        .error-line {{
            background: #2a0a0a;
            border-left: 3px solid #ff4444;
            display: block;
        }}
        
        .error-line .line-number {{
            color: #ff8888;
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div style="display: flex;gap: 11px;align-items: center;justify-content: space-between;width: fit-content;">
            <div style="width: 25px;height: 25px;">
                {__LOGO__}
            </div>
            <a href="/">HOME</a> 
        </div>
        <span style="color: #333;"> | </span>
        <a href="/docs">DOCS</a>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="title">ROUTE VALIDATION FAILED</div>
            <div class="count">{len(errors)} error(s) found</div>
        </div>
        
        <div class="validation-errors">
            {errors_html}
        </div>
        
        <div class="suggestions">
            <div class="suggestions-title">FIX SUGGESTIONS</div>
            <ul class="suggestions-list">
                <li>Remove duplicate HTTP method definitions in the same file</li>
                <li>Ensure each route path is unique for each HTTP method</li>
                <li>Handler functions must accept at least 'request' parameter</li>
                <li>Avoid circular references in route groups</li>
                <li>Check for conflicting route patterns like (auth)/path and path</li>
            </ul>
        </div>
    </div>
</body>
</html>'''
    
    @staticmethod
    def generate_route_error_page(url_path: str, file_path: Path, error_msg: str) -> str:
        """Generate error page for a failed route - shows only user code errors"""
        
        # Extract user code error
        error_type, error_message, user_traceback, error_line_num, error_line_content = ErrorPageGenerator.extract_user_code_error(error_msg, file_path)
        
        # Try to read the actual file content to show the error line
        file_content = ""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if i == error_line_num:
                            file_content += f'<div class="error-line"><span class="line-number">{i}</span><span style="color: #ff8888;">{line.rstrip()}</span></div>'
                        else:
                            file_content += f'<div><span class="line-number">{i}</span>{line.rstrip()}</div>'
            except:
                file_content = "Unable to read file"
        
        # Build traceback HTML (only user code)
        traceback_html = ""
        for line in user_traceback:
            escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if 'Error:' in line or 'Exception:' in line:
                traceback_html += f'<div class="traceback-line error">{escaped_line}</div>'
            else:
                traceback_html += f'<div class="traceback-line">{escaped_line}</div>'
        
        # If no user traceback found, show simplified error
        if not traceback_html:
            traceback_html = f'<div class="traceback-line error">{error_type}: {error_message}</div>'
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FastAPI Route - Route Error: {url_path}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            background: #000000;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        
        .navbar {{
            background: #0a0a0a;
            border-bottom: 1px solid #1a1a1a;
            padding: 1rem 2rem;
            display: flex;
            gap: 10px;
        }}
        
        .navbar a {{
            color: #ffffff;
            text-decoration: none;
            border-bottom: 1px solid #333;
        }}
        
        .navbar a:hover {{
            border-bottom-color: #fff;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .error-header {{
            background: #050505;
            border-left: 3px solid #ff4444;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .error-type {{
            font-size: 1.2rem;
            font-weight: bold;
            color: #ff4444;
            margin-bottom: 0.5rem;
        }}
        
        .error-path {{
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 1rem;
        }}
        
        .error-message {{
            font-size: 0.9rem;
            color: #ff8888;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #1a1a1a;
        }}
        
        .file-info {{
            background: #0a0a0a;
            padding: 1rem;
            margin-bottom: 2rem;
            border: 1px solid #1a1a1a;
        }}
        
        .file-path {{
            color: #44ff44;
            margin-bottom: 1rem;
        }}
        
        .section-title {{
            font-size: 0.9rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .file-content {{
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 1rem;
            margin-bottom: 2rem;
            overflow-x: auto;
            font-family: monospace;
            font-size: 0.8rem;
            line-height: 1.5;
        }}
        
        .line-number {{
            color: #555;
            display: inline-block;
            width: 40px;
            text-align: right;
            margin-right: 1rem;
            user-select: none;
        }}
        
        .error-line {{
            background: #2a0a0a;
            border-left: 3px solid #ff4444;
            display: block;
            margin-left: -1rem;
            padding-left: 1rem;
        }}
        
        .error-line .line-number {{
            color: #ff8888;
        }}
        
        .traceback {{
            background: #000000;
            border: 1px solid #1a1a1a;
            padding: 1rem;
            overflow-x: auto;
            font-family: monospace;
            font-size: 0.75rem;
            line-height: 1.4;
            margin-bottom: 2rem;
        }}
        
        .traceback-line {{
            padding: 0.1rem 0;
            white-space: pre-wrap;
            word-break: break-all;
            color: #aaa;
        }}
        
        .traceback-line.error {{
            background: #110000;
            border-left: 3px solid #ff4444;
            padding-left: 0.5rem;
            margin-left: -0.5rem;
            color: #ff8888;
        }}
        
        .suggestions {{
            background: #050505;
            border-left: 3px solid #6bcbff;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        
        .suggestions-title {{
            font-weight: bold;
            margin-bottom: 0.75rem;
            color: #6bcbff;
            text-transform: uppercase;
            font-size: 0.85rem;
        }}
        
        .suggestions-list {{
            margin-left: 1.5rem;
            list-style: none;
        }}
        
        .suggestions-list li {{
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
            color: #ccc;
            position: relative;
        }}
        
        .suggestions-list li::before {{
            content: ">";
            position: absolute;
            left: -1rem;
            color: #6bcbff;
        }}
        
        code {{
            background: #1a1a1a;
            padding: 0.2rem 0.4rem;
            font-family: monospace;
            font-size: 0.8rem;
            color: #ffb86b;
        }}
        
        .refresh-note {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #1a1a1a;
            color: #555;
            font-size: 0.8rem;
        }}
        
        .method-badge {{
            display: inline-block;
            background: #0a0a0a;
            color: #ffb86b;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            font-weight: bold;
            margin-right: 0.5rem;
            border: 1px solid #ffb86b;
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div style="display: flex;gap: 11px;align-items: center;justify-content: space-between;width: fit-content;">
            <div style="width: 25px;height: 25px;">
                {__LOGO__}
            </div>
            <span style="color: #ff4444;">FASTAPI ROUTE</span> 
        </div>
        <span style="color: #333;">/</span>
        <a href="/">HOME</a>
        <span style="color: #333;"> → </span>
        <span style="color: #ff8888;">{url_path}</span>
    </div>
    
    <div class="container">
        <div class="error-header">
            <div class="error-type">
                <span class="method-badge">ROUTE ERROR</span>
                {error_type}
            </div>
            <div class="error-path">ROUTE: {url_path}</div>
            <div class="error-message">{error_message}</div>
        </div>
        
        <div class="file-info">
            <div class="file-path">📁 {file_path}</div>
            <div style="color: #555;">This route file contains errors and could not be loaded</div>
        </div>
        
        <div class="section-title">SOURCE CODE</div>
        <div class="file-content">
            {file_content}
        </div>
        
        <div class="section-title">ERROR DETAILS</div>
        <div class="traceback">
            {traceback_html}
        </div>
        
        <div class="suggestions">
            <div class="suggestions-title">FIX SUGGESTIONS</div>
            <ul class="suggestions-list">
                {ErrorPageGenerator._get_suggestions(error_msg)}
            </ul>
        </div>
        
        <div class="refresh-note">
            Fix the error in <code>{file_path.name}</code> and save the file<br>
            The server will automatically reload once the error is resolved
        </div>
    </div>
</body>
</html>'''
    
    @staticmethod
    def generate_config_error_page(config_path: Path, error_msg: str) -> str:
        """Generate error page for config.py errors"""
        
        # Parse error to show line number if available
        error_detail = error_msg
        line_num = None
        line_content = None
        
        # Try to extract line number from syntax error
        match = re.search(r'line (\d+)', error_msg)
        if match:
            line_num = int(match.group(1))
            try:
                with open(config_path, 'r') as f:
                    lines = f.readlines()
                    if line_num <= len(lines):
                        line_content = lines[line_num - 1].rstrip()
            except:
                pass
        
        # Try to read config file content
        file_content = ""
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    start = max(0, (line_num or 1) - 3)
                    end = min(len(lines), (line_num or 1) + 2)
                    for i in range(start, end):
                        if i + 1 == line_num:
                            file_content += f'<div class="error-line"><span class="line-number">{i+1}</span><span style="color: #ff8888;">{lines[i].rstrip()}</span></div>'
                        else:
                            file_content += f'<div><span class="line-number">{i+1}</span>{lines[i].rstrip()}</div>'
            except:
                pass
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FastAPI Route - Configuration Error</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            background: #000000;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        
        .navbar {{
            background: #0a0a0a;
            border-bottom: 1px solid #1a1a1a;
            padding: 1rem 2rem;
            display: flex;
            gap: 10px;
        }}
        
        .navbar a {{
            color: #ffffff;
            text-decoration: none;
            border-bottom: 1px solid #333;
        }}
        
        .navbar a:hover {{
            border-bottom-color: #fff;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .header {{
            border-left: 3px solid #ff4444;
            padding: 1.5rem;
            margin-bottom: 2rem;
            background: #050505;
        }}
        
        .title {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #ff4444;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: #ff8888;
            font-size: 0.9rem;
        }}
        
        .file-info {{
            background: #0a0a0a;
            padding: 1rem;
            margin-bottom: 2rem;
            border: 1px solid #1a1a1a;
        }}
        
        .file-path {{
            color: #44ff44;
        }}
        
        .file-content {{
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 1rem;
            margin-bottom: 2rem;
            overflow-x: auto;
            font-family: monospace;
            font-size: 0.8rem;
            line-height: 1.5;
        }}
        
        .line-number {{
            color: #555;
            display: inline-block;
            width: 40px;
            text-align: right;
            margin-right: 1rem;
            user-select: none;
        }}
        
        .error-line {{
            background: #2a0a0a;
            border-left: 3px solid #ff4444;
            display: block;
            margin-left: -1rem;
            padding-left: 1rem;
        }}
        
        .error-line .line-number {{
            color: #ff8888;
        }}
        
        .error-detail {{
            background: #050505;
            border-left: 3px solid #6bcbff;
            padding: 1rem;
            margin-top: 2rem;
            font-family: monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        
        .suggestions {{
            background: #050505;
            border-left: 3px solid #6bcbff;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        
        .suggestions-title {{
            color: #6bcbff;
            margin-bottom: 0.75rem;
        }}
        
        .suggestions-list {{
            margin-left: 1.5rem;
        }}
        
        .suggestions-list li {{
            margin: 0.5rem 0;
        }}
        
        code {{
            background: #1a1a1a;
            padding: 0.2rem 0.4rem;
        }}
        
        .refresh-note {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #1a1a1a;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div style="display: flex;gap: 11px;align-items: center;justify-content: space-between;width: fit-content;">
            <div style="width: 25px;height: 25px;">
                {__LOGO__}
            </div>
            <span style="color: #ff4444;">FASTAPI ROUTE</span>
        </div>
        <span style="color: #333;"> | </span>
        <span style="color: #ff8888;">CONFIGURATION ERROR</span>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="title">Configuration Error</div>
            <div class="subtitle">Failed to load config.py</div>
        </div>
        
        <div class="file-info">
            <div class="file-path">📁 {config_path}</div>
            <div style="color: #555;">This configuration file contains errors</div>
        </div>
        
        {f'''
        <div class="file-content">
            {file_content}
        </div>
        ''' if file_content else ''}
        
        <div class="error-detail">
            <strong>Error Details:</strong><br>
            {error_detail.replace(chr(10), '<br>')}
        </div>
        
        <div class="suggestions">
            <div class="suggestions-title">FIX SUGGESTIONS</div>
            <ul class="suggestions-list">
                <li>Check the syntax of your config.py file</li>
                <li>Verify all variable names are correct</li>
                <li>Make sure types match expected values (strings, booleans, lists)</li>
                <li>Remove any unknown configuration fields</li>
                <li>Check the error message above for specific line numbers</li>
            </ul>
        </div>
        
        <div class="refresh-note">
            Fix the error in <code>config.py</code> and save the file<br>
            The server will automatically reload once the error is resolved
        </div>
    </div>
</body>
</html>'''
    
    @staticmethod
    def _get_suggestions(error_msg: str) -> str:
        """Generate helpful suggestions based on error"""
        suggestions = []
        
        if "Syntax error" in error_msg:
            suggestions.append("Verify all colons, parentheses, brackets, and quotes are properly placed")
            suggestions.append("Ensure consistent indentation (4 spaces standard)")
            suggestions.append("Check that all brackets and parentheses are correctly closed")
        elif "Duplicate" in error_msg:
            suggestions.append("Remove duplicate HTTP method definitions in the same file")
            suggestions.append("Each route file can only have one handler per HTTP method (GET, POST, etc.)")
        elif "IndentationError" in error_msg:
            suggestions.append("Use consistent indentation (4 spaces recommended, avoid tabs)")
            suggestions.append("Never mix tabs with spaces in Python files")
        elif "NameError" in error_msg:
            suggestions.append("Check spelling of variable or function name")
            suggestions.append("Ensure variable is defined before referencing it")
            suggestions.append("Import any missing modules or define the variable before use")
        elif "ImportError" in error_msg:
            suggestions.append("Install missing module: pip install <module-name>")
            suggestions.append("Verify import path is correct")
            suggestions.append("Check for circular imports")
        elif "TypeError" in error_msg:
            suggestions.append("Check that function arguments match the expected types")
            suggestions.append("Verify that you're not calling a non-callable object")
        else:
            suggestions.append("Review the error message above for specific details")
            suggestions.append("Check Python syntax in your code")
            suggestions.append("Ensure all functions have correct parameters")
        
        html_items = []
        for suggestion in suggestions:
            html_items.append(f'<li>{suggestion}</li>')
        
        return '\n'.join(html_items)
    
    @staticmethod
    def generate_404_page(url_path: str) -> str:
        """Generate custom 404 page"""
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>404 - Route Not Found</title>
    <style>
        body {{
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            background: #000000;
            color: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            text-align: center;
            max-width: 600px;
        }}
        .code {{
            font-size: 7rem;
            font-weight: bold;
            color: #ff4444;
            margin-bottom: 1rem;
            letter-spacing: -5px;
        }}
        .message {{
            font-size: 1.2rem;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .path {{
            font-family: monospace;
            background: #0a0a0a;
            padding: 0.5rem 1rem;
            border: 1px solid #1a1a1a;
            display: inline-block;
            margin: 1rem 0;
            color: #ff8888;
        }}
        .suggestion {{
            color: #555;
            margin-top: 2rem;
            font-size: 0.85rem;
        }}
        a {{
            color: #ffffff;
            text-decoration: none;
            border-bottom: 1px solid #333;
        }}
        a:hover {{
            border-bottom-color: #fff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="code">404</div>
        <div class="message">Route Not Found</div>
        <div class="path">{url_path}</div>
        <div class="suggestion">
            The route {url_path} does not exist in the system<br>
            Check your <code>routes/</code> directory structure
        </div>
        <div style="margin-top: 2rem;">
            <a href="/">[BACK TO HOME]</a>
        </div>
    </div>
</body>
</html>'''
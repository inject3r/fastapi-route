"""Error page for custom handler failures"""

from pathlib import Path
from typing import List
from ..project import __LOGO__


class CustomHandlerErrorPage:
    """Generate error page for custom handler failures"""
    
    @staticmethod
    def generate_not_found_error_page(file_path: Path, errors: List[str]) -> str:
        """Generate error page for invalid not-found.py"""
        errors_html = ""
        for error in errors:
            errors_html += f'<li>{error}</li>'
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FastAPI Route - Custom 404 Handler Error</title>
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
        
        .file-info {{
            background: #0a0a0a;
            padding: 1rem;
            margin-bottom: 2rem;
            border: 1px solid #1a1a1a;
        }}
        
        .file-path {{
            color: #44ff44;
        }}
        
        .errors-list {{
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 1rem;
            margin-bottom: 2rem;
        }}
        
        .errors-list li {{
            margin: 0.5rem 0;
            margin-left: 1.5rem;
            color: #ff8888;
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
        <span style="color: #ff8888;">CUSTOM HANDLER ERROR</span>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="title">404 HANDLER ERROR</div>
        </div>
        
        <div class="file-info">
            <div class="file-path">📁 {file_path}</div>
            <div style="color: #555;">This custom 404 handler contains errors</div>
        </div>
        
        <div class="errors-list">
            <ul>
                {errors_html}
            </ul>
        </div>
        
        <div class="suggestions">
            <div class="suggestions-title">FIX SUGGESTIONS</div>
            <ul class="suggestions-list">
                <li>Define a function named <code>handler(request)</code> or <code>GET(request)</code></li>
                <li>The function must accept at least one parameter (request)</li>
                <li>The function should return a string (HTML) or a dict (JSON)</li>
                <li>Don't import from <code>fastapi</code> directly, use <code>fastapi_route</code> instead</li>
            </ul>
        </div>
        
        <div class="refresh-note">
            Fix the error in <code>{file_path.name}</code> and save the file
        </div>
    </div>
</body>
</html>'''
    
    @staticmethod
    def generate_docs_error_page(file_path: Path, errors: List[str]) -> str:
        """Generate error page for invalid docs.py"""
        errors_html = ""
        for error in errors:
            errors_html += f'<li>{error}</li>'
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FastAPI Route - Custom Docs Error</title>
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
        
        .file-info {{
            background: #0a0a0a;
            padding: 1rem;
            margin-bottom: 2rem;
            border: 1px solid #1a1a1a;
        }}
        
        .file-path {{
            color: #44ff44;
        }}
        
        .errors-list {{
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 1rem;
            margin-bottom: 2rem;
        }}
        
        .errors-list li {{
            margin: 0.5rem 0;
            margin-left: 1.5rem;
            color: #ff8888;
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
        <span style="color: #ff8888;">CUSTOM DOCS ERROR</span>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="title">DOCS HANDLER ERROR</div>
        </div>
        
        <div class="file-info">
            <div class="file-path">📁 {file_path}</div>
            <div style="color: #555;">This custom docs handler contains errors</div>
        </div>
        
        <div class="errors-list">
            <ul>
                {errors_html}
            </ul>
        </div>
        
        <div class="suggestions">
            <div class="suggestions-title">FIX SUGGESTIONS</div>
            <ul class="suggestions-list">
                <li>Define a function named <code>handler(request)</code> or <code>GET(request)</code></li>
                <li>The function must accept at least one parameter (request)</li>
                <li>The function should return a string (HTML) or a dict (JSON)</li>
                <li>Don't import from <code>fastapi</code> directly, use <code>fastapi_route</code> instead</li>
            </ul>
        </div>
        
        <div class="refresh-note">
            Fix the error in <code>{file_path.name}</code> and save the file
        </div>
    </div>
</body>
</html>'''
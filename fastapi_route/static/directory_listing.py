"""
Directory listing HTML generator for static file serving.

This module generates beautiful HTML directory listings when directory
listing is enabled for the public folder. It provides a clean, dark-themed
interface for browsing static files with file icons, sizes, and modification dates.

Features:
- Folder and file icons
- Clickable links to navigate directories
- Parent directory navigation
- Responsive design (hides size/date on mobile)
- File size formatting (B, KB, MB, GB, TB)
- Dark theme matching the FastAPI Route aesthetic
"""

from datetime import datetime
from pathlib import Path


class DirectoryListing:
    """
    Generate HTML directory listings for the static file server.
    
    This class creates beautiful HTML pages that display the contents
    of directories when directory listing is enabled. It is used by
    the StaticFileMiddleware when a directory is requested and
    static_directory_listing is set to True.
    """
    
    @staticmethod
    def generate_listing(path: str, items: list) -> str:
        """
        Generate HTML for a directory listing page.
        
        Args:
            path: The current directory path being listed
            items: List of item dictionaries, each containing:
                - name: File/directory name
                - path: Relative path from public directory
                - is_directory: True for directories, False for files
                - size: File size in bytes (0 for directories)
                - modified: Last modification timestamp
                
        Returns:
            Complete HTML string for the directory listing page
        """
        rows = ""
        for item in items:
            icon = "📁" if item['is_directory'] else "📄"
            size = DirectoryListing._format_size(item['size']) if not item['is_directory'] else "-"
            modified = datetime.fromtimestamp(item['modified']).strftime("%Y-%m-%d %H:%M:%S")
            
            rows += f'''
            <tr>
                <td class="icon">{icon}</td>
                <td class="name"><a href="/{item['path']}{'/' if item['is_directory'] else ''}">{item['name']}</a></td>
                <td class="size">{size}</td>
                <td class="modified">{modified}</td>
            </tr>
            '''
        
        # Generate parent directory link (..)
        parent_link = ""
        if path and path != "/":
            parent_path = "/".join(path.split('/')[:-1]) if '/' in path else ""
            parent_link = f'<a href="/{parent_path}" class="parent-link">← Parent Directory</a>'
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Index of /{path}</title>
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
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .header {{
            border-bottom: 1px solid #1a1a1a;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 1.5rem;
            color: #44ff44;
            margin-bottom: 0.5rem;
        }}
        
        .path {{
            color: #ffb86b;
            font-family: monospace;
        }}
        
        .parent-link {{
            display: inline-block;
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
            color: #6bcbff;
            text-decoration: none;
            font-size: 0.85rem;
        }}
        
        .parent-link:hover {{
            background: #1a1a1a;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            text-align: left;
            padding: 0.75rem;
            background: #0a0a0a;
            border-bottom: 1px solid #1a1a1a;
            color: #ffb86b;
            font-weight: normal;
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 1px;
        }}
        
        td {{
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid #1a1a1a;
        }}
        
        .icon {{
            width: 30px;
            font-size: 1.2rem;
        }}
        
        .name a {{
            color: #ffffff;
            text-decoration: none;
            border-bottom: 1px solid #333;
        }}
        
        .name a:hover {{
            border-bottom-color: #fff;
        }}
        
        .size {{
            text-align: right;
            font-family: monospace;
            color: #888;
        }}
        
        .modified {{
            font-family: monospace;
            font-size: 0.8rem;
            color: #888;
        }}
        
        .footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #1a1a1a;
            text-align: center;
            color: #555;
            font-size: 0.75rem;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            .size, .modified {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Index of <span class="path">/{path}</span></h1>
        </div>
        
        {parent_link}
        
        <table>
            <thead>
                <tr>
                    <th></th>
                    <th>Name</th>
                    <th>Size</th>
                    <th>Last Modified</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        
        <div class="footer">
            FastAPI Route - Static File Server
        </div>
    </div>
</body>
</html>'''
    
    @staticmethod
    def _format_size(size: int) -> str:
        """
        Format file size for human-readable display.
        
        Converts bytes to appropriate units (B, KB, MB, GB, TB)
        with one decimal place for consistency.
        
        Args:
            size: File size in bytes
            
        Returns:
            Formatted string with appropriate unit
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
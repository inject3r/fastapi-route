"""
Middleware for serving static files from the public directory.

This middleware intercepts requests and serves static files from the
/public directory before passing to the route handlers. It handles:
- File serving with proper MIME types
- Directory listing (optional)
- Security (path traversal prevention)
- Caching headers for performance

The middleware runs early in the request chain to ensure static files
are served quickly without going through the routing system.
"""

from pathlib import Path
from fastapi import Request
from fastapi.responses import Response, FileResponse, HTMLResponse
import os

from ..utils.logger import logger
from .handler import StaticFileHandler
from .directory_listing import DirectoryListing


class StaticFileMiddleware:
    """
    ASGI middleware for serving static files from the public directory.
    
    This middleware intercepts all HTTP requests and checks if the requested
    path corresponds to a file in the public directory. If found, it serves
    the file directly. If not, it passes the request to the next middleware.
    
    Features:
    - Automatic file serving from /public directory
    - Path traversal attack prevention
    - Optional directory listing for browsing
    - Proper MIME type detection
    - Cache headers for improved performance
    - Efficient file reading with caching
    
    The middleware is added to the FastAPI application early in the
    middleware chain to ensure static files are served before any
    route matching occurs.
    """
    
    def __init__(self, public_dir: Path = None, enable_directory_listing: bool = False):
        """
        Initialize the static file middleware.
        
        Args:
            public_dir: Path to the public directory (default: ./public)
            enable_directory_listing: If True, show HTML directory listings
                                      when a directory is requested
        """
        if public_dir is None:
            public_dir = Path.cwd() / "public"
        self.public_dir = public_dir
        self.handler = StaticFileHandler(public_dir)
        self.enable_directory_listing = enable_directory_listing
        self.directory_listing = DirectoryListing()
        
        # Ensure public directory exists
        self.handler.create_directory()
    
    async def __call__(self, request: Request, call_next):
        """
        Process the request and serve static files if matched.
        
        This method is called for every HTTP request. It checks if the
        requested path corresponds to a file or directory in the public
        directory. If found, it serves the appropriate response.
        
        Args:
            request: The incoming FastAPI request
            call_next: The next middleware/route handler in the chain
            
        Returns:
            Response: Either a static file response, directory listing,
                      or passes through to the next handler
        """
        path = request.url.path
        
        # Skip if the path doesn't start with / (should never happen)
        if not path.startswith('/'):
            return await call_next(request)
        
        # Remove leading slash to get path relative to public directory
        relative_path = path.lstrip('/')
        
        # Try to serve as a file
        content, mime_type, last_modified = self.handler.get_file(relative_path)
        
        if content is not None:
            # File found - serve it with caching headers
            from fastapi.responses import Response as FastAPIResponse
            return FastAPIResponse(
                content=content,
                media_type=mime_type,
                headers={
                    "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                    "Last-Modified": str(last_modified),
                }
            )
        
        # Check if it's a directory listing request (and directory listing is enabled)
        if self.enable_directory_listing:
            full_path = self.public_dir / relative_path
            if full_path.exists() and full_path.is_dir():
                items = self.handler.list_directory(relative_path)
                if items is not None:
                    html = self.directory_listing.generate_listing(relative_path, items)
                    return HTMLResponse(content=html, status_code=200)
        
        # Not a static file or directory listing - continue to next middleware
        return await call_next(request)
"""
Static file handler for public directory.

This module provides efficient static file serving from the /public directory
with security features, caching, MIME type detection, and directory listing support.
Files are served from the root URL path (e.g., /css/style.css serves public/css/style.css).

Security features:
- Path traversal attack prevention
- Path normalization and validation
- File access restricted to public directory only

Performance features:
- In-memory file caching (up to 100MB per file)
- MIME type detection for proper content-type headers
- Efficient file streaming for large files

Directory listing:
- Optional directory listing for browsing folders
- Sort directories first, then files alphabetically
- File size formatting and modification timestamps
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from ..utils.logger import logger


class StaticFileHandler:
    """
    Handles static files from the public directory with caching and security.
    
    This class is responsible for:
    - Serving static files (CSS, JS, images, fonts, etc.)
    - Preventing path traversal attacks (../ sequences)
    - Caching frequently accessed files for performance
    - Detecting MIME types for proper content-type headers
    - Listing directory contents for browsing (optional)
    
    The handler is used by the StaticFileMiddleware to serve files when
    requests match files in the public directory.
    """
    
    def __init__(self, public_dir: Path):
        """
        Initialize the static file handler.
        
        Args:
            public_dir: Path to the public directory containing static assets
        """
        self.public_dir = public_dir
        self.cache = {}  # Cache for file contents: path -> (content, mtime)
        self._init_mimetypes()
    
    def _init_mimetypes(self):
        """
        Initialize MIME type mappings for common file extensions.
        
        This ensures proper Content-Type headers are set for all file types.
        Missing mappings default to 'application/octet-stream'.
        """
        # CSS and JavaScript
        mimetypes.add_type('text/css', '.css')
        mimetypes.add_type('text/javascript', '.js')
        mimetypes.add_type('application/javascript', '.mjs')
        
        # HTML and text
        mimetypes.add_type('text/html', '.html')
        mimetypes.add_type('text/plain', '.txt')
        
        # Images
        mimetypes.add_type('image/png', '.png')
        mimetypes.add_type('image/jpeg', '.jpg')
        mimetypes.add_type('image/jpeg', '.jpeg')
        mimetypes.add_type('image/gif', '.gif')
        mimetypes.add_type('image/svg+xml', '.svg')
        mimetypes.add_type('image/webp', '.webp')
        mimetypes.add_type('image/x-icon', '.ico')
        
        # Fonts
        mimetypes.add_type('font/woff', '.woff')
        mimetypes.add_type('font/woff2', '.woff2')
        mimetypes.add_type('font/ttf', '.ttf')
        mimetypes.add_type('font/otf', '.otf')
        
        # Data formats
        mimetypes.add_type('application/json', '.json')
        mimetypes.add_type('application/pdf', '.pdf')
        mimetypes.add_type('application/zip', '.zip')
        
        # Media
        mimetypes.add_type('video/mp4', '.mp4')
        mimetypes.add_type('video/webm', '.webm')
        mimetypes.add_type('audio/mpeg', '.mp3')
        mimetypes.add_type('audio/ogg', '.ogg')
    
    def get_file(self, file_path: str) -> Tuple[Optional[bytes], Optional[str], Optional[int]]:
        """
        Get file content, MIME type, and last modified time.
        
        This method performs security checks, caching, and file reading.
        
        Args:
            file_path: Requested file path relative to public directory
            
        Returns:
            Tuple of (content, mime_type, last_modified) if file exists,
            or (None, None, None) if not found or access denied.
        """
        # Security: Normalize path and check for traversal attacks
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith('..') or os.path.isabs(normalized_path):
            logger.warning(f"Path traversal attempt: {file_path}")
            return None, None, None
        
        full_path = self.public_dir / normalized_path
        
        # Security: Verify the resolved path is still inside public directory
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(self.public_dir.resolve())):
                logger.warning(f"Path traversal attempt: {file_path}")
                return None, None, None
        except Exception:
            return None, None, None
        
        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            return None, None, None
        
        # Get file modification time
        stat = full_path.stat()
        last_modified = int(stat.st_mtime)
        
        # Check cache for unchanged file
        cache_key = str(full_path)
        if cache_key in self.cache:
            cached_content, cached_mtime = self.cache[cache_key]
            if cached_mtime == last_modified:
                mime_type = mimetypes.guess_type(str(full_path))[0]
                return cached_content, mime_type, last_modified
        
        # Read file from disk
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            # Cache file if under size limit (100MB)
            if len(content) < 100 * 1024 * 1024:
                self.cache[cache_key] = (content, last_modified)
            
            # Determine MIME type
            mime_type = mimetypes.guess_type(str(full_path))[0]
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            return content, mime_type, last_modified
            
        except Exception as e:
            logger.error(f"Error reading file {full_path}: {e}")
            return None, None, None
    
    def clear_cache(self):
        """Clear the in-memory file cache."""
        self.cache.clear()
        logger.debug("Static file cache cleared")
    
    def directory_exists(self) -> bool:
        """
        Check if the public directory exists.
        
        Returns:
            True if directory exists and is accessible
        """
        return self.public_dir.exists() and self.public_dir.is_dir()
    
    def create_directory(self):
        """Create the public directory if it doesn't exist."""
        if not self.public_dir.exists():
            self.public_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created public directory: {self.public_dir}")
    
    def list_directory(self, dir_path: str) -> Optional[list]:
        """
        List contents of a directory for directory listing.
        
        Args:
            dir_path: Directory path relative to public directory
            
        Returns:
            List of item dictionaries with name, path, is_directory,
            size, and modified timestamp, or None if directory doesn't exist.
            Items are sorted with directories first, then files alphabetically.
        """
        # Security: Normalize and validate path
        normalized_path = os.path.normpath(dir_path)
        if normalized_path.startswith('..') or os.path.isabs(normalized_path):
            return None
        
        full_path = self.public_dir / normalized_path
        
        if not full_path.exists() or not full_path.is_dir():
            return None
        
        items = []
        for item in full_path.iterdir():
            items.append({
                'name': item.name,
                'path': str(item.relative_to(self.public_dir)),
                'is_directory': item.is_dir(),
                'size': item.stat().st_size if item.is_file() else 0,
                'modified': item.stat().st_mtime,
            })
        
        # Sort: directories first, then files, alphabetically within each group
        return sorted(items, key=lambda x: (not x['is_directory'], x['name']))
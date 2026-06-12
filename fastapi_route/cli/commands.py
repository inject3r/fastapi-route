"""
Command Line Interface for FastAPI Route.

This module provides the CLI interface for managing FastAPI Route projects.
Commands include project initialization, building cache, running development
and production servers, and managing build artifacts.

Color output is used throughout for better readability and user experience.
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional
from ..version import __version__


# Prevent Python from writing .pyc files to keep project clean
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True


def main():
    """Main CLI entry point - parses arguments and dispatches to commands."""
    parser = argparse.ArgumentParser(description=f"FastAPI Route CLI v{__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # ========== INIT COMMAND ==========
    # Creates a new project with default structure and configuration
    init_parser = subparsers.add_parser("init", help="Initialize new FastAPI Route project")
    init_parser.add_argument("-y", "--yes", action="store_true", help="Use default values without prompting")
    init_parser.add_argument("--name", help="Project name")
    init_parser.add_argument("--with-docs", action="store_true", help="Enable documentation")

    # ========== BUILD COMMAND ==========
    # Compiles routes into encrypted/compressed production cache
    build_parser = subparsers.add_parser("build", help="Build project and create cache")
    build_parser.add_argument("-f", "--force", action="store_true", help="Force rebuild (clear cache first)")
    build_parser.add_argument("--compression", type=int, choices=range(1, 10), help="Compression level (1-9)")

    # ========== RUN COMMAND ==========
    # Production server - requires existing build cache
    run_parser = subparsers.add_parser("run", help="Run the application in production mode (requires build)")
    run_parser.add_argument("--host", help="Host to bind")
    run_parser.add_argument("-p", "--port", type=int, help="Port to bind")
    run_parser.add_argument("--workers", type=int, help="Number of worker processes")
    run_parser.add_argument("--no-docs", action="store_true", help="Disable documentation")

    # ========== DEV COMMAND ==========
    # Development server with hot reload and file watching
    dev_parser = subparsers.add_parser("dev", help="Run the application in development mode with hot reload")
    dev_parser.add_argument("--host", help="Host to bind")
    dev_parser.add_argument("-p", "--port", type=int, help="Port to bind")
    dev_parser.add_argument("--no-docs", action="store_true", help="Disable documentation")
    dev_parser.add_argument("--no-cache", action="store_true", help="Disable build cache in dev mode")

    # ========== CLEAN COMMAND ==========
    # Removes build cache directory
    clean_parser = subparsers.add_parser("clean", help="Clean build cache")

    # ========== STATUS COMMAND ==========
    # Shows information about existing build cache
    status_parser = subparsers.add_parser("status", help="Show build status")

    args = parser.parse_args()

    # Route to appropriate command handler
    if args.command == "init":
        cmd_init(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "dev":
        cmd_dev(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        # Unknown command - try to execute as custom command from config.py
        _try_run_custom_command(args.command, args)
        parser.print_help()


def _try_run_custom_command(command_name: str, args):
    """
    Attempt to execute a custom command defined in config.py.
    
    Users can define their own commands in the `commands` dictionary
    inside config.py. This allows project-specific shortcuts like
    'make deploy' or 'make test'.
    
    Args:
        command_name: The command name entered by user
        args: Parsed command line arguments
    
    Returns:
        False if config doesn't exist or command not found
    """
    config_path = Path.cwd() / "config.py"
    
    # Only attempt to load config if the file actually exists
    if not config_path.exists():
        return False
    
    try:
        from ..config.loader import ConfigLoader
        config = ConfigLoader.load()
        
        if command_name in config.commands:
            cmd_template = config.commands[command_name]
            server = config.server

            # Substitute template variables with CLI args or config defaults
            cmd = cmd_template.format(
                host=getattr(args, 'host', server.host),
                port=getattr(args, 'port', server.port),
                **vars(args)
            )

            print(f"\n\033[96m[RUNNING]\033[0m {cmd}\n")
            result = subprocess.run(cmd, shell=True)
            sys.exit(result.returncode)
    except Exception:
        pass
    
    return False


def prompt_user(question: str, default: str = "", is_boolean: bool = False) -> str:
    """
    Interactive prompt for user input during project initialization.
    
    Args:
        question: The prompt text to display
        default: Default value if user presses Enter
        is_boolean: If True, accepts y/n responses and returns 'y' or 'n'
    
    Returns:
        User input or default value
    """
    if is_boolean:
        default_str = "Y/n" if default.lower() == "y" else "y/N"
        response = input(f"{question} [{default_str}]: ").strip().lower()
        if not response:
            return default.lower()
        return "y" if response in ["y", "yes"] else "n"
    else:
        default_str = f" [{default}]" if default else ""
        response = input(f"{question}{default_str}: ").strip()
        return response if response else default


def cmd_init(args):
    """
    Initialize a new FastAPI Route project with interactive setup.
    
    Creates:
    - routes/ directory with index.py example
    - config.py with advanced configuration
    - public/ directory for static files
    - .gitignore for Python projects
    """
    from ..config.loader import ConfigLoader

    project_root = Path.cwd()

    print("\n" + "=" * 60)
    print("\033[96mFASTAPI ROUTE PROJECT INITIALIZATION\033[0m")
    print("=" * 60)

    # Gather project information from user or use defaults
    if args.name:
        project_name = args.name
    elif args.yes:
        project_name = "my-fastapi-app"
    else:
        project_name = prompt_user("Project name", "my-fastapi-app")

    if args.with_docs:
        docs_enabled = True
    elif args.yes:
        docs_enabled = False
    else:
        docs_response = prompt_user("Enable documentation?", "n", is_boolean=True)
        docs_enabled = docs_response == "y"

    # Create routes directory with example endpoint
    routes_dir = project_root / "routes"
    routes_dir.mkdir(exist_ok=True)

    index_file = routes_dir / "index.py"
    index_file.write_text(f'''from fastapi_route import Request

def GET(request: Request):
    """
    Root endpoint
    ---
    Returns a welcome message
    :return: Welcome message
    """
    return {{"message": "Welcome to {project_name}!", "endpoint": "/"}}

def POST(request: Request):
    """
    Root POST endpoint
    ---
    Accepts POST requests to root
    :return: Confirmation message
    """
    return {{"message": "POST request to root"}}
''')

    # Create advanced configuration file
    ConfigLoader.create_default_config()

    # Create public directory for static assets
    public_dir = project_root / "public"
    public_dir.mkdir(exist_ok=True)

    # Create .gitignore if not exists
    gitignore_file = project_root / ".gitignore"
    if not gitignore_file.exists():
        gitignore_file.write_text('''# FastAPI Route
.cache/
__pycache__/
*.pyc
.env
.venv
venv/
.env/
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
''')

    # Display success message with next steps
    print("\n" + "=" * 60)
    print("\033[92mPROJECT INITIALIZED\033[0m")
    print("=" * 60)
    print(f"  Project: {project_name}")
    print(f"  Routes:  {routes_dir}/")
    print(f"  Config:  config.py")
    print(f"  Public:  {public_dir}/")
    print(f"  Docs:    {'enabled' if docs_enabled else 'disabled'}")
    print("=" * 60)
    print("\n\033[93mNext steps:\033[0m")
    print("  1. Edit config.py to customize your application")
    print("  2. Create routes:  Add files to routes/ directory")
    print("  3. Build project:  fastapi-route build")
    print("  4. Run dev:        fastapi-route dev")
    print("  5. Run prod:       fastapi-route run")
    print("")


def cmd_build(args):
    """
    Build project and create production cache.
    
    This command:
    - Scans all route files
    - Validates route structure
    - Detects duplicates and conflicts
    - Compresses and encrypts route metadata
    - Stores cache in .cache directory
    """
    from ..build import ProjectBuilder
    from ..config.loader import ConfigLoader

    project_root = Path.cwd()
    config = ConfigLoader.load()

    # Override compression level if provided via CLI
    compression_level = args.compression or config.build.compression_level

    builder = ProjectBuilder(project_root)
    builder.cache.COMPRESSION_LEVEL = compression_level

    success, error = builder.build(force=args.force)

    if not success:
        print("\n\033[91mBuild failed. Please fix the errors above and try again.\033[0m")
        sys.exit(1)


def cmd_run(args):
    """
    Run production server using built cache.
    
    This command requires a successful build first. It loads routes from
    the cache rather than scanning the filesystem, resulting in faster
    startup and reduced memory usage.
    """
    from ..build import CacheLoader
    from ..app import FastAPIRouterApp
    from ..config.loader import ConfigLoader
    from ..utils.logger import Logger

    project_root = Path.cwd()
    config = ConfigLoader.load()

    # CLI args take precedence over config file
    host = args.host or config.server.host
    port = args.port or config.server.port
    workers = args.workers or config.server.workers

    # Suppress verbose logging in production
    Logger.set_production_mode(True)

    cache_loader = CacheLoader(project_root)

    # Verify cache exists before attempting to run
    if not cache_loader.has_valid_cache():
        print("\n" + "=" * 60)
        print("\033[91mERROR: No valid build found!\033[0m")
        print("=" * 60)
        print("Please run 'fastapi-route build' first to compile your routes.")
        print("=" * 60 + "\n")
        sys.exit(1)

    # Display build information for transparency
    build_info = cache_loader.get_build_info()
    if build_info:
        print(f"\n\033[92m[BUILD]\033[0m Using cache from {build_info.get('created_at', 'unknown')}")
        print(f"\033[92m[BUILD]\033[0m Routes: {build_info.get('total_routes', 0)}")
        print(f"\033[92m[BUILD]\033[0m Workers: {workers}")

    enable_docs = not args.no_docs

    app = FastAPIRouterApp(
        enable_docs=enable_docs,
        use_cache=True,
        is_production=True
    )

    # Configure uvicorn with production settings
    import uvicorn

    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["loggers"]["uvicorn"]["level"] = "WARNING"
    log_config["loggers"]["uvicorn.access"]["level"] = "WARNING"
    log_config["loggers"]["uvicorn.error"]["level"] = "WARNING"

    uvicorn.run(
        app.build(),
        host=host,
        port=port,
        workers=workers,
        timeout_keep_alive=config.server.timeout_keep_alive,
        limit_concurrency=config.server.limit_concurrency,
        limit_max_requests=config.server.limit_max_requests,
        backlog=config.server.backlog,
        log_config=log_config,
        access_log=False,
    )


def cmd_dev(args):
    """
    Run development server with hot reload and file watching.
    
    Development mode features:
    - Automatically rebuilds cache on file changes
    - Watches routes/, config.py, and custom handlers
    - Provides detailed error pages with syntax highlighting
    - No need to manually rebuild between changes
    """
    from ..dev.server import DevServer
    from ..build import ProjectBuilder
    from ..config.loader import ConfigLoader

    config = ConfigLoader.load()

    # CLI args override config values
    host = args.host or config.server.host
    port = args.port or config.server.port

    project_root = Path.cwd()

    # Pre-build cache for faster initial startup (unless disabled)
    if not args.no_cache:
        builder = ProjectBuilder(project_root)
        print("\n\033[96m[BUILD]\033[0m Pre-building cache for development...")
        builder.build(force=False)

    server = DevServer(
        host=host,
        port=port,
        enable_docs=not args.no_docs,
        use_cache=not args.no_cache
    )
    server.start()


def cmd_clean(args):
    """Clean build cache - removes .cache directory completely."""
    from ..build import ProjectBuilder

    project_root = Path.cwd()
    builder = ProjectBuilder(project_root)
    builder.clean()


def cmd_status(args):
    """Display build cache status and statistics."""
    from ..build import ProjectBuilder

    project_root = Path.cwd()
    builder = ProjectBuilder(project_root)
    status = builder.status()

    print("\n" + "=" * 60)
    print("\033[96mBUILD STATUS\033[0m")
    print("=" * 60)

    if status.get('built'):
        print(f"  \033[92mStatus:\033[0m        Built")
        print(f"  \033[92mCreated:\033[0m       {status.get('created_at')}")
        print(f"  \033[92mTotal routes:\033[0m  {status.get('total_routes')}")
        print(f"  \033[92mStatic routes:\033[0m {status.get('static_routes')}")
        print(f"  \033[92mDynamic routes:\033[0m{status.get('dynamic_routes')}")
        print(f"  \033[92mCache size:\033[0m    {status.get('cache_size', 0) / 1024:.2f} KB")
        print(f"  \033[92mCache path:\033[0m    {project_root / '.cache'}")
    else:
        print("  \033[93mStatus:\033[0m        Not built")
        print("\n  Run 'fastapi-route build' to build the project")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
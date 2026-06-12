<p align="center">
  <img src="https://raw.githubusercontent.com/fastapi-route/fastapi-route/main/docs/logo.png" alt="FastAPI Route Logo" width="300">
</p>

# FastAPI Route

A file-based routing system for FastAPI — build APIs with the simplicity of files and folders, not decorators.

**[Full Documentation](https://inject3r.github.io/fastapi-route)** — Complete API reference, advanced guides, and examples

<br/>

## Why FastAPI Route?

Stop writing decorators. Start organizing your API with files and folders. Just drop Python files in directories — each file becomes an endpoint, each directory becomes a route segment. Dynamic parameters? Use `[param]` directories. Route groups? Use `(group)` directories. It's that simple.

## Features

- **File-Based Routing**: Routes defined by directory structure — no decorators needed
- **Dynamic Routes**: `[user_id]` directories automatically become `{user_id}` parameters
- **Cache-All Routes**: `[...slug]` captures unlimited path segments
- **Route Groups**: `(auth)` directories organize code without affecting URLs
- **Hot Reload**: Instant rebuild on file changes during development
- **Production Build Cache**: Pre-compiled routes for lightning-fast startup
- **Beautiful Error Pages**: Syntax highlighting, line numbers, and helpful suggestions
- **Custom Handlers**: Bring your own `docs.py` and `not-found.py`
- **Custom Middleware**: Intercept requests with `middleware.py`
- **Static File Serving**: Drop files in `/public` — served automatically
- **Built-in Documentation**: Auto-generated API docs at `/docs`
- **CLI Tools**: `init`, `build`, `run`, `dev`, `clean`, `status` commands
- **Zero Config**: Works out of the box — but fully customizable when you need it
- **Type Hints**: Full typing support for excellent IDE autocompletion

## Installation

```bash
pip install fastapi-route
```

With development dependencies:

```bash
pip install fastapi-route[dev]
```

## Quick Start

### 1. Initialize a new project

```bash
fastapi-route init
```

### 2. Create your first route

```python
# routes/index.py
from fastapi_route import Request

def GET(request: Request):
    return {"message": "Hello World!"}

def POST(request: Request):
    data = await request.json()
    return {"received": data}
```

### 3. Add a dynamic route

```python
# routes/users/[user_id]/route.py
from fastapi_route import Request

def GET(request: Request, user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}
```

### 4. Run your API

```bash
# Development mode (with hot reload)
fastapi-route dev

# Production mode (requires build first)
fastapi-route build
fastapi-route run
```

Visit `http://localhost:8000/docs` for auto-generated documentation.

## How It Works

```text
routes/
├── index.py                    → GET /, POST /
├── about/
│   └── route.py                → GET /about
├── users/
│   ├── route.py                → GET /users, POST /users
│   ├── [user_id]/
│   │   └── route.py            → GET /users/{user_id}, PUT /users/{user_id}
│   └── [user_id]/posts/
│       └── route.py            → GET /users/{user_id}/posts
├── docs/
│   └── [...slug]/
│       └── route.py            → GET /docs/*
└── (auth)/                     # Route group (ignored in URL)
    └── profile/
        └── route.py            → GET /profile
```

## CLI Commands

| Command                | Description                                 |
| ---------------------- | ------------------------------------------- |
| `fastapi-route init`   | Create a new project with default structure |
| `fastapi-route build`  | Compile routes into production cache        |
| `fastapi-route run`    | Start production server (requires build)    |
| `fastapi-route dev`    | Start development server with hot reload    |
| `fastapi-route clean`  | Remove build cache                          |
| `fastapi-route status` | Show build cache information                |

## Customization

### Configuration (`config.py`)

```python
app_name = "My API"
debug = False
cors_enabled = True
cors_origins = ["https://example.com"]

server = {
    "host": "0.0.0.0",
    "port": 8080,
    "workers": 4
}

logging = {
    "level": "INFO",
    "format": "[%Y-%m-%d %H:%M:%S]",
    "color": True
}

commands = {
    "deploy": "fastapi-route build && rsync -avz .cache/ deploy/"
}
```

### Custom Middleware (`middleware.py`)

```python
from fastapi_route import Request

async def middleware(request: Request, call_next):
    # Log every request
    print(f"{request.method} {request.path}")

    # Continue to the route handler
    response = await call_next(request)

    # Add custom header
    response.headers["X-Powered-By"] = "FastAPI Route"

    return response
```

### Custom 404 Page (`not-found.py`)

```python
from fastapi_route import Request, HTMLResponse

def handler(request: Request, context):
    routes = context.get_routes()

    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>404 - Not Found</title></head>
    <body>
        <h1>404 - Page Not Found</h1>
        <p>{request.path} does not exist</p>
        <p>Total routes: {len(routes)}</p>
        <a href="/">Go Home</a>
    </body>
    </html>
    """, status_code=404)
```

## Documentation

For complete documentation, API reference, and advanced usage examples, visit:

**[https://inject3r.github.io/fastapi-route](https://inject3r.github.io/fastapi-route)**

The documentation includes:

- Detailed API reference for all modules and classes
- Advanced routing patterns and best practices
- Configuration options and their effects
- Error handling strategies
- Migration guides from traditional FastAPI
- Production deployment guides

## Repository

Source code and issue tracking:

**[https://github.com/inject3r/fastapi-route](https://github.com/inject3r/fastapi-route)**

## Requirements

- Python 3.9+
- FastAPI 0.100.0+
- Uvicorn 0.23.0+

## Running Tests

```bash
# Run all tests with coverage
./scripts/test.sh

# Clean test output files
./scripts/test_clean.sh
```

## Project Structure

```text
your-project/
├── routes/                 # Your API routes (file-based)
│   ├── index.py
│   └── ...
├── public/                 # Static files (served at /)
│   ├── css/
│   ├── js/
│   └── images/
├── config.py               # Application configuration
├── middleware.py           # Custom middleware (optional)
├── docs.py                 # Custom documentation (optional)
├── not-found.py            # Custom 404 page (optional)
└── .cache/                 # Build cache (auto-generated)
```

## Why No Decorators?

FastAPI Route was built for developers who think in terms of files and directories, not decorators and route registrations. Just create files — they become endpoints. Create directories — they become route segments. Use `[param]` for dynamic parameters. Use `(group)` for organization.

No decorators. No route registration. Just files.

## License

This project is licensed under the MIT License.

## Author

**Abolfazl Hosseini**

- Email: tryuzr@gmail.com
- GitHub: [@inject3r](https://github.com/inject3r)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - The amazing web framework
- All contributors and users of this project

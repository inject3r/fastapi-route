"""Sample route definitions for testing"""

from pathlib import Path
from fastapi_route import Request


def create_sample_route_file(path: Path, content: str):
    """Create a sample route file at given path"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# Sample route file contents (fixed: removed await from non-async functions)
SIMPLE_ROUTE = '''
from fastapi_route import Request

def GET(request: Request):
    return {"message": "GET request"}

def POST(request: Request):
    return {"message": "POST request"}
'''

DYNAMIC_ROUTE = '''
from fastapi_route import Request

def GET(request: Request, user_id: int):
    return {"user_id": user_id}

def PUT(request: Request, user_id: int):
    # Without await for sync function
    return {"updated": user_id}
'''

CATCH_ALL_ROUTE = '''
from fastapi_route import Request

def GET(request: Request, slug: list):
    return {"segments": slug}
'''

ROUTE_WITH_CONTEXT = '''
from fastapi_route import Request

def GET(request: Request, context):
    routes = context.get_routes()
    return {"route_count": len(routes)}
'''

INDEX_ROUTE = '''
from fastapi_route import Request

def GET(request: Request):
    return {"home": True}
'''

ABOUT_ROUTE = '''
from fastapi_route import Request

def GET(request: Request):
    return {"about": "About page"}
'''

CONTACT_ROUTE = '''
from fastapi_route import Request

def GET(request: Request):
    return {"contact": "contact@example.com"}

def POST(request: Request):
    # Without await for sync function
    return {"sent": True}
'''

# Async versions for tests that need async
ASYNC_SIMPLE_ROUTE = '''
from fastapi_route import Request

async def GET(request: Request):
    return {"message": "GET request"}

async def POST(request: Request):
    data = await request.json()
    return {"received": data}
'''

ASYNC_DYNAMIC_ROUTE = '''
from fastapi_route import Request

async def GET(request: Request, user_id: int):
    return {"user_id": user_id}

async def PUT(request: Request, user_id: int):
    data = await request.json()
    return {"updated": user_id, "data": data}
'''
"""
Vercel Serverless Function Entry Point for OmniPulse FastAPI Backend.
Exposes the FastAPI ASGI application instance as `app` for Vercel's Python runtime.
Includes ASGI path normalization middleware to prevent routing 404 mismatches
when invoked behind Vercel rewrites.
"""
import os
import sys

# Ensure backend and current directory are on the Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PARENT_DIR, "backend")

for directory in [BACKEND_DIR, PARENT_DIR, CURRENT_DIR]:
    if os.path.exists(directory) and directory not in sys.path:
        sys.path.insert(0, directory)

# Import the FastAPI ASGI app instance
try:
    from app.main import app as fastapi_app
except ImportError:
    from backend.app.main import app as fastapi_app


class VercelPathMiddleware:
    """
    ASGI middleware ensuring that Vercel serverless requests with rewrites
    (/api/(.*) -> /api/index.py) preserve the true incoming URI path
    instead of being masked as /api/index.py.
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            current_path = scope.get("path", "")
            headers = dict(scope.get("headers", []))

            # Check for Vercel routing headers
            matched_path = (
                headers.get(b"x-matched-path")
                or headers.get(b"x-now-route-matches")
                or headers.get(b"x-forwarded-uri")
                or headers.get(b"x-original-uri")
            )

            if matched_path:
                try:
                    decoded = matched_path.decode("utf-8")
                    if decoded and not decoded.endswith("index.py"):
                        scope["path"] = decoded.split("?")[0]
                except Exception:
                    pass
            elif current_path.endswith("index.py") or current_path == "/api":
                # Fallback: check query parameters if encoded
                query_string = scope.get("query_string", b"").decode("utf-8")
                if "path=" in query_string:
                    for part in query_string.split("&"):
                        if part.startswith("path="):
                            scope["path"] = "/" + part.split("=", 1)[1].lstrip("/")
                            break

        await self.inner_app(scope, receive, send)


app = VercelPathMiddleware(fastapi_app)
__all__ = ["app"]

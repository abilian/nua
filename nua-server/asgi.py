"""
Entry point for asgi servers, e.g. uvicorn
"""

from nua_server.main import create_app

app = create_app()

__all__ = ["app"]

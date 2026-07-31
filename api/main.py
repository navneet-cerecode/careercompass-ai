"""ASGI entry point used by Uvicorn."""

from api.application import create_app

app = create_app()

"""Compatibility shim for legacy imports and direct execution."""

import uvicorn

from app.main import app  # noqa: F401
from app.schemas.config import settings


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT)

"""
Compatibility shim for legacy imports.
The canonical ASGI application is now at app.main:app
"""
from app.main import app  # noqa: F401

# For backwards compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

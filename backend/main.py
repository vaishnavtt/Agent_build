"""AgentForge AI Backend Application Entry Point.

Starts the FastAPI server with SQLite persistence, CORS middleware, and REST routes.
Can be run via:
    uvicorn main:app --reload --port 8000
or:
    uvicorn app.main:app --reload --port 8000
"""

from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

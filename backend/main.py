if __package__ in (None, ""):
    # Allow `python backend/main.py` from the project root as well as the
    # recommended `python -m uvicorn backend.main:app` command.
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.routes.health_routes import router as health_router
from backend.routes.meeting_routes import router as meeting_router
from backend.routes.transcript_routes import router as transcript_router
from backend.routes.screen_routes import router as screen_router
from backend.routes.important_routes import router as important_router
from backend.routes.report_routes import router as report_router
from backend.routes.export_routes import router as export_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", description="Google Meet notes and insights MVP")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"], allow_headers=["Content-Type"])
for router in (health_router, meeting_router, transcript_router, screen_router, important_router, report_router, export_router):
    app.include_router(router)

@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.api_host, port=settings.api_port)

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import kpi, genie, email, campaigns

app = FastAPI(title="MSC Cargo Brand Manager", version="0.1.0")

app.include_router(kpi.router)
app.include_router(genie.router)
app.include_router(email.router)
app.include_router(campaigns.router)


@app.get("/api/health", operation_id="healthCheck")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Serve frontend
DIST_DIR = Path(__file__).parent.parent / "__dist__"


@app.get("/{path:path}")
async def serve_frontend(path: str):
    if DIST_DIR.exists():
        file_path = DIST_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")
    return {"error": "Frontend not built"}

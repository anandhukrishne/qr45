"""
qr45 - FastAPI Backend (45 Studios)
Production-ready backend for deployment on Render, container services, or local servers.
Allows cross-origin requests from the frontend at https://qr45.anandhukrishne.tech.
"""

import os
import io
import pathlib
import urllib.request
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Support both qr_engine and legacy qrengine import names
try:
    import qr_engine as engine
except ImportError:
    import qrengine as engine

BASE_DIR = pathlib.Path(__file__).parent

app = FastAPI(
    title="qr45 API - 45 Studios",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Configuration ────────────────────────────────────────────────────────
# Using allow_origin_regex to support any localhost port, Render backend URLs,
# custom domains (e.g. https://qr45.anandhukrishne.tech), and staging environments
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

# ── Static & Frontend Routes ──────────────────────────────────────────────────
if (BASE_DIR / "static").is_dir():
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/health", summary="Health check endpoint for Render / monitoring", tags=["System"])
def health_check():
    return JSONResponse(content={"status": "healthy", "service": "qr45-engine", "version": "2.0.0"})

@app.get("/", include_in_schema=False)
def serve_index():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(content={"message": "qr45 API is running. Access API documentation at /docs."})

@app.get("/styles.css", include_in_schema=False)
def serve_styles():
    css_file = BASE_DIR / "styles.css"
    if css_file.exists():
        return FileResponse(str(css_file), media_type="text/css")
    raise HTTPException(status_code=404, detail="Stylesheet not found")

@app.get("/favicon.png", include_in_schema=False)
def serve_favicon():
    fav_file = BASE_DIR / "favicon.png"
    if fav_file.exists():
        return FileResponse(str(fav_file), media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/favicon.ico", include_in_schema=False)
def serve_favicon_ico():
    fav_file = BASE_DIR / "favicon.png"
    if fav_file.exists():
        return FileResponse(str(fav_file), media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/{filename}.svg", include_in_schema=False)
def serve_svg_file(filename: str):
    svg_path = BASE_DIR / f"{filename}.svg"
    if svg_path.exists() and svg_path.is_file():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="SVG not found")


# ── Unified QR Generation Endpoint ───────────────────────────────────────────
@app.post("/api/qr/generate", summary="Generate qr45 code (PNG, SVG, or Animated GIF)", tags=["QR Generator"])
async def generate_qr(
    data: str = Form(..., description="Text or URL to encode"),
    fill_color: str = Form("#FB542B", description="Foreground hex color"),
    back_color: str = Form("#0E1117", description="Background hex color"),
    box_size: int = Form(10, ge=1, le=50, description="Pixels per module"),
    border: int = Form(2, ge=0, le=10, description="Border quiet zone in modules"),
    module_shape: str = Form("square", description="square | rounded | circle | gapped"),
    format: str = Form("png", description="png | svg | animated"),
    media_mode: str = Form("none", description="none | logo | gif"),
    media_url: Optional[str] = Form(None, description="Direct URL to logo or background GIF"),
    media_file: Optional[UploadFile] = File(None, description="Uploaded logo or GIF"),
):
    if not data.strip():
        raise HTTPException(status_code=400, detail="Data payload cannot be empty.")

    # 1. Resolve media bytes if media_mode != 'none'
    media_bytes = None
    if media_mode in ("logo", "gif"):
        if media_file and media_file.filename:
            media_bytes = await media_file.read()
        elif media_url and media_url.strip():
            try:
                req = urllib.request.Request(
                    media_url.strip(),
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) qr45/2.0"},
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    media_bytes = resp.read()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to fetch media from URL: {str(e)}")

    try:
        # 2. Animated GIF mode
        if media_mode == "gif" and media_bytes:
            buf = engine.generate_qr45_animated(
                data=data,
                background_gif_bytes=media_bytes,
                scale=max(3, min(box_size, 16)),
            )
            return Response(content=buf.getvalue(), media_type="image/gif")

        # 3. Vector SVG format
        if format.lower() == "svg":
            svg_content = engine.generate_qr45_svg(
                data=data,
                fill_color=fill_color,
                back_color=back_color,
                box_size=box_size,
                border=border,
            )
            return Response(content=svg_content, media_type="image/svg+xml")

        # 4. Standard / Styled PNG (with optional logo)
        buf = engine.generate_qr45_png(
            data=data,
            fill_color=fill_color,
            back_color=back_color,
            box_size=box_size,
            border=border,
            module_shape=module_shape,
            logo_bytes=media_bytes if media_mode == "logo" else None,
        )
        return Response(content=buf.getvalue(), media_type="image/png")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(exc)}")


# Backward compatibility aliases
@app.post("/api/qr/standard", include_in_schema=False)
async def legacy_standard_qr(
    data: str = Form(...),
    fill_color: str = Form("#FB542B"),
    back_color: str = Form("#0E1117"),
    box_size: int = Form(10),
    border: int = Form(2),
):
    return await generate_qr(
        data=data,
        fill_color=fill_color,
        back_color=back_color,
        box_size=box_size,
        border=border,
        module_shape="square",
        format="png",
        media_mode="none",
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=False)

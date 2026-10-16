"""
qr45 - FastAPI Backend (45 Studios)
Unified endpoint for generating standard, styled, logo, and animated QR codes with PNG & SVG exports.
"""

import io
import pathlib
import urllib.request
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

import qrengine

BASE_DIR = pathlib.Path(__file__).parent

app = FastAPI(title="qr45 API - 45 Studios", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

# ── Static & Frontend Routes ──────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/styles.css", include_in_schema=False)
def serve_styles():
    return FileResponse(str(BASE_DIR / "styles.css"), media_type="text/css")

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
@app.post("/api/qr/generate", summary="Generate qr45 code (PNG, SVG, or Animated GIF)")
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
            buf = qrengine.generate_qr45_animated(
                data=data,
                background_gif_bytes=media_bytes,
                scale=max(3, min(box_size, 16)),
            )
            return Response(content=buf.getvalue(), media_type="image/gif")

        # 3. Vector SVG format
        if format.lower() == "svg":
            svg_content = qrengine.generate_qr45_svg(
                data=data,
                fill_color=fill_color,
                back_color=back_color,
                box_size=box_size,
                border=border,
            )
            return Response(content=svg_content, media_type="image/svg+xml")

        # 4. Standard / Styled PNG (with optional logo)
        buf = qrengine.generate_qr45_png(
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bknd:app", host="127.0.0.1", port=8000, reload=True)
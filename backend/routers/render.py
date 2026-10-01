import sys
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from models.schemas import RenderRequest, RenderResponse
from services.renderer import render_handwriting
from config import ASSETS_DIR, RENDERS_DIR, FONTS_DIR
import os

router = APIRouter(prefix="/api/render", tags=["render"])


def _get_font_path(session_id: str) -> str:
    """Get the font path for a session, falling back to a system font."""
    font_path = FONTS_DIR / session_id / "handwriting.ttf"
    
    if font_path.exists():
        return str(font_path)
    
    # Fallback to a reliable system font
    if sys.platform == 'win32':
        fallbacks = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    else:
        fallbacks = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    
    for fb in fallbacks:
        if os.path.exists(fb):
            return fb
    
    return "arial.ttf"  # Last resort


@router.get("/status/{session_id}")
def font_status(session_id: str):
    """Check if the font has been built for a given session."""
    font_path = FONTS_DIR / session_id / "handwriting.ttf"
    return {
        "session_id": session_id,
        "font_ready": font_path.exists(),
        "font_path": str(font_path) if font_path.exists() else None
    }


@router.post("", response_model=RenderResponse)
def render_text(req: RenderRequest):
    font_path = _get_font_path(req.session_id)
        
    try:
        result = render_handwriting(
            text=req.text,
            font_path=font_path,
            paper_style=req.paper_style,
            pen_color=req.pen_color,
            jitter_intensity=req.jitter_intensity,
            assets_dir=ASSETS_DIR,
            renders_dir=RENDERS_DIR
        )
        return RenderResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{render_id}")
def export_render(render_id: str, format: str = "png"):
    if format.lower() == "pdf":
        file_path = RENDERS_DIR / f"{render_id}.pdf"
        media = "application/pdf"
    else:
        file_path = RENDERS_DIR / f"{render_id}.png"
        media = "image/png"
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Render not found")
        
    return FileResponse(file_path, media_type=media, filename=f"handwriting.{format.lower()}")

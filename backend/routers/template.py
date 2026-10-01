from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict
import uuid
import os
import aiofiles
from pathlib import Path

from config import UPLOADS_DIR, GLYPHS_DIR, ASSETS_DIR, FONTS_DIR, ALLOWED_FILE_TYPES, MAX_UPLOAD_SIZE
from models.schemas import TemplateUploadResponse
from services.extractor import extract_glyphs
from services.vectorizer import vectorize_all_glyphs
from services.font_builder import build_font

router = APIRouter(prefix="/api/template", tags=["template"])

def process_font_background(session_id: str):
    try:
        session_glyphs = GLYPHS_DIR / session_id
        svg_paths = vectorize_all_glyphs(session_glyphs)
        build_font(session_id, svg_paths, FONTS_DIR)
        print(f"Successfully compiled font for session {session_id}")
    except Exception as e:
        print(f"Failed to build font for {session_id}: {e}")

@router.get("/download")
def download_template():
    template_path = ASSETS_DIR / "template.pdf"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    return FileResponse(template_path, media_type="application/pdf", filename="handwriting_template.pdf")

@router.post("/upload", response_model=TemplateUploadResponse)
async def upload_template(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG/PNG allowed.")
        
    session_id = str(uuid.uuid4())
    upload_path = UPLOADS_DIR / f"{session_id}_{file.filename}"
    
    # Save the uploaded file
    try:
        async with aiofiles.open(upload_path, 'wb') as out_file:
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=400, detail="File too large")
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save file")
        
    # Extract glyphs
    try:
        quality_map = extract_glyphs(str(upload_path), session_id, ASSETS_DIR, GLYPHS_DIR)
        
        # Trigger vectorization and font compilation in the background
        background_tasks.add_task(process_font_background, session_id)
        
        return TemplateUploadResponse(
            session_id=session_id,
            status="extracted",
            character_quality=quality_map
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

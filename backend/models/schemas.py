from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal

class TemplateUploadResponse(BaseModel):
    session_id: str
    status: str
    character_quality: Dict[str, str] = Field(description="Map of character to quality status ('good', 'needs_redo')")

class RenderRequest(BaseModel):
    text: str
    session_id: str
    paper_style: Literal['lined', 'blank', 'grid'] = 'blank'
    pen_color: str = '#1a1a6b'  # Dark blue default
    jitter_intensity: float = Field(1.0, ge=0.0, le=3.0)

class RenderResponse(BaseModel):
    render_id: str
    preview_url: str
    download_url: str

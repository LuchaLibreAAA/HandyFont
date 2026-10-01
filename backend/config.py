import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = BASE_DIR / "assets"

# Storage subdirectories
UPLOADS_DIR = STORAGE_DIR / "uploads"
GLYPHS_DIR = STORAGE_DIR / "glyphs"
FONTS_DIR = STORAGE_DIR / "fonts"
RENDERS_DIR = STORAGE_DIR / "renders"

# Ensure directories exist
for directory in [UPLOADS_DIR, GLYPHS_DIR, FONTS_DIR, RENDERS_DIR, ASSETS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Application constants
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ["image/jpeg", "image/png"]

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:5173",
]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, STORAGE_DIR, ASSETS_DIR
import os

app = FastAPI(title="AI Handwriting Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for assets (like the template PDF) and renders
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/renders", StaticFiles(directory=str(STORAGE_DIR / "renders")), name="renders")

from routers import template, render
app.include_router(template.router)
app.include_router(render.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

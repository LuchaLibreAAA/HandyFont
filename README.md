<p align="center">
  <img src="https://img.shields.io/badge/HandyFont-AI%20Handwriting%20Generator-8b5cf6?style=for-the-badge" alt="HandyFont Badge" />
</p>

# ✍️ HandyFont

**Turn your handwriting into a digital font — then render any text in your own hand.**

HandyFont is a full-stack web app that lets you digitize your handwriting from a simple template, generate a personal font, and render any text as a realistic handwritten image — complete with natural jitter, baseline wobble, and paper backgrounds.

---

## 🎯 How It Works

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌───────────────┐
│  1. Download │     │  2. Upload    │     │  3. Type     │     │  4. Download  │
│   Template   │ ──▶ │   Filled Scan │ ──▶ │   Your Text  │ ──▶ │   Result      │
│   (PDF)      │     │   (PNG/JPEG)  │     │              │     │   (PNG/PDF)   │
└──────────────┘     └───────────────┘     └──────────────┘     └───────────────┘
```

1. **Download** the character template PDF — it has a box for every letter, number, and punctuation mark.
2. **Print, fill it in by hand**, scan or photograph it, and upload the image.
3. The backend **extracts** each glyph, **vectorizes** them, and **builds a TTF font** from your handwriting.
4. **Type any text**, pick a paper style and pen color, and get a handwritten rendering with realistic imperfections.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 · Vite 8 · Tailwind CSS 4 · React Router 7 · Lucide Icons |
| **Backend** | Python · FastAPI · Uvicorn |
| **Image Processing** | OpenCV (contour detection, segmentation) · Pillow (rendering, compositing) |
| **Font Pipeline** | fonttools (TTF compilation) · potrace (raster → vector tracing) |
| **Export** | img2pdf (PDF export) · Pillow (PNG export) |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **potrace** (for glyph vectorization) — [install guide](http://potrace.sourceforge.net/)

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Health check: `GET /health`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## 📡 API Endpoints

### Template

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/template/download` | Download the handwriting capture template (PDF) |
| `POST` | `/api/template/upload` | Upload a filled template image for glyph extraction |

### Rendering

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/render/status/{session_id}` | Check if font has been built for a session |
| `POST` | `/api/render` | Render text with the user's custom font |
| `GET` | `/api/render/export/{render_id}` | Export a render as PNG or PDF |

### Render Request Body

```json
{
  "text": "Hello, world!",
  "session_id": "abc123",
  "paper_style": "lined",
  "pen_color": "#1a1a6b",
  "jitter_intensity": 1.0
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | *required* | The text to render |
| `session_id` | string | *required* | Session from template upload |
| `paper_style` | `"lined"` \| `"blank"` \| `"grid"` | `"blank"` | Background paper style |
| `pen_color` | hex string | `"#1a1a6b"` | Ink color |
| `jitter_intensity` | float (0–3) | `1.0` | Randomization strength for natural look |

---

## 📁 Project Structure

```
HandyFont/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Paths, constants, CORS config
│   ├── requirements.txt         # Python dependencies
│   ├── assets/                  # Template PDF & paper backgrounds
│   │   ├── template.pdf
│   │   └── backgrounds/         # lined.png, blank.png, grid.png
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── template.py          # Template download & upload routes
│   │   └── render.py            # Text rendering & export routes
│   ├── services/
│   │   ├── extractor.py         # Glyph segmentation from template scan
│   │   ├── vectorizer.py        # Raster → vector outline tracing
│   │   ├── font_builder.py      # TTF font compilation from glyphs
│   │   └── renderer.py          # Text-to-image rendering engine
│   └── scripts/
│       ├── generate_template.py # Template PDF generator
│       └── generate_backgrounds.py  # Paper background generator
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx             # React entry point
│       ├── App.jsx              # Router & layout shell
│       ├── api.js               # Centralized API client
│       ├── pages/
│       │   ├── Upload.jsx       # Template download & upload flow
│       │   ├── Editor.jsx       # Text input & rendering options
│       │   └── Preview.jsx      # Rendered output preview & export
│       └── index.css            # Global styles
│
└── README.md
```

---

## 🔧 Processing Pipeline

The core magic happens in the backend services, in this order:

```
Upload (JPEG/PNG)
  │
  ▼
┌─────────────────┐
│   Extractor      │  Segment each character from its template box
│   (OpenCV)       │  → deskew, binarize, trim whitespace
└────────┬────────┘
         ▼
┌─────────────────┐
│   Vectorizer     │  Trace raster glyph bitmaps to vector outlines
│   (potrace)      │  → clean SVG-style paths
└────────┬────────┘
         ▼
┌─────────────────┐
│   Font Builder   │  Map vector glyphs to Unicode codepoints
│   (fonttools)    │  → compile into a .ttf font file
└────────┬────────┘
         ▼
┌─────────────────┐
│   Renderer       │  Draw text character-by-character with:
│   (Pillow)       │  → rotation jitter, baseline wobble,
│                  │  → spacing variation, ink color
│                  │  → composite onto paper background
└─────────────────┘
         │
         ▼
    PNG / PDF export
```

---

## 🎨 Rendering Features

- **Per-character jitter** — each letter gets slight random rotation, offset, and scale changes
- **Baseline wobble** — text lines gently undulate like real handwriting
- **Spacing variation** — letter spacing is slightly randomized
- **Paper backgrounds** — lined, blank, or grid paper textures
- **Custom pen color** — any hex color for the ink
- **Adjustable intensity** — control how much randomization to apply (0 = perfect, 3 = chaotic)

---

## 🗺️ Roadmap

- [ ] Multiple handwriting styles per user
- [ ] Cursive / connected-letter support (stroke-based generation)
- [ ] Ink pressure simulation & texture effects
- [ ] Real-time live preview while typing
- [ ] Multi-language / non-Latin character sets
- [ ] Mobile-responsive capture flow
- [ ] User accounts & font library

---

## 📄 License

This project is for personal use. Please use responsibly — HandyFont is designed for digitizing **your own** handwriting. Do not use it to forge signatures or impersonate others.

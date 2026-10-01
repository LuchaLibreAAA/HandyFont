# MVP Plan: AI Handwriting Generator

## Core concept
User uploads a sample of their handwriting → uploads/pastes typed text → app outputs an image of that text rendered in their handwriting on a paper background.

## Pick your technical approach first

This is the single biggest decision, since it changes the entire build.

**Option A — Custom font from glyphs (recommended for MVP)**
Extract individual letters from the handwriting sample, build a font file from them, then render text with that font plus randomized jitter/rotation/spacing so it doesn't look robotic.
- Pros: Fast to build, deterministic, cheap to run, no model training/hosting needed, works well enough to feel personal.
- Cons: Doesn't capture natural letter-to-letter connections (ligatures) as well as true generative stroke models; same letter always looks similar (unless you add variation logic).

**Option B — Generative stroke synthesis (RNN/diffusion, style-conditioned)**
Use a model (e.g. an implementation of Alex Graves' handwriting synthesis, or a newer diffusion-based handwriting model) conditioned on the user's style to generate pen-stroke sequences, then render those as an image.
- Pros: More naturalistic, better letter connections, more "generative AI" in the literal sense.
- Cons: Needs stroke/pen-trajectory data (not just a photo) for best results, harder to fine-tune per-user in an MVP timeframe, heavier infra (GPU inference), higher risk of not shipping on time.

**For an MVP, go with Option A.** It gets a working, demoable product fastest, and you can swap in Option B later as a "v2 realism upgrade" without changing the product experience.

## MVP user flow
1. User signs up.
2. User is shown a **handwriting capture template** (a PDF/page with each letter, number, and common punctuation in a box) — print it, write in it, take a photo/scan and upload. This structured capture is what makes glyph extraction reliable.
3. Backend extracts each character image from the template.
4. Backend generates a personal font file from those glyphs.
5. User pastes or uploads text.
6. User picks paper style (lined/blank/grid) and pen color.
7. App renders the text using their font onto the paper background, with slight per-character jitter/rotation/baseline wobble so it doesn't look like a uniform font.
8. User downloads the result as an image or PDF.

## MVP feature scope

**Must have (v1):**
- Handwriting capture template (fixed character set)
- Glyph extraction from uploaded template photo
- Font generation from glyphs
- Text-to-handwritten-image rendering with basic randomization (rotation, spacing, baseline jitter)
- One or two paper backgrounds
- Export as PNG/PDF

**Explicitly cut from v1 (do later):**
- Multiple handwriting styles per user
- Cursive/connected-letter realism (stroke-based generation)
- Ink texture/pressure simulation
- Mobile app (start web-only)
- Multi-language/non-Latin character sets
- Real-time editing/preview while typing

## Suggested tech stack
- **Glyph extraction:** OpenCV (contour detection on the scanned template) + a bit of manual cropping fallback for messy scans
- **Font generation:** FontForge (scriptable) or a Python library like `fonttools` to build a TTF/OTF from traced glyph outlines (use `potrace` to convert raster glyphs to vector outlines)
- **Rendering:** A rendering layer (e.g. Pillow/HTML canvas) that draws each character with the custom font, applying randomized transform per character, onto a paper texture image
- **Backend:** Any standard API framework (FastAPI/Node) to handle upload → processing → font generation → render pipeline
- **Storage:** Object storage for fonts, templates, and generated outputs, tied to user accounts

## Key technical steps (the actual pipeline)
1. **Template design** — fixed layout so glyph positions are predictable, making extraction reliable without ML.
2. **Segmentation** — crop each written character from its box.
3. **Cleanup** — deskew, binarize, trim whitespace per glyph.
4. **Vectorization** — trace raster glyphs to vector paths (needed for a proper font file).
5. **Font compilation** — map vector glyphs to Unicode codepoints, build TTF.
6. **Rendering engine** — draw text character-by-character (not as one string) so you can jitter each letter's rotation/position/size slightly and vary spacing — this randomization is what sells the "handwritten" feel and hides font repetition.
7. **Background compositing** — overlay onto a paper texture with subtle color/ink variation.

## Biggest MVP risks
- **Bad scans** (lighting, skew, cropped letters) break extraction — plan for a guided capture UI and a manual "redo this letter" fallback.
- **Repetition artifonting** — same letter rendered identically every time looks fake; randomization logic matters more than font quality.
- **Missing characters** — user might type a character not in their template (accents, symbols); need a fallback (default font or a "recapture" prompt).
- **Legal/consent** — since this mimics someone's handwriting, be clear in ToS this is for the account owner's own handwriting/personal use, and consider disclaimers around signature-forgery misuse.

## Rough phase plan
1. **Week 1–2:** Template design + capture flow + glyph extraction
2. **Week 3:** Font generation pipeline
3. **Week 4:** Text rendering with jitter + paper background compositing
4. **Week 5:** End-to-end flow, export, basic UI
5. **Week 6:** Test with real users' handwriting, tune randomization for realism

---

Want me to turn this into a shareable doc, or start sketching the actual capture-template layout / rendering code?
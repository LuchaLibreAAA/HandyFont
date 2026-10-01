import random
import math
import uuid
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def _load_font(font_path: str, font_size: int) -> ImageFont.FreeTypeFont:
    """Load font with robust fallback chain."""
    try:
        return ImageFont.truetype(str(font_path), font_size)
    except IOError:
        pass

    fallback_fonts = []
    if sys.platform == 'win32':
        fallback_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]
    else:
        fallback_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]

    for fb in fallback_fonts:
        try:
            return ImageFont.truetype(fb, font_size)
        except IOError:
            continue

    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple:
    """Parse hex color string to (r, g, b) tuple."""
    hex_color = hex_color.lstrip('#')
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (26, 26, 107)  # default dark blue


def _get_char_width(font: ImageFont.FreeTypeFont, char: str, font_size: int) -> float:
    """Get the rendered width of a character, with a safe fallback."""
    try:
        w = font.getlength(char)
        if w > 0:
            return w
    except Exception:
        pass
    return font_size * 0.5


def _get_word_width(font: ImageFont.FreeTypeFont, word: str, font_size: int) -> float:
    """Get the estimated rendered width of a word."""
    return sum(_get_char_width(font, c, font_size) for c in word)


def render_handwriting(
    text: str,
    font_path: str,
    paper_style: str,
    pen_color: str,
    jitter_intensity: float,
    assets_dir: Path,
    renders_dir: Path
) -> dict:
    """
    Renders text onto a paper background with handwriting-like jitter effects.

    The jitter_intensity controls how "messy" the handwriting looks:
      0.0 = perfectly neat (no randomization)
      1.0 = natural handwriting level
      2.0+ = increasingly messy

    Effects applied:
      - Per-character rotation jitter
      - Per-character X/Y position jitter
      - Per-word baseline drift (slow sine wave)
      - Ink opacity/pressure variation
      - Character spacing variation
      - Slight size variation per character
    """

    # ── 1. Load Background ──────────────────────────────────────────────
    bg_path = assets_dir / "backgrounds" / f"{paper_style}.png"
    if not bg_path.exists():
        bg_path = assets_dir / "backgrounds" / "blank.png"

    try:
        bg_img = Image.open(bg_path).convert("RGBA")
    except Exception:
        bg_img = Image.new("RGBA", (1200, 1600), "white")

    canvas = bg_img.copy()

    # ── 2. Paper layout constants ────────────────────────────────────────
    # These must match the background generator (generate_backgrounds.py)
    LINE_SPACING = 60          # px between horizontal lines on lined paper
    FIRST_LINE_Y = 150         # first horizontal line y-position
    MARGIN_LEFT_LINE = 100     # red margin line x-position on lined paper

    # Determine layout based on paper style
    if paper_style == 'lined':
        margin_left = MARGIN_LEFT_LINE + 15   # write just right of the margin line
        margin_right = canvas.width - 60
        first_baseline = FIRST_LINE_Y         # first ruled line
        line_height = LINE_SPACING
    elif paper_style == 'grid':
        margin_left = 50
        margin_right = canvas.width - 50
        first_baseline = 80
        line_height = 80  # 2 grid squares
    else:  # blank
        margin_left = 80
        margin_right = canvas.width - 80
        first_baseline = 120
        line_height = 70

    margin_bottom = canvas.height - 80

    # ── 3. Font setup ────────────────────────────────────────────────────
    # Choose font size to fit within line spacing
    # For lined paper, characters should be ~70-80% of line height
    font_size = int(line_height * 0.65)
    font_size = max(font_size, 20)
    font_size = min(font_size, 64)

    font = _load_font(font_path, font_size)

    # For the baseline: text is drawn so that the bottom of typical characters
    # (excluding descenders) sits on the ruled line. We need to offset Y
    # so the baseline of the font lands on the line.
    # Pillow draws text from the top of the bounding box, so we need to
    # account for ascent. We estimate ascent from font metrics.
    try:
        ascent, descent = font.getmetrics()
    except Exception:
        ascent = int(font_size * 0.8)
        descent = int(font_size * 0.2)

    # The y-coordinate for Pillow's text drawing such that the baseline
    # of the text lands on a given line_y:
    #   draw_y = line_y - ascent
    # (because Pillow draws from the top of the glyph)
    baseline_offset = ascent

    # ── 4. Color setup ───────────────────────────────────────────────────
    r, g, b = _hex_to_rgb(pen_color)

    # ── 5. Global jitter parameters (seeded per render for consistency) ──
    j = jitter_intensity  # shorthand

    # Baseline drift: a slow sine wave that shifts the baseline up/down
    # across the line, simulating natural hand movement
    drift_amplitude = 2.0 * j        # max pixels of drift
    drift_frequency = 0.02 * j       # how fast the drift oscillates

    # Per-character rotation (degrees)
    rotation_sigma = 1.5 * j

    # Per-character position jitter (pixels)
    x_jitter_sigma = 0.8 * j
    y_jitter_sigma = 1.2 * j

    # Spacing variation
    spacing_sigma = 0.8 * j

    # Ink opacity variation
    min_opacity = max(0.80, 1.0 - 0.15 * j)

    # ── 6. Render text ───────────────────────────────────────────────────
    text_lines = text.split('\n')
    current_line_idx = 0  # which ruled line we're on
    char_global_idx = 0   # global character counter for drift wave

    for text_line in text_lines:
        # Calculate y position for this ruled line
        line_y = first_baseline + current_line_idx * line_height

        if line_y > margin_bottom:
            break

        if not text_line.strip():
            # Empty line — skip one ruled line
            current_line_idx += 1
            continue

        x = margin_left
        words = text_line.split(' ')

        for word_idx, word in enumerate(words):
            if not word:
                # Extra space
                space_w = _get_char_width(font, ' ', font_size)
                x += space_w
                continue

            # Check if word fits on current line, if not wrap
            word_width = _get_word_width(font, word, font_size)

            if x + word_width > margin_right and x > margin_left + 10:
                # Wrap to next line
                current_line_idx += 1
                line_y = first_baseline + current_line_idx * line_height
                x = margin_left
                if line_y > margin_bottom:
                    break

            # Draw each character in the word
            for char in word:
                char_w = _get_char_width(font, char, font_size)

                # ── Jitter calculations ──
                # Baseline drift (slow sine wave across the line)
                drift_y = drift_amplitude * math.sin(
                    drift_frequency * char_global_idx * 3.0 + current_line_idx * 1.7
                )

                # Per-character position jitter
                jx = random.gauss(0, x_jitter_sigma) if j > 0 else 0
                jy = random.gauss(0, y_jitter_sigma) if j > 0 else 0

                # Per-character rotation
                rotation = random.gauss(0, rotation_sigma) if j > 0 else 0

                # Ink opacity variation
                alpha = int(255 * random.uniform(min_opacity, 1.0))

                # Slight size variation (±5% at jitter=1)
                size_var = 1.0 + random.gauss(0, 0.02 * j) if j > 0 else 1.0
                size_var = max(0.9, min(1.1, size_var))

                # ── Draw the character ──
                # Create a temporary image for the character
                char_img_w = int(char_w + 24)
                char_img_h = int(font_size + descent + 24)
                char_img = Image.new("RGBA", (char_img_w, char_img_h), (0, 0, 0, 0))
                char_draw = ImageDraw.Draw(char_img)

                fill_color = (r, g, b, alpha)
                char_draw.text((12, 12), char, font=font, fill=fill_color)

                # Apply size variation
                if abs(size_var - 1.0) > 0.005:
                    new_w = max(1, int(char_img_w * size_var))
                    new_h = max(1, int(char_img_h * size_var))
                    char_img = char_img.resize((new_w, new_h), Image.LANCZOS)

                # Apply rotation
                if abs(rotation) > 0.1:
                    char_img = char_img.rotate(
                        rotation, expand=True, resample=Image.BICUBIC,
                        fillcolor=(0, 0, 0, 0)
                    )

                # Calculate paste position
                # The baseline should land on line_y
                draw_y = line_y - baseline_offset
                paste_x = int(x + jx - 12)
                paste_y = int(draw_y + jy + drift_y - 12)

                # Clamp to canvas bounds
                paste_x = max(0, paste_x)
                paste_y = max(0, paste_y)

                if (paste_y + char_img.height < canvas.height and
                    paste_x + char_img.width < canvas.width):
                    canvas.alpha_composite(char_img, dest=(paste_x, paste_y))

                # Advance x
                spacing_var = random.gauss(0, spacing_sigma) if j > 0 else 0
                x += char_w * size_var + spacing_var

                char_global_idx += 1

            # Space between words
            space_width = _get_char_width(font, ' ', font_size)
            word_space_jitter = random.gauss(0, 1.5 * j) if j > 0 else 0
            x += space_width + word_space_jitter

        if line_y > margin_bottom:
            break

        # End of text line — move to next ruled line
        current_line_idx += 1

    # ── 7. Save output ───────────────────────────────────────────────────
    render_id = str(uuid.uuid4())
    out_png = renders_dir / f"{render_id}.png"

    # Convert to RGB for smaller file size
    final_img = canvas.convert("RGB")
    final_img.save(out_png, "PNG")

    # Also save as PDF
    out_pdf = renders_dir / f"{render_id}.pdf"
    final_img.save(out_pdf, "PDF", resolution=100.0)

    return {
        "render_id": render_id,
        "preview_url": f"/renders/{render_id}.png",
        "download_url": f"/api/render/export/{render_id}"
    }

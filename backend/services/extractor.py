import cv2
import numpy as np
import json
import os
from pathlib import Path

def extract_glyphs(image_path: str, session_id: str, config_dir: Path, output_dir: Path):
    """
    Extracts glyphs from a filled template image.
    Returns a dict mapping character to status (e.g. 'good', 'needs_redo').
    """
    ref_path = config_dir / "template_reference.json"
    if not ref_path.exists():
        raise FileNotFoundError("Template reference JSON not found.")

    with open(ref_path, 'r') as f:
        ref_data = json.load(f)

    # Create output directory for this session
    session_out_dir = output_dir / session_id
    os.makedirs(session_out_dir, exist_ok=True)

    # 1. Load image and grayscale
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("Could not read image file.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Resize to expected template dimensions
    expected_w, expected_h = ref_data["page_size"]
    resized = cv2.resize(gray, (expected_w, expected_h), interpolation=cv2.INTER_AREA)

    results = {}

    # 3. Extract each cell
    for cell in ref_data["cells"]:
        char = cell["char"]
        x, y, cw, ch = cell["x"], cell["y"], cell["w"], cell["h"]

        # Crop cell
        cell_img = resized[y:y+ch, x:x+cw]

        # Binarize cell using adaptive threshold
        cell_thresh = cv2.adaptiveThreshold(
            cell_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
        )

        # Remove border artifacts (crop inner region)
        margin = 15
        inner_thresh = cell_thresh[margin:ch-margin, margin:cw-margin]

        # Find ink (non-zero pixels)
        ink_pixels = cv2.countNonZero(inner_thresh)

        # Validation: Is there enough ink?
        if ink_pixels < 50:
            results[char] = "needs_redo"
            continue

        # Find bounding box of the ink
        coords = cv2.findNonZero(inner_thresh)
        if coords is not None:
            bx, by, bw, bh = cv2.boundingRect(coords)
            # Crop to tight bounding box
            char_crop = inner_thresh[by:by+bh, bx:bx+bw]

            # ── Improved glyph preparation ──

            # Clean up noise with morphological ops
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            char_crop = cv2.morphologyEx(char_crop, cv2.MORPH_CLOSE, kernel, iterations=1)

            # Pad to square with margin
            padding = 20
            size = max(bw, bh) + padding * 2
            padded = np.zeros((size, size), dtype=np.uint8)

            # Center the character
            y_offset = (size - bh) // 2
            x_offset = (size - bw) // 2
            padded[y_offset:y_offset+bh, x_offset:x_offset+bw] = char_crop

            # The extractor outputs white ink on black background
            # (THRESH_BINARY_INV makes ink=255, bg=0)
            # For vectorization, we need: black ink on white background
            # (vectorizer does THRESH_BINARY_INV again, so it expects
            #  dark ink on light bg)
            final_img = cv2.bitwise_not(padded)

            # Save
            out_path = session_out_dir / f"char_{ord(char)}.png"
            cv2.imwrite(str(out_path), final_img)

            results[char] = "good"
        else:
            results[char] = "needs_redo"

    return results

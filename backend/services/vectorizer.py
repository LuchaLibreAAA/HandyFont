import cv2
import numpy as np
import os
from pathlib import Path


def vectorize_glyph(image_path: Path) -> dict:
    """
    Converts a binary glyph image (PNG) to an SVG path string using
    OpenCV contour detection with smooth cubic Bezier approximation.

    Returns a dict with:
      - 'd': the SVG path d-attribute string
      - 'width': the SVG viewBox width
      - 'height': the SVG viewBox height
    """
    try:
        # Load grayscale image
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not read image file {image_path}")

        h, w = img.shape

        # Apply a slight Gaussian blur to smooth jagged edges before contour detection
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Threshold: ink (dark) on white background from the extractor.
        # THRESH_BINARY_INV makes ink white (255) and background black (0)
        _, thresh = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY_INV)

        # Clean up noise with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        # Find contours (RETR_TREE for outer boundaries + inner holes)
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS
        )

        if not contours:
            raise ValueError("No contours found in the image")

        # Filter: keep only contours with significant area (remove noise specks)
        min_area = max(10, (w * h) * 0.0005)
        valid_contours = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area >= min_area or (hierarchy is not None and hierarchy[0][i][3] != -1):
                valid_contours.append(contour)

        if not valid_contours:
            valid_contours = contours  # fallback to all contours

        path_commands = []

        for contour in valid_contours:
            if len(contour) < 3:
                continue

            # Use a moderate epsilon for smooth but accurate approximation
            peri = cv2.arcLength(contour, True)
            epsilon = 0.003 * peri
            approx = cv2.approxPolyDP(contour, epsilon, True)
            pts = approx.reshape(-1, 2)

            if len(pts) < 3:
                continue

            # Convert polygon points to cubic Bezier curves for smoother rendering
            path_d = _points_to_smooth_svg(pts)
            if path_d:
                path_commands.append(path_d)

        if not path_commands:
            # Fallback: simple polygon paths
            for contour in valid_contours:
                if len(contour) < 3:
                    continue
                epsilon = 0.005 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                pts = approx.reshape(-1, 2)
                if len(pts) >= 3:
                    cmds = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
                    for pt in pts[1:]:
                        cmds.append(f"L {pt[0]:.1f} {pt[1]:.1f}")
                    cmds.append("Z")
                    path_commands.append(" ".join(cmds))

        path_data = " ".join(path_commands)

        return {
            'd': path_data,
            'width': float(w),
            'height': float(h)
        }

    except Exception as e:
        print(f"Vectorization failed for {image_path}: {e}")
        # Fallback to a dummy square
        return {
            'd': "M 10 10 L 90 10 L 90 90 L 10 90 Z",
            'width': 100.0,
            'height': 100.0
        }


def _points_to_smooth_svg(pts: np.ndarray) -> str:
    """
    Convert a polygon's vertices into a smooth closed SVG path
    using cubic Bezier curves (Catmull-Rom → Cubic Bezier conversion).

    This produces much smoother, more natural-looking glyph outlines
    compared to raw polyline segments.
    """
    n = len(pts)
    if n < 3:
        return ""

    # For small polygons (< 6 points), use line segments — not enough
    # points for meaningful smoothing
    if n < 6:
        cmds = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
        for pt in pts[1:]:
            cmds.append(f"L {pt[0]:.1f} {pt[1]:.1f}")
        cmds.append("Z")
        return " ".join(cmds)

    # Catmull-Rom to Bezier conversion for smooth curves
    # For each segment from pts[i] to pts[i+1], we compute control points
    # using the neighboring points
    cmds = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]

    tension = 0.35  # Controls curve tightness (0 = sharp, 0.5 = very smooth)

    for i in range(n):
        p0 = pts[(i - 1) % n].astype(float)
        p1 = pts[i].astype(float)
        p2 = pts[(i + 1) % n].astype(float)
        p3 = pts[(i + 2) % n].astype(float)

        # Catmull-Rom control points converted to cubic Bezier
        cp1x = p1[0] + (p2[0] - p0[0]) * tension
        cp1y = p1[1] + (p2[1] - p0[1]) * tension
        cp2x = p2[0] - (p3[0] - p1[0]) * tension
        cp2y = p2[1] - (p3[1] - p1[1]) * tension

        cmds.append(
            f"C {cp1x:.1f} {cp1y:.1f} {cp2x:.1f} {cp2y:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        )

    cmds.append("Z")
    return " ".join(cmds)


def vectorize_all_glyphs(glyphs_dir: Path) -> dict:
    """
    Iterates over all char_*.png files in the directory, vectorizes them,
    and returns a mapping of character to glyph data dict.
    Each value is: {'d': str, 'width': float, 'height': float}
    """
    glyph_data = {}
    for img_file in glyphs_dir.glob("char_*.png"):
        try:
            char_code = int(img_file.stem.split('_')[1])
            char = chr(char_code)

            data = vectorize_glyph(img_file)
            glyph_data[char] = data
        except Exception as e:
            print(f"Failed processing file {img_file}: {e}")

    return glyph_data

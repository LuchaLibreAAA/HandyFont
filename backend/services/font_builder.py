"""
Font builder: compiles a TrueType font from vectorized glyph data.

Takes a dict of char -> {'d': svg_path_d, 'width': float, 'height': float}
and produces a .ttf file using fontTools.
"""

import os
import re
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

# UPEM = units per em — the coordinate space for the font
UPEM = 1024
ASCENT = 800
DESCENT = -224
CAP_HEIGHT = 700    # Expected height for uppercase letters
X_HEIGHT = 500      # Expected height for lowercase letters


def _parse_svg_d(d_string: str):
    """
    Parse an SVG path 'd' attribute into a list of commands.
    Each command is (type, [args...]).
    Supports: M, L, C, Q, Z (and lowercase relatives).
    Potrace only outputs M, C, L, Z so that's our main concern.
    """
    # Tokenize: split into commands + numbers
    # SVG allows implicit repeated commands and comma/space separation
    tokens = re.findall(r'[MmLlCcQqZzHhVvSsTtAa]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', d_string)

    commands = []
    i = 0
    current_cmd = None

    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            current_cmd = token
            i += 1
        else:
            # It's a number — use the current command
            pass

        if current_cmd is None:
            i += 1
            continue

        if current_cmd in ('Z', 'z'):
            commands.append(('Z', []))
            current_cmd = None

        elif current_cmd in ('M', 'm'):
            if i < len(tokens) and not tokens[i].isalpha():
                x, y = float(tokens[i]), float(tokens[i+1])
                commands.append((current_cmd, [x, y]))
                i += 2
                # After M, implicit commands are L
                if current_cmd == 'M':
                    current_cmd = 'L'
                else:
                    current_cmd = 'l'
            else:
                break

        elif current_cmd in ('L', 'l'):
            if i < len(tokens) and not tokens[i].isalpha():
                x, y = float(tokens[i]), float(tokens[i+1])
                commands.append((current_cmd, [x, y]))
                i += 2
            else:
                break

        elif current_cmd in ('H', 'h'):
            if i < len(tokens) and not tokens[i].isalpha():
                x = float(tokens[i])
                commands.append((current_cmd, [x]))
                i += 1
            else:
                break

        elif current_cmd in ('V', 'v'):
            if i < len(tokens) and not tokens[i].isalpha():
                y = float(tokens[i])
                commands.append((current_cmd, [y]))
                i += 1
            else:
                break

        elif current_cmd in ('C', 'c'):
            if i + 5 < len(tokens):
                coords = [float(tokens[i+j]) for j in range(6)]
                commands.append((current_cmd, coords))
                i += 6
            else:
                break

        elif current_cmd in ('Q', 'q'):
            if i + 3 < len(tokens):
                coords = [float(tokens[i+j]) for j in range(4)]
                commands.append((current_cmd, coords))
                i += 4
            else:
                break
        else:
            # Skip unsupported commands
            i += 1

    return commands


def _get_path_bounds(commands):
    """
    Calculate the bounding box of parsed SVG path commands.
    Returns (min_x, min_y, max_x, max_y) or None if no points found.
    """
    xs = []
    ys = []
    cur_x, cur_y = 0.0, 0.0

    for cmd_type, args in commands:
        if cmd_type == 'M':
            cur_x, cur_y = args[0], args[1]
            xs.append(cur_x)
            ys.append(cur_y)
        elif cmd_type == 'm':
            cur_x += args[0]
            cur_y += args[1]
            xs.append(cur_x)
            ys.append(cur_y)
        elif cmd_type == 'L':
            cur_x, cur_y = args[0], args[1]
            xs.append(cur_x)
            ys.append(cur_y)
        elif cmd_type == 'l':
            cur_x += args[0]
            cur_y += args[1]
            xs.append(cur_x)
            ys.append(cur_y)
        elif cmd_type == 'H':
            cur_x = args[0]
            xs.append(cur_x)
        elif cmd_type == 'h':
            cur_x += args[0]
            xs.append(cur_x)
        elif cmd_type == 'V':
            cur_y = args[0]
            ys.append(cur_y)
        elif cmd_type == 'v':
            cur_y += args[0]
            ys.append(cur_y)
        elif cmd_type == 'C':
            for j in range(0, 6, 2):
                xs.append(args[j])
                ys.append(args[j+1])
            cur_x, cur_y = args[4], args[5]
        elif cmd_type == 'c':
            for j in range(0, 6, 2):
                xs.append(cur_x + args[j])
                ys.append(cur_y + args[j+1])
            cur_x += args[4]
            cur_y += args[5]
        elif cmd_type == 'Q':
            xs.extend([args[0], args[2]])
            ys.extend([args[1], args[3]])
            cur_x, cur_y = args[2], args[3]
        elif cmd_type == 'q':
            xs.extend([cur_x + args[0], cur_x + args[2]])
            ys.extend([cur_y + args[1], cur_y + args[3]])
            cur_x += args[2]
            cur_y += args[3]

    if not xs or not ys:
        return None

    return min(xs), min(ys), max(xs), max(ys)


def _cubic_to_quadratic(p0, p1, p2, p3):
    """
    Approximate a cubic bezier with a single quadratic bezier.
    This is a rough approximation that works when the cubic is "gentle enough",
    which is usually the case for potrace output.

    Uses midpoint approximation:
    Q_control = (3*P1 - P0 + 3*P2 - P3) / 4
    """
    qx = (3 * p1[0] - p0[0] + 3 * p2[0] - p3[0]) / 4.0
    qy = (3 * p1[1] - p0[1] + 3 * p2[1] - p3[1]) / 4.0
    return (qx, qy)


def _draw_glyph_on_pen(pen, commands, scale_x, scale_y, offset_x, offset_y):
    """
    Draw parsed SVG path commands onto a TTGlyphPen, applying scaling
    and coordinate transforms (SVG y-down to font y-up).

    All sub-paths are drawn as closed contours (closePath), which is
    required for TrueType glyphs.
    """
    def tx(x, y):
        """Transform SVG coordinates to font coordinates."""
        fx = x * scale_x + offset_x
        fy = (y * scale_y * -1) + offset_y  # Flip Y axis
        return (int(round(fx)), int(round(fy)))

    cur_x, cur_y = 0.0, 0.0
    first_x, first_y = 0.0, 0.0
    path_started = False

    for cmd_type, args in commands:
        if cmd_type == 'M':
            if path_started:
                pen.closePath()
            cur_x, cur_y = args[0], args[1]
            first_x, first_y = cur_x, cur_y
            pen.moveTo(tx(cur_x, cur_y))
            path_started = True

        elif cmd_type == 'm':
            if path_started:
                pen.closePath()
            cur_x += args[0]
            cur_y += args[1]
            first_x, first_y = cur_x, cur_y
            pen.moveTo(tx(cur_x, cur_y))
            path_started = True

        elif cmd_type == 'L':
            cur_x, cur_y = args[0], args[1]
            pen.lineTo(tx(cur_x, cur_y))

        elif cmd_type == 'l':
            cur_x += args[0]
            cur_y += args[1]
            pen.lineTo(tx(cur_x, cur_y))

        elif cmd_type == 'H':
            cur_x = args[0]
            pen.lineTo(tx(cur_x, cur_y))

        elif cmd_type == 'h':
            cur_x += args[0]
            pen.lineTo(tx(cur_x, cur_y))

        elif cmd_type == 'V':
            cur_y = args[0]
            pen.lineTo(tx(cur_x, cur_y))

        elif cmd_type == 'v':
            cur_y += args[0]
            pen.lineTo(tx(cur_x, cur_y))

        elif cmd_type == 'C':
            x1, y1, x2, y2, x3, y3 = args
            # Convert cubic to quadratic approximation
            p0 = (cur_x, cur_y)
            p1 = (x1, y1)
            p2 = (x2, y2)
            p3 = (x3, y3)
            q_ctrl = _cubic_to_quadratic(p0, p1, p2, p3)
            pen.qCurveTo(tx(q_ctrl[0], q_ctrl[1]), tx(x3, y3))
            cur_x, cur_y = x3, y3

        elif cmd_type == 'c':
            x1, y1 = cur_x + args[0], cur_y + args[1]
            x2, y2 = cur_x + args[2], cur_y + args[3]
            x3, y3 = cur_x + args[4], cur_y + args[5]
            p0 = (cur_x, cur_y)
            p1 = (x1, y1)
            p2 = (x2, y2)
            p3 = (x3, y3)
            q_ctrl = _cubic_to_quadratic(p0, p1, p2, p3)
            pen.qCurveTo(tx(q_ctrl[0], q_ctrl[1]), tx(x3, y3))
            cur_x, cur_y = x3, y3

        elif cmd_type == 'Q':
            qx, qy, ex, ey = args
            pen.qCurveTo(tx(qx, qy), tx(ex, ey))
            cur_x, cur_y = ex, ey

        elif cmd_type == 'q':
            qx, qy = cur_x + args[0], cur_y + args[1]
            ex, ey = cur_x + args[2], cur_y + args[3]
            pen.qCurveTo(tx(qx, qy), tx(ex, ey))
            cur_x, cur_y = ex, ey

        elif cmd_type in ('Z', 'z'):
            pen.closePath()
            path_started = False
            cur_x, cur_y = first_x, first_y

    if path_started:
        pen.closePath()


def build_font(session_id: str, glyph_data: dict, fonts_dir: Path) -> Path:
    """
    Compiles a TrueType font from vectorized glyph data.

    Args:
        session_id: unique session identifier
        glyph_data: dict of char -> {'d': str, 'width': float, 'height': float}
        fonts_dir: directory to save the font file

    Returns:
        Path to the generated .ttf file
    """
    out_dir = fonts_dir / session_id
    os.makedirs(out_dir, exist_ok=True)
    out_path = out_dir / "handwriting.ttf"

    # 1. Initialize FontBuilder
    fb = FontBuilder(UPEM, isTTF=True)

    # 2. Setup glyph order
    glyph_order = [".notdef", "space"]
    char_to_glyph_name = {}

    for char in sorted(glyph_data.keys()):
        # Create a safe glyph name
        if char.isalnum():
            glyph_name = char
        else:
            glyph_name = f"uni{ord(char):04X}"
        char_to_glyph_name[char] = glyph_name
        glyph_order.append(glyph_name)

    fb.setupGlyphOrder(glyph_order)

    # 3. Character map
    cmap = {ord(c): char_to_glyph_name[c] for c in glyph_data.keys()}
    cmap[0x20] = "space"  # Space character
    fb.setupCharacterMap(cmap)

    # 4. Build glyphs
    glyphs = {}
    metrics = {}

    # Left side bearing for all glyphs
    LSB = 50

    # .notdef glyph (empty rectangle)
    pen = TTGlyphPen(glyphSet=None)
    pen.moveTo((50, 0))
    pen.lineTo((50, 700))
    pen.lineTo((450, 700))
    pen.lineTo((450, 0))
    pen.closePath()
    glyphs[".notdef"] = pen.glyph()
    metrics[".notdef"] = (500, 50)

    # Space glyph (empty — no contours needed)
    pen = TTGlyphPen(glyphSet=None)
    # An empty glyph with no drawing commands — just call glyph() directly
    glyphs["space"] = pen.glyph()
    metrics["space"] = (UPEM // 4, 0)  # ~256 units wide

    # ── Compute a consistent scale factor across all glyphs ──
    # We want all characters to be scaled consistently so they look
    # proportional to each other. Use the median height of all glyphs
    # as the reference.
    heights = []
    widths = []
    for char, data in glyph_data.items():
        commands = _parse_svg_d(data['d'])
        bounds = _get_path_bounds(commands)
        if bounds:
            _, min_y, _, max_y = bounds
            _, min_x, _, max_x = bounds
            h = max_y - min_y
            w = max_x - min_x
            if h > 0:
                heights.append(h)
            if w > 0:
                widths.append(w)

    if heights:
        # Use the median height for normalization
        heights.sort()
        median_height = heights[len(heights) // 2]
    else:
        median_height = 100.0  # fallback

    # Scale so the median glyph height maps to CAP_HEIGHT in font units
    global_scale = CAP_HEIGHT / max(median_height, 1)

    # Process each character
    for char, data in glyph_data.items():
        glyph_name = char_to_glyph_name[char]
        d_string = data['d']

        # Parse the SVG path
        commands = _parse_svg_d(d_string)

        if not commands:
            # If parsing failed, use a simple placeholder
            pen = TTGlyphPen(glyphSet=None)
            pen.moveTo((100, 0))
            pen.lineTo((100, 500))
            pen.lineTo((400, 500))
            pen.lineTo((400, 0))
            pen.closePath()
            glyphs[glyph_name] = pen.glyph()
            metrics[glyph_name] = (500, 50)
            continue

        # Get the actual bounds of this glyph's path
        bounds = _get_path_bounds(commands)
        if bounds is None:
            pen = TTGlyphPen(glyphSet=None)
            pen.moveTo((100, 0))
            pen.lineTo((100, 500))
            pen.lineTo((400, 500))
            pen.lineTo((400, 0))
            pen.closePath()
            glyphs[glyph_name] = pen.glyph()
            metrics[glyph_name] = (500, 50)
            continue

        min_x, min_y, max_x, max_y = bounds
        glyph_w = max_x - min_x
        glyph_h = max_y - min_y

        if glyph_w < 1 or glyph_h < 1:
            pen = TTGlyphPen(glyphSet=None)
            pen.moveTo((100, 0))
            pen.lineTo((100, 500))
            pen.lineTo((400, 500))
            pen.lineTo((400, 0))
            pen.closePath()
            glyphs[glyph_name] = pen.glyph()
            metrics[glyph_name] = (500, 50)
            continue

        # Use the global scale for consistent proportions
        scale = global_scale

        # Calculate offset to center the glyph:
        # - X: shift so the glyph starts at LSB (left side bearing)
        # - Y: shift so the baseline is at y=0 and the glyph sits above it
        #       In SVG, y increases downward. In fonts, y increases upward.
        #       After flipping (scale_y * -1), we need to offset so the
        #       bottom of the glyph is at approximately y=0 (baseline).
        offset_x = LSB - min_x * scale
        # After Y-flip: font_y = -svg_y * scale + offset_y
        # We want the bottom of the glyph (max_y in SVG) to map to y ≈ 0 (baseline)
        # So: 0 = -max_y * scale + offset_y  =>  offset_y = max_y * scale
        offset_y = max_y * scale

        # Draw the glyph
        pen = TTGlyphPen(glyphSet=None)
        try:
            _draw_glyph_on_pen(
                pen, commands,
                scale_x=scale,
                scale_y=scale,
                offset_x=int(round(offset_x)),
                offset_y=int(round(offset_y))
            )
            glyphs[glyph_name] = pen.glyph()

            # Calculate advance width: scaled glyph width + side bearings
            advance_width = int(glyph_w * scale) + LSB * 2
            advance_width = max(advance_width, 150)
            advance_width = min(advance_width, UPEM)
            metrics[glyph_name] = (advance_width, LSB)
        except Exception as e:
            print(f"Warning: Failed to build glyph for '{char}': {e}")
            # Fallback to a simple square
            pen = TTGlyphPen(glyphSet=None)
            pen.moveTo((100, 0))
            pen.lineTo((100, 500))
            pen.lineTo((400, 500))
            pen.lineTo((400, 0))
            pen.closePath()
            glyphs[glyph_name] = pen.glyph()
            metrics[glyph_name] = (500, 50)

    # 5. Assemble font tables
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT)
    fb.setupPost()
    fb.setupNameTable({
        "familyName": "HandyFont Custom",
        "styleName": "Regular"
    })

    # 6. Save font
    fb.font.save(str(out_path))
    print(f"Font saved to {out_path}")
    return out_path

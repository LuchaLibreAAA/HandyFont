import json
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

# A4 at 300 DPI: 2480 x 3508
WIDTH = 2480
HEIGHT = 3508
MARGIN = 150
MARKER_SIZE = 60

# We want 80 characters. Let's do 8 columns x 10 rows.
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?'\"-:;()@#&$"

def create_template():
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')
    draw = ImageDraw.Draw(img)
    
    # 1. Draw corner alignment markers (black squares)
    markers = [
        [MARGIN, MARGIN],  # Top-left
        [WIDTH - MARGIN - MARKER_SIZE, MARGIN],  # Top-right
        [MARGIN, HEIGHT - MARGIN - MARKER_SIZE],  # Bottom-left
        [WIDTH - MARGIN - MARKER_SIZE, HEIGHT - MARGIN - MARKER_SIZE]  # Bottom-right
    ]
    for x, y in markers:
        draw.rectangle([x, y, x + MARKER_SIZE, y + MARKER_SIZE], fill='black')
        
    # 2. Draw instructions
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
        
    draw.text((MARGIN + 100, MARGIN), "Handwriting Capture Template", fill='black', font=font)
    draw.text((MARGIN + 100, MARGIN + 50), "Write each character inside its box. Do not touch the box borders.", fill='black', font=font)

    # 3. Draw grid and generate JSON reference
    ref_data = {
        "page_size": [WIDTH, HEIGHT],
        "markers": markers,
        "cells": []
    }
    
    grid_start_y = 400
    grid_start_x = 200
    cell_w = 220
    cell_h = 240
    
    idx = 0
    for row in range(10):
        for col in range(8):
            if idx >= len(CHARS):
                break
            char = CHARS[idx]
            x = grid_start_x + col * cell_w
            y = grid_start_y + row * cell_h
            
            # Draw box
            draw.rectangle([x, y, x + 160, y + 160], outline='black', width=3)
            # Draw label below box
            draw.text((x + 60, y + 170), char, fill='gray', font=font)
            
            ref_data["cells"].append({
                "char": char,
                "row": row,
                "col": col,
                "x": x,
                "y": y,
                "w": 160,
                "h": 160
            })
            idx += 1

    pdf_path = ASSETS_DIR / "template.pdf"
    json_path = ASSETS_DIR / "template_reference.json"
    
    img.save(pdf_path, "PDF", resolution=100.0)
    
    with open(json_path, 'w') as f:
        json.dump(ref_data, f, indent=2)
        
    print(f"Generated {pdf_path} and {json_path}")

if __name__ == "__main__":
    create_template()

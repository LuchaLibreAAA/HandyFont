import os
from PIL import Image, ImageDraw
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BG_DIR = BASE_DIR / "assets" / "backgrounds"
os.makedirs(BG_DIR, exist_ok=True)

WIDTH, HEIGHT = 1200, 1600

def create_blank():
    img = Image.new('RGB', (WIDTH, HEIGHT), '#fdfdf8') # slightly off-white
    img.save(BG_DIR / "blank.png")

def create_lined():
    img = Image.new('RGB', (WIDTH, HEIGHT), '#fdfdf8')
    draw = ImageDraw.Draw(img)
    
    # Margin line
    draw.line([(100, 0), (100, HEIGHT)], fill='#ffb3b3', width=2)
    
    # Horizontal lines
    for y in range(150, HEIGHT, 60):
        draw.line([(0, y), (WIDTH, y)], fill='#b3d9ff', width=2)
        
    img.save(BG_DIR / "lined.png")

def create_grid():
    img = Image.new('RGB', (WIDTH, HEIGHT), '#fdfdf8')
    draw = ImageDraw.Draw(img)
    
    grid_size = 40
    for y in range(0, HEIGHT, grid_size):
        draw.line([(0, y), (WIDTH, y)], fill='#e6e6e6', width=1)
    for x in range(0, WIDTH, grid_size):
        draw.line([(x, 0), (x, HEIGHT)], fill='#e6e6e6', width=1)
        
    img.save(BG_DIR / "grid.png")

if __name__ == "__main__":
    create_blank()
    create_lined()
    create_grid()
    print("Backgrounds generated.")

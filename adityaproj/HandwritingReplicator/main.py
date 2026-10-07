import os
from PIL import Image

# --- Step 1: Path setup ---
dataset_dir = "/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/CharectersDataSet/uniform_dataset"
text_file = "/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/file.txt"
output_file = "/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/output_text.png"

# --- Step 2: Load all character images ---
char_images = {}
for filename in os.listdir(dataset_dir):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        # get just the first character from filename, e.g., 'a' from 'a_uniform.png'
        char_name = os.path.splitext(filename)[0][0].lower()
        img_path = os.path.join(dataset_dir, filename)
        char_images[char_name] = Image.open(img_path).convert("RGBA")

if not char_images:
    raise FileNotFoundError(f"No images found in {dataset_dir}")

# --- Step 3: Read input text ---
with open(text_file, "r", encoding="utf-8") as f:
    text = f.read().strip()

if not text:
    raise ValueError("Text file is empty!")

# --- Step 4: Layout setup ---
sample_img = next(iter(char_images.values()))
char_width, char_height = sample_img.size
padding = 0
max_chars_per_line = 40

# Split text into lines
lines = [text[i:i + max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]

# --- Step 5: Create output canvas ---
img_width = (char_width + padding) * max_chars_per_line + padding
img_height = (char_height + padding) * len(lines) + padding
output_img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 255))  # white background

# --- Step 6: Paste each character ---
y_offset = padding
for line in lines:
    x_offset = padding
    for char in line:
        lower_char = char.lower()
        if lower_char in char_images:
            char_img = char_images[lower_char]
            # Paste respecting transparency (mask = alpha channel)
            output_img.paste(char_img, (x_offset, y_offset), mask=char_img.split()[3])
        x_offset += char_width + padding
    y_offset += char_height + padding

# --- Step 7: Save final image ---
output_img.save(output_file)
print(f"✅ Handwritten image saved as: {output_file}")
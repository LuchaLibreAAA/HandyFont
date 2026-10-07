from PIL import Image

# --- Step 1: Load your handwritten character image ---
# Example: your handwritten 'a' image file (PNG or JPG)
handwritten_a = Image.open("/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/CharectersDataSet/a.jpeg")
# handwritten_b

# --- Step 2: Read text from file ---
with open("/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/README.txt", "r") as f:
    text = f.read()

# --- Step 3: Define spacing and image size ---
char_width, char_height = handwritten_a.size
padding=0
img_width = (char_width + padding) * len(text)
img_height = char_height + 2 * padding

# --- Step 4: Create a blank white image ---
output_img = Image.new("RGB", (img_width, img_height), "white")

# --- Step 5: Paste each character ---
x_offset = padding
for char in text:
    if char == "a":  # Only 'a' supported now
        output_img.paste(handwritten_a, (x_offset, padding))
    x_offset += char_width + padding

# --- Step 6: Save output image ---
output_img.save("/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/output_text.png")
print("✅ Image saved as output_text.png")

import cv2
import numpy as np
import os
import argparse

# Try importing ML dependencies
try:
    import pytesseract
    from PIL import Image
    HAS_ML_TOOLS = True
except ImportError:
    HAS_ML_TOOLS = False

def get_unique_filepath(output_dir: str, char: str, ext: str = "jpeg") -> str:
    """Generate a unique filepath by appending a counter if the file already exists."""
    filename = f"{char}.{ext}"
    filepath = os.path.join(output_dir, filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{char}_{counter}.{ext}"
        filepath = os.path.join(output_dir, filename)
        counter += 1
    return filepath


def extract_characters_classic(image_path: str, transcript: str, output_dir: str = "ExtractedDataSet") -> None:
    """
    Classic Computer Vision approach (Contours).
    Requires a manual transcript to map bounding boxes to characters.
    """
    print("🔬 Running Classic CV Extraction...")
    os.makedirs(output_dir, exist_ok=True)
        
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Error: Could not load image {image_path}")
        return
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    kernel = np.ones((3,3), np.uint8)
    thresh_dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    contours, _ = cv2.findContours(thresh_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [c for c in contours if cv2.contourArea(c) > 50]
    boxes = [cv2.boundingRect(c) for c in valid_contours]
    
    boxes.sort(key=lambda b: b[1])
    lines, current_line = [], []
    
    for box in boxes:
        if not current_line:
            current_line.append(box)
        else:
            if abs(box[1] - current_line[-1][1]) < 30:
                current_line.append(box)
            else:
                lines.append(current_line)
                current_line = [box]
    if current_line: lines.append(current_line)
        
    sorted_boxes = []
    for line in lines:
        line.sort(key=lambda b: b[0])
        sorted_boxes.extend(line)
        
    transcript_chars = [char for char in transcript if not char.isspace()]
    limit = min(len(sorted_boxes), len(transcript_chars))
    saved_count = 0
    
    for i in range(limit):
        x, y, w, h = sorted_boxes[i]
        char = transcript_chars[i].lower()
        if not char.isalnum(): continue
            
        pad = 4
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
        
        char_img = img[y1:y2, x1:x2]
        
        filepath = get_unique_filepath(output_dir, char)
            
        cv2.imwrite(filepath, char_img)
        saved_count += 1
        
    print(f"✅ Classic CV Extraction complete! {saved_count} characters saved.\n")


def extract_characters_ml(image_path: str, output_dir: str = "ExtractedDataSet") -> None:
    """
    Machine Learning powered extraction using Tesseract OCR (LSTM).
    Automatically segments connected characters AND auto-labels them!
    No transcript is required.
    """
    print("🤖 Running ML Powered Extraction (Tesseract)...")
    if not HAS_ML_TOOLS:
        print("❌ Error: Missing ML dependencies.")
        print("Please run: pip install pytesseract Pillow")
        return

    os.makedirs(output_dir, exist_ok=True)

    img_cv = cv2.imread(image_path)
    if img_cv is None:
        print(f"❌ Error: Could not load image {image_path}")
        return

    # Convert to grayscale for better ML inference
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    img_pil = Image.fromarray(gray)
    h, w = img_cv.shape[:2]

    try:
        # image_to_boxes uses the ML model to find character-level bounding boxes and their predicted labels
        box_data = pytesseract.image_to_boxes(img_pil)
    except pytesseract.TesseractNotFoundError:
        print("❌ Error: Tesseract engine is not installed or not in PATH.")
        print("Download for Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("Mac: brew install tesseract | Linux: sudo apt install tesseract-ocr")
        return

    if not box_data.strip():
        print("⚠️ No characters detected by the ML model.")
        return

    saved_count = 0
    for line in box_data.splitlines():
        parts = line.split(' ')
        if len(parts) >= 5:
            char = parts[0].lower()
            
            # Skip punctuation/noise
            if not char.isalnum():
                continue

            # Tesseract coordinates: left, bottom, right, top (from bottom-left origin)
            left, bottom, right, top = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])

            # Convert to OpenCV coordinates (top-left origin)
            x1, y1 = max(0, left), max(0, h - top)
            x2, y2 = min(w, right), min(h, h - bottom)
            
            # Add padding
            pad = 3
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(w, x2 + pad), min(h, y2 + pad)

            if x2 <= x1 or y2 <= y1:
                continue

            char_img = img_cv[y1:y2, x1:x2]

            # Save with auto-label
            filepath = get_unique_filepath(output_dir, char)

            cv2.imwrite(filepath, char_img)
            saved_count += 1

    print(f"✅ ML Extraction complete! {saved_count} characters auto-labeled and saved.\n")


# ==========================================
# 🧪 USAGE EXAMPLE
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract characters from an image for handwriting replication.")
    parser.add_argument("image", help="Path to the input image file")
    parser.add_argument("--method", choices=["classic", "ml"], default="classic", help="Extraction method to use")
    parser.add_argument("--transcript", help="Transcript string required for 'classic' method", default="")
    parser.add_argument("--output", help="Directory to save extracted characters", default="ExtractedDataSet")
    
    args = parser.parse_args()
    
    if args.method == "classic":
        if not args.transcript:
            print("❌ Error: --transcript is required for classic method.")
        else:
            extract_characters_classic(args.image, args.transcript, output_dir=args.output)
    elif args.method == "ml":
        extract_characters_ml(args.image, output_dir=args.output)

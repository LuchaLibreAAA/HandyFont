import cv2
import os
import easyocr

def ml_auto_extract(image_path, output_dir="ecodataset"):
    """
    Uses EasyOCR to detect handwritten words, reads them, 
    and then mathematically slices them into individual letter images.
    """
    print("🤖 Initializing EasyOCR (this may take a moment to load the model)...")
    reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have an NVIDIA GPU
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Error loading image {image_path}")
        return
        
    print(f"📖 Reading text from {image_path}...")
    
    # readtext returns a list of tuples: (bounding_box, text, confidence)
    results = reader.readtext(image_path, decoder='greedy')
    
    saved_count = 0
    print(f"Found {len(results)} words/components.")
    
    for (bbox, text, prob) in results:
        # Ignore very low confidence reads or punctuation noise
        if prob < 0.2 or len(text.strip()) == 0:
            continue
            
        text = text.strip()
        # bbox is a list of 4 points: [top-left, top-right, bottom-right, bottom-left]
        tl = bbox[0]
        br = bbox[2]
        
        x1, y1 = int(tl[0]), int(tl[1])
        x2, y2 = int(br[0]), int(br[1])
        
        # Ensure coordinates are within image
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
        
        if x2 <= x1 or y2 <= y1:
            continue
            
        word_img = img[y1:y2, x1:x2]
        word_width = x2 - x1
        
        # We slice the word image equally among its characters
        char_width = word_width / len(text)
        
        for i, char in enumerate(text):
            char = char.lower()
            if not char.isalnum():
                continue # Skip punctuation
                
            # Calculate the crop for this specific letter
            c_x1 = int(i * char_width)
            c_x2 = int((i + 1) * char_width)
            
            # Add a tiny bit of overlap padding
            c_x1 = max(0, c_x1 - 2)
            c_x2 = min(word_img.shape[1], c_x2 + 2)
            
            char_img = word_img[:, c_x1:c_x2]
            
            # Save it!
            filename = f"{char}.jpeg"
            counter = 1
            filepath = os.path.join(output_dir, filename)
            while os.path.exists(filepath):
                filename = f"{char}_{counter}.jpeg"
                filepath = os.path.join(output_dir, filename)
                counter += 1
                
            cv2.imwrite(filepath, char_img)
            saved_count += 1
            
    print(f"✅ Awesome! Auto-extracted {saved_count} individual characters using AI!")


if __name__ == "__main__":
    # You can loop through all your PDF pages here
    ml_auto_extract("temp_pdf_images/page_0.png", output_dir="ecodataset")

import fitz  # PyMuPDF
import cv2
import os
from dataset_extractor import extract_characters_classic

def convert_pdf_to_images(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    image_paths = []
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img_path = os.path.join(output_dir, f"page_{page_num}.png")
        pix.save(img_path)
        image_paths.append(img_path)
        
    return image_paths

if __name__ == "__main__":
    print("Converting PDF to images...")
    img_paths = convert_pdf_to_images("fletgal.pdf", "temp_pdf_images")
    
    print("Running extraction on PDF pages...")
    # Assuming fletgal.pdf contains a-z in order
    transcript = "abcdefghijklmnopqrstuvwxyz"
    
    # We can run the classic extractor on the first page
    # Since we want it identical to CharectersDataSet, we save to 'ecodataset'
    extract_characters_classic(img_paths[0], transcript, output_dir="ecodataset")
    
    print("Done! Check ecodataset directory.")

import cv2
import numpy as np
import os

def process_image(input_path, output_path, threshold=200, target_size=(128, 128)):
    """
    Converts white background to transparent and resizes image to a fixed size.
    """
    img = cv2.imread(input_path)
    if img is None:
        print(f"❌ Error: Cannot load {input_path}")
        return False

    # Convert to BGRA (adds alpha channel)
    bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    # Mask all near-white pixels
    white_mask = np.all(img > threshold, axis=2)

    # Set alpha channel to 0 for white pixels
    bgra[white_mask, 3] = 0

    # Resize image to exact target size (no aspect ratio preservation)
    resized = cv2.resize(bgra, target_size, interpolation=cv2.INTER_AREA)

    # Save the processed image
    cv2.imwrite(output_path, resized)
    print(f"✅ Saved: {output_path} ({target_size[0]}x{target_size[1]})")
    return True


def batch_process_images(input_dir, output_dir, target_size=(128, 128)):
    """
    Process all images in input_dir and save uniformly sized images to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    supported_ext = (".png", ".jpg", ".jpeg")

    count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_ext):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + "_uniform.png"
            output_path = os.path.join(output_dir, output_filename)
            if process_image(input_path, output_path, target_size=target_size):
                count += 1

    print(f"\n🎯 Finished! Processed {count} images into uniform {target_size[0]}x{target_size[1]} PNGs.")


# ----------------------------
# 🧪 USAGE EXAMPLE
# ----------------------------
input_folder = "/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/CharectersDataSet"
output_folder = os.path.join(input_folder, "uniform_dataset")

# change (128,128) to whatever final size you want
batch_process_images(input_folder, output_folder, target_size=(128, 128))
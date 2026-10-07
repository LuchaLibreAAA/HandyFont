import cv2
import numpy as np

def make_white_transparent_opencv(input_path, output_path, threshold=200):
    """
    Make white background transparent using OpenCV
    """
    # Read image
    img = cv2.imread(input_path)
    
    if img is None:
        print(f"Error: Could not load image from {input_path}")
        return None
    
    # Convert BGR to BGRA (add alpha channel)
    bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Create mask for white pixels
    white_mask = np.all(img > threshold, axis=2)
    
    # Set alpha channel to 0 for white pixels
    bgra[white_mask, 3] = 0
    
    # Save image
    cv2.imwrite(output_path, bgra)
    print(f"Transparent image saved as: {output_path}")
    
    return bgra

def display_image(image, window_name="Image", max_display_size=800):
    """
    Display image with automatic scaling if too large
    """
    height, width = image.shape[:2]
    
    # Scale down if image is too large for display
    if height > max_display_size or width > max_display_size:
        scale = max_display_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        display_img = cv2.resize(image, (new_width, new_height))
        print(f"Image scaled from {width}x{height} to {new_width}x{new_height} for display")
    else:
        display_img = image
    
    cv2.imshow(window_name, display_img)
    print("Press any key to close the image window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Usage
input_image = "/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/CharectersDataSet/a.jpeg"
output_image = "/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/CharectersDataSet/a_transparent.png"

result = make_white_transparent_opencv(input_image, output_image)

if result is not None:
    display_image(result, "Transparent Character")
else:
    print("Failed to process the image.")
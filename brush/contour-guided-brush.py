import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import cv2
import random
import math
import os

def generate_contour_mask(normal_map, bands=10, hsv_channel=0, smoothing=5):
    """
    Generate a binary mask of contours from a normal map using HSV color space.
    
    Args:
        normal_map: Path to normal map or numpy array
        bands: Number of contour bands to generate
        hsv_channel: Which HSV channel to use (0=Hue, 1=Saturation, 2=Value)
        smoothing: Size of Gaussian blur kernel for smoothing
    
    Returns:
        contour_mask: Binary image with contours
    """
    # Load normal map if it's a path
    if isinstance(normal_map, str):
        normal_img = cv2.imread(normal_map)
        normal_img = cv2.cvtColor(normal_img, cv2.COLOR_BGR2RGB)
    else:
        normal_img = normal_map
        
    # Ensure the normal map is in the right format for conversion
    if normal_img.dtype != np.uint8:
        normal_img = (normal_img * 255).astype(np.uint8)
    
    # Get dimensions
    height, width = normal_img.shape[:2]
    contour_map = np.zeros((height, width), dtype=np.uint8)
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(normal_img, cv2.COLOR_RGB2HSV)
    
    # Choose HSV component
    component = hsv[:, :, hsv_channel].copy().astype(np.float32)
    
    # Apply smoothing
    if smoothing > 0:
        component = cv2.GaussianBlur(component, (smoothing, smoothing), 0)
    
    # Create band thresholds
    min_val = np.min(component)
    max_val = np.max(component)
    step = (max_val - min_val) / bands
    
    # Generate contours at each threshold level
    for i in range(1, bands):
        threshold = min_val + i * step
        binary = (component > threshold).astype(np.uint8) * 255
        
        # Find edges of each band
        edges = cv2.Canny(binary, 50, 150)
        contour_map = cv2.bitwise_or(contour_map, edges)
    
    # Optional: Clean up the contours and make them thicker for better detection
    kernel = np.ones((3, 3), np.uint8)
    contour_map = cv2.dilate(contour_map, kernel, iterations=1)
    
    return contour_map

def apply_contour_guided_brush_strokes(texture_path, normal_path, contour_bands=10, 
                                      num_strokes=1000, stroke_width=5, stroke_length=20, 
                                      rotation_degrees=45, hsv_channel=0,
                                      texture_output=None, normal_output=None):
    """
    Apply brush strokes guided by contours from normal map - strokes don't cross contour edges.
    
    Parameters:
    - texture_path: Path to the texture image
    - normal_path: Path to the normal map image
    - contour_bands: Number of contour bands to use for edge detection
    - num_strokes: Number of brush strokes to apply
    - stroke_width: Width of each stroke
    - stroke_length: Length of each stroke
    - rotation_degrees: Rotation angle in degrees
    - hsv_channel: HSV channel to use for contour detection
    - texture_output: Path to save the modified texture
    - normal_output: Path to save the modified normal map
    """
    # Determine output paths if not specified
    if texture_output is None:
        base, ext = os.path.splitext(texture_path)
        texture_output = f"{base}_contour_painted{ext}"
    
    if normal_output is None:
        base, ext = os.path.splitext(normal_path)
        normal_output = f"{base}_contour_painted{ext}"
    
    # Load the images - we'll modify these directly
    texture_img = Image.open(texture_path).convert("RGBA")
    normal_img = Image.open(normal_path).convert("RGBA")
    
    # Ensure both images have the same dimensions
    if texture_img.size != normal_img.size:
        raise ValueError("Texture and normal map must have the same dimensions")
    
    width, height = texture_img.size
    
    # Generate contour mask from normal map
    normal_np = np.array(normal_img)
    contour_mask = generate_contour_mask(normal_np, bands=contour_bands, hsv_channel=hsv_channel)
    
    # Create PIL-compatible mask
    contour_mask_pil = Image.fromarray(contour_mask)
    
    # Create drawing objects
    texture_draw = ImageDraw.Draw(texture_img)
    normal_draw = ImageDraw.Draw(normal_img)
    
    # Convert rotation to radians
    rotation_rad = math.radians(rotation_degrees)
    
    # Debug counters
    total_strokes = 0
    broken_strokes = 0
    
    # Apply strokes
    for _ in range(num_strokes):
        # Random starting point
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Calculate end point based on length and rotation
        end_x = x + stroke_length * math.cos(rotation_rad)
        end_y = y + stroke_length * math.sin(rotation_rad)
        
        # Clip end points to image boundaries
        end_x = min(max(0, end_x), width - 1)
        end_y = min(max(0, end_y), height - 1)
        
        # Get colors from both images at the starting point
        try:
            texture_color = texture_img.getpixel((x, y))
            normal_color = normal_img.getpixel((x, y))
            
            # Check if the stroke crosses any contour by sampling along the path
            num_samples = max(int(stroke_length), 2)
            crosses_contour = False
            
            # Previous valid point
            last_valid_x, last_valid_y = x, y
            
            # Sample points along the line
            for t in np.linspace(0, 1, num_samples):
                sample_x = int(x + t * (end_x - x))
                sample_y = int(y + t * (end_y - y))
                
                # Ensure sample point is within bounds
                if 0 <= sample_x < width and 0 <= sample_y < height:
                    # Check if this point is on a contour
                    if contour_mask[sample_y, sample_x] > 0:
                        crosses_contour = True
                        end_x = last_valid_x
                        end_y = last_valid_y
                        broken_strokes += 1
                        break
                    
                    last_valid_x, last_valid_y = sample_x, sample_y
            
            # Draw the stroke up to the contour or the full length if no crossing
            texture_draw.line([(x, y), (end_x, end_y)], fill=texture_color, width=stroke_width)
            normal_draw.line([(x, y), (end_x, end_y)], fill=normal_color, width=stroke_width)
            total_strokes += 1
            
        except (IndexError, ValueError):
            continue
    
    print(f"Applied {total_strokes} strokes, {broken_strokes} were cut at contour boundaries")
    
    # Save the results
    texture_img.save(texture_output)
    normal_img.save(normal_output)
    
    # Save the contour mask for reference
    cv2.imwrite("contour_mask.png", contour_mask)
    
    return texture_img, normal_img, contour_mask

def display_results(original_texture, original_normal, painted_texture, painted_normal, contour_mask):
    """Display original and painted images along with the contour mask"""
    # Load images if paths are provided
    if isinstance(original_texture, str):
        orig_texture = np.array(Image.open(original_texture))
    else:
        orig_texture = np.array(original_texture)
        
    if isinstance(original_normal, str):
        orig_normal = np.array(Image.open(original_normal))
    else:
        orig_normal = np.array(original_normal)
        
    if isinstance(painted_texture, str):
        paint_texture = np.array(Image.open(painted_texture))
    else:
        paint_texture = np.array(painted_texture)
        
    if isinstance(painted_normal, str):
        paint_normal = np.array(Image.open(painted_normal))
    else:
        paint_normal = np.array(painted_normal)
    
    # Create figure
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Display images
    axes[0, 0].imshow(orig_texture)
    axes[0, 0].set_title("Original Texture")
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(paint_texture)
    axes[0, 1].set_title("Painted Texture")
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(contour_mask, cmap='gray')
    axes[0, 2].set_title("Contour Mask")
    axes[0, 2].axis('off')
    
    axes[1, 0].imshow(orig_normal)
    axes[1, 0].set_title("Original Normal Map")
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(paint_normal)
    axes[1, 1].set_title("Painted Normal Map")
    axes[1, 1].axis('off')
    
    # Create an overlay of normal map with contours
    normal_with_contours = orig_normal.copy()
    for i in range(3):  # Apply to each RGB channel
        channel = normal_with_contours[:, :, i]
        channel[contour_mask > 0] = 255 if i == 0 else 0  # Highlight contours in red
    
    axes[1, 2].imshow(normal_with_contours)
    axes[1, 2].set_title("Normal Map with Contours")
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.show()

# Main execution
if __name__ == "__main__":
    # Replace with your image paths
    texture_path = "Boat_BaseColor.PNG"
    normal_path = "Boat_Normal.PNG"
    
    # Define output paths
    texture_output = "texture_contour_painted.png"
    normal_output = "normal_map_contour_painted.png"
    
    # Make a copy of the original images for comparison (optional)
    texture_orig = Image.open(texture_path)
    normal_orig = Image.open(normal_path)
    texture_orig.save("texture_original_copy.png")
    normal_orig.save("normal_original_copy.png")
    
    # Apply contour-guided brush strokes
    texture_result, normal_result, contour_mask = apply_contour_guided_brush_strokes(
        texture_path=texture_path,
        normal_path=normal_path,
        contour_bands=10,        # Number of contour bands
        num_strokes=15000,       # Number of strokes
        stroke_width=30,         # Width of each stroke
        stroke_length=30,        # Length of each stroke
        rotation_degrees=30,     # Rotation angle
        hsv_channel=0,           # Use Hue channel for contours
        texture_output=texture_output,
        normal_output=normal_output
    )
    
    # Display results
    display_results(
        "texture_original_copy.png", 
        "normal_original_copy.png", 
        texture_output, 
        normal_output,
        contour_mask
    )
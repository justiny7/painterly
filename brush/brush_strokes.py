import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import random
import math
import os

def apply_brush_strokes_inplace(texture_path, normal_path, num_strokes=1000, 
                               stroke_width=5, stroke_length=20, rotation_degrees=45,
                               texture_output=None, normal_output=None):
    """
    Apply identical brush strokes directly to a texture map and a normal map.
    
    Parameters:
    - texture_path: Path to the texture image
    - normal_path: Path to the normal map image
    - num_strokes: Number of brush strokes to apply
    - stroke_width: Width of each stroke
    - stroke_length: Length of each stroke
    - rotation_degrees: Rotation angle in degrees
    - texture_output: Path to save the modified texture (if None, will use '_painted' suffix)
    - normal_output: Path to save the modified normal map (if None, will use '_painted' suffix)
    """
    # Determine output paths if not specified
    if texture_output is None:
        base, ext = os.path.splitext(texture_path)
        texture_output = f"{base}_painted{ext}"
    
    if normal_output is None:
        base, ext = os.path.splitext(normal_path)
        normal_output = f"{base}_painted{ext}"
    
    # Load the images - we'll modify these directly
    texture_img = Image.open(texture_path).convert("RGBA")
    normal_img = Image.open(normal_path).convert("RGBA")
    
    # Ensure both images have the same dimensions
    if texture_img.size != normal_img.size:
        raise ValueError("Texture and normal map must have the same dimensions")
    
    width, height = texture_img.size
    
    # Create drawing objects to draw directly on the images
    texture_draw = ImageDraw.Draw(texture_img)
    normal_draw = ImageDraw.Draw(normal_img)
    
    # Convert rotation to radians
    rotation_rad = math.radians(rotation_degrees)
    
    # Generate stroke parameters once and apply to both images
    for _ in range(num_strokes):
        # Random starting point
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Calculate end point based on length and rotation
        end_x = x + stroke_length * math.cos(rotation_rad)
        end_y = y + stroke_length * math.sin(rotation_rad)
        
        # Get colors from both images at the starting point
        try:
            texture_color = texture_img.getpixel((x, y))
            normal_color = normal_img.getpixel((x, y))
            
            # Draw on both images
            texture_draw.line([(x, y), (end_x, end_y)], fill=texture_color, width=stroke_width)
            normal_draw.line([(x, y), (end_x, end_y)], fill=normal_color, width=stroke_width)
        except IndexError:
            continue
    
    # Save the results
    texture_img.save(texture_output)
    normal_img.save(normal_output)
    
    return texture_img, normal_img

def display_images(original_texture, original_normal, painted_texture, painted_normal):
    """Display original and painted images side by side"""
    # Load original images
    orig_texture = Image.open(original_texture)
    orig_normal = Image.open(original_normal)
    
    # Load painted images
    paint_texture = Image.open(painted_texture)
    paint_normal = Image.open(painted_normal)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].imshow(np.array(orig_texture))
    axes[0, 0].set_title("Original Texture")
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(np.array(paint_texture))
    axes[0, 1].set_title("Painted Texture")
    axes[0, 1].axis('off')
    
    axes[1, 0].imshow(np.array(orig_normal))
    axes[1, 0].set_title("Original Normal Map")
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(np.array(paint_normal))
    axes[1, 1].set_title("Painted Normal Map")
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Replace with your image paths
    texture_path = "Boat_BaseColor.PNG"
    normal_path = "Boat_Normal.PNG"
    
    # Define output paths
    texture_output = "texture_painted.png"
    normal_output = "normal_map_painted.png"
    
    # Make a copy of the original images for comparison (optional)
    texture_orig = Image.open(texture_path)
    normal_orig = Image.open(normal_path)
    texture_orig.save("texture_original_copy.png")
    normal_orig.save("normal_original_copy.png")
    
    # Apply brush strokes directly to both images
    apply_brush_strokes_inplace(
        texture_path=texture_path,
        normal_path=normal_path,
        num_strokes=15000,       # Number of strokes
        stroke_width=30,         # Width of each stroke
        stroke_length=30,       # Length of each stroke
        rotation_degrees=30,    # Rotation angle
        texture_output=texture_output,
        normal_output=normal_output
    )
    
    # Display comparison
    display_images(
        "texture_original_copy.png", 
        "normal_original_copy.png", 
        texture_output, 
        normal_output
    )
import cv2
import numpy as np
import random
import tqdm

def apply_brush_strokes(texture_path, normal_path, stroke_size=30, edge_noise=5, angle_variation=20, sparsity=0.0001):
    def random_angle():
        return random.uniform(-angle_variation, angle_variation)

    def add_noise(size):
        return size + random.uniform(-edge_noise, edge_noise)

    # Read the images
    texture = cv2.imread(texture_path)
    normal = cv2.imread(normal_path)
    h, w, _ = texture.shape

    # Create a canvas to draw the brush strokes
    texture_canvas = np.zeros_like(texture)
    normal_canvas = np.zeros_like(normal)

    # Convert image to HSV to mask out black parts
    hsv_image = cv2.cvtColor(texture, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, (0, 0, 10), (179, 255, 10))

    # Invert mask to cover colored parts
    mask = cv2.bitwise_not(mask)

    # Random sampling points in the image based on sparsity
    non_zero_indices = np.argwhere(mask == 255)
    print(f"Total non-zero points: {len(non_zero_indices)}")
    selected_points = random.sample(list(non_zero_indices), max(1, int(sparsity * len(non_zero_indices))))
    print(f"Selected {len(selected_points)} points")

    # Create a combined mask to track all brush strokes
    all_texture_strokes_mask = np.zeros((h, w), dtype=np.uint8)
    all_normal_strokes_mask = np.zeros((h, w), dtype=np.uint8)

    for point in tqdm.tqdm(selected_points):
        y, x = point
        # print(f"Processing point: ({x}, {y})")
        angle = random_angle()

        # Define brush stroke rectangle
        length = add_noise(stroke_size)
        width = add_noise(stroke_size // 2)
        
        # Create an empty mask
        brush_stroke = np.zeros((h, w), dtype=np.uint8)
        
        # Draw brush stroke on the mask
        cv2.rectangle(
            brush_stroke,
            (int(x - width // 2), int(y - length // 2)),
            (int(x + width // 2), int(y + length // 2)),
            255,
            -1
        )
        
        # Rotate brush stroke
        M = cv2.getRotationMatrix2D((float(x), float(y)), angle, 1.0)
        brush_stroke = cv2.warpAffine(brush_stroke, M, (w, h))

        # Extract color from original image
        texture_color = texture[y, x]
        normal_color = normal[y, x]
        
        # Apply brush stroke with extracted color
        # Handle each color channel separately
        for c in range(3):  # BGR channels
            texture_canvas[:, :, c] = np.where(brush_stroke == 255, texture_color[c], texture_canvas[:, :, c])
            normal_canvas[:, :, c] = np.where(brush_stroke == 255, normal_color[c], normal_canvas[:, :, c])
        
        # Add to the combined mask
        all_texture_strokes_mask = np.maximum(all_texture_strokes_mask, brush_stroke)
        all_normal_strokes_mask = np.maximum(all_normal_strokes_mask, brush_stroke)
    
    # Create final image by combining original image and brush strokes
    # Only replace pixels where brush strokes were applied
    texture_result = texture.copy()
    normal_result = normal.copy()
    texture_brush_mask = all_texture_strokes_mask == 255
    normal_brush_mask = all_normal_strokes_mask == 255
    texture_result[texture_brush_mask] = texture_canvas[texture_brush_mask]
    normal_result[normal_brush_mask] = normal_canvas[normal_brush_mask]
    
    return texture_result, normal_result

# Usage:
output_texture, output_normal = apply_brush_strokes("M_Truck_BaseColor.png", "M_Truck_Normal_OGL.png", stroke_size=300, edge_noise=1, angle_variation=20, sparsity=0.0001)
cv2.imwrite("output_texture.png", output_texture)
cv2.imwrite("output_normal.png", output_normal)
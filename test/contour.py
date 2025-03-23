import cv2
import numpy as np
import matplotlib.pyplot as plt

def generate_normal_band_contours_hsv(normal_map, bands=15, hsv_channel=0, smoothing=5):
    """
    Generate evenly spaced contours based on a specific component of the normal map
    using HSV color space.
    
    Args:
        normal_map: RGB normal map
        bands: Number of contour bands to generate
        hsv_channel: Which HSV channel to use (0=Hue, 1=Saturation, 2=Value)
        smoothing: Size of Gaussian blur kernel for smoothing
    
    Returns:
        contour_map: Binary image with band contours
    """
    # Ensure the normal map is in the right format for conversion
    if normal_map.dtype != np.uint8 and normal_map.max() <= 1.0:
        normal_map_uint8 = (normal_map * 255).astype(np.uint8)
    else:
        normal_map_uint8 = normal_map.copy()
    
    # Get dimensions
    height, width = normal_map.shape[:2]
    contour_map = np.zeros((height, width), dtype=np.uint8)
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(normal_map_uint8, cv2.COLOR_RGB2HSV)
    
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
    
    # Optional: Clean up the contours
    # Use a horizontal kernel to preserve horizontal lines
    kernel = np.ones((1, 3), np.uint8)
    contour_map = cv2.morphologyEx(contour_map, cv2.MORPH_CLOSE, kernel)
    
    return contour_map

def visualize_hsv_components(normal_map):
    """
    Visualize each HSV component of the normal map to help choose which one to use for banding.
    """
    # Ensure the normal map is in the right format for conversion
    if normal_map.dtype != np.uint8 and normal_map.max() <= 1.0:
        normal_map_uint8 = (normal_map * 255).astype(np.uint8)
    else:
        normal_map_uint8 = normal_map.copy()
    
    # Convert to HSV
    hsv = cv2.cvtColor(normal_map_uint8, cv2.COLOR_RGB2HSV)
    
    fig, axs = plt.subplots(1, 4, figsize=(20, 5))
    component_names = ['Original', 'Hue', 'Saturation', 'Value']
    
    axs[0].imshow(normal_map)
    axs[0].set_title('Original Normal Map')
    axs[0].axis('off')
    
    for i in range(3):
        axs[i+1].imshow(hsv[:, :, i], cmap='viridis')
        axs[i+1].set_title(f'{component_names[i+1]} Component')
        axs[i+1].axis('off')
    
    plt.tight_layout()
    plt.show()

def generate_hsv_contours_with_preview(normal_map, bands_list=[10, 15, 20], hsv_channel=0):
    """
    Generate and display contours with different band settings using HSV space.
    """
    fig, axs = plt.subplots(1, len(bands_list) + 1, figsize=(5 * (len(bands_list) + 1), 5))
    
    # Display original normal map
    axs[0].imshow(normal_map)
    axs[0].set_title('Original Normal Map')
    axs[0].axis('off')
    
    # Display contours with different band settings
    for i, bands in enumerate(bands_list):
        contour_map = generate_normal_band_contours_hsv(normal_map, bands=bands, hsv_channel=hsv_channel)
        axs[i + 1].imshow(contour_map, cmap='gray')
        axs[i + 1].set_title(f'{bands} Bands')
        axs[i + 1].axis('off')
    
    plt.tight_layout()
    plt.show()

def apply_contours_to_normal_map(normal_map, contour_map, contour_color=[1, 1, 1]):
    """
    Overlay contours on the original normal map.
    
    Args:
        normal_map: Original RGB normal map
        contour_map: Binary image with contours
        contour_color: RGB color for contours
    
    Returns:
        result: Normal map with contours overlaid
    """
    # Normalize the normal map if needed
    if normal_map.max() > 1.0:
        normal_map = normal_map.astype(float) / 255.0
    
    # Create RGB contour image
    contour_color = np.array(contour_color)
    contour_rgb = np.zeros((*contour_map.shape, 3), dtype=np.float32)
    for i in range(3):
        contour_rgb[:, :, i] = contour_map / 255.0 * contour_color[i]
    
    # Blend normal map with contours
    alpha = 0.7  # Opacity of the normal map
    beta = 1.0   # Opacity of the contours
    
    result = cv2.addWeighted(normal_map, alpha, contour_rgb, beta, 0)
    return result

# Example usage
if __name__ == "__main__":
    # Load normal map
    normal_map = cv2.imread('Boat_Normal.png')
    normal_map = cv2.cvtColor(normal_map, cv2.COLOR_BGR2RGB)
    
    # Visualize HSV components to choose the best one for banding
    visualize_hsv_components(normal_map)
    
    # For your normal map, hue (channel 0) will likely work best
    hsv_channel = 0  # 0=Hue, 1=Saturation, 2=Value
    
    # Generate contours with different band settings
    generate_hsv_contours_with_preview(normal_map, bands_list=[10, 20, 30], hsv_channel=hsv_channel)
    
    # Generate final contour map with chosen settings
    contour_map = generate_normal_band_contours_hsv(
        normal_map, 
        bands=20,         # Adjust this parameter to control number of contours
        hsv_channel=hsv_channel,
        smoothing=5       # Control smoothness
    )
    
    # Display results
    plt.figure(figsize=(15, 5))
    
    plt.subplot(131)
    plt.imshow(normal_map)
    plt.title('Original Normal Map')
    plt.axis('off')
    
    plt.subplot(132)
    plt.imshow(contour_map, cmap='gray')
    plt.title('Contour Map')
    plt.axis('off')
    
    plt.subplot(133)
    result = apply_contours_to_normal_map(normal_map, contour_map, contour_color=[1, 1, 1])
    plt.imshow(result)
    plt.title('Contours Overlaid')
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
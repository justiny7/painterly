import bpy
import bmesh
import numpy as np
import os
import random
import math
from mathutils import Vector
from time import time

def create_complete_coverage_painterly_maps(stroke_width_range=(8, 15), stroke_length_range=(20, 40)):
    start_time = time()
    print("Starting painterly texture generation with complete coverage...")
    
    # Make sure we're in object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get selected mesh objects
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    
    if not selected_objects:
        print("No mesh objects selected. Please select mesh objects.")
        return None
    
    print(f"Processing {len(selected_objects)} selected mesh objects")
    
    # Set resolution
    resolution = 1024
    
    # Create new images for normal map and color/texture map
    normal_map = bpy.data.images.new("NormalMap_Painterly", width=resolution, height=resolution)
    normal_map.colorspace_settings.name = 'Non-Color'
    
    color_map = bpy.data.images.new("ColorMap_Painterly", width=resolution, height=resolution)
    
    # Initialize numpy arrays for images
    normal_array = np.zeros((resolution, resolution, 4), dtype=np.float32)
    normal_array[:, :, 0] = 0.5  # R - X
    normal_array[:, :, 1] = 0.5  # G - Y
    normal_array[:, :, 2] = 1.0  # B - Z
    normal_array[:, :, 3] = 1.0  # A - Alpha
    
    color_array = np.ones((resolution, resolution, 4), dtype=np.float32)
    
    # Create a mask to track which pixels belong to which object
    object_ownership = np.full((resolution, resolution), -1, dtype=np.int32)
    
    # First pass: Create object masks
    for obj_index, obj in enumerate(selected_objects):
        print(f"Creating mask for object {obj_index+1}/{len(selected_objects)}: {obj.name}")
        
        # Check if the object has UVs, if not unwrap it
        if not obj.data.uv_layers:
            print(f"  No UV map found for {obj.name}, creating one...")
            # Select only this object
            for o in bpy.context.selected_objects:
                o.select_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            
            # Unwrap
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
            bpy.ops.object.mode_set(mode='OBJECT')
            print(f"  UV unwrapping completed for {obj.name}")
        
        # Create BMesh for this object
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        
        # Make sure we have UV data
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            print(f"  Error: No active UV layer found for {obj.name} even after unwrapping")
            bm.free()
            continue
        
        # Fill object mask with UV coordinates
        for face in bm.faces:
            if len(face.loops) < 3:
                continue
                
            # Get UVs for this face
            uvs = [loop[uv_layer].uv for loop in face.loops]
            pixel_uvs = [(int(uv.x * (resolution-1)), int(uv.y * (resolution-1))) for uv in uvs]
            
            # Triangulate the face
            for i in range(1, len(face.loops) - 1):
                tri_uvs = [pixel_uvs[0], pixel_uvs[i], pixel_uvs[i+1]]
                
                # Calculate bounding box for the triangle
                min_x = max(0, min(x for x, y in tri_uvs))
                max_x = min(resolution-1, max(x for x, y in tri_uvs))
                min_y = max(0, min(y for x, y in tri_uvs))
                max_y = min(resolution-1, max(y for x, y in tri_uvs))
                
                # Fill the triangle in the mask
                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        if is_point_in_triangle((x, y), tri_uvs):
                            object_ownership[y, x] = obj_index
        
        bm.free()
    
    # Second pass: Generate complete coverage strokes for each object
    for obj_index, obj in enumerate(selected_objects):
        print(f"Adding brush strokes for object {obj_index+1}/{len(selected_objects)}: {obj.name}")
        
        # Create BMesh again for normal calculations
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        
        # Calculate normals
        bm.normal_update()
        
        # Get UV layer
        uv_layer = bm.loops.layers.uv.active
        
        # Get object color
        obj_color = get_object_color(obj)
        
        # Create a mapping of pixels to face normals
        pixel_to_normal = {}
        
        for face in bm.faces:
            if len(face.loops) < 3:
                continue
                
            # Get face normal
            face_normal = face.normal
            
            # Get UVs for this face
            uvs = [loop[uv_layer].uv for loop in face.loops]
            pixel_uvs = [(int(uv.x * (resolution-1)), int(uv.y * (resolution-1))) for uv in uvs]
            
            # Triangulate the face
            for i in range(1, len(face.loops) - 1):
                tri_uvs = [pixel_uvs[0], pixel_uvs[i], pixel_uvs[i+1]]
                
                # Calculate bounding box for the triangle
                min_x = max(0, min(x for x, y in tri_uvs))
                max_x = min(resolution-1, max(x for x, y in tri_uvs))
                min_y = max(0, min(y for x, y in tri_uvs))
                max_y = min(resolution-1, max(y for x, y in tri_uvs))
                
                # Fill the triangle with normals
                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        if is_point_in_triangle((x, y), tri_uvs):
                            pixel_to_normal[(x, y)] = face_normal
        
        # Find all pixels owned by this object
        obj_pixels = np.argwhere(object_ownership == obj_index)
        
        if len(obj_pixels) == 0:
            print(f"  No pixels found for object {obj.name}")
            bm.free()
            continue
        
        print(f"  Found {len(obj_pixels)} pixels for object {obj.name}")
        
        # Calculate grid spacing based on stroke size
        avg_stroke_width = (stroke_width_range[0] + stroke_width_range[1]) / 2
        avg_stroke_length = (stroke_length_range[0] + stroke_length_range[1]) / 2
        
        # Calculate grid size - determine how many cells to divide the texture into
        # We want strokes to overlap slightly to ensure complete coverage
        grid_size = int(min(avg_stroke_length, avg_stroke_width) * 0.7)
        grid_size = max(5, grid_size)  # Ensure reasonable grid size
        
        print(f"  Using grid size {grid_size} for stroke placement")
        
        # Create a grid of stroke centers
        coverage_grid = np.zeros((resolution // grid_size + 1, resolution // grid_size + 1), dtype=bool)
        
        # Create a set of all object pixels for quick lookup
        obj_pixels_set = set((x, y) for y, x in obj_pixels)
        
        # Place strokes in a grid pattern to ensure complete coverage
        for grid_y in range(0, resolution, grid_size):
            for grid_x in range(0, resolution, grid_size):
                # Check if any pixel in this grid cell belongs to the object
                cell_has_obj_pixel = False
                
                for y in range(grid_y, min(grid_y + grid_size, resolution)):
                    for x in range(grid_x, min(grid_x + grid_size, resolution)):
                        if (x, y) in obj_pixels_set:
                            cell_has_obj_pixel = True
                            break
                    if cell_has_obj_pixel:
                        break
                
                if not cell_has_obj_pixel:
                    continue
                
                # Find a suitable pixel in this grid cell
                best_pixel = None
                
                # First try center of grid cell
                center_x = grid_x + grid_size // 2
                center_y = grid_y + grid_size // 2
                
                if (center_x, center_y) in obj_pixels_set:
                    best_pixel = (center_x, center_y)
                else:
                    # Try to find any pixel in this cell that belongs to the object
                    for y in range(grid_y, min(grid_y + grid_size, resolution)):
                        for x in range(grid_x, min(grid_x + grid_size, resolution)):
                            if (x, y) in obj_pixels_set:
                                best_pixel = (x, y)
                                break
                        if best_pixel:
                            break
                
                if not best_pixel:
                    continue
                
                # Get the pixel normal
                x, y = best_pixel
                if (x, y) not in pixel_to_normal:
                    continue
                
                normal = pixel_to_normal[(x, y)]
                
                # Calculate stroke direction (tangent to normal)
                up = Vector((0, 0, 1))
                tangent = normal.cross(up)
                if tangent.length < 0.001:
                    tangent = Vector((1, 0, 0))
                else:
                    tangent.normalize()
                
                # Add randomness to direction
                angle = math.atan2(tangent.y, tangent.x) + random.uniform(-math.pi/4, math.pi/4)
                dir_x = math.cos(angle)
                dir_y = math.sin(angle)
                
                # Stroke parameters - random width and length
                stroke_width = random.randint(stroke_width_range[0], stroke_width_range[1])
                stroke_length = random.randint(stroke_length_range[0], stroke_length_range[1])
                
                # Calculate stroke endpoints
                half_length = stroke_length / 2
                x0 = int(x - dir_x * half_length)
                y0 = int(y - dir_y * half_length)
                x1 = int(x + dir_x * half_length)
                y1 = int(y + dir_y * half_length)
                
                # Colors
                normal_color = np.array([
                    normal.x * 0.5 + 0.5,
                    normal.y * 0.5 + 0.5,
                    normal.z * 0.5 + 0.5,
                    1.0
                ])
                
                # Varied object color with less variation for more consistency
                color_variation = np.random.uniform(-0.05, 0.05, 3)
                varied_color = np.array([
                    max(0.0, min(1.0, obj_color[0] + color_variation[0])),
                    max(0.0, min(1.0, obj_color[1] + color_variation[1])),
                    max(0.0, min(1.0, obj_color[2] + color_variation[2])),
                    1.0
                ])
                
                # Draw the brush strokes
                draw_brush_stroke(normal_array, x0, y0, x1, y1, normal_color, stroke_width, 
                                 resolution, object_ownership, obj_index)
                draw_brush_stroke(color_array, x0, y0, x1, y1, varied_color, stroke_width,
                                 resolution, object_ownership, obj_index)
                
                # Mark this grid cell as covered
                grid_cell_x = grid_x // grid_size
                grid_cell_y = grid_y // grid_size
                if grid_cell_x < len(coverage_grid) and grid_cell_y < len(coverage_grid[0]):
                    coverage_grid[grid_cell_x, grid_cell_y] = True
        
        bm.free()
        
        # Check coverage and add additional strokes if needed
        covered_cells = np.sum(coverage_grid)
        total_cells = np.sum(np.zeros_like(coverage_grid))
        print(f"  Initial coverage: {covered_cells}/{total_cells} grid cells")
        
        # Add some random strokes for variety
        num_random_strokes = len(obj_pixels) // 1000  # Adjust as needed
        print(f"  Adding {num_random_strokes} random strokes for variety")
        
        for _ in range(num_random_strokes):
            # Pick a random pixel owned by this object
            if len(obj_pixels) == 0:
                continue
                
            idx = random.randint(0, len(obj_pixels) - 1)
            y, x = obj_pixels[idx]
            
            if (x, y) not in pixel_to_normal:
                continue
                
            normal = pixel_to_normal[(x, y)]
            
            # Random direction
            angle = random.uniform(0, 2 * math.pi)
            dir_x = math.cos(angle)
            dir_y = math.sin(angle)
            
            # Random stroke parameters
            stroke_width = random.randint(stroke_width_range[0], stroke_width_range[1])
            stroke_length = random.randint(stroke_length_range[0], stroke_length_range[1])
            
            # Calculate stroke endpoints
            half_length = stroke_length / 2
            x0 = int(x - dir_x * half_length)
            y0 = int(y - dir_y * half_length)
            x1 = int(x + dir_x * half_length)
            y1 = int(y + dir_y * half_length)
            
            # Colors
            normal_color = np.array([
                normal.x * 0.5 + 0.5,
                normal.y * 0.5 + 0.5,
                normal.z * 0.5 + 0.5,
                1.0
            ])
            
            # More vibrant color variation for the random strokes
            color_variation = np.random.uniform(-0.1, 0.1, 3)
            varied_color = np.array([
                max(0.0, min(1.0, obj_color[0] + color_variation[0])),
                max(0.0, min(1.0, obj_color[1] + color_variation[1])),
                max(0.0, min(1.0, obj_color[2] + color_variation[2])),
                1.0 ])
            
            # Draw random brush strokes with lower opacity for variety
            draw_brush_stroke(normal_array, x0, y0, x1, y1, normal_color, stroke_width, 
                             resolution, object_ownership, obj_index, opacity=0.6)
            draw_brush_stroke(color_array, x0, y0, x1, y1, varied_color, stroke_width,
                             resolution, object_ownership, obj_index, opacity=0.6)
    
    # Convert numpy arrays to Blender pixels
    normal_pixels = normal_array.flatten()
    color_pixels = color_array.flatten()
    
    normal_map.pixels = normal_pixels.tolist()
    color_map.pixels = color_pixels.tolist()
    
    # Save to desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    normal_path = os.path.join(desktop_path, "normal_map_painterly.png")
    color_path = os.path.join(desktop_path, "color_map_painterly.png")
    
    normal_map.filepath_raw = normal_path
    normal_map.file_format = 'PNG'
    normal_map.save()
    
    color_map.filepath_raw = color_path
    color_map.file_format = 'PNG'
    color_map.save()
    
    end_time = time()
    print(f"Painterly maps generated in {end_time - start_time:.2f} seconds")
    print(f"Painterly normal map saved to: {normal_path}")
    print(f"Painterly color map saved to: {color_path}")
    
    # Re-select all objects
    for obj in selected_objects:
        obj.select_set(True)
    
    return normal_map, color_map

def draw_brush_stroke(image_array, x0, y0, x1, y1, color, thickness, resolution, mask, obj_index, opacity=0.8):
    """Draw a thick brush stroke with tapered ends for a more painterly look"""
    # Make sure points are in bounds
    x0 = max(0, min(resolution-1, x0))
    y0 = max(0, min(resolution-1, y0))
    x1 = max(0, min(resolution-1, x1))
    y1 = max(0, min(resolution-1, y1))
    
    # Calculate line parameters
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    # Get total line length for tapering
    line_length = math.sqrt(dx*dx + dy*dy)
    if line_length == 0:
        line_length = 1
    
    # For each point on the line
    x, y = x0, y0
    step_count = 0
    
    while True:
        # Calculate position along the line (0 to 1)
        t = step_count / line_length
        
        # Taper the stroke width - thicker in middle, thinner at ends
        local_thickness = int(thickness * (1.0 - 0.5 * (2*t - 1)**2))
        local_thickness = max(1, local_thickness)
        
        # Define bounds of the brush square
        half_t = local_thickness // 2
        min_x = max(0, x - half_t)
        max_x = min(resolution - 1, x + half_t)
        min_y = max(0, y - half_t)
        max_y = min(resolution - 1, y + half_t)
        
        # Create a slice for the brush region
        region = image_array[min_y:max_y+1, min_x:max_x+1]
        mask_region = mask[min_y:max_y+1, min_x:max_x+1]
        
        # Create masks for object ownership
        ownership_mask = (mask_region == obj_index)
        
        # Apply color blending only where the object owns the pixels
        if np.any(ownership_mask):
            for c in range(3):  # For R, G, B channels
                region[ownership_mask, c] = region[ownership_mask, c] * (1 - opacity) + color[c] * opacity
            
            # Set alpha to 1.0
            region[ownership_mask, 3] = 1.0
        
        # Exit condition
        if x == x1 and y == y1:
            break
        
        # Move to next point on the line
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
            
        step_count += 1

def is_point_in_triangle(point, triangle):
    """Check if point is inside triangle using barycentric coordinates"""
    px, py = point
    (ax, ay), (bx, by), (cx, cy) = triangle
    
    # Compute vectors
    v0x, v0y = cx - ax, cy - ay
    v1x, v1y = bx - ax, by - ay
    v2x, v2y = px - ax, py - ay
    
    # Compute dot products
    d00 = v0x * v0x + v0y * v0y
    d01 = v0x * v1x + v0y * v1y
    d11 = v1x * v1x + v1y * v1y
    d20 = v2x * v0x + v2y * v0y
    d21 = v2x * v1x + v2y * v1y
    
    # Compute barycentric coordinates
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 0.00001:
        return False  # Degenerate triangle
    
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    
    # Point is inside if all barycentric coordinates are >= 0 and sum to 1
    return (u >= 0) and (v >= 0) and (w >= 0)

def get_object_color(obj):
    """Extract the base color of an object from its materials"""
    if obj.material_slots and obj.material_slots[0].material:
        mat = obj.material_slots[0].material
        if mat.use_nodes:
            # Try to find a Principled BSDF node
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    # Get base color from Principled BSDF
                    rgb = node.inputs['Base Color'].default_value
                    return (rgb[0], rgb[1], rgb[2])
    
    # Fallback to a random color if no material is found
    return (
        random.uniform(0.3, 0.9),
        random.uniform(0.3, 0.9),
        random.uniform(0.3, 0.9)
    )

# Run the script with thick brush strokes
create_complete_coverage_painterly_maps(
    stroke_width_range=(8, 15),   # Thick strokes
    stroke_length_range=(20, 40)  # Long strokes
)
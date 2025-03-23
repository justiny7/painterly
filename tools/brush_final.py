import bpy
import bmesh
import numpy as np
import os
import random
import math
from mathutils import Vector
from time import time
from collections import defaultdict, deque

def create_painterly_maps_with_shared_texture(stroke_width_range=(8, 15), stroke_length_range=(20, 40), 
                                            normal_angle_threshold=10.0):
    start_time = time()
    print("Starting painterly texture generation with shared texture cache...")
    
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
    
    # Store normal data, face IDs, region IDs and UV coordinates for each pixel
    normal_data = np.zeros((resolution, resolution, 3), dtype=np.float32)
    face_id_data = np.full((resolution, resolution), -1, dtype=np.int32)
    region_id_data = np.full((resolution, resolution), -1, dtype=np.int32)
    uv_data = np.zeros((resolution, resolution, 2), dtype=np.float32)
    
    # Find a texture to cache (just need one for all objects)
    print("Searching for a texture to cache...")
    shared_texture_data = None
    default_color = (0.5, 0.5, 0.5)  # Default gray
    
    # Try to find any texture from the selected objects
    for obj in selected_objects:
        texture_image = get_texture_from_material(obj)
        if texture_image and texture_image.pixels:
            print(f"Found texture: {texture_image.name}")
            
            # Get texture dimensions
            width = texture_image.size[0]
            height = texture_image.size[1]
            
            try:
                # Convert the flat pixels list to a numpy array and reshape
                pixels = np.array(texture_image.pixels[:])
                texture_array = pixels.reshape((height, width, 4))
                
                shared_texture_data = (texture_array, width, height)
                print(f"Cached texture: {width}x{height}")
                break
            except Exception as e:
                print(f"Error caching texture: {e}")
    
    if shared_texture_data:
        print("Using shared texture for all objects")
    else:
        print("No usable texture found, using default colors")
    
    # Process each object to build face regions and fill the texture data
    total_face_id_offset = 0
    total_region_id_offset = 0
    
    for obj_index, obj in enumerate(selected_objects):
        print(f"\nProcessing object {obj_index+1}/{len(selected_objects)}: {obj.name}")
        
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
        
        # Calculate normals
        bm.normal_update()
        
        # Step 1: Filter valid faces (with non-zero normals)
        valid_faces = []
        for face in bm.faces:
            if face.normal.length > 0.001:  # Skip faces with zero-length normals
                valid_faces.append(face)
        
        print(f"  Found {len(valid_faces)} valid faces out of {len(bm.faces)} total faces")
        
        # Step 2: Create face regions using union-find to ensure strict edge constraints
        region_map = {}  # Maps face_id to region_id
        next_region_id = 0
        
        # Create a mapping of edge to its faces for quicker lookup
        edge_to_faces = {}
        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                face1, face2 = edge.link_faces
                if face1 in valid_faces and face2 in valid_faces:
                    edge_to_faces[edge] = (face1, face2)
        
        # First, assign each face to its own region
        for face in valid_faces:
            face_id = face.index + total_face_id_offset
            region_map[face_id] = next_region_id + total_region_id_offset
            next_region_id += 1
        
        # Convert angle threshold to radians
        angle_threshold_radians = math.radians(normal_angle_threshold)
        
        # List of edges with similar normals
        similar_edges = []
        
        # Find edges where faces have similar normals
        for edge, (face1, face2) in edge_to_faces.items():
            face1_id = face1.index + total_face_id_offset
            face2_id = face2.index + total_face_id_offset
            
            # Compare face normals
            normal1 = face1.normal
            normal2 = face2.normal
            
            # Calculate angle between normals
            cos_angle = normal1.dot(normal2)
            # Handle numerical precision issues
            cos_angle = max(-1.0, min(1.0, cos_angle))
            angle = math.acos(cos_angle)
            
            # If angle is less than threshold, these faces should be in the same region
            if angle <= angle_threshold_radians:
                similar_edges.append((face1_id, face2_id))
        
        # Union-find data structure for merging regions
        parent = {}
        rank = {}
        
        def find(x):
            if x != parent[x]:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                if rank[root_x] < rank[root_y]:
                    parent[root_x] = root_y
                else:
                    parent[root_y] = root_x
                    if rank[root_x] == rank[root_y]:
                        rank[root_x] += 1
        
        # Initialize union-find
        for face_id, region_id in region_map.items():
            parent[region_id] = region_id
            rank[region_id] = 0
        
        # Merge regions for faces with similar normals
        for face1_id, face2_id in similar_edges:
            region1 = region_map[face1_id]
            region2 = region_map[face2_id]
            union(region1, region2)
        
        # Update region_map with final region assignments
        for face_id in region_map:
            region_map[face_id] = find(region_map[face_id])
        
        # Compact region IDs (make them sequential)
        region_id_remapping = {}
        next_compact_id = total_region_id_offset
        
        for face_id, region_id in region_map.items():
            if region_id not in region_id_remapping:
                region_id_remapping[region_id] = next_compact_id
                next_compact_id += 1
            
            # Update the region map with compact IDs
            region_map[face_id] = region_id_remapping[region_id]
        
        final_region_count = len(region_id_remapping)
        print(f"  Created {final_region_count} distinct face regions after merging")
        
        # Step 3: Fill the texture data
        print("  Filling texture data...")
        
        for face in valid_faces:
            face_id = face.index + total_face_id_offset
            region_id = region_map.get(face_id, -1)
            
            # Get face normal
            face_normal = face.normal
            
            # Get UVs for this face
            uvs = [loop[uv_layer].uv for loop in face.loops]
            pixel_uvs = [(uv.x * (resolution-1), uv.y * (resolution-1)) for uv in uvs]
            
            # Triangulate the face
            for i in range(1, len(face.loops) - 1):
                tri_uvs = [pixel_uvs[0], pixel_uvs[i], pixel_uvs[i+1]]
                tri_real_uvs = [uvs[0], uvs[i], uvs[i+1]]  # Store original UVs (0-1 range)
                
                # Calculate expanded bounding box with 1px margin for the triangle
                min_x = max(0, int(min(x for x, y in tri_uvs) - 1))
                max_x = min(resolution-1, int(max(x for x, y in tri_uvs) + 1))
                min_y = max(0, int(min(y for x, y in tri_uvs) - 1))
                max_y = min(resolution-1, int(max(y for x, y in tri_uvs) + 1))
                
                # Test each pixel in the bounding box
                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        # Check if any corner of the pixel is inside the triangle
                        pixel_corners = [
                            (x - 0.5, y - 0.5),  # Bottom-left
                            (x + 0.5, y - 0.5),  # Bottom-right
                            (x - 0.5, y + 0.5),  # Top-left
                            (x + 0.5, y + 0.5)   # Top-right
                        ]
                        
                        inside = False
                        for corner in pixel_corners:
                            if is_point_in_triangle_float(corner, tri_uvs):
                                inside = True
                                break
                                
                        # If no corner is inside, check if the center is inside
                        if not inside and is_point_in_triangle_float((x, y), tri_uvs):
                            inside = True
                            
                        # Also check edge intersections
                        if not inside:
                            pixel_edges = [
                                (pixel_corners[0], pixel_corners[1]),  # Bottom
                                (pixel_corners[1], pixel_corners[3]),  # Right
                                (pixel_corners[3], pixel_corners[2]),  # Top
                                (pixel_corners[2], pixel_corners[0])   # Left
                            ]
                            
                            tri_edges = [
                                (tri_uvs[0], tri_uvs[1]),
                                (tri_uvs[1], tri_uvs[2]),
                                (tri_uvs[2], tri_uvs[0])
                            ]
                            
                            for p_edge in pixel_edges:
                                for t_edge in tri_edges:
                                    if lines_intersect(p_edge[0], p_edge[1], t_edge[0], t_edge[1]):
                                        inside = True
                                        break
                                if inside:
                                    break
                        
                        if inside:
                            # This pixel is at least partially covered by the triangle
                            # Calculate barycentric coordinates to interpolate the UV values
                            center = (x, y)
                            uvw = get_barycentric_coords(center, tri_uvs)
                            
                            if uvw is not None:
                                # Interpolate UV coordinates
                                u = tri_real_uvs[0].x * uvw[0] + tri_real_uvs[1].x * uvw[1] + tri_real_uvs[2].x * uvw[2]
                                v = tri_real_uvs[0].y * uvw[0] + tri_real_uvs[1].y * uvw[1] + tri_real_uvs[2].y * uvw[2]
                                
                                # Store data for this pixel
                                object_ownership[y, x] = obj_index
                                normal_data[y, x] = [face_normal.x, face_normal.y, face_normal.z]
                                face_id_data[y, x] = face_id
                                region_id_data[y, x] = region_id
                                uv_data[y, x] = [u, v]  # Store UV coordinates for later texture sampling
        
        # Update offsets for next object
        total_face_id_offset += len(bm.faces)
        total_region_id_offset = next_compact_id
        
        bm.free()
    
    # Now generate brush strokes constrained to face regions
    print("\nGenerating brush strokes constrained to face regions...")
    
    for obj_index, obj in enumerate(selected_objects):
        print(f"Adding brush strokes for object {obj_index+1}/{len(selected_objects)}: {obj.name}")
        
        # Get base color as fallback
        base_color = get_object_base_color(obj)
        
        # Find all pixels owned by this object
        obj_pixels = np.argwhere(object_ownership == obj_index)
        
        if len(obj_pixels) == 0:
            print(f"  No pixels found for object {obj.name}")
            continue
        
        print(f"  Found {len(obj_pixels)} pixels for object {obj.name}")
        
        # Get all regions for this object
        object_regions = set()
        for y, x in obj_pixels:
            region_id = region_id_data[y, x]
            if region_id >= 0:
                object_regions.add(region_id)
        
        print(f"  Object has {len(object_regions)} regions")
        
        # Process each region separately to ensure strokes stay within regions
        for region_id in object_regions:
            # Get pixels for this region
            region_pixels = [(y, x) for y, x in obj_pixels if region_id_data[y, x] == region_id]
            
            if len(region_pixels) < 10:  # Skip very small regions
                continue
                
            print(f"  Processing region {region_id} with {len(region_pixels)} pixels")
            
            # Create a set for faster lookup
            region_pixels_set = set(region_pixels)
            
            # Calculate grid size based on stroke dimensions
            avg_stroke_width = (stroke_width_range[0] + stroke_width_range[1]) / 2
            avg_stroke_length = (stroke_length_range[0] + stroke_length_range[1]) / 2
            
            grid_size = int(min(avg_stroke_length, avg_stroke_width) * 0.6)
            grid_size = max(5, grid_size)  # Ensure reasonable grid size
            
            # Create a dictionary to track which grid cells are covered
            coverage_grid = {}
            
            # Create boundaries for the region
            min_x = min(x for _, x in region_pixels)
            max_x = max(x for _, x in region_pixels)
            min_y = min(y for y, _ in region_pixels)
            max_y = max(y for y, _ in region_pixels)
            
            # Place strokes in a grid pattern over the region
            for grid_y in range(min_y, max_y + 1, grid_size):
                for grid_x in range(min_x, max_x + 1, grid_size):
                    grid_key = (grid_x // grid_size, grid_y // grid_size)
                    
                    # Skip if this grid cell is already covered
                    if grid_key in coverage_grid:
                        continue
                    
                    # Find a pixel in this grid cell that belongs to the region
                    best_pixel = None
                    
                    # Try center of grid cell first
                    center_x = grid_x + grid_size // 2
                    center_y = grid_y + grid_size // 2
                    
                    if (center_y, center_x) in region_pixels_set:
                        best_pixel = (center_y, center_x)
                    else:
                        # Search for any pixel in this cell that belongs to the region
                        for y in range(grid_y, min(grid_y + grid_size, resolution)):
                            for x in range(grid_x, min(grid_x + grid_size, resolution)):
                                if (y, x) in region_pixels_set:
                                    best_pixel = (y, x)
                                    break
                            if best_pixel:
                                break
                    
                    if not best_pixel:
                        continue
                    
                    y, x = best_pixel
                    
                    # Get the normal for this pixel
                    normal_vec = normal_data[y, x]
                    normal = Vector((normal_vec[0], normal_vec[1], normal_vec[2]))
                    
                    if normal.length < 0.001:
                        continue
                        
                    normal.normalize()
                    
                    # Get UV coordinates for this pixel
                    u, v = uv_data[y, x]
                    
                    # Sample texture color from cached data if available
                    if shared_texture_data:
                        texture_color = sample_cached_texture(shared_texture_data, u, v)
                    else:
                        texture_color = base_color
                    
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
                    
                    # Varied texture color with less variation for more consistency
                    color_variation = np.random.uniform(-0.05, 0.05, 3)
                    varied_color = np.array([
                        max(0.0, min(1.0, texture_color[0] + color_variation[0])),
                        max(0.0, min(1.0, texture_color[1] + color_variation[1])),
                        max(0.0, min(1.0, texture_color[2] + color_variation[2])),
                        1.0
                    ])
                    
                    # Draw the brush strokes constrained to this region
                    draw_brush_stroke_in_region(
                        normal_array, x0, y0, x1, y1, normal_color, stroke_width, 
                        resolution, region_id_data, region_id
                    )
                    draw_brush_stroke_in_region(
                        color_array, x0, y0, x1, y1, varied_color, stroke_width,
                        resolution, region_id_data, region_id
                    )
                    
                    # Mark this grid cell as covered
                    coverage_grid[grid_key] = True
            
            # Add some random strokes for variety within each region
            num_random_strokes = len(region_pixels) // 800  # Fewer random strokes
            
            if num_random_strokes > 0:
                print(f"  Adding {num_random_strokes} random strokes to region {region_id}")
                
                for _ in range(num_random_strokes):
                    # Pick a random pixel in this region
                    if not region_pixels:
                        continue
                        
                    idx = random.randint(0, len(region_pixels) - 1)
                    y, x = region_pixels[idx]
                    
                    normal_vec = normal_data[y, x]
                    if np.sum(normal_vec**2) < 0.001:
                        continue
                        
                    normal = Vector(normal_vec)
                    normal.normalize()
                    
                    # Get UV coordinates for this pixel
                    u, v = uv_data[y, x]
                    
                    # Sample texture color from cached data if available
                    if shared_texture_data:
                        texture_color = sample_cached_texture(shared_texture_data, u, v)
                    else:
                        texture_color = base_color
                    
                    # Random direction with some influence from the normal
                    if random.random() < 0.7:  # 70% chance to align with normal
                        up = Vector((0, 0, 1))
                        tangent = normal.cross(up)
                        if tangent.length < 0.001:
                            tangent = Vector((1, 0, 0))
                        else:
                            tangent.normalize()
                        angle = math.atan2(tangent.y, tangent.x) + random.uniform(-math.pi/3, math.pi/3)
                    else:
                        # Completely random direction
                        angle = random.uniform(0, 2 * math.pi)
                        
                    dir_x = math.cos(angle)
                    dir_y = math.sin(angle)
                    
                    # Random stroke parameters - shorter for random strokes
                    stroke_width = random.randint(stroke_width_range[0], stroke_width_range[1])
                    stroke_length = random.randint(stroke_length_range[0] // 2, stroke_length_range[1] // 2)
                    
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
                    
                    # More varied color for random strokes
                    color_variation = np.random.uniform(-0.1, 0.1, 3)
                    varied_color = np.array([
                        max(0.0, min(1.0, texture_color[0] + color_variation[0])),
                        max(0.0, min(1.0, texture_color[1] + color_variation[1])),
                        max(0.0, min(1.0, texture_color[2] + color_variation[2])),
                        1.0
                    ])
                    
                    # Draw random brush strokes constrained to this region
                    draw_brush_stroke_in_region(
                        normal_array, x0, y0, x1, y1, normal_color, stroke_width, 
                        resolution, region_id_data, region_id, opacity=0.7
                    )
                    draw_brush_stroke_in_region(
                        color_array, x0, y0, x1, y1, varied_color, stroke_width,
                        resolution, region_id_data, region_id, opacity=0.7
                    )
    
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

def sample_cached_texture(cached_data, u, v):
    """Sample from the cached texture array using UV coordinates"""
    texture_array, width, height = cached_data
    
    # Calculate pixel position (clamped to texture boundaries)
    x = max(0, min(width - 1, int(u * width)))
    y = max(0, min(height - 1, int(v * height)))
    
    # Get pixel color (RGB)
    try:
        pixel = texture_array[y, x, :3]  # Just take RGB
        return (pixel[0], pixel[1], pixel[2])
    except:
        return (0.5, 0.5, 0.5)  # Default gray if access fails

def get_texture_from_material(obj):
    """Extract the color texture from the material if available"""
    if not obj.material_slots or not obj.material_slots[0].material:
        return None
    
    mat = obj.material_slots[0].material
    
    # Check if the material uses nodes
    if not mat.use_nodes:
        return None
    
    node_tree = mat.node_tree
    
    # Find active output node
    output_node = None
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
            output_node = node
            break
    
    if not output_node:
        # Try to find any output node
        for node in node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
                break
    
    if not output_node:
        return None
    
    # Find the shader connected to the output
    if not output_node.inputs['Surface'].links:
        return None
    
    shader_node = output_node.inputs['Surface'].links[0].from_node
    
    # Check if it's a mix shader and follow to find Principled BSDF
    if shader_node.type == 'MIX_SHADER':
        if shader_node.inputs[1].links:
            top_node = shader_node.inputs[1].links[0].from_node
            if top_node.type == 'BSDF_PRINCIPLED':
                shader_node = top_node
        elif shader_node.inputs[2].links:
            bottom_node = shader_node.inputs[2].links[0].from_node
            if bottom_node.type == 'BSDF_PRINCIPLED':
                shader_node = bottom_node
    
    # If we don't have a Principled BSDF, search for one
    if shader_node.type != 'BSDF_PRINCIPLED':
        principled_nodes = [node for node in node_tree.nodes if node.type == 'BSDF_PRINCIPLED']
        if principled_nodes:
            shader_node = principled_nodes[0]
        else:
            return None
    
    # Now check if Base Color is connected to a texture
    if not shader_node.inputs['Base Color'].links:
        return None
    
    color_source = shader_node.inputs['Base Color'].links[0].from_node
    
    # Check if it's a texture node
    if color_source.type == 'TEX_IMAGE' and color_source.image:
        return color_source.image
    
    # If color source is not directly a texture, search for a texture in its inputs
    if hasattr(color_source, 'inputs'):
        for input_socket in color_source.inputs:
            if input_socket.links:
                connected_node = input_socket.links[0].from_node
                if connected_node.type == 'TEX_IMAGE' and connected_node.image:
                    return connected_node.image
    
    return None

def get_object_base_color(obj):
    """Get a fallback base color if texture sampling fails"""
    if not obj.material_slots or not obj.material_slots[0].material:
        return (0.5, 0.5, 0.5)
    
    mat = obj.material_slots[0].material
    
    # Check if the material uses nodes
    if not mat.use_nodes:
        # If not using nodes, use the diffuse color
        return (mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2])
    
    # Try to find a Principled BSDF
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            color = node.inputs['Base Color'].default_value
            return (color[0], color[1], color[2])
    
    # Fallback to a medium gray
    return (0.5, 0.5, 0.5)

def draw_brush_stroke_in_region(image_array, x0, y0, x1, y1, color, thickness, resolution, 
                               region_id_data, region_id, opacity=0.8):
    """Draw a brush stroke constrained to a specific region"""
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
        # Skip points outside the region
        if 0 <= y < resolution and 0 <= x < resolution and region_id_data[y, x] == region_id:
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
            mask_region = region_id_data[min_y:max_y+1, min_x:max_x+1]
            
            # Create mask for region
            region_mask = (mask_region == region_id)
            
            # Apply color blending only where the mask is True
            if np.any(region_mask):
                for c in range(3):  # For R, G, B channels
                    region[region_mask, c] = region[region_mask, c] * (1 - opacity) + color[c] * opacity
                
                # Set alpha to 1.0
                region[region_mask, 3] = 1.0
        
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

def get_barycentric_coords(point, triangle):
    """Calculate barycentric coordinates of a point in a triangle"""
    try:
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
            return None  # Degenerate triangle
        
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w
        
        return (u, v, w)
    except:
        return None

def is_point_in_triangle_float(point, triangle):
    """Check if point is inside triangle using barycentric coordinates with float precision"""
    uvw = get_barycentric_coords(point, triangle)
    if uvw is None:
        return False
    
    u, v, w = uvw
    # Point is inside if all barycentric coordinates are >= 0 and sum to 1
    return (u >= 0) and (v >= 0) and (w >= 0)

def lines_intersect(p1, p2, p3, p4):
    """Check if line segments (p1,p2) and (p3,p4) intersect"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    # Calculate the direction vectors
    dx1 = x2 - x1
    dy1 = y2 - y1
    dx2 = x4 - x3
    dy2 = y4 - y3
    
    # Calculate the determinant
    d = dx1 * dy2 - dy1 * dx2
    
    # Lines are parallel if determinant is zero
    if abs(d) < 0.00001:
        return False
    
    # Calculate parameters for the intersection point
    s = ((x1 - x3) * dy2 - (y1 - y3) * dx2) / d
    t = ((x3 - x1) * dy1 - (y3 - y1) * dx1) / -d
    
    # Check if the intersection is within both line segments
    return (0 <= s <= 1) and (0 <= t <= 1)

# Run the script with shared texture caching
create_painterly_maps_with_shared_texture(
    stroke_width_range=(8, 15),    # Thick strokes
    stroke_length_range=(20, 40),  # Long strokes
    normal_angle_threshold=10.0    # Default 10 degrees for considering faces as part of the same region
)
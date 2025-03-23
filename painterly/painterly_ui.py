import bpy
import numpy as np
import os
import random
import math
from mathutils import Vector
from time import time
from . import brush_normal

# Property Group for brush parameters 
class PainterlyProperties(bpy.types.PropertyGroup):
    brush_width_min: bpy.props.IntProperty(
        name="Min Brush Width",
        default=30,
        min=1,
        max=100,
        description="Minimum width of the brush strokes"
    )
    
    brush_width_max: bpy.props.IntProperty(
        name="Max Brush Width",
        default=50,
        min=1,
        max=100,
        description="Maximum width of the brush strokes"
    )

    brush_length_min: bpy.props.IntProperty(
        name="Min Brush Length",
        default=40,
        min=1,
        max=200,
        description="Minimum length of the brush strokes"
    )
    
    brush_length_max: bpy.props.IntProperty(
        name="Max Brush Length",
        default=80,
        min=1,
        max=200,
        description="Maximum length of the brush strokes"
    )
    
    angle_variation: bpy.props.FloatProperty(
        name="Angle Variation",
        default=45.0,
        min=0.0,
        max=180.0,
        description="Random variation in brush stroke angles (degrees)"
    )
    
    edge_noise: bpy.props.FloatProperty(
        name="Edge Noise",
        default=2.0,
        min=0.0,
        max=10.0,
        description="Random variation in brush stroke edges"
    )
    
    sparsity: bpy.props.FloatProperty(
        name="Sparsity",
        default=0.001,
        min=0.0001,
        max=0.01,
        precision=4,
        description="Controls the density of random strokes (lower = denser)"
    )

    resolution: bpy.props.IntProperty(
        name="Resolution",
        default=1024,
        min=256,
        max=4096,
        description="Resolution of the generated maps"
    )

# Panel for UI
class PT_PainterlyPanel(bpy.types.Panel):
    bl_label = "Painterly"
    bl_idname = "PT_Painterly"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Painterly'

    def draw(self, context):
        layout = self.layout
        props = context.scene.painterly_props

        # Resolution setting
        layout.prop(props, "resolution")
        
        # Brush parameters section
        box = layout.box()
        box.label(text="Brush Settings", icon='BRUSH_DATA')
        
        # Brush dimensions
        brush_width_row = box.row()
        brush_width_row.prop(props, "brush_width_min", text="Width Min")
        brush_width_row.prop(props, "brush_width_max", text="Max")
        
        brush_length_row = box.row()
        brush_length_row.prop(props, "brush_length_min", text="Length Min")
        brush_length_row.prop(props, "brush_length_max", text="Max")
        
        # Variation parameters
        box.prop(props, "angle_variation")
        box.prop(props, "edge_noise")
        box.prop(props, "sparsity")
        
        # Info about selection
        if not context.selected_objects:
            layout.label(text="Select objects to apply effect", icon='INFO')
        else:
            num_mesh = len([obj for obj in context.selected_objects if obj.type == 'MESH'])
            layout.label(text=f"Selected: {num_mesh} mesh objects", icon='MESH_DATA')

        # Operators
        row = layout.row()
        row.scale_y = 1.5
        row.operator("painterly.apply", icon='TEXTURE')
        layout.operator("painterly.reset", icon='X')

# Operator to apply stylization
class OT_ApplyPainterly(bpy.types.Operator):
    bl_idname = "painterly.apply"
    bl_label = "Apply Painterly Effect"

    def execute(self, context):
        props = context.scene.painterly_props
        
        # Validate selection
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'ERROR'}, "Please select at least one mesh object")
            return {'CANCELLED'}
        
        try:
            # Create painterly maps with current parameters
            brush_normal.create_complete_coverage_painterly_maps(
                stroke_width_range=(props.brush_width_min, props.brush_width_max),
                stroke_length_range=(props.brush_length_min, props.brush_length_max)
            )
            
            self.report({'INFO'}, "Painterly effect applied successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error applying painterly effect: {str(e)}")
            return {'CANCELLED'}

# Operator to reset to original maps
class OT_ResetPainterly(bpy.types.Operator):
    bl_idname = "painterly.reset"
    bl_label = "Reset Maps"

    def execute(self, context):
        try:
            # Remove generated images
            if "NormalMap_Painterly" in bpy.data.images:
                bpy.data.images.remove(bpy.data.images["NormalMap_Painterly"])
            if "ColorMap_Painterly" in bpy.data.images:
                bpy.data.images.remove(bpy.data.images["ColorMap_Painterly"])
                
            self.report({'INFO'}, "Reset successful")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error during reset: {str(e)}")
            return {'CANCELLED'}
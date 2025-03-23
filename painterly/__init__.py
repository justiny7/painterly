bl_info = {
    "name": "Painterly Texture Generator",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Painterly",
    "description": "Generate painterly style textures and normal maps",
    "warning": "",
    "doc_url": "",
    "category": "Material",
}

import bpy
import bmesh
import numpy as np
import os
import random
import math
from mathutils import Vector

# Property Group for brush parameters and live preview toggle
class PainterlyProperties(bpy.types.PropertyGroup):
    prev_brush_width_min: bpy.props.IntProperty(default=8)
    prev_brush_width_max: bpy.props.IntProperty(default=15)
    prev_brush_length_min: bpy.props.IntProperty(default=20)
    prev_brush_length_max: bpy.props.IntProperty(default=40)
    prev_angle_variation: bpy.props.FloatProperty(default=45.0)
    prev_edge_noise: bpy.props.FloatProperty(default=2.0)
    prev_sparsity: bpy.props.FloatProperty(default=0.001)
    prev_resolution: bpy.props.IntProperty(default=1024)

    brush_width_min: bpy.props.IntProperty(
        name="Min Brush Width",
        default=8,
        min=1,
        max=50,
        description="Minimum width of the brush strokes"
    )
    
    brush_width_max: bpy.props.IntProperty(
        name="Max Brush Width",
        default=15,
        min=1,
        max=50,
        description="Maximum width of the brush strokes"
    )

    brush_length_min: bpy.props.IntProperty(
        name="Min Brush Length",
        default=20,
        min=1,
        max=100,
        description="Minimum length of the brush strokes"
    )
    
    brush_length_max: bpy.props.IntProperty(
        name="Max Brush Length",
        default=40,
        min=1,
        max=100,
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

class PT_PainterlyPanel(bpy.types.Panel):
    bl_label = "Painterly"
    bl_idname = "PT_Painterly"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Painterly'

    def draw(self, context):
        layout = self.layout
        props = context.scene.painterly
        
        # Add property fields
        layout.prop(props, "brush_width_min")
        layout.prop(props, "brush_width_max")
        layout.prop(props, "brush_length_min")
        layout.prop(props, "brush_length_max")
        layout.prop(props, "angle_variation")
        layout.prop(props, "edge_noise")
        layout.prop(props, "sparsity")
        layout.prop(props, "resolution")
        
        # Add operators
        layout.operator("painterly.apply")
        layout.operator("painterly.reset")

class OT_ApplyPainterly(bpy.types.Operator):
    bl_idname = "painterly.apply"
    bl_label = "Apply Painterly Effect"
    
    def execute(self, context):
        props = context.scene.painterly
        
        # Store current values before applying
        props.prev_brush_width_min = props.brush_width_min
        props.prev_brush_width_max = props.brush_width_max
        props.prev_brush_length_min = props.brush_length_min
        props.prev_brush_length_max = props.brush_length_max
        props.prev_angle_variation = props.angle_variation
        props.prev_edge_noise = props.edge_noise
        props.prev_sparsity = props.sparsity
        props.prev_resolution = props.resolution
        
        from . import brush_normal
        # Reload the module to ensure we have the latest version
        import importlib
        importlib.reload(brush_normal)
        
        try:
            brush_normal.create_complete_coverage_painterly_maps(
                (props.brush_width_min, props.brush_width_max),
                (props.brush_length_min, props.brush_length_max)
            )
            self.report({'INFO'}, "Painterly effect applied successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error applying painterly effect: {str(e)}")
            return {'CANCELLED'}

class OT_ResetPainterly(bpy.types.Operator):
    bl_idname = "painterly.reset"
    bl_label = "Reset Maps"
    
    def execute(self, context):
        props = context.scene.painterly
        
        # Restore previous values
        props.brush_width_min = props.prev_brush_width_min
        props.brush_width_max = props.prev_brush_width_max
        props.brush_length_min = props.prev_brush_length_min
        props.brush_length_max = props.prev_brush_length_max
        props.angle_variation = props.prev_angle_variation
        props.edge_noise = props.prev_edge_noise
        props.sparsity = props.prev_sparsity
        props.resolution = props.prev_resolution
        
        # Remove generated images
        if "NormalMap_Painterly" in bpy.data.images:
            bpy.data.images.remove(bpy.data.images["NormalMap_Painterly"])
        if "ColorMap_Painterly" in bpy.data.images:
            bpy.data.images.remove(bpy.data.images["ColorMap_Painterly"])
            
        self.report({'INFO'}, "Restored to previous state")
        return {'FINISHED'}

classes = (
    PainterlyProperties,
    PT_PainterlyPanel,
    OT_ApplyPainterly,
    OT_ResetPainterly,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.painterly = bpy.props.PointerProperty(type=PainterlyProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.painterly

if __name__ == "__main__":
    register()

import bpy
from . import brush_normal_with_texture

# Property Group for brush parameters and live preview toggle
class PainterlyProperties(bpy.types.PropertyGroup):
    brush_width: bpy.props.FloatProperty(
        name="Brush Width",
        default=10.0,
        min=0.0,
        update=lambda self, context: trigger_live_preview(self, context)
    )

    brush_length: bpy.props.FloatProperty(
        name="Brush Length",
        default=20.0,
        min=0.0,
        update=lambda self, context: trigger_live_preview(self, context)
    )

    brush_rotation: bpy.props.FloatProperty(
        name="Brush Rotation",
        default=0.0,
        min=0.0,
        max=360.0,
        update=lambda self, context: trigger_live_preview(self, context)
    )

    angle_variation: bpy.props.FloatProperty(
        name="Angle Variation",
        default=0.0,
        min=0.0,
        max=360.0,
        update=lambda self, context: trigger_live_preview(self, context)
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

        layout.prop(props, "brush_width")
        layout.prop(props, "brush_length")
        layout.prop(props, "brush_rotation")
        layout.prop(props, "angle_variation")
        
        layout.separator()
        
        layout.operator("painterly.apply")
        layout.operator("painterly.reset")


# Operator to apply stylization
class OT_ApplyPainterly(bpy.types.Operator):
    bl_idname = "painterly.apply"
    bl_label = "Apply Painterly"

    def execute(self, context):
        # Placeholder for stylization logic
#        self.report({'INFO'}, "Painterly applied.")
#        return {'FINISHED'}
    
        props = context.scene.painterly_props
        
        # Skip processing if width or length is zero
        if props.brush_width <= 0 or props.brush_length <= 0:
            self.report({'INFO'}, "Brush width or length is zero - no strokes applied.")
            return {'FINISHED'}
        
        width_value = int(props.brush_width)
        length_value = int(props.brush_length)
        
        # Call the generate function with UI parameters
#        brush_normal.create_complete_coverage_painterly_maps(
        brush_normal_with_texture.create_complete_coverage_painterly_maps(
            stroke_width_range=(width_value, width_value),
            stroke_length_range=(length_value, length_value)
        )
        
        self.report({'INFO'}, "Painterly applied with width: {:.1f}, length: {:.1f}".format(
            props.brush_width, props.brush_length))
        return {'FINISHED'}
    

# Operator to reset to original maps
class OT_ResetPainterly(bpy.types.Operator):
    bl_idname = "painterly.reset"
    bl_label = "Reset to Original"

    def execute(self, context):
        # Placeholder for reset logic
        self.report({'INFO'}, "Textures reset to original.")
        return {'FINISHED'}


# Register
classes = [
    PainterlyProperties,
    PT_PainterlyPanel,
    OT_ApplyPainterly,
    OT_ResetPainterly
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.painterly_props = bpy.props.PointerProperty(type=PainterlyProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.painterly_props
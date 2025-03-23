bl_info = {
    "name": "Painterly Add-on",
    "author": "Stanford Team",
    "version": (1, 0),
    "blender": (2, 80, 0),  # Works in Blender 2.8 and up
    "location": "View3D > Sidebar > Painterly",
    "description": "An add-on with painterly stylization parameters",
    "category": "3D View",
}

import bpy

# Property Group for brush parameters and live preview toggle
class PainterlyProperties(bpy.types.PropertyGroup):
    brush_width: bpy.props.FloatProperty(
        name="Brush Width",
        default=0.0,
        min=0.0,
        update=lambda self, context: trigger_live_preview(self, context)
    )

    brush_length: bpy.props.FloatProperty(
        name="Brush Length",
        default=0.0,
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

    live_preview: bpy.props.BoolProperty(
        name="Live Preview",
        default=False
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
        layout.prop(props, "live_preview")

        layout.operator("painterly.apply")
        layout.operator("painterly.reset")


# Operator to apply stylization
class OT_ApplyPainterly(bpy.types.Operator):
    bl_idname = "painterly.apply"
    bl_label = "Apply Painterly"

    def execute(self, context):
        # Placeholder for stylization logic
        self.report({'INFO'}, "Painterly applied.")
        return {'FINISHED'}

# Operator to reset to original maps
class OT_ResetPainterly(bpy.types.Operator):
    bl_idname = "painterly.reset"
    bl_label = "Reset to Original"

    def execute(self, context):
        # Placeholder for reset logic
        self.report({'INFO'}, "Textures reset to original.")
        return {'FINISHED'}

# Triggered when any param is changed
def trigger_live_preview(self, context):
    if self.live_preview:
        print("Live preview triggered")
        # Call your stylization update function here later


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

if __name__ == "__main__":
    register()
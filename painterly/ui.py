import bpy
from bpy.types import Panel

class PAINTERLY_PT_main_panel(Panel):
    bl_label = "Painterly Effect"
    bl_idname = "PAINTERLY_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Painterly'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.painterly_props
        
        # Update min/max constraints
        props.update_min_max(context)
        
        # Stroke Width
        box = layout.box()
        box.label(text="Stroke Width:")
        row = box.row()
        split = row.split(factor=0.5)
        col1 = split.column()
        col2 = split.column()
        col1.label(text="Min:")
        col1.prop(props, "stroke_width", index=0, text="")
        col2.label(text="Max:")
        col2.prop(props, "stroke_width", index=1, text="")
        
        # Stroke Length
        box = layout.box()
        box.label(text="Stroke Length:")
        row = box.row()
        split = row.split(factor=0.5)
        col1 = split.column()
        col2 = split.column()
        col1.label(text="Min:")
        col1.prop(props, "stroke_length", index=0, text="")
        col2.label(text="Max:")
        col2.prop(props, "stroke_length", index=1, text="")
        
        # Normal Angle Threshold with reset button
        box = layout.box()
        box.label(text="Normal Angle Threshold (degrees):")
        row = box.row()
        col = row.column()
        col.prop(props, "normal_angle_threshold", text="")
        col = row.column(align=True)
        col.scale_x = 0.5
        col.operator("painterly.reset_threshold", text="Reset", icon='LOOP_BACK')
        box.label(text=f"Current value: {props.normal_angle_threshold:.1f}°")
        
        # Color Variation (single value)
        box = layout.box()
        box.label(text="Color Variation:")
        box.prop(props, "color_variation", text="Amount", slider=True)
        
        # Reset All button
        layout.separator()
        row = layout.row()
        row.operator("painterly.force_reset_all", text="Reset All Parameters", icon='FILE_REFRESH')
        
        # Apply button
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("painterly.apply_effect", icon='BRUSH_DATA')

classes = (
    PAINTERLY_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
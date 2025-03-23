import bpy
from bpy.types import Operator
from . import painterly_core

class PAINTERLY_OT_apply_effect(Operator):
    """Apply painterly effect to selected objects"""
    bl_idname = "painterly.apply_effect"
    bl_label = "Apply Painterly Effect"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.painterly_props
        
        # Get parameters from the UI
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected. Please select at least one object.")
            return {'CANCELLED'}
            
        # Validate min/max values
        props.update_min_max(context)
        
        # Get the normal angle threshold from the internal property
        normal_angle = props.normal_angle_internal
        
        # Extra validation to ensure the angle is in range
        if normal_angle > 180.0 or normal_angle < 0.0:
            normal_angle = 10.0
            props.normal_angle_internal = 10.0
            self.report({'WARNING'}, f"Correcting abnormal threshold value to 10.0 degrees")
        
        try:
            # Debug print
            print(f"DEBUG - Using normal angle threshold: {normal_angle} degrees")
            
            # Call the actual painterly effect function
            painterly_core.create_painterly_maps_with_shared_texture(
                stroke_width_range=(props.stroke_width[0], props.stroke_width[1]),
                stroke_length_range=(props.stroke_length[0], props.stroke_length[1]),
                normal_angle_threshold=float(normal_angle),
                color_variation=float(props.color_variation)
            )
            
            self.report({'INFO'}, "Painterly effect applied!")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error applying painterly effect: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

class PAINTERLY_OT_reset_threshold(Operator):
    """Reset normal angle threshold to default value"""
    bl_idname = "painterly.reset_threshold"
    bl_label = "Reset Threshold"
    
    def execute(self, context):
        context.scene.painterly_props.reset_normal_angle_threshold()
        self.report({'INFO'}, "Normal angle threshold reset to 10.0")
        return {'FINISHED'}

class PAINTERLY_OT_force_reset_all(Operator):
    """Force reset all parameters to default values"""
    bl_idname = "painterly.force_reset_all"
    bl_label = "Reset All Values"
    
    def execute(self, context):
        props = context.scene.painterly_props
        
        # Reset all values to defaults
        props.normal_angle_internal = 10.0
        props.color_variation = 0.0
        props.stroke_width[0] = 8.0
        props.stroke_width[1] = 15.0
        props.stroke_length[0] = 20.0
        props.stroke_length[1] = 40.0
        
        self.report({'INFO'}, "All parameters reset to default values")
        return {'FINISHED'}

classes = (
    PAINTERLY_OT_apply_effect,
    PAINTERLY_OT_reset_threshold,
    PAINTERLY_OT_force_reset_all,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
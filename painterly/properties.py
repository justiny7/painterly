import bpy
from bpy.props import FloatProperty, FloatVectorProperty

class PainterlyEffectProperties(bpy.types.PropertyGroup):
    stroke_width: FloatVectorProperty(
        name="Stroke Width",
        description="Min and max stroke width",
        default=(8.0, 15.0),
        min=1.0,
        max=30.0,
        size=2,
        subtype='NONE',
    )
    
    stroke_length: FloatVectorProperty(
        name="Stroke Length",
        description="Min and max stroke length",
        default=(20.0, 40.0),
        min=1.0,
        max=100.0,
        size=2,
        subtype='NONE',
    )
    
    # Internal property without underscore
    normal_angle_internal: FloatProperty(
        name="Internal Angle",
        default=10.0,
        min=0.0,
        max=180.0
    )
    
    # Exposed property with getter/setter
    normal_angle_threshold: FloatProperty(
        name="Normal Angle Threshold",
        description="Threshold angle for normal map effects (degrees)",
        default=10.0,
        min=0.0,
        max=180.0,
        precision=1,
        subtype='NONE',  # Don't use 'ANGLE' subtype
        get=lambda self: self.normal_angle_internal,
        set=lambda self, value: setattr(self, "normal_angle_internal", 
                                       min(180.0, max(0.0, float(value))))
    )
    
    color_variation: FloatProperty(
        name="Color Variation",
        description="Amount of color variation in strokes (0-1)",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )

    def update_min_max(self, context):
        """Ensure min <= max for range properties"""
        # Stroke width
        if self.stroke_width[0] > self.stroke_width[1]:
            self.stroke_width[1] = self.stroke_width[0]
            
        # Stroke length
        if self.stroke_length[0] > self.stroke_length[1]:
            self.stroke_length[1] = self.stroke_length[0]
        
        # Force normal angle to be in valid range
        if self.normal_angle_internal > 180.0 or self.normal_angle_internal < 0.0:
            self.normal_angle_internal = 10.0

    # Reset function for normal angle threshold
    def reset_normal_angle_threshold(self):
        self.normal_angle_internal = 10.0

classes = (
    PainterlyEffectProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.painterly_props = bpy.props.PointerProperty(type=PainterlyEffectProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "painterly_props"):
        del bpy.types.Scene.painterly_props
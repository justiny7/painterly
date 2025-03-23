bl_info = {
    "name": "Painterly",
    "author": "Stanford Team",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Painterly",
    "description": "An add-on with painterly stylization parameters",
    "category": "3D View",
}

from . import apply_painterly

def register():
    apply_painterly.register()

def unregister():
    apply_painterly.unregister()

if __name__ == "__main__":
    register()
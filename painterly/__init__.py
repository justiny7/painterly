bl_info = {
    "name": "Painterly Effect",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Painterly Effect",
    "description": "Applies a painterly effect to normal maps and textures",
    "category": "Material",
}

import bpy
from . import ui
from . import operators
from . import properties

modules = (
    properties,
    operators,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
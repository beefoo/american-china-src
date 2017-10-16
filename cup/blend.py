# Creates a cup in Blender: blender --background --python blend.py
# Or run this in Blender: exec(compile(open("/absolute/path/to/cup/blend.py").read(), "/absolute/path/to/cup/blend.py", 'exec'))

import bpy
import json
import os

bpy.app.debug_wm = True

data = []
with open(bpy.path.abspath("//mesh.json")) as f:
    data = json.load(f)

# blend starts here
scene = bpy.context.scene

# convert scene to metric, centimeters
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01

# deselect all
bpy.ops.object.select_all(action='DESELECT')

# select all objects except camera and lamp
for obj in bpy.data.objects:
    if obj.name not in ["Camera", "Lamp"]:
        obj.select = True

# delete selected
bpy.ops.object.delete()

for d in data:

    # Define mesh and object
    mesh = bpy.data.meshes.new(d["name"])
    obj = bpy.data.objects.new(d["name"], mesh)

    # Set location and scene of object
    obj.location = tuple(d["location"])
    bpy.context.scene.objects.link(obj)

    # convert lists to tuples
    verts = [tuple(v) for v in d["verts"]]
    edges = [tuple(v) for v in d["edges"]]
    faces = [tuple(f) for f in d["faces"]]

    # Create mesh and flip the first face
    mesh.from_pydata(verts, edges, faces)
    mesh.update(calc_edges=True)
    mesh.polygons[0].flip()

    # Select the object
    obj.select = True

    # Add subsurf modifier
    obj.modifiers.new("subd", type='SUBSURF')
    obj.modifiers['subd'].levels = 1

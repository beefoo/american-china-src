# Creates a cup in Blender: blender --background --python blend.py
# Or run this in Blender:
    # import bpy
    # filepath = bpy.path.abspath("//blend.py")
    # exec(compile(open(filepath).read(), filepath, 'exec'))

import bpy
import json
import os

# bpy.app.debug_wm = True

data = []
with open(bpy.path.abspath("//mesh.json")) as f:
    data = json.load(f)

# blend starts here
scene = bpy.context.scene

# convert scene to metric, millimeters
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001

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

    # Create mesh from data
    mesh.from_pydata(verts, edges, faces)

    # Calculate the edges
    mesh.update(calc_edges=True)

    # Flip some of the faces
    for i in d["flipFaces"]:
        mesh.polygons[i].flip()

    # Select the object
    obj.select = True

    # Add subsurf modifier
    obj.modifiers.new("subd", type='SUBSURF')
    obj.modifiers['subd'].levels = 1
    obj.modifiers["subd"].render_levels = 1

    # # Add decimate modifier to reduce polys
    # obj.modifiers.new("dec", type='DECIMATE')
    # obj.modifiers["dec"].ratio = 0.3

# select all objects except camera and lamp
for obj in bpy.data.objects:
    if obj.name not in ["Camera", "Lamp"]:
        scene.objects.active = obj

## for showing object thickness
# bpy.ops.object.editmode_toggle()
# bpy.context.object.data.show_statvis = True
# scene.tool_settings.statvis.thickness_max = 3

# Creates a cup in Blender: blender --background --python cup.py
# Or run this in Blender: exec(compile(open(filename).read(), "/absolute/path/to/cup/cup.py", 'exec'))

import bpy

# config
CFG = {
    "origin": (0, 0, 0),
    "diameter": 7.0,            # in cm
    "height": 8.0,              # in cm
    "thickness": 0.5,           # in cm
    "baseDiameter": 0.9,        # percent of total diameter
    "baseHeight": 0.1,          # percent of total height
    "curviness": 0.5,           # percent of thickness
    "innerDiameter": 0.9,       # percent of total diameter minus thickness
    "innerCurveMidpoint": 0.5   # percent of inner height
}

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

# Define vertices, faces, edges
verts = [(0,0,0),(0,5,0),(5,5,0),(5,0,0),(0,0,5),(0,5,5),(5,5,5),(5,0,5)]
faces = [(0,1,2,3), (4,5,6,7), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]

# Define mesh and object
mesh = bpy.data.meshes.new("Cup")
obj = bpy.data.objects.new("Cup", mesh)

# Set location and scene of object
obj.location = CFG["origin"]
bpy.context.scene.objects.link(obj)

# Create mesh
mesh.from_pydata(verts,[],faces)
mesh.update(calc_edges=True)

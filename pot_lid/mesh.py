# -*- coding: utf-8 -*-

import json
from lib import *
import math
from pprint import pprint
import sys

# data config
INPUT_FILE = "../pot/pot_lid_config.json"
OUTPUT_FILE = "mesh.json"
# IMG_MAP_FILE = "imgMap.png"
PRECISION = 8

# cup config in mm
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 0 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 0
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

EDGE_RADIUS = 4.0
THICKNESS = 6.0
REDUCE_AMOUNT = 2.0 # increase this to reduce the width/length

BASE_HEIGHT = 6.0
BASE_THICKNESS = 4.0
BASE_EDGE = 2.0
IMG_OFFSET_AMOUNT = 4.0
DIME_WIDTH = 18.0

lidConfig = {}
with open(INPUT_FILE) as f:
    lidConfig = json.load(f)
SHAPE = lidConfig["shape"]
CENTER = lidConfig["center"]
Z = lidConfig["z"]
TOP_HEIGHT = lidConfig["height"]
OUTER_L, OUTER_W, _Z = tuple(lidConfig["outer"])
INNER_L, INNER_W, _Z = tuple(lidConfig["inner"])

print "Top height: %s" % TOP_HEIGHT

ER2 = EDGE_RADIUS * 2
BE2 = BASE_EDGE * 2
BT2 = BASE_THICKNESS * 2
LID = [
    (INNER_L-BT2-ER2, INNER_W-BT2-ER2, BASE_HEIGHT), # base inner top edge before
    (INNER_L-BT2, INNER_W-BT2, BASE_HEIGHT), # base inner top
    (INNER_L-BT2, INNER_W-BT2, BASE_HEIGHT-BASE_EDGE),  # base inner top edge after
    (INNER_L-BT2, INNER_W-BT2, BASE_EDGE),  # base inner bottom edge before
    (INNER_L-BT2, INNER_W-BT2, 0),  # base inner bottom
    (INNER_L-BT2+BE2, INNER_W-BT2+BE2, 0),  # base inner bottom edge after
    (INNER_L-BE2, INNER_W-BE2, 0),  # base outer bottom edge before
    (INNER_L, INNER_W, 0), # base outer bottom
    (INNER_L, INNER_W, BASE_EDGE), # base outer bottom edge after
    (INNER_L, INNER_W, BASE_HEIGHT-BASE_EDGE), # base outer top edge before
    (INNER_L, INNER_W, BASE_HEIGHT), # base outer top
    (INNER_L+BE2, INNER_W+BE2, BASE_HEIGHT), # base outer top edge after
    # (OUTER_L-BE2, OUTER_W-BE2, BASE_HEIGHT), # body bottom edge before
    (OUTER_L, OUTER_W, BASE_HEIGHT), # body bottom
    (OUTER_L, OUTER_W, BASE_HEIGHT+BASE_EDGE), # body bottom edge after
    (OUTER_L, OUTER_W, BASE_HEIGHT+TOP_HEIGHT-BASE_EDGE), # body top edge before
    (OUTER_L, OUTER_W, BASE_HEIGHT+TOP_HEIGHT), # body top
    (OUTER_L-ER2, OUTER_W-ER2, BASE_HEIGHT+TOP_HEIGHT), # body top edge after
]
lidLen = len(LID)

# add loops to top surface for high resolution
# step = EDGE_RADIUS
# minimum = step * 3.0
# lx, ly, lz = LID[-1]
# lx -= step
# ly -= step
# while lx > minimum and ly > minimum:
#     LID.append((lx, ly, lz))
#     lx -= step
#     ly -= step

# reduce size
for i, p in enumerate(LID):
    LID[i] = (p[0]-REDUCE_AMOUNT, p[1]-REDUCE_AMOUNT, p[2])

# spline the loops
# targetEdgeCount = lidLen * 2**SUBDIVIDE_Y
# splinedLid = bspline(LID, n=targetEdgeCount, degree=3, periodic=False)
# pprint(LID)
# pprint(splinedLid)

print "Dimensions: %s x %s x %s" % (max([d[0] for d in LID]), max([d[1] for d in LID]), max([d[2] for d in LID]))

# build the mesh
mesh = Mesh()

loops = []
for i, p in enumerate(LID):
    x, y, z = p
    if i <= 0:
        ll = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z)
        loops += ll
    elif i >= lidLen-1:
        ll = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z, True)
        loops += ll
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z)
        loops.append(loop)

# displace loops with image map
# print "Displacing loops..."
# displaceLoops = displaceWithMap(loops, IMG_MAP_FILE, IMG_OFFSET_AMOUNT, minZ=BASE_HEIGHT+TOP_HEIGHT-1.0)

mesh.addEdgeLoops(loops)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Pot lid",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": range((VERTICES_PER_EDGE_LOOP/4)**2)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

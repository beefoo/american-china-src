# -*- coding: utf-8 -*-

import json
from lib import *
import math
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 8

# cup config in mm
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 0 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 0
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

CENTER = (0, 0, 0)
WIDTH = 84.0
LENGTH = 125.0
HEIGHT = 125.0
EDGE_RADIUS = 4.0
THICKNESS = 4.0
DISPLACEMENT = (0, 3.0, -3.0)
BASE_INSET_HEIGHT = 3.0
INSET = 0.9
BODY = 0.96

BODY_HEIGHT = 0.6 * HEIGHT
HANDLE_HEIGHT = HEIGHT - BODY_HEIGHT
BODY_BASE_HEIGHT = BODY_HEIGHT * 0.1667

print "Check: %s > %s" % (BODY_BASE_HEIGHT-EDGE_RADIUS, EDGE_RADIUS)

# define pot: x, y, z
POT = [
    (LENGTH*INSET-EDGE_RADIUS*2, WIDTH*INSET-EDGE_RADIUS*2, BASE_INSET_HEIGHT), # base inset edge
    (LENGTH*INSET, WIDTH*INSET, BASE_INSET_HEIGHT),                             # base inset
    (LENGTH*INSET, WIDTH*INSET, 0),                                             # base inner
    (LENGTH, WIDTH, 0),                                                         # base outer
    (LENGTH, WIDTH, EDGE_RADIUS),                                               # base outer edge
    (LENGTH, WIDTH, BODY_BASE_HEIGHT-EDGE_RADIUS),                              # body base edge before
    (LENGTH, WIDTH, BODY_BASE_HEIGHT),                                          # body base top
    (LENGTH*BODY, WIDTH*BODY, BODY_BASE_HEIGHT),                                # body bottom
    (LENGTH*BODY, WIDTH*BODY, BODY_BASE_HEIGHT+EDGE_RADIUS),                    # body bottom edge after
    (LENGTH*BODY, WIDTH*BODY, BODY_HEIGHT-EDGE_RADIUS),                         # body top edge before
    (LENGTH*BODY, WIDTH*BODY, BODY_HEIGHT),                                     # body top edge before
]
potLen = len(POT)

# Define the shape of the cross-section of the iron, clock-wise starting from top left
EDGE_X = EDGE_RADIUS / LENGTH
EDGE_Y = EDGE_RADIUS / WIDTH
BODY1_X = 0.333
BODY1_W = 0.667
BODY1_Y = (1.0 - BODY1_W) * 0.5
BODY2_X = 0.667
BODY2_W = 0.92
BODY2_Y = (1.0 - BODY2_W) * 0.5
NOSE_X = 0.05
NOSE_W = 0.2
NOSE_Y = (1.0 - NOSE_W) * 0.5
NOSE_POINT_W = NOSE_W * 0.1
NOSE_POINT_Y = (1.0 - NOSE_POINT_W) * 0.5
SHAPE = [
    (NOSE_X, NOSE_Y),       # top nose
    (BODY1_X, BODY1_Y),     # top body 1
    (BODY2_X, BODY2_Y),     # top body 2
    (1.0-EDGE_X, 0.0),      # top right, edge before
    (1.0, 0.0),             # top right
    (1.0, EDGE_Y),          # top right, edge after
    (1.0, 0.5),             # middle right
    (1.0, 1.0-EDGE_Y),      # bottom right, edge before
    (1.0, 1.0),             # bottom right
    (1.0-EDGE_X, 1.0),      # bottom right, edge after
    (BODY2_X, 1.0-BODY2_Y),     # bottom body 2
    (BODY1_X, 1.0-BODY1_Y),   # bottom body 1
    (NOSE_X, 1.0-NOSE_Y),   # bottom nose
    (0.0, 1.0-NOSE_POINT_Y),    # bottom nose point
    (0.0, 0.5),             # middle left (point of iron)
    (0.0, NOSE_POINT_Y),# top nose point
]

# build the mesh
mesh = Mesh()

for i,p in enumerate(POT):
    x, y, z = p

    if i <= 0:
        loops = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z)
        mesh.addEdgeLoops(loops)
    elif i >= potLen-1:
        loops = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z, True)
        mesh.addEdgeLoops(loops)
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Pot",
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

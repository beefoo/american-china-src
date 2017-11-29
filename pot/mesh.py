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

WIDTH = 110.0
LENGTH = 160.0
HEIGHT = 125.0
EDGE_RADIUS = 4.0
THICKNESS = 6.0
BASE_HEIGHT = 3.0
BASE_INSET_HEIGHT = 3.0
BODY_TOP_INSET_HEIGHT = 3.0

OUTER_TOP_CENTER = (LENGTH*0.05, 0, 0)
TOP_CENTER = (LENGTH*0.1, 0, 0)
INNER_TOP_CENTER = (LENGTH*0.05, 0, 0)

BASE_W = 0.9
BASE_L = 0.95
BASE_INSET_W = (BASE_W * 0.8) * WIDTH
BASE_INSET_L = (BASE_L * 0.8875) * LENGTH
BODY_BTM = 0.95
BODY_TOP = 0.8
BODY_TOP_INSET = 0.7

BODY_HEIGHT = 0.6 * (HEIGHT-BASE_HEIGHT)
HANDLE_HEIGHT = (HEIGHT-BASE_HEIGHT) - BODY_HEIGHT
BODY_BASE_HEIGHT = BODY_HEIGHT * 0.2

T2 = THICKNESS*2
ER2 = EDGE_RADIUS*2

print "Check: %s > %s" % (BODY_BASE_HEIGHT-EDGE_RADIUS, EDGE_RADIUS)

# define pot: x, y, z
POT_OUTER = [
    (BASE_INSET_L-ER2, BASE_INSET_W-ER2, BASE_INSET_HEIGHT),                     # base inset edge
    (BASE_INSET_L, BASE_INSET_W, BASE_INSET_HEIGHT),                             # base inset
    (BASE_INSET_L, BASE_INSET_W, 0),                                             # base inner
    (LENGTH*BASE_L, WIDTH*BASE_W, 0),                                            # base outer bottom
    (LENGTH*BASE_L, WIDTH*BASE_W, BASE_HEIGHT),                                  # base outer top
    (LENGTH, WIDTH, BASE_HEIGHT),                                                # body bottom
    (LENGTH, WIDTH, BASE_HEIGHT+EDGE_RADIUS),                                    # base outer edge
    (LENGTH, WIDTH, BODY_BASE_HEIGHT-EDGE_RADIUS),                               # body base edge before
    (LENGTH, WIDTH, BODY_BASE_HEIGHT),                                           # body base top
    # (LENGTH*BODY_BTM, WIDTH*BODY_BTM, BODY_BASE_HEIGHT),                         # body bottom
    (LENGTH*BODY_BTM, WIDTH*BODY_BTM, BODY_BASE_HEIGHT+EDGE_RADIUS),             # body bottom edge after
    (LENGTH*BODY_BTM, WIDTH*BODY_BTM, BODY_BASE_HEIGHT+ER2),                     # body bottom edge after edge
    # (LENGTH*BODY_TOP, WIDTH*BODY_TOP, BODY_HEIGHT-EDGE_RADIUS),                  # body top edge before
    (LENGTH*BODY_TOP, WIDTH*BODY_TOP, BODY_HEIGHT-BODY_TOP_INSET_HEIGHT, OUTER_TOP_CENTER),               # body top
    (LENGTH*BODY_TOP_INSET, WIDTH*BODY_TOP_INSET, BODY_HEIGHT-BODY_TOP_INSET_HEIGHT, OUTER_TOP_CENTER),   # body top inset bottom
    (LENGTH*BODY_TOP_INSET, WIDTH*BODY_TOP_INSET, BODY_HEIGHT, OUTER_TOP_CENTER),                         # body top inset top
    (LENGTH*BODY_TOP_INSET-ER2*0.5, WIDTH*BODY_TOP_INSET-ER2*0.5, BODY_HEIGHT, OUTER_TOP_CENTER),          # body top inset top
]
print "Top inset length: %scm" % (LENGTH*BODY_TOP_INSET*0.1)

TOP_RADIUS = (WIDTH*BODY_TOP_INSET*0.82-ER2) * 0.5
TOP_RADIUS_INNER = TOP_RADIUS - 3.0
TOP_HOLE_OUTER_HEIGHT = BODY_HEIGHT - 3.0
TOP_HOLE_INNER_HEIGHT = TOP_HOLE_OUTER_HEIGHT - 3.0
print "Top opening is %scm" % (TOP_RADIUS_INNER*2*0.1)
POT_TOP = [
    (TOP_RADIUS+2.0, TOP_RADIUS+2.0, BODY_HEIGHT),              # top hole edge
    (TOP_RADIUS, TOP_RADIUS, BODY_HEIGHT),                                      # top hole
    (TOP_RADIUS, TOP_RADIUS, TOP_HOLE_OUTER_HEIGHT),                            # top hole bottom
    (TOP_RADIUS_INNER, TOP_RADIUS_INNER, TOP_HOLE_OUTER_HEIGHT),                # top inner hole
    (TOP_RADIUS_INNER, TOP_RADIUS_INNER, TOP_HOLE_INNER_HEIGHT),                # top inner hole bottom
    (TOP_RADIUS_INNER+EDGE_RADIUS, TOP_RADIUS_INNER+EDGE_RADIUS, TOP_HOLE_INNER_HEIGHT),  # top inner hole bottom edge
]

INNER_BODY_TOP = TOP_HOLE_INNER_HEIGHT
INNER_BODY_BOTTOM = BODY_BASE_HEIGHT
POT_INNER = [
    (LENGTH*BODY_TOP-T2-ER2, WIDTH*BODY_TOP-T2-ER2, INNER_BODY_TOP, INNER_TOP_CENTER),     # inner body top edge
    (LENGTH*BODY_TOP-T2, WIDTH*BODY_TOP-T2, INNER_BODY_TOP, INNER_TOP_CENTER),             # inner body top
    (LENGTH*BODY_BTM-T2, WIDTH*BODY_BTM-T2, INNER_BODY_BOTTOM+ER2*2),     # inner body bottom edge before
    (LENGTH*BODY_BTM-T2, WIDTH*BODY_BTM-T2, INNER_BODY_BOTTOM),                 # inner body bottom
    (LENGTH*BODY_BTM-T2-ER2*4, WIDTH*BODY_BTM-T2-ER2*4, INNER_BODY_BOTTOM),         # inner body bottom edge after
]
potInnerLen = len(POT_INNER)

# Define the shape of the cross-section of the iron, clock-wise starting from top left
EDGE_X = EDGE_RADIUS / LENGTH
EDGE_Y = EDGE_RADIUS / WIDTH
BODY1_X = 0.333
BODY1_W = 0.7
BODY1_Y = (1.0 - BODY1_W) * 0.5
BODY2_X = 0.667
BODY2_W = 0.95
BODY2_Y = (1.0 - BODY2_W) * 0.5
NOSE_X = 0.05
NOSE_W = 0.2
NOSE_Y = (1.0 - NOSE_W) * 0.5
NOSE_POINT_W = NOSE_W * 0.1667
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

for i,p in enumerate(POT_OUTER):
    if len(p)==4:
        x, y, z, center = p
    else:
        x, y, z = p
        center = CENTER

    if i <= 0:
        loops = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)
        mesh.addEdgeLoops(loops)
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)
        mesh.addEdgeLoop(loop)

for i,p in enumerate(POT_TOP):
    x, y, z = p

    loop = ellipse(VERTICES_PER_EDGE_LOOP, TOP_CENTER, x, y, z)
    mesh.addEdgeLoop(loop)

for i,p in enumerate(POT_INNER):
    if len(p)==4:
        x, y, z, center = p
    else:
        x, y, z = p
        center = CENTER

    if i >= potInnerLen-1:
        loops = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z, True)
        mesh.addEdgeLoops(loops)
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)
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

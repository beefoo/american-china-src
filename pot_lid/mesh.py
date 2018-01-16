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

HANDLE_TOP_WIDTH = DIME_WIDTH
HANDLE_TOP_HEIGHT = 6.0
HANDLE_NECK_WIDTH = 9.0
HANDLE_NECK_HEIGHT = 6.0

lidConfig = {}
with open(INPUT_FILE) as f:
    lidConfig = json.load(f)
SHAPE = lidConfig["shape"]
# CENTER = lidConfig["center"]
CENTER = (0, 0, 0)
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

HANDLE_TOP_WIDTH = DIME_WIDTH
HANDLE_TOP_HEIGHT = 6.0
HANDLE_NECK_WIDTH = 9.0
HANDLE_NECK_HEIGHT = 6.0
HANDLE_NECK_Z = BASE_HEIGHT+TOP_HEIGHT
HANDLE_EDGE_RADIUS = 2.0
HER2 = HANDLE_EDGE_RADIUS * 2
HANDLE_OFFSET_X = 3.0

HANDLE = [
    (HANDLE_NECK_WIDTH + HER2, HANDLE_NECK_Z), # handle neck bottom edge before
    (HANDLE_NECK_WIDTH, HANDLE_NECK_Z), # handle neck bottom
    (HANDLE_NECK_WIDTH, HANDLE_NECK_Z + HER2), # handle neck bottom edge after
    (HANDLE_NECK_WIDTH, HANDLE_NECK_Z + HANDLE_NECK_HEIGHT), # handle neck top
    (HANDLE_TOP_WIDTH - HER2, HANDLE_NECK_Z + HANDLE_NECK_HEIGHT), # handle top bottom edge before
    (HANDLE_TOP_WIDTH, HANDLE_NECK_Z + HANDLE_NECK_HEIGHT), # handle top bottom
    (HANDLE_TOP_WIDTH, HANDLE_NECK_Z + HANDLE_NECK_HEIGHT + HANDLE_TOP_HEIGHT), # handle top top
    (HANDLE_TOP_WIDTH - HER2, HANDLE_NECK_Z + HANDLE_NECK_HEIGHT + HANDLE_TOP_HEIGHT) # handle top edge after
]
handleLen = len(HANDLE)

# reduce size
for i, p in enumerate(LID):
    LID[i] = (p[0]-REDUCE_AMOUNT, p[1]-REDUCE_AMOUNT, p[2])

print "Dimensions: %s x %s x %s" % (max([d[0] for d in LID]), max([d[1] for d in LID]), max([d[1] for d in HANDLE]))

# build the mesh
mesh = Mesh()

loops = []
for i, p in enumerate(LID):
    x, y, z = p
    if i <= 0:
        ll = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z)
        loops += ll
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, CENTER, z)
        loops.append(loop)

c = (CENTER[0]+HANDLE_OFFSET_X, CENTER[1], CENTER[2])
for i, p in enumerate(HANDLE):
    w, z = p
    r = w * 0.5
    if i >= handleLen-1:
        ll = ellipseMesh(VERTICES_PER_EDGE_LOOP, c, r, r, z, reverse=True)
        loops += ll
    else:
        loop = ellipse(VERTICES_PER_EDGE_LOOP, c, r, r, z)
        loops.append(loop)

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

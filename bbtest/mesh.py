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
VERTICES_PER_EDGE_LOOP = 16
CENTER = (0, 0, 0)
WIDTH = 125.0
LENGTH = 200.0
HEIGHT = 125.0
EDGE_RADIUS = 6.0
THICKNESS = 6.0

RX = LENGTH * 0.5
RY = WIDTH * 0.5
LOOPS = [
    (RX-EDGE_RADIUS, RY-EDGE_RADIUS, 0.0),
    (RX, RY, 0.0),
    (RX, RY, EDGE_RADIUS),
    (RX, RY, HEIGHT-EDGE_RADIUS),
    (RX, RY, HEIGHT),
    (RX-THICKNESS, RY-THICKNESS, HEIGHT),
    (RX-THICKNESS, RY-THICKNESS, HEIGHT-EDGE_RADIUS),
    (RX-THICKNESS, RY-THICKNESS, THICKNESS),
    (RX-THICKNESS-EDGE_RADIUS, RY-THICKNESS-EDGE_RADIUS, THICKNESS),
]

mesh = Mesh()

# build the top hole of the pot
for i,l in enumerate(LOOPS):
    x, y, z = l
    if i <= 0:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, x, y, z)
        mesh.addEdgeLoops(loops)
    elif i >= len(LOOPS)-1:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, x, y, z, True)
        mesh.addEdgeLoops(loops)
    else:
        loop = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, x, y, z)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "BBTest",
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

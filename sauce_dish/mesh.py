# -*- coding: utf-8 -*-

# python mesh.py -percent 0.2

import argparse
import csv
import json
from lib import *
import os
from pprint import pprint
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-percent', dest="PERCENT", default=0.086, help="Percent of people serving in military during WW2: 8.6 percent of all Americans and 20 percent of Chinese in America")
args = parser.parse_args()

# data config
OUTPUT_FILE = "mesh.json"
PERCENT = args.PERCENT

# data config
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 2 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 4
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
LENGTH = 146.0
WIDTH = 72.0
HEIGHT = 25.0
BASE_HEIGHT = 6.0
EDGE_RADIUS = 4.0
CORNER_RADIUS = 6.0
THICKNESS = 6.0
BASE_THICKNESS = 6.0

# calculations
BASE_LENGTH = LENGTH - 6.0 * 2
BASE_WIDTH = WIDTH - 6.0 * 2
T2 = THICKNESS * 2
ER2 = EDGE_RADIUS * 2
BT2 = BASE_THICKNESS * 2

DISH = [
    [BASE_LENGTH-BT2-BT2-ER2, BASE_WIDTH-BT2-BT2-ER2, BASE_HEIGHT], # start at inner base top inner edge
    [BASE_LENGTH-BT2-BT2, BASE_WIDTH-BT2-BT2, BASE_HEIGHT], # move out to inner base top
    [BASE_LENGTH-BT2-BT2, BASE_WIDTH-BT2-BT2, 0], # move down to inner base bottom
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, 0], # move out to base bottom
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, BASE_HEIGHT], # move up to base top
    [BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT], # move out to body bottom
    [LENGTH, WIDTH, HEIGHT-EDGE_RADIUS], # move up to body top edge before
    [LENGTH, WIDTH, HEIGHT], # move up to body top
    [LENGTH-BT2, WIDTH-BT2, HEIGHT], # move in to body top inner
    [LENGTH-BT2, WIDTH-BT2, HEIGHT-EDGE_RADIUS], # move down to body top inner edge
    [LENGTH-BT2, WIDTH-BT2, BASE_HEIGHT+THICKNESS], # move down to body bottom inner edge
    [LENGTH-BT2-ER2, WIDTH-BT2-ER2, BASE_HEIGHT+THICKNESS] # move in to body bottom inset edge
]
dishLen = len(DISH)
targetEdgeCount = dishLen * 2**SUBDIVIDE_Y

# interpolate bowl data
xs = [d[0] for d in DISH]
ys = [d[1] for d in DISH]
zs = [d[2] for d in DISH]
domain = [1.0 * i / (dishLen-1)  for i, d in enumerate(DISH)]
splinedLengths = bspline(list(zip(domain, xs)), n=targetEdgeCount, degree=3, periodic=False)
splinedWidths = bspline(list(zip(domain, ys)), n=targetEdgeCount, degree=3, periodic=False)
splinedHeights = bspline(list(zip(domain, zs)), n=targetEdgeCount, degree=3, periodic=False)

# build the mesh
mesh = Mesh()

# get spline data
loopData = []
for i in range(targetEdgeCount):
    x = splinedLengths[i][1]
    y = splinedWidths[i][1]
    z = splinedHeights[i][1]
    loopData.append((x, y, z))

# add the loops before the displacement
for i, d in enumerate(loopData):
    x, y, z = d
    if i <= 0:
        loops = roundedRectMesh(VERTICES_PER_EDGE_LOOP, CENTER, x, y, z, CORNER_RADIUS)
        mesh.addEdgeLoops(loops)
    elif i >= targetEdgeCount-1:
        loops = roundedRectMesh(VERTICES_PER_EDGE_LOOP, CENTER, x, y, z, CORNER_RADIUS, reverse=True)
        mesh.addEdgeLoops(loops)
    else:
        loop = roundedRect(VERTICES_PER_EDGE_LOOP, CENTER, x, y, z, CORNER_RADIUS)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Sauce dish",
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

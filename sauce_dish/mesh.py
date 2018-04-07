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
VERTICES_PER_EDGE_LOOP = BASE_VERTICES
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
LENGTH = 146.0
WIDTH = 72.0
HEIGHT = 32.0
BASE_HEIGHT = 7.0
EDGE_RADIUS = 4.0
CORNER_RADIUS = 6.0
THICKNESS = 6.0
BASE_THICKNESS = 6.0
DIVIDER_THICKNESS = 6.0

# calculations
BASE_LENGTH = LENGTH - 6.0 * 2
BASE_WIDTH = WIDTH - 6.0 * 2
T2 = THICKNESS * 2
ER2 = EDGE_RADIUS * 2
BT2 = BASE_THICKNESS * 2

AVAILABLE_CENTER_SPACE = WIDTH - T2 - DIVIDER_THICKNESS
SPACE_LEFT = AVAILABLE_CENTER_SPACE * PERCENT
SPACE_RIGHT = AVAILABLE_CENTER_SPACE * (1.0-PERCENT)
DIVIDER_PADDING = 2.0
DIVIDER_LEFT = WIDTH * -0.5 + THICKNESS + SPACE_LEFT - DIVIDER_PADDING
DIVIDER_RIGHT = DIVIDER_LEFT + DIVIDER_PADDING + DIVIDER_THICKNESS + DIVIDER_PADDING

DISH = [
    [BASE_LENGTH-BT2-BT2-ER2, BASE_WIDTH-BT2-BT2-ER2, BASE_HEIGHT], # start at inner base top inner edge
    [BASE_LENGTH-BT2-BT2, BASE_WIDTH-BT2-BT2, BASE_HEIGHT], # move out to inner base top
    [BASE_LENGTH-BT2-BT2, BASE_WIDTH-BT2-BT2, 0], # move down to inner base bottom
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, 0], # move out to base bottom
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, BASE_HEIGHT], # move up to base top
    [BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT], # move out to body bottom
    [LENGTH, WIDTH, HEIGHT-EDGE_RADIUS], # move up to body top edge before
    [LENGTH, WIDTH, HEIGHT], # move up to body top
    [LENGTH-BT2, WIDTH-BT2, HEIGHT], # move in to body top inner - DIVIDER STARTS HERE
    [LENGTH-BT2, WIDTH-BT2, HEIGHT-EDGE_RADIUS], # move down to body top inner edge
    [lerp(LENGTH-BT2, BASE_LENGTH-BT2, 0.7), lerp(WIDTH-BT2, BASE_WIDTH-BT2, 0.7), BASE_HEIGHT+THICKNESS+EDGE_RADIUS], # move down to body bottom inner edge before
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, BASE_HEIGHT+THICKNESS], # move down to body bottom inner
    [BASE_LENGTH-BT2-ER2, BASE_WIDTH-BT2-ER2, BASE_HEIGHT+THICKNESS] # move in to body bottom inset edge
]
dishLen = len(DISH)
dividerIndexStart = 8
loopsForDivider = dishLen - dividerIndexStart - 1

# # interpolate bowl data
# targetEdgeCount = dishLen * 2**SUBDIVIDE_Y
# xs = [d[0] for d in DISH]
# ys = [d[1] for d in DISH]
# zs = [d[2] for d in DISH]
# domain = [1.0 * i / (dishLen-1)  for i, d in enumerate(DISH)]
# splinedLengths = bspline(list(zip(domain, xs)), n=targetEdgeCount, degree=3, periodic=False)
# splinedWidths = bspline(list(zip(domain, ys)), n=targetEdgeCount, degree=3, periodic=False)
# splinedHeights = bspline(list(zip(domain, zs)), n=targetEdgeCount, degree=3, periodic=False)

# # get spline data
# loopData = []
# for i in range(targetEdgeCount):
#     x = splinedLengths[i][1]
#     y = splinedWidths[i][1]
#     z = splinedHeights[i][1]
#     loopData.append((x, y, z))

# build the mesh
mesh = Mesh()

# add the loops
dividerVertexIndexStart = 0
for i, d in enumerate(DISH):
    x, y, z = d
    if i == dividerIndexStart:
        dividerVertexIndexStart = mesh.getVertexCount()
    if i <= 0:
        loops = roundedRectMesh(CENTER, x, y, z, CORNER_RADIUS, DIVIDER_LEFT, DIVIDER_RIGHT, EDGE_RADIUS)
        mesh.addEdgeLoops(loops)
    elif i >= dishLen-1:
        loops = roundedRectMesh(CENTER, x, y, z, CORNER_RADIUS, DIVIDER_LEFT, DIVIDER_RIGHT, EDGE_RADIUS, reverse=True)
        mesh.addEdgeLoops(loops)
    else:
        loop = roundedRect(CENTER, x, y, z, CORNER_RADIUS, DIVIDER_LEFT, DIVIDER_RIGHT)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()
totalOriginalVertCount = len(mesh.verts)

# remove faces for divider
indices = [-2, -7, -13, -21]
i = indices[-1]
for j in range(loopsForDivider*2-1):
    i -= 8
    indices.append(i)
mesh.removeFaces(indices)

print "Starting to add divider at vertex %s" % dividerVertexIndexStart
i = dividerVertexIndexStart
prev = False
for j in range(loopsForDivider):
    bl = i + 2
    br = i + 3
    tr = i + 10
    tl = i + 11

    corners = [tl, tr, br, bl]
    vtl, vtr, vbr, vbl = tuple([mesh.verts[c] for c in corners])

    verticesToAdd = [
        add(vtl, (0, -EDGE_RADIUS, 0)),
        add(vtr, (0, -EDGE_RADIUS, 0)),
        add(vtl, (0, -EDGE_RADIUS*2, 0)),
        add(vtr, (0, -EDGE_RADIUS*2, 0)),
        add(vbl, (0, EDGE_RADIUS*2, 0)),
        add(vbr, (0, EDGE_RADIUS*2, 0)),
        add(vbl, (0, EDGE_RADIUS, 0)),
        add(vbr, (0, EDGE_RADIUS, 0))
    ]

    if (j < loopsForDivider-1):
        indices = mesh.addVertices(verticesToAdd)
    else:
        # get indices from last two loops
        l0 = totalOriginalVertCount - 8 # inner loop
        l1 = totalOriginalVertCount - 8 - 16 # outer loop
        # indices = [l1+2, l1+3, l0+1, l0+2, l0+6, l0+5, l1+11, l1+10]
        indices = [l1+11, l1+10, l0+6, l0+5, l0+1, l0+2, l1+2, l1+3]
    v1, v2, v3, v4, v5, v6, v7, v8 = tuple(indices)

    if not prev:
        mesh.addFace((v1, v2, tr, tl))
        mesh.addFace((v3, v4, v2, v1))
        mesh.addFace((v5, v6, v4, v3))
        mesh.addFace((v7, v8, v6, v5))
        mesh.addFace((bl, br, v8, v7))
    else:
        ptl, ptr, pv1, pv2, pv3, pv4, pv5, pv6, pv7, pv8, pbl, pbr = tuple(prev)
        mesh.addFace((tl, v1, pv1, ptl))
        mesh.addFace((v2, tr, ptr, pv2))

        mesh.addFace((v1, v3, pv3, pv1))
        mesh.addFace((v4, v2, pv2, pv4))

        mesh.addFace((v3, v5, pv5, pv3))
        mesh.addFace((v6, v4, pv4, pv6))

        mesh.addFace((v5, v7, pv7, pv5))
        mesh.addFace((v8, v6, pv6, pv8))

        mesh.addFace((v7, bl, pbl, pv7))
        mesh.addFace((br, v8, pv8, pbr))


    prev = [tl, tr] + indices[:] + [bl, br]
    i += 16

# save data
data = [
    {
        "name": "Sauce dish",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": range(15)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

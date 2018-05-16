# -*- coding: utf-8 -*-

# python mesh.py -percent 0.2
# python mesh.py -out "both/mesh_08.json" -offset -22
# python mesh.py -out "both/mesh_20.json" -offset 22 -percent 0.2

import argparse
import csv
import json
from lib import *
import os
from pprint import pprint
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-percent', dest="PERCENT", type=float, default=0.086, help="Percent of people serving in military during WW2: 8.6 percent of all Americans and 20 percent of Chinese in America")
parser.add_argument('-offset', dest="OFFSET", type=float, default=0, help="Offset the position of the saucer")
parser.add_argument('-out', dest="OUTPUT_FILE", default="mesh.json", help="Output JSON file")
args = parser.parse_args()

# data config
OUTPUT_FILE = args.OUTPUT_FILE
OFFSET = args.OFFSET
PERCENT = args.PERCENT

# cup config in mm
CENTER = (0, OFFSET, 0)
PRECISION = 8
LENGTH = 100.0
WIDTH = 45.0
HEIGHT = 24.0
BASE_HEIGHT = 7.0
EDGE_RADIUS = 3.0
CORNER_RADIUS = 3.0
THICKNESS = 5.0
BASE_THICKNESS = 5.0
DIVIDER_THICKNESS = 5.0
DIVIDER_ADJUST = 1.15

# calculations
BASE_LENGTH = LENGTH - 2.0 * 2
BASE_WIDTH = WIDTH - 2.0 * 2
T2 = THICKNESS * 2
ER2 = EDGE_RADIUS * 2
BT2 = BASE_THICKNESS * 2

INNER_HEIGHT = (HEIGHT - BASE_HEIGHT - THICKNESS)
INNER_WIDTH = (BASE_WIDTH - T2)
INNER_LENGTH = (BASE_LENGTH - T2)
DIVIDER_AREA = DIVIDER_THICKNESS * INNER_WIDTH * INNER_HEIGHT
AVAILABLE_AREA = INNER_LENGTH * INNER_WIDTH * INNER_HEIGHT - DIVIDER_AREA
AREA_LEFT = AVAILABLE_AREA * PERCENT
SPACE_LEFT = AREA_LEFT / (INNER_WIDTH * INNER_HEIGHT) + DIVIDER_ADJUST
SPACE_RIGHT = INNER_LENGTH - THICKNESS - SPACE_LEFT
DIVIDER_PADDING = 0.0
DIVIDER_LEFT = BASE_LENGTH * -0.5 + THICKNESS + SPACE_LEFT - DIVIDER_PADDING
DIVIDER_RIGHT = DIVIDER_LEFT + DIVIDER_PADDING + DIVIDER_THICKNESS + DIVIDER_PADDING
DIVIDER_LEFT_EDGE_RADIUS = CORNER_RADIUS
DIVIDER_RIGHT_EDGE_RADIUS = CORNER_RADIUS

if PERCENT < 0.1:
    DIVIDER_LEFT_EDGE_RADIUS = 1.0

DISH = [
    [BASE_LENGTH-BT2-BT2-ER2*0.2, BASE_WIDTH-BT2-BT2-ER2*0.2, BASE_HEIGHT, 1.0], # start at inner base top inner edge
    [BASE_LENGTH-BT2-BT2, BASE_WIDTH-BT2-BT2, BASE_HEIGHT, CORNER_RADIUS/2], # move out to inner base top
    [BASE_LENGTH-BT2-BT2, BASE_WIDTH-BT2-BT2, 0, CORNER_RADIUS*0.5], # move down to inner base bottom
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, 0], # move out to base bottom
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, BASE_HEIGHT], # move up to base top
    [BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT], # move out to body bottom
    [LENGTH, WIDTH, HEIGHT-EDGE_RADIUS], # move up to body top edge before
    [LENGTH, WIDTH, HEIGHT], # move up to body top
    [LENGTH-BT2, WIDTH-BT2, HEIGHT], # move in to body top inner - DIVIDER STARTS HERE
    [LENGTH-BT2, WIDTH-BT2, HEIGHT-EDGE_RADIUS], # move down to body top inner edge
    # [lerp(LENGTH-BT2, BASE_LENGTH-BT2, 0.7), lerp(WIDTH-BT2, BASE_WIDTH-BT2, 0.7), BASE_HEIGHT+THICKNESS+EDGE_RADIUS], # move down to body bottom inner edge before
    [BASE_LENGTH-BT2, BASE_WIDTH-BT2, BASE_HEIGHT+THICKNESS], # move down to body bottom inner
    [BASE_LENGTH-BT2-ER2, BASE_WIDTH-BT2-ER2, BASE_HEIGHT+THICKNESS, CORNER_RADIUS/2] # move in to body bottom inset edge
]
dishLen = len(DISH)
dividerIndexStart = 8
loopsForDivider = dishLen - dividerIndexStart - 1

# build the mesh
mesh = Mesh()

# add the loops
dividerVertexIndexStart = 0
for i, d in enumerate(DISH):
    if len(d)==4:
        x, y, z, r = d
    else:
        x, y, z = d
        r = CORNER_RADIUS
    if i == dividerIndexStart:
        dividerVertexIndexStart = mesh.getVertexCount()
    if i <= 0:
        loops = roundedRectMesh(CENTER, x, y, z, r, DIVIDER_LEFT, DIVIDER_RIGHT, EDGE_RADIUS, DIVIDER_LEFT_EDGE_RADIUS, DIVIDER_RIGHT_EDGE_RADIUS)
        mesh.addEdgeLoops(loops)
    elif i >= dishLen-1:
        loops = roundedRectMesh(CENTER, x, y, z, r, DIVIDER_LEFT, DIVIDER_RIGHT, EDGE_RADIUS, DIVIDER_LEFT_EDGE_RADIUS, DIVIDER_RIGHT_EDGE_RADIUS, reverse=True)
        mesh.addEdgeLoops(loops)
    else:
        loop = roundedRect(CENTER, x, y, z, r, DIVIDER_LEFT, DIVIDER_RIGHT, DIVIDER_LEFT_EDGE_RADIUS, DIVIDER_RIGHT_EDGE_RADIUS)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()
totalOriginalVertCount = len(mesh.verts)

# remove faces for divider
indices = [-3, -10, -18]
i = indices[-1]
for j in range(loopsForDivider*2):
    i -= 10
    indices.append(i)
mesh.removeFaces(indices)

print "Starting to add divider at vertex %s" % dividerVertexIndexStart
i = dividerVertexIndexStart
prev = False
indicesPerLoop = 20
for j in range(loopsForDivider):
    bl = i + 3
    br = i + 4
    tr = i + 13
    tl = i + 14

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
        l0 = totalOriginalVertCount - (indicesPerLoop - 8) # inner loop
        l1 = totalOriginalVertCount - (indicesPerLoop - 8) - indicesPerLoop # outer loop
        # indices = [l1+2, l1+3, l0+1, l0+2, l0+6, l0+5, l1+11, l1+10]
        indices = [l1+14, l1+13, l0+9, l0+8, l0+2, l0+3, l1+3, l1+4]
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
    i += indicesPerLoop

# save data
data = [
    {
        "name": "Sauce dish",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": range(21)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

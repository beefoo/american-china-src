# -*- coding: utf-8 -*-

import colorsys
import json
from lib import *
import math
from PIL import Image, ImageDraw
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 8
IMAGE_MAP_FILE = "imgMap.png"

# retrieve image map data
im = Image.open(IMAGE_MAP_FILE)
IMAGE_MAP_W, IMAGE_MAP_H = im.size
IMAGE_MAP = list(im.getdata())

# cup config in mm
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 4 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 4
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

CENTER = (0, 0, 0)
WIDTH = 123.0
HEIGHT = 22.0
EDGE_RADIUS = 4.0
THICKNESS = 4.5
DISPLACEMENT = (-4.0, 4.0, -3.0)
BASE_HEIGHT = 8.0
MIN_HEIGHT = 1.5
BASE_STAND_WIDTH = 4.0

CENTER_WIDTH = WIDTH * 0.5
BASE_WIDTH = WIDTH * 0.6
INNER_BASE_WIDTH = BASE_WIDTH * 0.8
INSET_BASE_WIDTH = INNER_BASE_WIDTH * 0.8
INSET_BASE_HEIGHT = BASE_HEIGHT * 0.6
BODY_HEIGHT = (HEIGHT - BASE_HEIGHT) * 0.1 + BASE_HEIGHT
BODY_WIDTH = WIDTH * 0.8
CENTER_HEIGHT = INSET_BASE_HEIGHT + THICKNESS
TOP_EDGE_THINKNESS = THICKNESS * 1.1

print "%s should be bigger than %s" % (BODY_HEIGHT+THICKNESS, CENTER_HEIGHT)
print "%s should be bigger than %s" % (BASE_WIDTH, INNER_BASE_WIDTH + BASE_STAND_WIDTH*2)

# Adjust image data
IMAGE_SCALE = 1.0
IMAGE_TRANSLATE = (-CENTER_WIDTH*0.4, 0)

PLATE = [
    [INSET_BASE_WIDTH - EDGE_RADIUS, INSET_BASE_HEIGHT],      # start with base inset edge
    [INSET_BASE_WIDTH, INSET_BASE_HEIGHT],                      # move out to base inset
    [INNER_BASE_WIDTH, INSET_BASE_HEIGHT],                      # move out to base inset
    [INNER_BASE_WIDTH, 0],                                      # move down to inner base stand
    [INNER_BASE_WIDTH + BASE_STAND_WIDTH*2, 0],                 # move out to outer base stand
    [INNER_BASE_WIDTH + BASE_STAND_WIDTH*2, BASE_HEIGHT],       # move up to outer base stand top
    [BASE_WIDTH, BASE_HEIGHT],                                  # move up to base top
    [BODY_WIDTH, BODY_HEIGHT],                                  # move up and out to body
    [WIDTH, HEIGHT-TOP_EDGE_THINKNESS],                         # move up to outer top
    [WIDTH, HEIGHT],                                            # move up to outer top
    [WIDTH-THICKNESS*2, HEIGHT],                                # move in to inner top
    [BODY_WIDTH-THICKNESS*2, BODY_HEIGHT+THICKNESS],            # move down and in to inner body
    [CENTER_WIDTH, CENTER_HEIGHT],                # move down and in to inner base
    [CENTER_WIDTH - EDGE_RADIUS*2, CENTER_HEIGHT] # move in to inner base edge
]
plateLen = len(PLATE)
targetEdgeCount = plateLen * 2**SUBDIVIDE_Y

# interpolate bowl data
widths = [d[0] for d in PLATE]
heights = [d[1] for d in PLATE]
xs = [1.0 * i / (plateLen-1)  for i, d in enumerate(PLATE)]
splinedWidths = bspline(list(zip(xs, widths)), n=targetEdgeCount, degree=3, periodic=False)
splinedHeights = bspline(list(zip(xs, heights)), n=targetEdgeCount, degree=3, periodic=False)

# get spline data
loopData = []
for i in range(targetEdgeCount):
    width = splinedWidths[i][1]
    z = splinedHeights[i][1]
    r = width * 0.5
    loopData.append((r, z))

# build the mesh
mesh = Mesh()

# add the loops to mesh
for i, d in enumerate(loopData):
    r = d[0]
    z = d[1]
    if i <= 0:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoops(loops)
    elif i >= targetEdgeCount-1:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z, reverse=True)
        mesh.addEdgeLoops(loops)
    else:
        loop = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoop(loop)

# displace edge loops with image map
r = WIDTH * 0.5
bounds = [(-r, -r), (r, r)]
mesh.displaceEdgeLoops(IMAGE_MAP, IMAGE_MAP_W, IMAGE_MAP_H, bounds, DISPLACEMENT, IMAGE_SCALE, IMAGE_TRANSLATE, MIN_HEIGHT)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Plate",
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

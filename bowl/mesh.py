# -*- coding: utf-8 -*-

# Data source: https://earthquake.usgs.gov/earthquakes/events/1906calif/18april/got_seismogram.php

import csv
import json
from lib import *
import os
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
DATA_FILE = "data/gotNS_part2.json"

# data config
DATA_WINDOW_SIZE = 0.04

BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 2 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 2
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

# helpers
SHOW_GRAPH = False

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
WIDTH = 118.0
HEIGHT = 60.0
BASE_WIDTH = 55.0
BASE_HEIGHT = 9.0
EDGE_RADIUS = 4.0
THICKNESS = 5.0
MAX_WAVE = 6.8
BASE_EDGE_RADIUS = 2.0

# calculations
INSET_BASE_WIDTH = BASE_WIDTH - 10.0
INSET_BASE_HEIGHT = BASE_HEIGHT * 0.5
INNER_BASE_WIDTH = BASE_WIDTH - 6.0
BODY_HEIGHT = (HEIGHT - BASE_HEIGHT) * 0.1 + BASE_HEIGHT
BODY_WIDTH = WIDTH * 0.8

BOWL = [
    [INSET_BASE_WIDTH - EDGE_RADIUS*2, INSET_BASE_HEIGHT],      # 0, start with base inset edge
    [INSET_BASE_WIDTH, INSET_BASE_HEIGHT],                      # 1, move out to base inset
    [INSET_BASE_WIDTH, INSET_BASE_HEIGHT*0.5],                  # 2, move down to base inset edge
    [INNER_BASE_WIDTH, 0],                                      # 3, move down and out to inner base
    [BASE_WIDTH, 0],                                            # 4, move out to outer base
    [BASE_WIDTH, BASE_EDGE_RADIUS],                             # 5, move up to outer base edge
    [BASE_WIDTH, BASE_HEIGHT],                                  # 6, move up to base top; START DISPLACEMENT HERE
    [BODY_WIDTH, BODY_HEIGHT],                                  # 7, move up and out to body
    [WIDTH, HEIGHT - EDGE_RADIUS],                              # 8, move up and out to outer top edge
    [WIDTH, HEIGHT],                                            # 9, move up to outer top
    [WIDTH-THICKNESS*2, HEIGHT],                                # 10, move in to inner top; STOP DISPLACEMENT HERE
    [BODY_WIDTH-THICKNESS*2, BODY_HEIGHT],                      # 11, move down and in to inner body
    [INSET_BASE_WIDTH, BASE_HEIGHT+THICKNESS],                  # 12, move down and in to inner base
    [INSET_BASE_WIDTH - EDGE_RADIUS*2, BASE_HEIGHT+THICKNESS]   # 13, move in to inner base edge
]
bowlLen = len(BOWL)
DISPLACE_START = 6
DISPLACE_END = 10 * 0.95

targetEdgeCount = bowlLen * 2**SUBDIVIDE_Y
targetDataCount = targetEdgeCount * 4
highresEdgeCount = 1000

# read data
print "Processing data..."
data = []
with open(DATA_FILE) as f:
    data = json.load(f)
data = [tuple(d) for d in data]
# pad data
minY = min([d[1] for d in data])
data = [(0, 0.5)] + data + [(1, 0.5)]
# interpolate data
splinedData = bspline(data, n=targetDataCount, degree=3, periodic=False)
# normalize splined data
ys = [d[1] for d in splinedData]
minY = min(ys)
maxY = max(ys)
splinedData = [(d[0], norm(d[1], minY, maxY)-0.5) for d in splinedData]
# normalize raw data
ys = [d[1] for d in data]
minY = min(ys)
maxY = max(ys)
data = [(d[0], norm(d[1], minY, maxY)-0.5) for d in data]
# choose which data we should use for displacement
displaceData = data

# make widths correlate to absolute heights
ys = [abs(d[1]) for d in displaceData]
ysum = sum(ys)
x = 0
for i, d in enumerate(displaceData):
    w = 1.0 * abs(d[1]) / ysum
    displaceData[i] = (x + w * 0.5, d[1])
    x += w

# make the data quadratic
power = 0.75 # make this > 1 to exaggerate waves, make this < 1 to make waves closer in size to each other
for i, d in enumerate(displaceData):
    y = d[1] * 2
    ay = abs(y)
    y2 = ay**power
    direction = y / ay
    y = y2 * direction * 0.5
    displaceData[i] = (d[0], y)

if SHOW_GRAPH:
    import matplotlib.pyplot as plt
    xs = [d[0] for d in displaceData]
    ys = [d[1] for d in displaceData]
    plt.plot(xs, ys, '-')
    plt.show()
    sys.exit(1)

# interpolate bowl data
widths = [d[0] for d in BOWL]
heights = [d[1] for d in BOWL]
xs = [1.0 * i / (bowlLen-1)  for i, d in enumerate(BOWL)]
splinedWidths = bspline(list(zip(xs, widths)), n=targetEdgeCount, degree=3, periodic=False)
splinedHeights = bspline(list(zip(xs, heights)), n=targetEdgeCount, degree=3, periodic=False)
splinedWidthsHighres = bspline(list(zip(xs, widths)), n=1000, degree=3, periodic=False)
splinedHeightsHighres = bspline(list(zip(xs, heights)), n=1000, degree=3, periodic=False)

# build the mesh
mesh = Mesh()

# get spline data
loopData = []
for i in range(targetEdgeCount):
    width = splinedWidths[i][1]
    z = splinedHeights[i][1]
    r = width * 0.5
    loopData.append((r, z))
loopDataHighres = []
for i in range(highresEdgeCount):
    width = splinedWidthsHighres[i][1]
    z = splinedHeightsHighres[i][1]
    r = width * 0.5
    loopDataHighres.append((r, z))

# determine indices for displaced walls walls, cut off ends for normal calculations
displaceStart = int(round(1.0 * DISPLACE_START / bowlLen * targetEdgeCount))
displaceEnd = int(round(1.0 * DISPLACE_END / bowlLen * targetEdgeCount))
displaceStartHighres = int(round(1.0 * DISPLACE_START / bowlLen * highresEdgeCount))
displaceEndHighres = int(round(1.0 * DISPLACE_END / bowlLen * highresEdgeCount))

# add the loops before the displacement
for i, d in enumerate(loopData):
    if i >= displaceStart:
        break
    r = d[0]
    z = d[1]
    if i <= 0:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoops(loops)
    else:
        loop = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoop(loop)

# add displacement
displaceLoopData = loopDataHighres[displaceStartHighres:displaceEndHighres]
dLen = len(displaceLoopData)
for i, d in enumerate(displaceData):
    px = d[0]
    delta = d[1] * MAX_WAVE
    j = int(round(px * (dLen-1)))
    dd = displaceLoopData[j]
    r = dd[0]
    z = dd[1]

    if j > 0 and j < dLen-1:

        # get the point before and after
        before = displaceLoopData[j-1]
        after = displaceLoopData[j+1]

        p0 = (before[0], before[1])
        p1 = (r, z)
        p2 = (after[0], after[1])

        # determine the normal
        angle = angleBetweenPoints(p0, p2)
        normal = angle + 90
        pn = translatePoint(p1, normal, delta)

        # update the radius and z
        rDelta = pn[0] - r
        zDelta = pn[1] - z
        r += rDelta
        z += zDelta

        loop = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoop(loop)

# add loops after displacement
for i, d in enumerate(loopData):
    if i >= displaceEnd:
        r = d[0]
        z = d[1]
        if i >= targetEdgeCount-1:
            loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z, reverse=True)
            mesh.addEdgeLoops(loops)
        else:
            loop = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
            mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Bowl",
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

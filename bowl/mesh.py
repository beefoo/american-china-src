# -*- coding: utf-8 -*-

# Data source: https://earthquake.usgs.gov/earthquakes/events/1906calif/18april/got_seismogram.php

import csv
import json
import math
import numpy as np
import os
from pprint import pprint
from scipy import interpolate
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
WIDTH = 115.0
HEIGHT = 55.0
BASE_WIDTH = 55.0
BASE_HEIGHT = 9.0
EDGE_RADIUS = 4.0
THICKNESS = 5.0
MAX_WAVE = 6.4

# calculations
INSET_BASE_WIDTH = BASE_WIDTH * 0.5
INSET_BASE_HEIGHT = BASE_HEIGHT * 0.5
INNER_BASE_WIDTH = BASE_WIDTH * 0.7
BODY_HEIGHT = (HEIGHT - BASE_HEIGHT) * 0.1 + BASE_HEIGHT
BODY_WIDTH = WIDTH * 0.8

BOWL = [
    [INSET_BASE_WIDTH - EDGE_RADIUS*2, INSET_BASE_HEIGHT],      # 0, start with base inset edge
    [INSET_BASE_WIDTH, INSET_BASE_HEIGHT],                      # 1, move out to base inset
    [INNER_BASE_WIDTH, 0],                                      # 2, move down and out to inner base
    [BASE_WIDTH, 0],                                            # 3, move out to outer base
    [BASE_WIDTH, EDGE_RADIUS],                                  # 4, move up to outer base edge
    [BASE_WIDTH, BASE_HEIGHT],                                  # 5, move up to base top
    [BODY_WIDTH, BODY_HEIGHT],                                  # 6, move up and out to body
    [WIDTH, HEIGHT - EDGE_RADIUS],                              # 7, move up and out to outer top edge
    [WIDTH, HEIGHT],                                            # 8, move up to outer top
    [WIDTH-THICKNESS*2, HEIGHT],                                # 9, move in to inner top
    [BODY_WIDTH-THICKNESS*2, BODY_HEIGHT],                      # 10, move down and in to inner body
    [INSET_BASE_WIDTH, BASE_HEIGHT+THICKNESS],                  # 11, move down and in to inner base
    [INSET_BASE_WIDTH - EDGE_RADIUS*2, BASE_HEIGHT+THICKNESS]   # 12, move in to inner base edge
]
bowlLen = len(BOWL)
DISPLACE_START = 5
DISPLACE_END = 9 * 0.95

targetEdgeCount = bowlLen * 2**SUBDIVIDE_Y
targetDataCount = targetEdgeCount * 4
highresEdgeCount = 1000

def angleBetweenPoints(p1, p2):
    deltaX = p2[0] - p1[0]
    deltaY = p2[1] - p1[1]
    rad = math.atan2(deltaY, deltaX)
    return math.degrees(rad)

def bspline(cv, n=100, degree=3, periodic=True):
    """ Calculate n samples on a bspline

        cv :      Array ov control vertices
        n  :      Number of samples to return
        degree:   Curve degree
        periodic: True - Curve is closed
                  False - Curve is open
    """

    # If periodic, extend the point array by count+degree+1
    cv = np.asarray(cv)
    count = len(cv)

    if periodic:
        factor, fraction = divmod(count+degree+1, count)
        cv = np.concatenate((cv,) * factor + (cv[:fraction],))
        count = len(cv)
        degree = np.clip(degree,1,degree)

    # If opened, prevent degree from exceeding count-1
    else:
        degree = np.clip(degree,1,count-1)


    # Calculate knot vector
    kv = None
    if periodic:
        kv = np.arange(0-degree,count+degree+degree-1)
    else:
        kv = np.clip(np.arange(count+degree+1)-degree,0,count-degree)

    # Calculate query range
    u = np.linspace(periodic,(count-degree),n)

    # Calculate result
    return np.array(interpolate.splev(u, (kv,cv.T,degree))).T.tolist()

def ellipse(vertices, center, r1, r2, z):
    verts = []
    edgesPerSide = vertices / 4
    # add the top
    for i in range(edgesPerSide):
        x = 1.0 * i / edgesPerSide * 2 - 1
        verts.append((x,-1.0))
    # right
    for i in range(edgesPerSide):
        y = 1.0 * i / edgesPerSide * 2 - 1
        verts.append((1.0, y))
    # bottom
    for i in range(edgesPerSide):
        x = 1.0 * i / edgesPerSide * 2 - 1
        verts.append((-x, 1.0))
    # left
    for i in range(edgesPerSide):
        y = 1.0 * i / edgesPerSide * 2 - 1
        verts.append((-1.0, -y))

    e = []
    for v in verts:
        x = v[0]
        y = v[1]
        u = x * math.sqrt(1.0 - 0.5 * (y * y))
        v = y * math.sqrt(1.0 - 0.5 * (x * x))
        # convert to actual unit
        u = u * r1 + center[0]
        v = v * r2 + center[1]
        e.append((u,v,z))

    return e

def ellipseMesh(vertices, center, r1, r2, z, reverse=False):
    verts = []
    edgesPerSide = vertices / 4

    # create a rectangular matrix of vertices mapped to circular disc coordinates (UV)
    # https://stackoverflow.com/questions/13211595/how-can-i-convert-coordinates-on-a-circle-to-coordinates-on-a-square
    for row in range(edgesPerSide+1):
        for col in range(edgesPerSide+1):
            # x, y is between -1 and 1
            x = 1.0 * col / edgesPerSide * 2 - 1
            y = 1.0 * row / edgesPerSide * 2 - 1
            u = x * math.sqrt(1.0 - 0.5 * (y * y))
            v = y * math.sqrt(1.0 - 0.5 * (x * x))
            # convert to actual unit
            u = u * r1 + center[0]
            v = v * r2 + center[1]
            verts.append((u,v,z))

    vertLen = len(verts)
    centerIndex = int(vertLen / 2)
    centerRow = edgesPerSide / 2
    centerCol = edgesPerSide/ 2

    # start with one point at the center
    edgeLoops = [[verts[centerIndex]]]

    # add loops until we reach outer loop
    edges = 2
    while edges <= edgesPerSide:
        edgeLoop = []
        r = edges/2
        # add top
        for i in range(edges):
            row = centerRow - r
            col = centerCol + lerp(-r, r, 1.0 * i / edges)
            i = int(row*(edgesPerSide+1) + col)
            edgeLoop.append(verts[i])

        # add right
        for i in range(edges):
            row = centerRow + lerp(-r, r, 1.0 * i / edges)
            col = centerCol + r
            i = int(row*(edgesPerSide+1) + col)
            edgeLoop.append(verts[i])

        # add bottom
        for i in range(edges):
            row = centerRow + r
            col = centerCol + lerp(r, -r, 1.0 * i / edges)
            i = int(row*(edgesPerSide+1) + col)
            edgeLoop.append(verts[i])

        # add left
        for i in range(edges):
            row = centerRow + lerp(r, -r, 1.0 * i / edges)
            col = centerCol - r
            i = int(row*(edgesPerSide+1) + col)
            edgeLoop.append(verts[i])

        # add edges
        edgeLoops.append(edgeLoop)
        edges += 2

    if reverse:
        edgeLoops = reversed(edgeLoops)

    return edgeLoops

def lerp(a, b, mu):
    return (b-a) * mu + a

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

def savitzkyGolay(y, window_size, order=3, deriv=0, rate=1):
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    y = np.array(y)
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * math.factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')

def translatePoint(p, degrees, distance):
    radians = math.radians(degrees)
    x2 = p[0] + distance * math.cos(radians)
    y2 = p[1] + distance * math.sin(radians)
    return (x2, y2)

class Mesh:

    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces = []
        self.edgeLoops = []

    def addEdgeLoop(self, loop):
        self.edgeLoops.append(loop)

    def addEdgeLoops(self, loops):
        for loop in loops:
            self.addEdgeLoop(loop)

    def joinEdgeLoops(self, loopA, loopB, indexOffset):
        faces = []
        aLen = len(loopA)
        bLen = len(loopB)

        # number of vertices differ
        if abs(bLen - aLen) > 0:

            # assume we're going from bigger to smaller
            bigger = aLen
            smaller = bLen
            biggerOffset = indexOffset
            smallerOffset = indexOffset + aLen

            # going from smaller to bigger
            if smaller > bigger:
                bigger = bLen
                smaller = aLen
                smallerOffset = indexOffset
                biggerOffset = indexOffset + aLen

            edgesPerSide = bigger / 4

            for i in range(bigger-4):
                offset = abs(i-1) / (edgesPerSide-1)
                v1 = i + offset + biggerOffset
                v2 = v1 + 1
                v3 = i + offset - offset * 2 + smallerOffset
                v4 = v3 - 1

                # special case for first
                if i==0:
                    v1 = biggerOffset
                    v2 = v1 + 1
                    v3 = smallerOffset
                    v4 = bigger - 1 + biggerOffset

                # special case for reach corner face
                elif i % (edgesPerSide-1) == 0:
                    v3 = v2 + 1

                # special case for last
                elif i==(bigger-5):
                    v3 = smallerOffset

                faces.append((v1, v2, v3, v4))

        # equal number of vertices
        else:
            for i in range(aLen):
                v1 = i
                v2 = i + 1
                v3 = i + 1 + aLen
                v4 = i + aLen
                if v2 >= aLen:
                    v2 = 0
                    v3 = aLen
                faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))

        self.faces += faces

    # join all the edge loop together
    def processEdgeloops(self):
        indexOffset = 0

        for i, edgeLoop in enumerate(self.edgeLoops):
            # add loop's vertices
            self.verts += edgeLoop

            # if this is the first edge loop and it's a quad, add it's face
            if i == 0 and len(edgeLoop) == 4:
                self.faces.append(range(4))

            elif i > 0:
                prev = self.edgeLoops[i-1]
                self.joinEdgeLoops(prev, edgeLoop, indexOffset)
                indexOffset += len(prev)

        # if the last edge loop is a quad, add it's face
        if len(self.edgeLoops[-1]) == 4:
            self.faces.append([(i+indexOffset) for i in range(4)])

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

# made the data quadratic
for i, d in enumerate(displaceData):
    y = d[1] * 2
    ay = abs(y)
    y2 = ay**2
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

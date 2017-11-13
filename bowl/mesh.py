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
DATA_FILE = "data/gotNS.json"

BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 3 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 3
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
WIDTH = 115.0
HEIGHT = 50.0
BASE_WIDTH = 55.0
BASE_HEIGHT = 9.0
EDGE_RADIUS = 4.0
THICKNESS = 4.6
MAX_WAVE = 3.0

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
outerStart = 5
outerEnd = 8
innerStart = 9
innerEnd = 11

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
print "Interpolating data..."
data = []
targetEdgeCount = bowlLen * 2**SUBDIVIDE_Y
with open(DATA_FILE) as f:
    data = json.load(f)
data = [tuple(d) for d in data]
splinedData = bspline(data, n=targetEdgeCount, degree=3, periodic=False)

# interpolate bowl data
widths = [d[0] for d in BOWL]
heights = [d[1] for d in BOWL]
xs = [1.0 * i / (bowlLen-1)  for i, d in enumerate(BOWL)]
splinedWidths = bspline(list(zip(xs, widths)), n=targetEdgeCount, degree=3, periodic=False)
splinedHeights = bspline(list(zip(xs, heights)), n=targetEdgeCount, degree=3, periodic=False)

# build the mesh
mesh = Mesh()

outerStart = int(round(1.0 * outerStart / bowlLen * targetEdgeCount))
outerEnd = int(round(1.0 * outerEnd / bowlLen * targetEdgeCount))
innerStart = int(round(1.0 * innerStart / bowlLen * targetEdgeCount))
innerEnd = int(round(1.0 * innerEnd / bowlLen * targetEdgeCount))

for i in range(targetEdgeCount):
    width = splinedWidths[i][1]
    z = splinedHeights[i][1]
    delta = 0
    r = width * 0.5 + delta
    p = -1
    outer = True

    if outerStart <= i <= outerEnd:
        p = norm(i, outerStart, outerEnd) * 0.5

    elif innerStart <= i <= innerEnd:
        outer = False
        p = norm(i, innerStart, innerEnd) * 0.5 + 0.5

    if p >= 0:
        j = int(round(p * (targetEdgeCount-1)))
        delta = splinedData[j][1] * MAX_WAVE

        # TODO: get the normal of the edge and offset it with delta

    if i <= 0:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoops(loops)
    elif i >= targetEdgeCount-1:
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

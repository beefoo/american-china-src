# -*- coding: utf-8 -*-

import json
import math
from PIL import Image, ImageDraw
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 5

# cup config in cm
EDGES_PER_SIDE = 4 # 4, 128, 256, needs to be power of 2, needs to be high-res for letter displacement
VERTICES_PER_EDGE_LOOP = EDGES_PER_SIDE * 4
TOP_WIDTH = 8.2
HEIGHT = 8.2
EDGE_RADIUS = 0.25
TOP_CORNER_RADIUS = 1.2
THICKNESS = 0.6

# relative widths
BASE_OUTER_DIAMETER = 0.5 * TOP_WIDTH
BASE_INNER_DIAMETER = 0.667 * BASE_OUTER_DIAMETER
BASE_INSET_DIAMETER = 0.8 * BASE_INNER_DIAMETER
BODY_DIAMETER = 1.0 * TOP_WIDTH
NECK_DIAMETER = 0.9 * TOP_WIDTH
BODY_INNER_DIAMETER = NECK_DIAMETER - THICKNESS * 2
INNER_BASE_DIAMETER = BODY_INNER_DIAMETER * 0.5

# relative heights
BASE_INSET_HEIGHT = 0.25
BASE_HEIGHT = 0.1 * HEIGHT
BODY_HEIGHT = 0.167 * HEIGHT
NECK_HEIGHT = 0.85 * HEIGHT
INNER_BASE_HEIGHT = BASE_HEIGHT + THICKNESS
INNER_BODY_HEIGHT = BODY_HEIGHT

# config image data
CHARS_LINES = 4
CHARS_PER_LINE = 7
IMAGE_SCALE = 1.0

print "Max height for text: %scm" % (NECK_HEIGHT - BASE_HEIGHT - THICKNESS)
print "Max width for text: %scm" % (BODY_DIAMETER - THICKNESS * 2)

def circle(vertices, center, radius, z):
    angleStart = -135
    angleStep = 360.0 / vertices
    c = []
    for i in range(vertices):
        angle = angleStart + angleStep * i
        p = translatePoint(center, angle, radius)
        c.append((p[0], p[1], z))
    return c

def circleMesh(vertices, center, radius, z, reverse=False):
    verts = []
    edgesPerSide = vertices / 4

    # create a square matrix of vertices mapped to circular disc coordinates (UV)
    # https://stackoverflow.com/questions/13211595/how-can-i-convert-coordinates-on-a-circle-to-coordinates-on-a-square
    for row in range(edgesPerSide+1):
        for col in range(edgesPerSide+1):
            # x, y is between -1 and 1
            x = 1.0 * col / edgesPerSide * 2 - 1
            y = 1.0 * row / edgesPerSide * 2 - 1
            u = x * math.sqrt(1.0 - 0.5 * (y * y))
            v = y * math.sqrt(1.0 - 0.5 * (x * x))
            # convert to actual unit
            u = u * radius + center[0]
            v = v * radius + center[1]
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

def distance(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1) + (z2-z1)*(z2-z1))

def lerp(a, b, mu):
    return (b-a) * mu + a

# http://paulbourke.net/miscellaneous/interpolation/
def lerpCos(a, b, mu):
   mu2 = (1 - math.cos(mu * math.pi)) / 2.0
   return (y1 * (1 - mu2) + y2 * mu2)

# http://paulbourke.net/miscellaneous/interpolation/
def lerpCubic(a, b, c, d, mu):
   mu2 = mu * mu
   a0 = d - c - a + b
   a1 = a - b - a0
   a2 = c - a
   a3 = b
   return (a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3)

def lerpEdge(r1, r2, amt):
    lerpedEdge = []
    for i, t in enumerate(r1):
        p = []
        for j in range(3):
            pp = lerp(t[j], r2[i][j], amt)
            p.append(pp)
        lerpedEdge.append(tuple(p))
    return lerpedEdge

def roundedSquare(edgesPerSide, c, w, z, r):
    square = []

    hw = w * 0.5
    verticesAdd = edgesPerSide - 3

    # top side
    y = c[1] - hw
    x0 = c[0] - hw
    x0c = x0 + r
    x1c = c[0] + hw - r
    square += [(x0, y, z), (x0c, y, z)]
    for i in range(verticesAdd):
        x = lerp(x0c, x1c, 1.0*(i+1)/(verticesAdd+1))
        square.append((x, y, z))
    square.append((x1c, y, z))

    # right side
    x = c[0] + hw
    y0 = c[1] - hw
    y0c = y0 + r
    y1c = c[1] + hw - r
    square += [(x, y0, z), (x, y0c, z)]
    for i in range(verticesAdd):
        y = lerp(y0c, y1c, 1.0*(i+1)/(verticesAdd+1))
        square.append((x, y, z))
    square.append((x, y1c, z))

    # bottom side
    y = c[1] + hw
    x0 = c[0] + hw
    x0c = x0 - r
    x1c = c[0] - hw + r
    square += [(x0, y, z), (x0c, y, z)]
    for i in range(verticesAdd):
        x = lerp(x0c, x1c, 1.0*(i+1)/(verticesAdd+1))
        square.append((x, y, z))
    square.append((x1c, y, z))

    # left side
    x = c[0] - hw
    y0 = c[1]+ hw
    y0c = y0 - r
    y1c = c[1] - hw + r
    square += [(x, y0, z), (x, y0c, z)]
    for i in range(verticesAdd):
        y = lerp(y0c, y1c, 1.0*(i+1)/(verticesAdd+1))
        square.append((x, y, z))
    square.append((x, y1c, z))

    return square

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

def transform(vList, scale, translate):
    transformed = []
    # get minimums to offset to zero
    oX = min([v[0] for v in vList])
    oY = min([v[1] for v in vList])
    oZ = min([v[2] for v in vList])
    for v in vList:
        x = (v[0]-oX) * scale[0] + oX + translate[0]
        y = (v[1]-oX) * scale[1] + oY + translate[1]
        z = (v[2]-oZ) * scale[2] + oZ + translate[2]
        transformed.append((x, y, z))
    return transformed

# north => -90 degrees or 270 degrees
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

        self.queueEdgeAfter = False

    def addEdgeLoop(self, edge, edgeBefore=False, edgeAfter=False):
        # add an edge loop after the previous one
        if self.queueEdgeAfter is not False:
            self.addEdgeLoopHelper(edge, self.queueEdgeAfter, True)
            self.queueEdgeAfter = False
        # add an edge loop before the next one
        if edgeBefore is not False:
            self.addEdgeLoopHelper(edge, edgeBefore, False)
        # add an edge loop after the next one
        if edgeAfter is not False:
            self.queueEdgeAfter = edgeAfter

        self.edgeLoops.append(edge)

    def addEdgeLoops(self, edges):
        for edge in edges:
            self.addEdgeLoop(edge)

    def addEdgeLoopHelper(self, nextEdge, amount, after=True):
        prevEdge = self.edgeLoops[-1]
        d = distance(prevEdge[0], nextEdge[0])
        lerpAmount = amount / d
        if lerpAmount >= 0.5:
            return False
        if not after:
            lerpAmount = 1.0 - lerpAmount
        edge = lerpEdge(prevEdge, nextEdge, lerpAmount)
        self.edgeLoops.append(edge)

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

class Vector:

    def __init__(self, t):
        self.t = t

    def add(self, t2):
        return (self.t[0]+t2[0], self.t[1]+t2[1], self.t[2]+t2[2])

# determine center
halfWidth = TOP_WIDTH * 0.5
CENTER = (halfWidth, halfWidth, 0)

# init mesh
mesh = Mesh()

# create base inset as a circle which will be the first face
baseInset = circleMesh(VERTICES_PER_EDGE_LOOP, CENTER, BASE_INSET_DIAMETER * 0.5, BASE_INSET_HEIGHT)
mesh.addEdgeLoops(baseInset)

# move down and out to base inner
baseInner = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_INNER_DIAMETER * 0.5, 0)
mesh.addEdgeLoop(baseInner, False, EDGE_RADIUS)

# move out to base outer
baseOuter = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_OUTER_DIAMETER * 0.5, 0)
mesh.addEdgeLoop(baseOuter, EDGE_RADIUS, EDGE_RADIUS)

# move up to base
base = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_OUTER_DIAMETER * 0.5, BASE_HEIGHT)
mesh.addEdgeLoop(base, EDGE_RADIUS, EDGE_RADIUS)

# move up and out (lerp) to body
body = circle(VERTICES_PER_EDGE_LOOP, CENTER, BODY_DIAMETER * 0.5, BODY_HEIGHT)
mesh.addEdgeLoop(body)

# move up and out (lerp) to neck
neck = roundedSquare(EDGES_PER_SIDE, CENTER, NECK_DIAMETER, NECK_HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(neck)

# move up and out (lerp) to top
top = roundedSquare(EDGES_PER_SIDE, CENTER, TOP_WIDTH, HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(top, EDGE_RADIUS)

# move in to inner top
innerTop = roundedSquare(EDGES_PER_SIDE, CENTER, TOP_WIDTH-THICKNESS*2, HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(innerTop, False, EDGE_RADIUS)

# move in and down to inner neck
innerNeck = roundedSquare(EDGES_PER_SIDE, CENTER, NECK_DIAMETER-THICKNESS*2, NECK_HEIGHT, TOP_CORNER_RADIUS)

# move in and down to inner body
innerBody = circle(VERTICES_PER_EDGE_LOOP, CENTER, BODY_INNER_DIAMETER * 0.5, INNER_BODY_HEIGHT)

# retrieve image data
imageData = []
imgW = None
imgH = None
for i in range(CHARS_LINES):
    for j in range(CHARS_PER_LINE):
        filename = "chars/char_%s-%s.png" % (i+1, j+1)
        im = Image.open(filename)
        imageData.append(list(im.getdata()))
        if imgW is None:
            imgW, imgH = im.size

# lerp from neck to body
for i in range(EDGES_PER_SIDE):
    amt = 1.0 * i / (EDGES_PER_SIDE-1)
    edgeLoop = lerpEdge(innerNeck, innerBody, amt)
    mesh.addEdgeLoop(edgeLoop)

# move in and down to inner base
innerBase = circleMesh(VERTICES_PER_EDGE_LOOP, CENTER, INNER_BASE_DIAMETER * 0.5, INNER_BASE_HEIGHT, True)
mesh.addEdgeLoops(innerBase)

# create faces from edges
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Cup",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": [-halfWidth, -halfWidth, 0],
        "flipFaces": range(EDGES_PER_SIDE * EDGES_PER_SIDE)
    }
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

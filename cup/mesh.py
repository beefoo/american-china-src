# -*- coding: utf-8 -*-

import json
import math
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 3

# cup config in cm
VERTICES_PER_EDGE_LOOP = 16
TOP_WIDTH = 8.2
HEIGHT = 6.0
EDGE_RADIUS = 0.2
TOP_CORNER_RADIUS = 1.0

BASE_OUTER_DIAMETER = 0.5 * TOP_WIDTH
BASE_INNER_DIAMETER = 0.5 * BASE_OUTER_DIAMETER
BASE_INSET_DIAMETER = 0.8 * BASE_INNER_DIAMETER
BODY_DIAMETER = 1.0 * TOP_WIDTH
NECK_DIAMETER = 0.92 * TOP_WIDTH

BASE_INSET_HEIGHT = 0.3
BASE_HEIGHT = 0.1 * HEIGHT
BODY_HEIGHT = 0.167 * HEIGHT
NECK_HEIGHT = 0.8 * HEIGHT

def circle(vertices, center, radius, z):
    angleStart = -135
    angleStep = 360.0 / vertices
    c = []
    for i in range(vertices):
        angle = angleStart + angleStep * i
        p = translatePoint(center, angle, radius)
        c.append((p[0], p[1], z))
    return c

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

def roundedSquare(c, w, z, r):
    hw = w * 0.5
    baseOrigin = (c[0]-hw, c[1]-hw, z)
    bo = Vector(baseOrigin)
    square = [
        bo.t, bo.add((r, 0, 0)), bo.add((hw, 0, 0)), bo.add((w-r, 0, 0)),
        bo.add((w, 0, 0)), bo.add((w, r, 0)), bo.add((w, hw, 0)), bo.add((w, w-r, 0)),
        bo.add((w, w, 0)), bo.add((w-r, w, 0)), bo.add((hw, w, 0)), bo.add((r, w, 0)),
        bo.add((0, w, 0)), bo.add((0, w-r, 0)), bo.add((0, hw, 0)), bo.add((0, r, 0))
    ]
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

def squareToCircle(points):
    uv = []
    for p in points:
        x = p[0]
        y = p[1]
        z = p[2]
        u = x * math.sqrt( 1 - y * y * 0.5 )
        v = y * math.sqrt( 1 - x * x * 0.5 )
        uv.append((u,v,z))
    return uv

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

    def getFacesFromEdgeLoops(self, indexOffset, verticesPerEdgeLoop):
        faces = []
        for i in range(verticesPerEdgeLoop):
            v1 = i
            v2 = i + 1
            v3 = i + 1 + verticesPerEdgeLoop
            v4 = i + verticesPerEdgeLoop
            if v2 >= verticesPerEdgeLoop:
                v2 = 0
                v3 = verticesPerEdgeLoop
            faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))
        return faces

    # join all the edge loop together
    def processEdgeloops(self):
        verticesPerEdgeLoop = len(self.edgeLoops[0])
        # add the first edge's face
        self.faces.append(range(verticesPerEdgeLoop))
        # add faces for subsequent edges
        indexOffset = 0
        for i, edgeLoop in enumerate(self.edgeLoops):
            # add vertices
            self.verts += edgeLoop
            if i > 0:
                # add faces
                faces = self.getFacesFromEdgeLoops(indexOffset, verticesPerEdgeLoop)
                self.faces += faces
                indexOffset += verticesPerEdgeLoop

class Vector:

    def __init__(self, t):
        self.t = t

    def add(self, t2):
        return (self.t[0]+t2[0], self.t[1]+t2[1], self.t[2]+t2[2])

# determine center
halfWidth = TOP_WIDTH
CENTER = (halfWidth, halfWidth, 0)

# init mesh
mesh = Mesh()

# create base inset as a circle which will be the first face
baseInset = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_INSET_DIAMETER * 0.5, BASE_INSET_HEIGHT)
mesh.addEdgeLoop(baseInset)

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
neck = roundedSquare(CENTER, NECK_DIAMETER, NECK_HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(neck)

# move up and out (lerp) to top
top = roundedSquare(CENTER, TOP_WIDTH, HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(top, EDGE_RADIUS)

# solidify (duplicate, scale, translate, join)

# create faces from edges
mesh.processEdgeloops()

# save data
data = [
    {"name": "Cup", "verts": roundP(mesh.verts, PRECISION), "edges": [], "faces": mesh.faces, "location": [-halfWidth, -halfWidth, 0]}
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

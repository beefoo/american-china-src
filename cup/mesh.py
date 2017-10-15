# -*- coding: utf-8 -*-

import json
import math
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 3

# cup config in cm
VERTICES_PER_EDGE = 16
TOP_WIDTH = 8.2
HEIGHT = 6.0
EDGE_LOOP = 0.2
TOP_CORNER_RADIUS = 1.0

BASE_OUTER_DIAMETER = 0.4 * TOP_WIDTH
BASE_INNER_DIAMETER = 0.5 * BASE_OUTER_DIAMETER
BASE_INSET_DIAMETER = 0.8 * BASE_INNER_DIAMETER
BODY_DIAMETER = 0.6 * TOP_WIDTH
NECK_DIAMETER = 0.8 * TOP_WIDTH

BASE_INSET_HEIGHT = 0.3
BASE_HEIGHT = 0.1 * HEIGHT
BODY_HEIGHT = 0.2 * HEIGHT
NECK_HEIGHT = 0.8 * HEIGHT

def circle(vertices, center, radius, z):
    angleStart = -135
    angleStep = 360.0 / vertices
    c = []
    for i in range(VERTICES_PER_EDGE):
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

    def addEdge(self, edge, edgeLoopAfterPrevious=False, edgeLoopBeforeNext=False):
        # add an edge loop after previous edge
        if edgeLoopAfterPrevious is not False:
            self.addEdgeLoop(edge, edgeLoopAfterPrevious, True)
        # add an edge loop before adding the next one
        if edgeLoopBeforeNext is not False:
            self.addEdgeLoop(edge, edgeLoopBeforeNext, False)
        self.verts += edge
        self.edges.append(edge)

    def addEdgeLoop(self, nextEdge, amount, after=True):
        prevEdge = self.edges[-1]
        d = distance(prevEdge[0], nextEdge[0])
        lerpAmount = amount / d
        if not after:
            lerpAmount = 1.0 - lerpAmount
        edge = lerpEdge(prevEdge, nextEdge, lerpAmount)
        self.verts += edge
        self.edges.append(edge)

    def getFaces(self, indexOffset, verticesPerEdge):
        faces = []
        for i in range(verticesPerEdge):
            v1 = i
            v2 = i + 1
            v3 = i + 1 + verticesPerEdge
            v4 = i + verticesPerEdge
            if v2 >= verticesPerEdge:
                v2 = 0
                v3 = verticesPerEdge
            faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))
        return faces

    # join all the edges together
    def makeFaces(self):
        verticesPerEdge = len(self.edges[0])
        # add the first edge's face
        self.faces.append(range(verticesPerEdge))
        # add faces for subsequent edges
        indexOffset = 0
        for i, edge in enumerate(self.edges):
            if i > 0:
                faces = self.getFaces(indexOffset, verticesPerEdge)
                self.faces += faces
                indexOffset += verticesPerEdge

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
baseInset = circle(VERTICES_PER_EDGE, CENTER, BASE_INSET_DIAMETER * 0.5, BASE_INSET_HEIGHT)
mesh.addEdge(baseInset)

# move down and out to base inner
baseInner = circle(VERTICES_PER_EDGE, CENTER, BASE_INNER_DIAMETER * 0.5, 0)
mesh.addEdge(baseInner)

# move out to base outer
baseOuter = circle(VERTICES_PER_EDGE, CENTER, BASE_OUTER_DIAMETER * 0.5, 0)
mesh.addEdge(baseOuter, EDGE_LOOP, EDGE_LOOP)

# move up to base
base = circle(VERTICES_PER_EDGE, CENTER, BASE_OUTER_DIAMETER * 0.5, BASE_HEIGHT)
mesh.addEdge(base, EDGE_LOOP, EDGE_LOOP)

# determine top edge so we can lerp to it
top = roundedSquare(CENTER, TOP_WIDTH, HEIGHT, TOP_CORNER_RADIUS)

# move up and out (lerp) to body

# move up and out (lerp) to neck

# move up and out (lerp) to top

# solidify (duplicate, scale, translate, join)

# fix normals

# create faces from edges
mesh.makeFaces()

# save data
data = [
    {"name": "Cup", "verts": roundP(mesh.verts, PRECISION), "edges": [], "faces": mesh.faces, "location": [-halfWidth, -halfWidth, 0]}
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

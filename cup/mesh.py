# -*- coding: utf-8 -*-

import json
import math
import sys

OUTPUT_FILE = "mesh.json"
PRECISION = 3

# config
CFG = {
    "diameter": 7.0,            # in cm
    "height": 8.0,              # in cm
    "thickness": 0.5,           # in cm
    "edge": 0.2,                # in cm
    "baseDiameter": 0.6         # percent of diameter
}

def lerp(a, b, amt):
    return (b-a) * amt + a

def lerpRow(r1, r2, amt):
    lerpedRow = []
    for i, t in enumerate(r1):
        p = []
        for j in range(3):
            pp = lerp(t[j], r2[i][j], amt)
            p.append(pp)
        lerpedRow.append(tuple(p))
    return lerpedRow

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

    def __init__(self, verts):
        self.verticesPerRow = len(verts)
        self.verts = verts[:]
        self.edges = []
        self.faces = [range(self.verticesPerRow)]

        self.currentRow = verts[:]
        self.indexOffset = 0

    def addEdges(self, edges):
        self.edges += edges

    def addFaces(self, faces):
        self.faces += faces

    def addRow(self, row):
        nextRow = row[:]
        self.verts += nextRow
        self.faces += self.getFaces()
        self.currentRow = nextRow[:]
        self.indexOffset += self.verticesPerRow

    def addVerts(self, verts):
        self.verts += verts

    def getFaces(self):
        indexOffset = self.indexOffset
        rLen = self.verticesPerRow
        faces = []
        for i in range(rLen):
            v1 = i
            v2 = i + 1
            v3 = i + 1 + rLen
            v4 = i + rLen
            if v2 >= rLen:
                v2 = 0
                v3 = rLen
            faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))
        return faces

class Vector:

    def __init__(self, t):
        self.t = t

    def add(self, t2):
        return (self.t[0]+t2[0], self.t[1]+t2[1], self.t[2]+t2[2])

# determine center
radius = CFG["diameter"] * 0.5
c = (radius, radius, 0)

# define start shape: a square base with 16 vertices
bd = CFG["baseDiameter"] * CFG["diameter"]
halfBd = bd * 0.5
baseOrigin = (c[0]-halfBd, c[1]-halfBd, 0)
bo = Vector(baseOrigin)
edge = CFG["edge"]
vRowStart = [
    bo.t, bo.add((edge, 0, 0)), bo.add((halfBd, 0, 0)), bo.add((bd-edge, 0, 0)),
    bo.add((bd, 0, 0)), bo.add((bd, edge, 0)), bo.add((bd, halfBd, 0)), bo.add((bd, bd-edge, 0)),
    bo.add((bd, bd, 0)), bo.add((bd-edge, bd, 0)), bo.add((halfBd, bd, 0)), bo.add((edge, bd, 0)),
    bo.add((0, bd, 0)), bo.add((0, bd-edge, 0)), bo.add((0, halfBd, 0)), bo.add((0, edge, 0))
]
verticesPerRow = len(vRowStart)

# define end shape: a circle with 16 vertices
angleStart = -135
angleStep = 360.0 / verticesPerRow
height = CFG["height"]
vRowEnd = []
for i in range(verticesPerRow):
    angle = angleStart + angleStep * i
    p = translatePoint(c, angle, radius)
    vRowEnd.append((p[0], p[1], height))

# inset the starting row to avoid n-gon weirdness
insetScale = 0.5
insetDiameter = bd * insetScale
insetOffset = (bd - insetDiameter) * 0.5
vRowBaseInset = transform(vRowStart, (insetScale, insetScale, 1.0), (insetOffset, insetOffset, 0))

# init mesh
# model will start at base inset, then move out and up
mesh = Mesh(vRowBaseInset)

# add base inner edge
innerDiameter = bd - edge * 2
innerScale = innerDiameter / bd
vRowBaseInner = transform(vRowStart, (innerScale, innerScale, 1.0), (edge, edge, 0))
mesh.addRow(vRowBaseInner)

# add base row
mesh.addRow(vRowStart)

# add base outer edge
lerpAmount = edge / height
vRowBaseOuter = lerpRow(vRowStart, vRowEnd, lerpAmount)
mesh.addRow(vRowBaseOuter)

# add top outer edge
lerpAmount = (height - edge) / height
vRowTopOuter = lerpRow(vRowStart, vRowEnd, lerpAmount)
mesh.addRow(vRowTopOuter)

# add top
mesh.addRow(vRowEnd)

# save data
data = [
    {"name": "Cup", "verts": roundP(mesh.verts, PRECISION), "edges": [], "faces": mesh.faces, "location": [-radius, -radius, 0]}
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

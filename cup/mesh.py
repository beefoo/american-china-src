# -*- coding: utf-8 -*-

import json

OUTPUT_FILE = "mesh.json"
PRECISION = 3

class Vector:

    def __init__(self, t):
        self.t = t

    def add(self, t2):
        return (self.t[0]+t2[0], self.t[1]+t2[1], self.t[2]+t2[2])

def getFaces(row1, row2, indexOffset=0):
    rLen = len(row1)
    faces = []
    for i, t in enumerate(row1):
        v1 = i
        v2 = i + 1
        v3 = i + 1 + rLen
        v4 = i + rLen
        if v2 >= rLen:
            v2 = 0
            v3 = rLen
        faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))
    return faces

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

def transform(vList, scale, translate):
    transformed = []
    for v in vList:
        t = (v[0] * scale[0] + translate[0], v[1] * scale[1] + translate[1], v[2] * scale[2] + translate[2])
        transformed.append(t)
    return transformed

# config
CFG = {
    "diameter": 7.0,            # in cm
    "height": 8.0,              # in cm
    "thickness": 0.5,           # in cm
    "edge": 0.1,                # in cm
    "baseDiameter": 0.8         # percent of diameter
}

# init empty vertices and faces
verts = []
faces = []

# determine center
radius = CFG["diameter"] * 0.5
c = (radius, radius, 0)

# define start shape
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

# inset the starting row to avoid n-gon weirdness
insetDiameter = bd - edge * 2
insetScale = insetDiameter / bd
vRowStartInset = transform(vRowStart, (insetScale, insetScale, 1.0), (edge, edge, 0))

# model will start at base inset, then move out and up
verts += vRowStartInset
verts += vRowStart

# the first base is the base inset
faces.append(range(len(vRowStartInset)))

# connect base inset to base
faces += getFaces(vRowStartInset, vRowStart, 0)

vRowEnd = []

# save data
data = [
    {"name": "Cup", "verts": roundP(verts, PRECISION), "edges": [], "faces": faces, "location": [-radius, -radius, 0]}
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

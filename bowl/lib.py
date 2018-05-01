# -*- coding: utf-8 -*-

import math
import numpy as np
from scipy import interpolate

def angleBetweenPoints(p1, p2):
    deltaX = p2[0] - p1[0]
    deltaY = p2[1] - p1[1]
    rad = math.atan2(deltaY, deltaX)
    return math.degrees(rad)

def bspline(cv, n=1000, degree=3, periodic=False):
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

def bsplineLerp(plist, mu):
    count = 10000
    spl = bspline(plist, n=count)
    i = int(round(mu*(count-1)))
    return tuple(spl[i])

def circle(vertices, center, r, z):
    angle = 360.0 / vertices

    result = []
    for i in range(vertices):
        a = i * angle
        p = translatePoint(center, a, r)
        result.append((p[0], p[1], z))

    return result

def lerp(a, b, mu):
    return (b-a) * mu + a

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def normalBetweenPoints(p1, p2):
    angle = angleBetweenPoints(p1, p2)
    return angle + 90

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

def translatePoint(p, degrees, distance):
    radians = math.radians(degrees)
    x2 = p[0] + distance * math.cos(radians)
    y2 = p[1] + distance * math.sin(radians)
    return (x2, y2)



def displacePoint(p, triangle, displace, direction="out"):
    p0 = p
    p1, p2, p3 = triangle

    # normalize Z
    deltaZBefore = p1[2] - p0[2]
    deltaZAfter = p3[2] - p0[2]
    p0 = (p0[0], p0[1], 0)
    p1 = (p1[0], p1[1], deltaZBefore)
    p2 = (p2[0], p2[1], deltaZBefore)
    p3 = (p3[0], p3[1], deltaZAfter)

    # calculate normal of triangle made from points above, below, and adjacent
    # https://stackoverflow.com/questions/19350792/calculate-normal-of-a-single-triangle-in-3d-space
    p1 = np.array(p1)
    p2 = np.array(p2)
    p3 = np.array(p3)

    # if we want normals to go away from center
    u = p3 - p1
    v = p2 - p1

    # if we want normals to go towards center
    if direction == "in":
        u = p2 - p1
        v = p3 - p1

    # cross product is the normal
    n = np.cross(u, v)

    # calculate distance bewteen point and normal
    # https://math.stackexchange.com/questions/105400/linear-interpolation-in-3-dimensions
    p0 = np.array(p0)
    p1 = n
    dist = p1 - p0
    ndist = np.linalg.norm(dist)
    pd = p0 - (displace / ndist) * dist
    pd = tuple(pd)
    pd = (pd[0], pd[1], pd[2] + p[2])
    return pd

def getVerticesFromFace(bl, br, tr, tl, displaceAmount):
    verts = []
    mu = 0.125

    # move points in towards center of face
    v1 = (lerp(bl[0], tr[0], mu), lerp(bl[1], tr[1], mu), lerp(bl[2], tr[2], mu))
    v2 = (lerp(br[0], tl[0], mu), lerp(br[1], tl[1], mu), lerp(br[2], tl[2], mu))
    v3 = (lerp(tr[0], bl[0], mu), lerp(tr[1], bl[1], mu), lerp(tr[2], bl[2], mu))
    v4 = (lerp(tl[0], br[0], mu), lerp(tl[1], br[1], mu), lerp(tl[2], br[2], mu))

    # move points out
    tc = (lerp(tl[0], tr[0], 0.5), lerp(tl[1], tr[1], 0.5), lerp(tl[2], tr[2], 0.5))
    v5 = displacePoint(v1, (bl, br, tc), displaceAmount)
    v6 = displacePoint(v2, (bl, br, tc), displaceAmount)
    v7 = displacePoint(v3, (bl, br, tc), displaceAmount)
    v8 = displacePoint(v4, (bl, br, tc), displaceAmount)

    # move points in torwards center of face
    mu = 0.275
    v5 = (lerp(v5[0], v7[0], mu), lerp(v5[1], v7[1], mu), lerp(v5[2], v7[2], mu))
    v6 = (lerp(v6[0], v8[0], mu), lerp(v6[1], v8[1], mu), lerp(v6[2], v8[2], mu))
    v7 = (lerp(v7[0], v5[0], mu), lerp(v7[1], v5[1], mu), lerp(v7[2], v5[2], mu))
    v8 = (lerp(v8[0], v6[0], mu), lerp(v8[1], v6[1], mu), lerp(v8[2], v6[2], mu))

    verts = [v1, v2, v3, v4, v5, v6, v7, v8]

    return verts

class Mesh:

    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces = []
        self.edgeLoops = []
        self.displaceLoops = []

    def addDisplaceLoop(self, value):
        self.displaceLoops.append(value)

    def addEdgeLoop(self, loop):
        self.edgeLoops.append(loop)

    def addEdgeLoops(self, loops):
        for loop in loops:
            self.addEdgeLoop(loop)

    def closeEdgeLoop(self, loop, indexOffset, end=False):
        faces = []
        loopLen = len(loop)
        for i, v in enumerate(loop):
            a = i
            b = i+1
            if b >= loopLen:
                b = 0
            if end:
                faces.append((indexOffset+loopLen, indexOffset+a, indexOffset+b))
            else:
                faces.append((indexOffset, indexOffset+a+1, indexOffset+b+1))
        self.faces += faces

    def displaceEdgeLoops(self, loopA, loopB, indexOffset, amount):
        faces = []
        aLen = len(loopA)
        bLen = len(loopB)

        if aLen != bLen:
            print "Warning: length mismatch"

        initialIndexOffset = len(self.verts)

        # assume equal number of vertices
        for i in range(aLen):
            v1 = i
            v2 = i + 1
            v3 = i + 1 + aLen
            v4 = i + aLen
            if v2 >= aLen:
                v2 = 0
                v3 = aLen
            v1 += indexOffset
            v2 += indexOffset
            v3 += indexOffset
            v4 += indexOffset
            bl = self.verts[v1]
            br = self.verts[v2]
            tr = self.verts[v3]
            tl = self.verts[v4]
            newVerts = getVerticesFromFace(bl, br, tr, tl, amount)
            self.verts += newVerts

            u = initialIndexOffset
            self.faces.append((v1, v2, u+1, u))
            self.faces.append((v2, v3, u+2, u+1))
            self.faces.append((v3, v4, u+3, u+2))
            self.faces.append((v4, v1, u, u+3))
            v = u + 4
            self.faces.append((u, u+1, v+1, v))
            self.faces.append((u+1, u+2, v+2, v+1))
            self.faces.append((u+2, u+3, v+3, v+2))
            self.faces.append((u+3, u, v, v+3))
            self.faces.append((v, v+1, v+2, v+3))

            initialIndexOffset = len(self.verts)

    def getVertexCount(self):
        return sum([len(l) for l in self.edgeLoops])

    def joinEdgeLoops(self, loopA, loopB, indexOffset):
        faces = []
        aLen = len(loopA)
        bLen = len(loopB)

        if aLen != bLen:
            print "Warning: length mismatch"

        # assume equal number of vertices
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

            displace = self.displaceLoops[i]

            # add loop's vertices
            self.verts += edgeLoop

            # skip start
            if i <= 0:
                continue

            prev = self.edgeLoops[i-1]

            # if this is the first or last edge loop, add tris
            if len(prev) == 1:
                self.closeEdgeLoop(edgeLoop, indexOffset)

            elif len(edgeLoop) == 1:
                self.closeEdgeLoop(prev, indexOffset, end=True)

            elif displace <= 0:
                self.joinEdgeLoops(prev, edgeLoop, indexOffset)

            indexOffset += len(prev)

        # add displace loops
        indexOffset = 0
        for i, edgeLoop in enumerate(self.edgeLoops):

            if i <= 0:
                continue

            prev = self.edgeLoops[i-1]
            displace = self.displaceLoops[i]
            # prevDisplace = self.displaceLoops[i-1]
            # displace = max(displace, prevDisplace)

            if displace > 0:
                self.displaceEdgeLoops(prev, edgeLoop, indexOffset, displace)

            indexOffset += len(prev)

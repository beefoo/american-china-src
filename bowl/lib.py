# -*- coding: utf-8 -*-

import math
import numpy as np
from scipy import interpolate

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

            else:
                self.joinEdgeLoops(prev, edgeLoop, indexOffset)

            indexOffset += len(prev)

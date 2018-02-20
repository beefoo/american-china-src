# -*- coding: utf-8 -*-

import math
import numpy as np
from scipy import interpolate

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

def lerp(a, b, mu):
    return (b-a) * mu + a

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def roundedRect(vertices, c, w, h, z, r):
    rect = []
    hw = w * 0.5
    hh = h * 0.5

    # top left -> top right
    y = c[1] - hh
    x = c[0] - hw
    rect += [(x, y), (x + r, y), (c[0], y), (x + w - r, y)]
    # top right to bottom right
    x = c[0] + hw
    y = c[1] - hh
    rect += [(x, y), (x, y+r), (x, c[1]), (x, y + h - r)]
    # bottom right to bottom left
    y = c[1] + hh
    x = c[0] + hw
    rect += [(x, y), (x - r, y), (c[0], y), (x - w + r, y)]
    # bottom left to top left
    x = c[0] - hw
    y = c[1] + hh
    rect += [(x, y), (x, y - r), (x, c[1]), (x, y - h + r)]

    if vertices > 16:
        # use b-spline for rounding
        rounded = bspline(rect, vertices+1)
        # offset
        rounded = rounded[:-1]
        offset = vertices / 8
        a = rounded[(vertices-offset):]
        b = rounded[:(vertices-offset)]
        rounded = a + b
    else:
        rounded = rect

    # add z
    rounded = [(r[0], r[1], z) for r in rounded]
    return rounded

def roundedRectMesh(vertices, c, w, h, z, r, reverse=False):
    loops = [[(c[0], c[1], z)]] # start as a point in the center
    vertPerSide = 2
    targetVertPerSide = vertices / 4
    steps = targetVertPerSide / 2
    widthStep = w / steps
    heightStep = h / steps
    radiusStep = r / steps
    vw = widthStep
    vh = heightStep
    vr = radiusStep

    while vertPerSide <= targetVertPerSide:
        if vertPerSide >= 4:
            loops.append(roundedRect(vertPerSide*4, c, vw, vh, z, vr))
        # A simple 8-point rectangle
        else:
            loops.append([
                (-vw*0.5, -vh*0.5, z),
                (0, -vh*0.5, z),
                (vw*0.5, -vh*0.5, z),
                (vw*0.5, 0, z),
                (vw*0.5, vh*0.5, z),
                (0, vh*0.5, z),
                (-vw*0.5, vh*0.5, z),
                (-vw*0.5, 0, z),
            ])
        vertPerSide += 2
        vw += widthStep
        vh += heightStep
        vr += radiusStep

    if reverse:
        loops = reversed(loops)

    return loops


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

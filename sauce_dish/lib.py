# -*- coding: utf-8 -*-

import math
import numpy as np
import operator
from pprint import pprint
from scipy import interpolate

def add(a, b):
    return tuple(map(operator.add, a, b))

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

def rect(c, w, h, z, r, dl, dr, dlr, drr):
    loop = []
    hw = w * 0.5
    hh = h * 0.5

    # top left -> top right
    y = c[1] - hh
    x = c[0] - hw
    if x > (dl - dlr):
        print "Warning divider is too far left (%s > %s)" % (x, dl-dlr)
    loop += [(x, y), (dl - dlr, y), (dl, y), (dr, y), (dr + drr, y)]
    # top right to bottom right
    x = c[0] + hw
    y = c[1] - hh
    loop += [(x, y)]
    # bottom right to bottom left
    y = c[1] + hh
    x = c[0] + hw
    loop += [(x, y), (dr + drr, y), (dr, y), (dl, y), (dl - dlr, y)]
    # bottom left to top left
    x = c[0] - hw
    y = c[1] + hh
    loop += [(x, y)]

    # add z
    loop = [(r[0], r[1], z) for r in loop]
    return loop

def roundedRect(c, w, h, z, r, dl, dr, dlr, drr):
    loop = []
    hw = w * 0.5
    hh = h * 0.5

    # top left -> top right
    y = c[1] - hh
    x = c[0] - hw
    loop += [(x, y), (x + r, y), (dl - dlr, y), (dl, y), (dr, y), (dr + drr, y), (x + w - r, y)]
    # top right to bottom right
    x = c[0] + hw
    y = c[1] - hh
    loop += [(x, y), (x, y+r), (x, y + h - r)]
    # bottom right to bottom left
    y = c[1] + hh
    x = c[0] + hw
    loop += [(x, y), (x - r, y), (dr + drr, y), (dr, y), (dl, y), (dl - dlr, y), (x - w + r, y)]
    # bottom left to top left
    x = c[0] - hw
    y = c[1] + hh
    loop += [(x, y), (x, y - r), (x, y - h + r)]

    # add z
    rounded = [(r[0], r[1], z) for r in loop]
    return rounded

def roundedRectMesh(c, w, h, z, r, dl, dr, edge, dlr, drr, reverse=False):
    loops = [
        rect(c, w-edge, h-edge, z, r, dl, dr, dlr, drr),
        roundedRect(c, w, h, z, r, dl, dr, dlr, drr)
    ]
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

    def addFace(self, face):
        self.faces.append(face)

    def addFaces(self, faces):
        self.faces += faces

    def addVertices(self, verts):
        index = len(self.verts)
        self.verts += verts
        # return indices
        return [(index+i) for i, v in enumerate(verts)]

    def getVertexCount(self):
        return sum([len(l) for l in self.edgeLoops])

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

            so = smallerOffset
            bo = biggerOffset

            corners = [6, 8, 14]
            offsetBigger = 0
            offsetSmaller = 0
            for i in range(bigger-4):
                v1 = i + offsetBigger + biggerOffset
                v2 = v1 + 1
                v3 = i + offsetSmaller + smallerOffset
                v4 = v3 - 1

                # special case for first
                if i==0:
                    v4 = bigger - 1 + biggerOffset

                # special case for reach corner face
                elif i in corners:
                    v3 = v2 + 1
                    offsetBigger += 1
                    offsetSmaller -= 1

                # special case for last
                elif i==(bigger-5):
                    v3 = smallerOffset

                faces.append((v1, v2, v3, v4))


            # faces += [
            #     # top
            #     (bo, bo+1, so, bo+15),
            #     (bo+1, bo+2, so+1, so),
            #     (bo+2, bo+3, so+2, so+1),
            #     (bo+3, bo+4, so+3, so+2),
            #     # right
            #     (bo+4, bo+5, bo+6, so+3),
            #     (bo+6, bo+7, so+4, so+3),
            #     # bottom
            #     (bo+7, bo+8, bo+9, so+4),
            #     (bo+9, bo+10, so+5, so+4),
            #     (bo+10, bo+11, so+6, so+5),
            #     (bo+11, bo+12, so+7, so+6),
            #     # left
            #     (bo+12, bo+13, bo+14, so+7),
            #     (bo+14, bo+15, so, so+7)
            # ]

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

        bottomFaceCount = 5
        bl = 11
        bottomFaces = []
        for i in range(bottomFaceCount):
            bottomFaces.append([i, i+1, bl-i-1, bl-i])

        for i, edgeLoop in enumerate(self.edgeLoops):
            # add loop's vertices
            self.verts += edgeLoop

            # if this is the first edge loop, add the divider's face
            if i == 0:
                self.faces += tuple(bottomFaces)

            elif i > 0:
                prev = self.edgeLoops[i-1]
                self.joinEdgeLoops(prev, edgeLoop, indexOffset)
                indexOffset += len(prev)

        # add the last divider's face
        topFaces = []
        for f in bottomFaces:
            t = [(ff+indexOffset) for ff in f]
            topFaces.append(t)
        self.faces += tuple(topFaces)

    def removeFaces(self, indices):
        for i in indices:
            self.faces[i] = False
        self.faces = [f for f in self.faces if f is not False]

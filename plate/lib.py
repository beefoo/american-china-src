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

    def displaceEdgeLoops(self, imgMap, imgW, imgH, bounds, displacement, scale, translate):
        dx, dy, dz = displacement
        for i, loop in enumerate(self.edgeLoops):
            newLoop = []
            for v in loop:
                x, y, z = v
                nx = norm(x, bounds[0][0], bounds[1][0])
                ny = norm(y, bounds[0][1], bounds[1][1])
                ix = round(nx * imgW * scale - translate[0])
                iy = round(ny * imgH * scale - translate[1])
                if 0 <= ix < imgW and 0 <= ix < imgH:
                    imgIndex = int(iy * imgW + ix)
                    r, g, b = imgMap[imgIndex]
                    x = x + dx * (r / 255.0)
                    y = y + dy * (g / 255.0)
                    z = z + dz * (b / 255.0)
                    z = max([z, 0])
                newLoop.append((x, y, z))
            self.edgeLoops[i] = newLoop

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

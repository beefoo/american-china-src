import math
import numpy as np
from pprint import pprint
from scipy import interpolate

def addZ(tup, z):
    return (tup[0], tup[1], z)

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

def bsplineShape(points, vertices):
    points = bspline(points, n=vertices+1, periodic=True)
    points = points[:-1]
    offset = vertices / 8
    a = points[(vertices-offset):]
    b = points[:(vertices-offset)]
    points = a + b
    return points

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

def lerpBetweenLoops(a, b, sampleSize, centerZ, heightZ):
    aX, aY, aZ, aC = a
    bX, bY, bZ, bC = b
    z0 = centerZ - heightZ*0.5
    z1 = centerZ + heightZ*0.5
    zDelta = bZ - aZ
    direction = zDelta / abs(zDelta)
    if direction < 0:
        zt = z0
        z0 = z1
        z1 = zt
        # print "%s > %s > %s > %s" % (aZ, z0, z1, bZ)
    p0 = norm(z0, aZ, bZ)
    p1 = norm(z1, aZ, bZ)
    lerped = []
    for i in range(sampleSize):
        percent = 1.0 * i / (sampleSize-1)
        p = lerp(p0, p1, percent)
        x = lerp(aX, bX, p)
        y = lerp(aY, bY, p)
        z = lerp(aZ, bZ, p)
        c = (lerp(aC[0], bC[0], p), lerp(aC[1], bC[1], p), lerp(aC[2], bC[2], p))
        lerped.append((x, y, z, c))
    return lerped

def lerpEdgeloop(l1, l2, mu):
    lerpedEdgeloop = []
    for i, t in enumerate(l1):
        p = []
        pLen = len(t)
        for j in range(pLen):
            pp = lerp(t[j], l2[i][j], mu)
            p.append(pp)
        lerpedEdgeloop.append(tuple(p))
    return lerpedEdgeloop

def lerpPoint(p1, p2, mu):
    xs = [p1[0], p2[0]]
    ys = [p1[1], p2[1]]
    deltaX = p2[0] - p1[0]
    x = deltaX * mu + p1[0]
    func = interpolate.interp1d(xs, ys)
    y = func(x)
    return (x, y)

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

# http://www.petercollingridge.co.uk/pygame-3d-graphics-tutorial/rotation-3d
def rotateX(points, center, degrees):
    radians = math.radians(degrees)
    cx, cy, cz = center
    rotated = []
    for p in points:
        x, y, z = p
        y = y - cy
        z = z - cz
        d = math.hypot(y, z)
        theta  = math.atan2(y, z) + radians
        z = cz + d * math.cos(theta)
        y = cy + d * math.sin(theta)
        rotated.append((x, y, z))
    return rotated

def rotateY(points, center, degrees):
    radians = math.radians(degrees)
    cx, cy, cz = center
    rotated = []
    for p in points:
        x, y, z = p
        x = x - cx
        z = z - cz
        d = math.hypot(x, z)
        theta  = math.atan2(x, z) + radians
        z = cz + d * math.cos(theta)
        x = cx + d * math.sin(theta)
        rotated.append((x, y, z))
    return rotated

def rotateZ(points, center, degrees):
    radians = math.radians(degrees)
    cx, cy, cz = center
    rotated = []
    for p in points:
        x, y, z = p
        x = x - cx
        y = y - cy
        d = math.hypot(y, x)
        theta = math.atan2(y, x) + radians
        x = cx + d * math.cos(theta)
        y = cy + d * math.sin(theta)
        rotated.append((x, y, z))
    return rotated

def roundedRect(vertices, c, w, h, z, r):
    square = []
    hw = w * 0.5
    hh = h * 0.5

    # top left -> top right
    y = c[1] - hh
    x = c[0] - hw
    square += [(x, y), (x + r, y), (c[0], y), (x + w - r, y)]
    # top right to bottom right
    x = c[0] + hw
    y = c[1] - hh
    square += [(x, y), (x, y+r), (x, c[1]), (x, y + h - r)]
    # bottom right to bottom left
    y = c[1] + hh
    x = c[0] + hw
    square += [(x, y), (x - r, y), (c[0], y), (x - w + r, y)]
    # bottom left to top left
    x = c[0] - hw
    y = c[1] + hh
    square += [(x, y), (x, y - r), (x, c[1]), (x, y - h + r)]

    if vertices > 16:
        # use b-spline for rounding
        rounded = bspline(square, vertices+1)
        # offset
        rounded = rounded[:-1]
        offset = vertices / 8
        a = rounded[(vertices-offset):]
        b = rounded[:(vertices-offset)]
        rounded = a + b
    else:
        rounded = square

    # add z
    rounded = [(r[0], r[1], z) for r in rounded]
    return rounded

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

def shape(points, width, height, vertices, center, z):
    loop = []
    hw = width * 0.5
    hh = height * 0.5

    if vertices > len(points):
        points = bsplineShape(points, vertices)

    for p in points:
        x = p[0] * width
        y = p[1] * height
        x =  x - hw + center[0]
        y =  y - hh + center[1]
        loop.append((x, y, z))
    return loop

def shapeMesh(points, width, height, vertices, center, z, reverse=False):
    verts = []
    edgesPerSide = vertices / 4
    hw = width * 0.5
    hh = height * 0.5

    if vertices > len(points):
        points = bsplineShape(points, vertices)

    for row in range(edgesPerSide+1):
        yp = 1.0 * row / edgesPerSide
        yi = int(yp * edgesPerSide)
        for col in range(edgesPerSide+1):
            xp = 1.0 * col / edgesPerSide
            xi = int(xp * edgesPerSide)
            point = False

            # point is on the perimeter, select point from list
            if row == 0:
                point = points[col]
            elif row == edgesPerSide:
                point = points[edgesPerSide*3-col]
            elif col == 0:
                point = points[vertices-row]
            elif col == edgesPerSide:
                point = points[edgesPerSide+row]

            # point is inside the mesh, interpolate
            if not point:
                p1 = points[vertices-row]
                p2 = points[edgesPerSide+row]
                point = lerpPoint(p1, p2, xp)

            x = (point[0] * width - hw) + center[0]
            y = (point[1] * height - hh) + center[1]
            verts.append((x, y, z))

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

# interpolate outer pot to accommodate hole for spout
def splineBetweenLoopGroups(a, b, sampleSize, centerZ, heightZ):
    lenSample = min([len(a), len(b)])
    sample = a[-lenSample:] + b[:lenSample]
    xs = [d[0] for d in sample]
    ys = [d[1] for d in sample]
    zs = [d[2] for d in sample]
    cs = [d[3] for d in sample]
    xSplined = bspline(xs, n=1000, periodic=False)
    ySplined = bspline(ys, n=1000, periodic=False)
    zSplined = bspline(zs, n=1000, periodic=False)
    cSplined = bspline(cs, n=1000, periodic=False)
    z0 = centerZ - heightZ*0.5
    z1 = centerZ + heightZ*0.5
    zDelta = zs[-1] - zs[0]
    direction = zDelta / abs(zDelta)
    if direction < 0:
        zt = z0
        z0 = z1
        z1 = zt
    zStartIndex = False
    zEndIndex = False
    for i, z in enumerate(zSplined):
        if zStartIndex is False and (z >= z0 and direction >= 0 or z <= z0 and direction < 0):
            zStartIndex = i
        elif zStartIndex is not False and zEndIndex is False and (z > z1 and direction >= 0 or z < z1 and direction < 0):
            zEndIndex = i - 1
    splined = []
    for i in range(sampleSize):
        percent = 1.0 * i / (sampleSize-1)
        index = lerp(zStartIndex, zEndIndex, percent)
        index = int(round(index))
        x = xSplined[index]
        y = ySplined[index]
        z = zSplined[index]
        c = cSplined[index]
        splined.append((x, y, z, c))
    return splined

def translateLoop(loop, v):
    newLoop = []
    tx, ty, tz = v
    for l in loop:
        x, y, z = l
        newLoop.append((x+tx, y+ty, z+tz))
    return newLoop

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

        self.edgeLoopOpenings = []
        self.vertOpenings = []
        self.openings = {}

    def addEdgeLoop(self, loop, loopOpenings=False):
        self.edgeLoops.append(loop)
        self.edgeLoopOpenings.append(loopOpenings)

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

    # join another mesh to this mesh
    def joinMesh(self, otherMesh, openingIds):
        otherVerts = otherMesh.verts[:]
        otherFaces = otherMesh.faces[:]
        otherOpenings = otherMesh.openings.copy()
        thisOpenings = self.openings
        offset = len(self.verts)

        # add other verts to this mesh
        self.verts += otherVerts

        # offset other faces and add to this mesh
        for i, face in enumerate(otherFaces):
            otherFace = []
            for j, vIndex in enumerate(face):
                otherFace.append(vIndex + offset)
            otherFaces[i] = tuple(otherFace)
        self.faces += otherFaces

        # offset other openings
        for openingId in otherOpenings:
            for j, vIndex in enumerate(otherOpenings[openingId]):
                otherOpenings[openingId][j] = vIndex + offset

        # join the meshes on the openings
        newFaces = []
        for o in openingIds:
            openingId = o[0]
            reverse = o[1]
            openingA = thisOpenings[openingId][:]
            openingB = otherOpenings[openingId][:]
            openingLen = len(openingA)

            if reverse:
                openingA = otherOpenings[openingId][:]
                openingB = thisOpenings[openingId][:]

            for j, vIndex in enumerate(openingA):
                v1 = j
                v2 = j + 1
                v3 = j + 1
                v4 = j
                if v2 >= openingLen:
                    v2 = 0
                    v3 = 0
                v1 = openingA[v1]
                v2 = openingA[v2]
                v3 = openingB[v3]
                v4 = openingB[v4]
                newFaces.append((v1, v2, v3, v4))
        self.faces += newFaces

    # join all the edge loop together
    def processEdgeloops(self):
        indexOffset = 0

        for i, edgeLoop in enumerate(self.edgeLoops):
            # add loop's vertices
            self.verts += edgeLoop

            edgeLoopOpening = self.edgeLoopOpenings[i]
            if edgeLoopOpening is False:
                self.vertOpenings += [True for v in edgeLoop]
            else:
                self.vertOpenings += edgeLoopOpening

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

        # prepare to remove "False" vertices
        offsets = [0 for v in self.verts]
        offset = 0
        for i, v in enumerate(self.verts):
            if v is False:
                offset += 1
            else:
                offsets[i] = offset
        # remove faces with "False" vertices
        verts = self.verts
        self.faces = [f for f in self.faces if len(f)==4 and False not in [verts[f[0]], verts[f[1]], verts[f[2]], verts[f[3]]]]
        # remove "False" vertices
        self.verts = [v for v in verts if v is not False]
        self.vertOpenings = [v for v in self.vertOpenings if v is not False]
        # update faces with new indices
        for i, f in enumerate(self.faces):
            tup = []
            for j, vIndex in enumerate(f):
                tup.append(vIndex - offsets[vIndex])
            self.faces[i] = tuple(tup)

        # populate openings
        openings = {}
        for i, v in enumerate(self.vertOpenings):
            if v is not True:
                vId = v[0]
                vIndex = v[1]
                vTotal = v[2]
                if vId not in openings:
                    openings[vId] = [-1 for vv in range(vTotal)]
                openings[vId][vIndex] = i
        self.openings = openings
        # pprint(openings)

# -*- coding: utf-8 -*-

import colorsys
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from pprint import pprint
from scipy import interpolate
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 8
IMAGE_MAP_FILE = "imgMap.png"

# retrieve image map data
im = Image.open(IMAGE_MAP_FILE)
IMAGE_MAP_W, IMAGE_MAP_H = im.size
IMAGE_MAP = list(im.getdata())

# cup config in mm
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 6 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 5
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

TOP_WIDTH = 70.0
HEIGHT = 66.0
TOP_LIP = 2.5
EDGE_RADIUS = 4.0
TOP_CORNER_RADIUS = 15.0
THICKNESS = 4.8
DISPLACEMENT_DEPTH = 3.0
BASE_INSET_HEIGHT = 3.0
BASE_EDGE_RADIUS = 1.0

# relative widths
BASE_OUTER_DIAMETER = 0.56 * TOP_WIDTH
BASE_INNER_DIAMETER = 0.8 * BASE_OUTER_DIAMETER
BASE_INSET_DIAMETER = 0.9 * BASE_INNER_DIAMETER
BODY_DIAMETER = 0.875 * TOP_WIDTH
NECK_DIAMETER = 0.875 * TOP_WIDTH
NECK_INNER_DIAMETER = NECK_DIAMETER * 1.0 - THICKNESS * 2
BODY_INNER_DIAMETER = BODY_DIAMETER * 1.0 - THICKNESS * 2
INNER_BASE_DIAMETER = BODY_INNER_DIAMETER * 0.667

# relative heights
BASE_HEIGHT = 0.0667 * HEIGHT
BODY_HEIGHT = 0.167 * HEIGHT
NECK_HEIGHT = 0.85 * HEIGHT
INNER_BASE_HEIGHT = BASE_HEIGHT + THICKNESS
INNER_BODY_HEIGHT = BODY_HEIGHT * 1.3

print "Max height for text: %smm" % (NECK_HEIGHT - BASE_HEIGHT - THICKNESS)
print "Max width for text: %smm" % (BODY_DIAMETER - THICKNESS * 2)

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

def bsplineEdgeLoops(loops, targetLength):
    splinedLoops = [[] for l in range(targetLength)]
    vertices = len(loops[0])
    for i in range(vertices):
        cv = [loop[i] for loop in loops]
        splined = bspline(cv, n=targetLength, periodic=False)
        for j, v in enumerate(splined):
            splinedLoops[j].append(v)
    return splinedLoops

def circle(vertices, center, radius, z):
    angleStart = -135
    angleStep = 360.0 / vertices
    c = []
    for i in range(vertices):
        angle = angleStart + angleStep * i
        p = translatePoint(center, angle, radius)
        c.append((p[0], p[1], z))
    return c

def circleMesh(vertices, center, radius, z, reverse=False):
    verts = []
    edgesPerSide = vertices / 4

    # create a square matrix of vertices mapped to circular disc coordinates (UV)
    # https://stackoverflow.com/questions/13211595/how-can-i-convert-coordinates-on-a-circle-to-coordinates-on-a-square
    for row in range(edgesPerSide+1):
        for col in range(edgesPerSide+1):
            # x, y is between -1 and 1
            x = 1.0 * col / edgesPerSide * 2 - 1
            y = 1.0 * row / edgesPerSide * 2 - 1
            u = x * math.sqrt(1.0 - 0.5 * (y * y))
            v = y * math.sqrt(1.0 - 0.5 * (x * x))
            # convert to actual unit
            u = u * radius + center[0]
            v = v * radius + center[1]
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

def displaceEdgeLoop(loop, loopBefore, loopAfter, pixelRow, depth, direction="out"):
    displaced = []

    for i, p in enumerate(loop):
        x = 1.0 - 1.0 * i / (len(loop)-1)
        ii = int(round(x * (len(pixelRow)-1)))
        rgb = pixelRow[ii]
        hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
        displace = depth * (1.0 - hls[1])

        j = i + 1
        h = i - 1
        if j >= len(loop):
            j = 0

        p0 = p
        p1 = loopBefore[h]
        p2 = loopBefore[j]
        p3 = loopAfter[i]

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

        displaced.append(pd)

    return displaced


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

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def roundedSquare(vertices, c, w, z, r):
    square = []
    hw = w * 0.5

    # top left -> top right
    y = c[1] - hw
    x = c[0] - hw
    square += [(x, y), (x + r, y), (c[0], y), (x + w - r, y)]
    # top right to bottom right
    x = c[0] + hw
    y = c[1] - hw
    square += [(x, y), (x, y+r), (x, c[1]), (x, y + w - r)]
    # bottom right to bottom left
    y = c[1] + hw
    x = c[0] + hw
    square += [(x, y), (x - r, y), (c[0], y), (x - w + r, y)]
    # bottom left to top left
    x = c[0] - hw
    y = c[1] + hw
    square += [(x, y), (x, y - r), (x, c[1]), (x, y - w + r)]

    # use b-spline for rounding
    rounded = bspline(square, vertices+1)
    # offset
    rounded = rounded[:-1]
    offset = vertices / 8
    a = rounded[(vertices-offset):]
    b = rounded[:(vertices-offset)]
    rounded = a + b
    # add z
    rounded = [(r[0], r[1], z) for r in rounded]
    return rounded

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

    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces = []
        self.edgeLoops = []

        self.queueLoopAfter = False

    def addEdgeLoop(self, loop, loopBefore=False, loopAfter=False):
        # add an edge loop after the previous one
        if self.queueLoopAfter is not False:
            self.addEdgeLoopHelper(loop, self.queueLoopAfter, True)
            self.queueLoopAfter = False
        # add an edge loop before the next one
        if loopBefore is not False:
            self.addEdgeLoopHelper(loop, loopBefore, False)
        # add an edge loop after the next one
        if loopAfter is not False:
            self.queueLoopAfter = loopAfter

        self.edgeLoops.append(loop)

    def addEdgeLoops(self, loops):
        for loop in loops:
            self.addEdgeLoop(loop)

    def addEdgeLoopHelper(self, nextLoop, amount, after=True):
        prevLoop = self.edgeLoops[-1]
        d = distance(prevLoop[0], nextLoop[0])
        lerpAmount = amount / d
        if lerpAmount >= 0.5:
            print "Edge loop %s helper too close to neighbor loop" % len(self.edgeLoops)
            return False
        if not after:
            lerpAmount = 1.0 - lerpAmount
        loop = lerpEdge(prevLoop, nextLoop, lerpAmount)
        self.edgeLoops.append(loop)

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

    def updateEdgeLoops(self, loops, offset0=None, offset1=None):
        if offset0 is None and offset1 is None:
            self.edgeLoops = loops[:]
        else:
            before = self.edgeLoops[:offset0]
            after = self.edgeLoops[offset1:]
            self.edgeLoops = before + loops + after

# determine center
halfWidth = TOP_WIDTH * 0.5
CENTER = (0, 0, 0)

# init mesh
mesh = Mesh()

# create base inset as a circle which will be the first face
baseInset = circleMesh(VERTICES_PER_EDGE_LOOP, CENTER, BASE_INSET_DIAMETER * 0.49, BASE_INSET_HEIGHT)
mesh.addEdgeLoops(baseInset)
subdivideStart = len(mesh.edgeLoops)

# move out to base inset helper
baseInsetHelper = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_INSET_DIAMETER * 0.5, BASE_INSET_HEIGHT)
mesh.addEdgeLoop(baseInsetHelper)
baseInsetHelper = circle(VERTICES_PER_EDGE_LOOP, CENTER, (BASE_INSET_DIAMETER + BASE_INNER_DIAMETER) * 0.5 * 0.5, BASE_INSET_HEIGHT)
mesh.addEdgeLoop(baseInsetHelper)

# move down and out to base inner
baseInner = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_INNER_DIAMETER * 0.5, 0)
mesh.addEdgeLoop(baseInner, False, EDGE_RADIUS)

# move out to base outer
baseOuter = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_OUTER_DIAMETER * 0.5, 0)
mesh.addEdgeLoop(baseOuter, BASE_EDGE_RADIUS, BASE_EDGE_RADIUS)

# move up to base
base = circle(VERTICES_PER_EDGE_LOOP, CENTER, BASE_OUTER_DIAMETER * 0.5, BASE_HEIGHT)
mesh.addEdgeLoop(base, BASE_EDGE_RADIUS, BASE_EDGE_RADIUS)

# move up and out (lerp) to body
body = circle(VERTICES_PER_EDGE_LOOP, CENTER, BODY_DIAMETER * 0.5, BODY_HEIGHT)
mesh.addEdgeLoop(body)

# move up and out (lerp) to neck
neck = roundedSquare(VERTICES_PER_EDGE_LOOP, CENTER, NECK_DIAMETER, NECK_HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(neck)

# move up and out (lerp) to top
outerTop = roundedSquare(VERTICES_PER_EDGE_LOOP, CENTER, TOP_WIDTH, HEIGHT-TOP_LIP, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(outerTop)

# move up and in to top
top = roundedSquare(VERTICES_PER_EDGE_LOOP, CENTER, TOP_WIDTH-THICKNESS, HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(top)

# move in to inner top
innerTop = roundedSquare(VERTICES_PER_EDGE_LOOP, CENTER, TOP_WIDTH-THICKNESS*2, HEIGHT-TOP_LIP, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(innerTop)

# move in and down to inner neck
displaceStart = len(mesh.edgeLoops)
innerNeck = roundedSquare(VERTICES_PER_EDGE_LOOP, CENTER, NECK_INNER_DIAMETER, NECK_HEIGHT, TOP_CORNER_RADIUS)
mesh.addEdgeLoop(innerNeck)

# move in and down to inner body
innerBody = circle(VERTICES_PER_EDGE_LOOP, CENTER, BODY_INNER_DIAMETER * 0.5, INNER_BODY_HEIGHT)
mesh.addEdgeLoop(innerBody)
displaceEnd = len(mesh.edgeLoops)

# move in and down to inner base helper
innerBaseHelper = circle(VERTICES_PER_EDGE_LOOP, CENTER, (INNER_BASE_DIAMETER + BODY_INNER_DIAMETER) * 0.5 * 0.5, INNER_BASE_HEIGHT)
mesh.addEdgeLoop(innerBaseHelper)
innerBaseHelper = circle(VERTICES_PER_EDGE_LOOP, CENTER, INNER_BASE_DIAMETER * 0.5, INNER_BASE_HEIGHT)
mesh.addEdgeLoop(innerBaseHelper)
subdivideEnd = len(mesh.edgeLoops)

# move in to inner base
innerBase = circleMesh(VERTICES_PER_EDGE_LOOP, CENTER, INNER_BASE_DIAMETER * 0.49, INNER_BASE_HEIGHT, True)
mesh.addEdgeLoops(innerBase)

# subdivide edge loops
anchorEdgeLoops = mesh.edgeLoops[subdivideStart:subdivideEnd]
targetLength = (len(anchorEdgeLoops) - 1) * 2**SUBDIVIDE_Y + 1
splinedEdgeLoops = bsplineEdgeLoops(anchorEdgeLoops, targetLength)
mesh.updateEdgeLoops(splinedEdgeLoops, subdivideStart, subdivideEnd)

# displace edge loops
offsetBefore = 0.05
offsetAfter = 0
delta = (displaceEnd-displaceStart) * 2**SUBDIVIDE_Y
displaceStart = subdivideStart + (displaceStart-subdivideStart) * 2**SUBDIVIDE_Y + int(offsetBefore * delta)
displaceEnd = displaceStart + delta + int(offsetAfter * delta)
originalEdgeLoops = mesh.edgeLoops[displaceStart:displaceEnd]
displacedEdgeLoops = []

# displace the edgeloops
print "Displacing %s edge loops" % len(originalEdgeLoops)
z0 = originalEdgeLoops[0][0][2]
z1 = originalEdgeLoops[-1][0][2]
for i, edgeLoop in enumerate(originalEdgeLoops):
    # don't displace edges
    if i > 0 and i < len(originalEdgeLoops)-1:
        py = norm(edgeLoop[0][2], z0, z1)
        y = int(py * IMAGE_MAP_H)
        offset = int(y * IMAGE_MAP_W)
        pixelRow = IMAGE_MAP[offset:(offset+IMAGE_MAP_W)]
        displacedLoop = displaceEdgeLoop(edgeLoop, originalEdgeLoops[i-1], originalEdgeLoops[i+1], pixelRow, DISPLACEMENT_DEPTH)
        displacedEdgeLoops.append(displacedLoop)

    else:
        displacedEdgeLoops.append(edgeLoop)
mesh.updateEdgeLoops(displacedEdgeLoops, displaceStart, displaceEnd)

print "Calculating faces..."
# create faces from edges
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Cup",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": range((VERTICES_PER_EDGE_LOOP/4)**2)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

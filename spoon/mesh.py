# -*- coding: utf-8 -*-

# Data source:
    # Table 4.	Region and Country or Area of Birth of the Foreign-Born Population,
    # With Geographic Detail Shown in Decennial Census Publications of 1930 or Earlier:
    # 1850 to 1930 and 1960 to 1990
    # https://www.census.gov/population/www/documentation/twps0029/tab04.html

import csv
import json
import math
import numpy as np
import os
from pprint import pprint
from scipy import interpolate
import sys

# data config
OUTPUT_FILE = "mesh.json"
DATA_FILE = "data.csv"
VALUE_KEY = "percent"
DATA_PRECISION = 3
START_YEAR = 1880
END_YEAR = 2010
YEAR_INCR = 10
BASE_YEARS = [1920, 1950]           # these years will be the flat base
CUP_YEARS = [START_YEAR, 1960]      # these years will make the cup of the spoon
HANDLE_YEARS = [1970, END_YEAR]     # these years will make the handle of the spoon

# helper options
ADD_MISSING_YEARS = False
SHOW_GRAPH = False
OUTPUT_SVG = False
SVG_FILE = "data.svg"

BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 0 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 0
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
LENGTH = 140.0
WIDTH = 50.0
HEIGHT = 40.0
EDGE_RADIUS = 2.0
THICKNESS = 3.0
DISPLACEMENT_DEPTH = 2.0
INSET_WIDTH = 3.0

WIDTHS = [(0, 0.2), (0.2, 1.0), (0.6, 0.8), (0.9, 0.4), (1.0, 0.35)]

BASE_WIDTH = WIDTH * 0.5

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

def readCSV(filename):
    rows = []
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            lines = [line for line in f if not line.startswith("#")]
            reader = csv.DictReader(lines, skipinitialspace=True)
            rows = list(reader)
            for i, row in enumerate(rows):
                for key in row:
                    value = row[key]
                    try:
                        num = float(value)
                        if "." not in value:
                            num = int(value)
                        rows[i][key] = num
                    except ValueError:
                        rows[i][key] = value
    return rows

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

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
        self.offsets = []
        self.closedLoops = []

    def addEdgeLoop(self, loop, offsetStart=False, offsetEnd=False, closed=True):
        self.edgeLoops.append(loop)
        self.offsets.append((offsetStart, offsetEnd))
        self.closedLoops.append(closed)

    def addEdgeLoops(self, loops):
        for loop in loops:
            self.addEdgeLoop(loop)

    def closeOpenLoops(self):

        # find the first open loop
        loopOffset = 0
        vertOffset = 0
        openLoops = []
        for i, loop in enumerate(self.edgeLoops):
            closed = self.closedLoops[i]
            if not closed:
                openLoops.append(loop)
            elif len(openLoops) <= 0:
                loopOffset += 1
                vertOffset += len(loop)

        # connect each of the loops on the handle
        faces = []
        openLoopCount = len(openLoops)
        half = openLoopCount / 2 - 1
        i = half - 1
        offset = self.offsets[loopOffset]
        partialLoopLen = offset[1] - offset[0]
        while i >= 0:
            j = i + (half-i) * 2 + 1
            a = i
            b = i + 1
            c = j - 1
            d = j

            loopA = openLoops[a][offset[0]:offset[1]]
            loopB = openLoops[b][offset[0]:offset[1]]
            loopC = openLoops[c][offset[0]:offset[1]]
            loopD = openLoops[d][offset[0]:offset[1]]

            aVertOffset = a * partialLoopLen + vertOffset
            bVertOffset = b * partialLoopLen + vertOffset
            cVertOffset = c * partialLoopLen + vertOffset
            dVertOffset = d * partialLoopLen + vertOffset

            # connect on the north side
            faces.append((aVertOffset, bVertOffset, cVertOffset, dVertOffset))
            # connect on the south side
            faces.append((dVertOffset+partialLoopLen-1, cVertOffset+partialLoopLen-1, bVertOffset+partialLoopLen-1, aVertOffset+partialLoopLen-1))
            i -= 1

        # connect the closed loops right before and after the open loops
        a = loopOffset - 1
        b = loopOffset + openLoopCount
        loopA = self.edgeLoops[a]
        loopB = self.edgeLoops[b]
        aVertOffset = vertOffset - len(loopA)
        bVertOffset = vertOffset + openLoopCount * partialLoopLen
        loopLen = len(loopA)
        for i in range(loopLen):
            # skip the ones already connect
            if offset[0] <= i < offset[1]-1:
                continue
            v1 = i
            v2 = i + 1
            v3 = i + 1
            v4 = i
            if v2 >= loopLen:
                v2 = 0
                v3 = 0
            faces.append((v1+aVertOffset, v2+aVertOffset, v3+bVertOffset, v4+bVertOffset))

        # finally connect the last open loop with the first closed loop
        aVertOffset = aVertOffset + offset[0]
        bVertOffset = bVertOffset + offset[0]
        cVertOffset = vertOffset + (openLoopCount - 1) * partialLoopLen
        dVertOffset = vertOffset
        # south side
        faces.append((dVertOffset, cVertOffset, bVertOffset, aVertOffset))
        # north side
        faces.append((aVertOffset+partialLoopLen-1, bVertOffset+partialLoopLen-1, cVertOffset+partialLoopLen-1, dVertOffset+partialLoopLen-1))

        self.faces += faces
        return faces

    def joinEdgeLoops(self, a, b, indexOffset):
        faces = []
        loopA = self.edgeLoops[a]
        loopB = self.edgeLoops[b]
        offsetA = self.offsets[a]
        offsetB = self.offsets[b]
        closedA = self.closedLoops[a]
        closedB = self.closedLoops[b]

        # deal with partial loops
        if offsetA[0] is not False:
            loopA = loopA[offsetA[0]:offsetA[1]]
        if offsetB[0] is not False:
            loopB = loopB[offsetB[0]:offsetB[1]]

        aLen = len(loopA)
        bLen = len(loopB)

        # an offset is defined and number of vertices differ
        if (offsetA[0] is not False or offsetB[0] is not False) and aLen != bLen:

            # we are going from bigger to smaller
            if aLen > bLen:
                offset = offsetB[0]
                amtSmaller = bLen
                amtBigger = aLen
                # print "Going from bigger (%s) to smaller (%s)" % (amtBigger, amtSmaller)

                for i in range(amtSmaller-1):
                    v1 = i + offset
                    v2 = i + offset + 1
                    v3 = i + 1 + amtBigger
                    v4 = i + amtBigger
                    if v2 >= amtBigger:
                        v2 = 0
                        v3 = amtBigger
                    faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))

            # we are going from smaller to bigger
            else:
                offset = offsetA[0]
                amtSmaller = aLen
                amtBigger = bLen
                # print "Going from smaller (%s) to bigger (%s)" % (amtSmaller, amtBigger)

                for i in range(amtSmaller-1):
                    v1 = i
                    v2 = i + 1
                    v3 = i + 1 + amtSmaller + offset
                    v4 = i + amtSmaller + offset
                    faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))

        # number of vertices differ
        elif aLen != bLen:

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
            amt = aLen
            if closedA is False and closedB is False:
                amt -= 1
            for i in range(amt):
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
            offset = self.offsets[i]
            loop = edgeLoop

            # this is a partial loop
            if offset[0] is not False:
                loop = edgeLoop[offset[0]:offset[1]]

            # add loop's vertices
            self.verts += loop

            # if this is the first edge loop and it's a quad, add it's face
            if i == 0 and len(loop) == 4:
                self.faces.append(range(4))

            elif i > 0:
                offsetBefore = self.offsets[i-1]
                loopBefore = self.edgeLoops[i-1]
                if offsetBefore[0] is not False:
                    loopBefore = loopBefore[offsetBefore[0]:offsetBefore[1]]

                self.joinEdgeLoops(i-1, i, indexOffset)
                indexOffset += len(loopBefore)

        # if the last edge loop is a quad, add it's face
        if len(self.edgeLoops[-1]) == 4:
            self.faces.append([(i+indexOffset) for i in range(4)])

    def removeLoop(self, index):
        removed = self.edgeLoops.pop(index)

    def solidify(self, center, thickness):
        originalLength = len(self.edgeLoops) - 1
        index = originalLength

        while index >= 0:
            loop = self.edgeLoops[index]
            offset = self.offsets[index]
            closed = self.closedLoops[index]
            closedBefore = True
            closedAfter = True
            displaced = []

            if index < len(self.edgeLoops) - 1:
                closedBefore = self.closedLoops[index+1]
            if index > 0:
                closedAfter = self.closedLoops[index-1]

            # case: first, or going from open to closed, add a reference loop before
            if index >= len(self.edgeLoops) - 1 or (not closedBefore and closed):
                loopAfter = self.edgeLoops[index-1]
                deltaZ = loop[0][2] - loopAfter[0][2]
                loopBefore = [(v[0], v[1], v[2] + deltaZ) for v in loop]

            # case: last, add a reference loop after
            elif index <= 0:
                loopBefore = self.edgeLoops[index+1]
                deltaZ = loop[0][2] - loopBefore[0][2]
                loopAfter = [(v[0], v[1], v[2] + deltaZ) for v in loop]

            else:
                loopBefore = self.edgeLoops[index+1]
                loopAfter = self.edgeLoops[index-1]

            # Check for a flat surface, just point the normal straight up
            if loopBefore[0][2] == loop[0][2] and loop[0][2] == loopAfter[0][2]:
                for i, p in enumerate(loop):
                    dp = (p[0], p[1], p[2]+thickness)
                    displaced.append(dp)
                self.addEdgeLoop(displaced, offsetStart=offset[0], offsetEnd=offset[1], closed=closed)
                index -= 1
                continue

            # Deal with loops with different numbers
            length = len(loop)
            beforeLen = len(loopBefore)
            afterLen = len(loopAfter)
            if length != beforeLen or length != afterLen:
                print "Abort: length mismatch at %s!" % index
                break

            # make displaced loop
            for i, p in enumerate(loop):
                j = i + 1
                h = i - 1
                if j >= len(loop):
                    j = 0

                # points 1, 2, 3 is the triangle to derive normal from
                p0 = p
                p1 = loopBefore[h]
                p2 = loopBefore[j]
                p3 = loopAfter[i]

                # normalize Z to make z=0 at central point
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

                # we want normals to go towards center
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
                pd = p0 + (thickness / ndist) * dist
                pd = tuple(pd)
                pd = (pd[0], pd[1], pd[2] + p[2])
                displaced.append(pd)

            self.addEdgeLoop(displaced, offsetStart=offset[0], offsetEnd=offset[1], closed=closed)

            index -= 1

    def updateEdgeLoops(self, loops, offset0=None, offset1=None):
        if offset0 is None and offset1 is None:
            self.edgeLoops = loops[:]
        else:
            before = self.edgeLoops[:offset0]
            after = self.edgeLoops[offset1:]
            self.edgeLoops = before + loops + after

# read data
data = readCSV(DATA_FILE)

# add missing years
if ADD_MISSING_YEARS:
    dataLookup = dict([(d["year"], d[VALUE_KEY]) for d in data])
    year = START_YEAR
    lastValue = None
    while year <= END_YEAR:
        if year in dataLookup:
            lastValue = dataLookup[year]
        else:
            d = {"year": year}
            d[VALUE_KEY] = lastValue
            data.append(d)
        year += YEAR_INCR
    data = sorted(data, key=lambda k: k['year'])

# round data
for i,d in enumerate(data):
    data[i][VALUE_KEY] = round(d[VALUE_KEY], DATA_PRECISION)

# normalize data
values = [d[VALUE_KEY] for d in data]
minValue = min(values)
maxValue = max(values)
ndata = []
for d in data:
    year = d["year"]
    if START_YEAR <= year <= END_YEAR:
        x = norm(d["year"], START_YEAR, END_YEAR)
        y = norm(d[VALUE_KEY], minValue, maxValue)
        ndata.append((x, y))

# interpolate data
xs = [d[0] for d in ndata]
ys = [d[1] for d in ndata]
func1 = interpolate.interp1d(xs, ys, kind='linear')
func3 = interpolate.interp1d(xs, ys, kind='cubic')
xyears = np.linspace(0, 1, num=(END_YEAR-START_YEAR))
func3y = interpolate.interp1d([w[0] for w in WIDTHS], [w[1] for w in WIDTHS], kind='cubic')

# plot data
if SHOW_GRAPH:
    import matplotlib.pyplot as plt
    plt.plot(xs, ys, 'o', xyears, func1(xyears), '-', xyears, func3(xyears), '--', xyears, func3t(xyears), '--')
    plt.show()

# output svg line
if OUTPUT_SVG:
    import svgwrite
    svgW = 800
    svgH = 600
    xnew = np.linspace(0, 1, num=100)
    ynew = func1(xnew)
    points = list(zip(xnew, ynew))
    points = [(p[0]*svgW, svgH-p[1]*svgH) for p in points]
    dwg = svgwrite.Drawing(SVG_FILE, size=(svgW, svgH), profile='full')
    dwg.add(dwg.polyline(points=points, stroke="#000000", stroke_width=2, fill="none"))
    dwg.save()
    print "Saved SVG file: %s" % SVG_FILE


mesh = Mesh()
baseRadiusX = 1.0 * (BASE_YEARS[1]-BASE_YEARS[0]) / (END_YEAR-START_YEAR) * LENGTH * 0.5
baseRadiusY = BASE_WIDTH * 0.5

# start at the base inset with an ellipse mesh
r1 = baseRadiusX - INSET_WIDTH*0.5
r2 = baseRadiusY - INSET_WIDTH*0.5
baseInset = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r1, r2, 0)
mesh.addEdgeLoops(baseInset)

# move out to base
base = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, baseRadiusX, baseRadiusY, 0)
mesh.addEdgeLoop(base)

# get cup data
cupYears = (norm(CUP_YEARS[0], START_YEAR, END_YEAR), norm(CUP_YEARS[1], START_YEAR, END_YEAR))
baseYears = (norm(BASE_YEARS[0], START_YEAR, END_YEAR), norm(BASE_YEARS[1], START_YEAR, END_YEAR))
baseYearCenter = (baseYears[1] - baseYears[0]) * 0.5 +  baseYears[0]
cupData = [d for d in ndata if d[0] >= cupYears[0] and d[0] < baseYears[0] or d[0] > baseYears[1] and d[0] <= cupYears[1]]
cupData = sorted(cupData, key=lambda d: d[1])

for i, d in enumerate(cupData):

    xsample = np.linspace(baseYears[1], 1, num=100)

    # point is right of the base
    if d[0] > baseYears[0]:
        xsample = np.linspace(0, baseYears[0], num=100)

    # get the curve of the opposite side
    ysample1 = func3(xsample)
    straightLine = interpolate.interp1d([0, 1], [d[1], d[1]], kind='linear')
    ysample2 = straightLine(xsample)

    # https://stackoverflow.com/questions/28766692/intersection-of-two-graphs-in-python-find-the-x-value
    intersections = list(np.argwhere(np.diff(np.sign(ysample2 - ysample1)) != 0).reshape(-1) + 0)

    if len(intersections) > 0:
        intersectionX = xsample[intersections[0]]

        cx = d[0] - (d[0] - intersectionX) * 0.5

        center = ((cx-baseYearCenter) * LENGTH, 0, d[1] * HEIGHT)
        width = lerp(BASE_WIDTH, WIDTH, d[1])
        width = func3y(cx) * width
        r1 = abs(d[0] - intersectionX) * LENGTH * 0.5
        r2 = width * 0.5
        # move up and out to next layer of the cup
        edgeLoop = ellipse(VERTICES_PER_EDGE_LOOP, center, r1, r2, center[2])
        mesh.addEdgeLoop(edgeLoop)

    else:
        print "No intersection found for (%s, %s)" % d

# get handle data
handleYears = (norm(HANDLE_YEARS[0], START_YEAR, END_YEAR), norm(HANDLE_YEARS[1], START_YEAR, END_YEAR))
handleData = [d for d in ndata if d[0] >= handleYears[0] and d[0] <= handleYears[1]]
handleCenter = baseYearCenter

for i, d in enumerate(handleData):

    handleCenter = d[0] - 0.2 # bigger this number, the more inset the handle is
    center = ((handleCenter-baseYearCenter) * LENGTH, 0, d[1] * HEIGHT)
    width = func3y(d[0]) * WIDTH
    r1 = (d[0] - handleCenter) * LENGTH
    r2 = width * 0.5
    # move up and out to next layer of the cup
    edgeLoop = ellipse(VERTICES_PER_EDGE_LOOP, center, r1, r2, center[2])
    # edgeLoop = warpLoop(edgeLoop)

    vPerSide = VERTICES_PER_EDGE_LOOP / 4
    mesh.addEdgeLoop(edgeLoop, offsetStart=vPerSide, offsetEnd=(vPerSide*2+1), closed=False)

mesh.solidify(CENTER, THICKNESS)

# hack: remove the loop before the inner circle mesh to get rid of some weirdness
removeIndex = len(mesh.edgeLoops)-len(baseInset)-1
mesh.removeLoop(removeIndex)
# remove another loop because it's too tight
removeIndex = len(mesh.edgeLoops)-len(baseInset)-3
mesh.removeLoop(removeIndex)

print "Calculating faces..."
# create faces from edges
mesh.processEdgeloops()

print "Closing open loops..."
facesAdded = mesh.closeOpenLoops()

# Flip the faces of the first circle mesh
flipFaces = range((VERTICES_PER_EDGE_LOOP/4)**2)

# TODO: flip the faces of the north side of the closed open loops

# save data
data = [
    {
        "name": "Spoon",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": flipFaces
    }
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

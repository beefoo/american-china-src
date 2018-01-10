# -*- coding: utf-8 -*-

# Data source:
    # Table 4.	Region and Country or Area of Birth of the Foreign-Born Population,
    # With Geographic Detail Shown in Decennial Census Publications of 1930 or Earlier:
    # 1850 to 1930 and 1960 to 1990
    # https://www.census.gov/population/www/documentation/twps0029/tab04.html

import json
from lib import *
import numpy as np
from pprint import pprint
from scipy import interpolate
import sys

# data config
OUTPUT_FILE = "mesh.json"
DATA_FILE = "data.csv"
VALUE_KEY = "percent"
DATA_PRECISION = 3
START_YEAR = 1880
END_YEAR = 2015
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
LENGTH = 150.0
WIDTH = 66.0
HEIGHT = 54.0
BASE_HEIGHT = 2.0
SPOON_HEIGHT = HEIGHT - BASE_HEIGHT
EDGE_RADIUS = 2.0
THICKNESS = 4.8
DISPLACEMENT_DEPTH = 2.0
INSET_WIDTH = 3.0
SPOON_DISTORT_CENTER_X = 0.4

WIDTHS = [(0, 0.25), (0.15, 1.0), (0.5, 0.75), (0.9, 0.4), (1.0, 0.4)]

BASE_WIDTH = WIDTH * 0.5

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
if baseRadiusY > baseRadiusX:
    baseRadiusY = baseRadiusX

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
        edgeLoop = ellipse(VERTICES_PER_EDGE_LOOP, center, r1, r2, center[2], SPOON_DISTORT_CENTER_X)
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
removeIndex = len(mesh.edgeLoops)-len(baseInset)-1
mesh.removeLoop(removeIndex)

# TODO: add base

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

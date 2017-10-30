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

# helper options
ADD_MISSING_YEARS = False
SHOW_GRAPH = False
OUTPUT_SVG = False
SVG_FILE = "data.svg"

# cup config in mm
PRECISION = 8
LENGTH = 140.0
WIDTH = 45.0
HEIGHT = 60.0
EDGE_RADIUS = 2.0
THICKNESS = 4.0
DISPLACEMENT_DEPTH = 2.0

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

# plot data
if SHOW_GRAPH:
    import matplotlib.pyplot as plt
    plt.plot(xs, ys, 'o', xyears, func1(xyears), '-', xyears, func3(xyears), '--')
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

MESH_X = 64
MESH_Y = 64
WIDTHS = [(0, 0.2), (0.2, 1.0), (0.6, 0.4), (0.9, 0.3), (1.0, 0.1)]
func3y = interpolate.interp1d([w[0] for w in WIDTHS], [w[1] for w in WIDTHS], kind='cubic')

# turn data into a mesh
xpoints = np.linspace(0, 1, num=(MESH_X+1))
ypoints = func3y(xpoints)
zpoints = func1(xpoints)
points = list(zip(xpoints, ypoints, zpoints))
points = [(p[0]*LENGTH, p[1]*WIDTH, p[2]*HEIGHT) for p in points]

# generate verts
verts = []
for row in range(MESH_Y+1):
    py = 1.0 * row / MESH_Y
    my = 0
    if py < 0.5:
        my = 0.5 - py
    elif py > 0.5:
        my = -1 * (py - 0.5)
    for col in range(MESH_X+1):
        x = points[col][0]
        y = points[col][1] * my
        z = points[col][2]
        verts.append((x,y,z))

# generate faces
faces = []
for row in range(MESH_Y):
    for col in range(MESH_X):
        v1 = row * (MESH_X+1) + col
        v2 = v1 + 1
        v3 = v1 + MESH_X + 2
        v4 = v1 + MESH_X + 1
        faces.append((v1, v2, v3, v4))

# save data
data = [
    {"name": "spoon", "verts": verts, "edges": [], "faces": faces, "location": [-LENGTH*0.5, 0, 0]}
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

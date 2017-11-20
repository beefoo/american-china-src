# -*- coding: utf-8 -*-

import json
import math
from PIL import Image, ImageDraw
from pprint import pprint
from pyproj import Proj
import sys

INPUT_FILE = "data/DistributionOfSlip.json"
OUTPUT_FILE = "imgMap.png"
TARGET_W = 2048
TARGET_H = 2048

def angleBetweenPoints(p1, p2):
    deltaX = p2[0] - p1[0]
    deltaY = p2[1] - p1[1]
    rad = math.atan2(deltaY, deltaX)
    return math.degrees(rad)

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def rotate(origin, point, angle):
    angle = math.radians(angle)
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

data = []
with open(INPUT_FILE) as f:
    data = json.load(f)

# UTM, 10N is California
utmProj = Proj(proj='utm', zone=10, ellps='WGS84')

# project lon,lat using LCC
for i,d in enumerate(data):
    x,y = utmProj(d["lon"], d["lat"])
    data[i]["x"] = x
    data[i]["y"] = y

# get x,y bounds
xs = [d["x"] for d in data]
ys = [d["y"] for d in data]
xBound = (min(xs), max(xs))
yBound = (max(ys), min(ys))
xLen = abs(xBound[1]-xBound[0])
yLen = abs(yBound[0]-yBound[1])
print "Bounds ratio: %s x %s" % (xLen, yLen)
boundsRatio = xLen / yLen

bWidth = TARGET_W
bHeight = TARGET_H
xOffset = 0
yOffset = 0
if boundsRatio < 1:
    bWidth = TARGET_W * boundsRatio
    xOffset = (TARGET_W-bWidth) * 0.5
else:
    bHeight = TARGET_H * boundsRatio
    yOffset = (TARGET_H-bHeight) * 0.5

# normalize x,y
for i,d in enumerate(data):
    data[i]["x"] = norm(d["x"], xBound[0], xBound[1]) * bWidth + xOffset
    data[i]["y"] = norm(d["y"], yBound[0], yBound[1]) * bHeight + yOffset

# find the distance between the first and last point
p1 = data[0]
p2 = data[-1]
dist = math.hypot(p2["x"] - p1["x"], p2["y"] - p1["y"])

# resize and rotate the pixels around center so that the first and last points are at the center
resizeAmount = TARGET_H / dist
offset = (TARGET_H - TARGET_H * resizeAmount) * 0.5
angle = 90 - angleBetweenPoints((p1["x"], p1["y"]), (p2["x"], p2["y"]))
center = (TARGET_W*0.5, TARGET_H*0.5)
for i,d in enumerate(data):
    x = d["x"] * resizeAmount + offset
    y = d["y"] * resizeAmount + offset
    x, y = rotate(center, (x, y), angle)
    data[i]["x"] = x
    data[i]["y"] = y

imBase = Image.new('RGB', (TARGET_W, TARGET_H), (0,0,0))
draw = ImageDraw.Draw(imBase)

# draw data
for i,d in enumerate(data):
    if i > 0:
        d0 = data[i-1]
        draw.line((d0["x"], d0["y"], d["x"], d["y"]), fill=(255,255,255))

del draw

imBase.save(OUTPUT_FILE)
print "Saved %s" % OUTPUT_FILE

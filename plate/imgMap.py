# -*- coding: utf-8 -*-

import json
import math
import numpy as np
from PIL import Image, ImageDraw
from pprint import pprint
from pyproj import Proj
from scipy import interpolate
import sys

INPUT_FILE = "data/DistributionOfSlip.json"
OUTPUT_FILE = "imgMap.png"
TARGET_W = 2048
TARGET_H = 2048
MIN_NORMAL_LENGTH = 1
MAX_NORMAL_LENGTH = TARGET_W * 0.1

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

def translatePoint(p, degrees, distance):
    radians = math.radians(degrees)
    x2 = p[0] + distance * math.cos(radians)
    y2 = p[1] + distance * math.sin(radians)
    return (x2, y2)

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

im = Image.new('RGB', (TARGET_W, TARGET_H), (255,255,255))
draw = ImageDraw.Draw(im)

# initialize image by making left-of-fault black and right-of-fault white
xs = [d["y"] for d in data]
xs[0] = 0
xs[-1] = TARGET_H
ys = [d["x"] for d in data]
func1 = interpolate.interp1d(xs, ys, kind='linear')
imgData = []
for y in range(TARGET_H):
    for x in range(TARGET_W):
        rgb = (255, 255, 255)
        yp = 1.0 * y / (TARGET_H-1)
        xp = 1.0 * y / (TARGET_W-1)
        xActual = func1(y)
        if x < xActual:
            rgb = (0, 0, 0)
        imgData.append(rgb)
im.putdata(imgData)

# draw data
prevP3 = None
for i,d in enumerate(data):
    if i > 0:
        d0 = data[i-1]
        p1 = (d0["x"], d0["y"])
        p2 = (d["x"], d["y"])
        draw.line([p1, p2], fill=(0,0,0))
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

        # determine the normal
        angle = angleBetweenPoints(p1, p2)
        normal = angle + 90
        p3 = translatePoint(p2, normal, MAX_NORMAL_LENGTH)
        if prevP3:
            p4 = prevP3
        else:
            p4 = translatePoint(p1, normal, MAX_NORMAL_LENGTH)
        prevP3 = p3
        draw.polygon([p1, p2, p3, p4], outline=(255,0,0))

del draw

im.save(OUTPUT_FILE)
print "Saved %s" % OUTPUT_FILE

# -*- coding: utf-8 -*-

import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pprint import pprint
from pyproj import Proj
from scipy import interpolate
import sys

INPUT_FILE = "data/DistributionOfSlip.json"
OUTPUT_FILE = "imgMap.png"
TARGET_W = 2048
TARGET_H = 2048
X_DELTA = int(round(TARGET_W * 0.01))
MIN_Z_DELTA = 1
MAX_Z_DELTA = TARGET_W * 0.1
BLUR_RADIUS = 6

def angleBetweenPoints(p1, p2):
    deltaX = p2[0] - p1[0]
    deltaY = p2[1] - p1[1]
    rad = math.atan2(deltaY, deltaX)
    return math.degrees(rad)

def lerp(a, b, mu):
    return (b-a) * mu + a

def lerpPoint(p1, p2, mu):
    xs = [p1[0], p2[0]]
    ys = [p1[1], p2[1]]
    deltaX = p2[0] - p1[0]
    x = deltaX * mu + p1[0]
    func = interpolate.interp1d(xs, ys)
    y = func(x)
    return (x, y)

def lim(value, v0, v1):
    if value < v0:
        value = v0
    if value > v1:
        value = v1
    return value

def limPoint(p, rangeX, rangeY):
    return (lim(p[0], rangeX[0], rangeX[1]), lim(p[1], rangeY[0], rangeY[1]))

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
slippages = [d["slippageFeet"] for d in data]
slippageMin = min(slippages)
slippageMax = max(slippages)

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

im = Image.new('RGB', (TARGET_W, TARGET_H), (0,0,0))
draw = ImageDraw.Draw(im)

# R = x delta, 255 => highest delta
# G = y delta, 255 => highest delta
# B = z delta, 255 => highest delta

# draw data
print "Drawing fault z direction..."
prevP4 = None
for i,d in enumerate(data):
    if i > 0:
        d0 = data[i-1]
        p1 = (d0["x"], d0["y"])
        p2 = (d["x"], d["y"])
        # dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

        amount = norm(d["slippageFeet"], slippageMin, slippageMax)
        zDelta = lerp(MIN_Z_DELTA, MAX_Z_DELTA, amount)

        # determine the normal
        angle = angleBetweenPoints(p1, p2)
        normal = angle + 90
        if i == 1:
            normal = 180
        p4 = translatePoint(p2, normal, zDelta)
        if prevP4:
            p3 = prevP4
        else:
            p3 = translatePoint(p1, normal, zDelta)
        p3 = limPoint(p3, (0, TARGET_W), (0, TARGET_H))
        p4 = limPoint(p4, (0, TARGET_W), (0, TARGET_H))
        prevP4 = p4

        # draw.polygon([p1, p2, p4, p3], outline=(0,0,255))
        distTop = math.hypot(p4[0] - p1[0], p4[1] - p1[1])
        distBottom = math.hypot(p3[0] - p2[0], p3[1] - p2[1])
        dist = int(round(max([distTop, distBottom])))

        for j in range(dist):
            percent = 1.0 * j / (dist-1)
            pTop = lerpPoint(p1, p3, percent)
            pBottom = lerpPoint(p2, p4, percent)
            pTop = limPoint(pTop, (0, TARGET_W), (0, TARGET_H))
            pBottom = limPoint(pBottom, (0, TARGET_W), (0, TARGET_H))
            b = int(round(255*percent))
            draw.line([pTop, pBottom], fill=(0, 0, b))
del draw

print "Drawing fault x,y direction..."
# make left-of-fault white (total delta) and right-of-fault black (no delta), make a gradient by the edge
xs = [d["y"] for d in data]
xs[0] = 0
xs[-1] = TARGET_H
ys = [d["x"] for d in data]
func1 = interpolate.interp1d(xs, ys, kind='linear')
imgData = list(im.getdata())
newImgData = []
for y in range(TARGET_H):
    for x in range(TARGET_W):
        i = y * TARGET_W + x
        (r, g, b) = imgData[i]
        xActual = func1(y)

        if b == 0 and x < xActual:
            b = 255
        rgb = (0, 0, b)

        if x < xActual:
            rgb = (255, 255, b)
            # make a gradient
            delta = (xActual-x)
            if delta < X_DELTA:
                percent = 1.0 * delta / X_DELTA
                color = int(round(percent * 255))
                rgb = (color, color, b)
        newImgData.append(rgb)
im.putdata(newImgData)

print "Adding blur..."
# add Gaussian filter
im = im.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))

im.save(OUTPUT_FILE)
print "Saved %s" % OUTPUT_FILE

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

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

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

imBase = Image.new('RGB', (TARGET_W, TARGET_H), (255,255,255))
draw = ImageDraw.Draw(imBase)

# draw data
for i,d in enumerate(data):
    if i > 0:
        d0 = data[i-1]
        draw.line((d0["x"], d0["y"], d["x"], d["y"]), fill=(0,0,0))

del draw
imBase.save(OUTPUT_FILE)
print "Saved %s" % OUTPUT_FILE

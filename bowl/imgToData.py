# -*- coding: utf-8 -*-

# python imgToData.py -in data/gotEW.png -out data/gotEW.json

# Data source:
    # USGS, 1906 San Francisco Earthquake - Shaking at Gottingen, Germany
    # https://earthquake.usgs.gov/earthquakes/events/1906calif/18april/got_seismogram.php

import argparse
import json
import math
from PIL import Image, ImageDraw
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/gotNS.png", help="Image input file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/gotNS.json", help="JSON output file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
OUTPUT_FILE = args.OUTPUT_FILE

im = Image.open(INPUT_FILE)
imW, imH = im.size
pixels = im.load()
centerY = None
direction = 0
values = []
maxValue = None

for i in range(imW):
    x = i
    topY = centerY
    bottomY = centerY
    for j in range(imH):
        y = j
        rgb = pixels[x, y]
        # we hit a black pixel
        if rgb[0] < 10:
            # first, define a center
            if centerY is None:
                centerY = j
            elif y < topY:
                topY = y
            elif y > bottomY:
                bottomY = y

    if x <= 0:
        continue

    # determine a direction
    if direction==0:
        if topY < centerY:
            direction = 1
            maxValue = [x, topY]
        elif bottomY > centerY:
            direction = -1
            maxValue = [x, bottomY]
    # we're going from top down
    elif direction > 0:
        if topY < maxValue[1]:
            maxValue = [x, topY]
        elif bottomY > centerY:
            values.append(maxValue)
            direction = -1
            maxValue = [x, bottomY]
    # we're going from bottom to top
    elif direction < 0:
        if bottomY > maxValue[1]:
            maxValue = [x, bottomY]
        elif topY < centerY:
            values.append(maxValue)
            direction = 1
            maxValue = [x, topY]
values.append(maxValue)

# # verify
# imBase = Image.new('RGB', (imW, imH), (255,255,255))
# imBase.paste(im, (0, 0))
# draw = ImageDraw.Draw(imBase)
# for v in values:
#     draw.point((v[0],v[1]), fill=(255,0,0))
# del draw
# imBase.save(INPUT_FILE.replace(".png", "_verified.png"))

# normalize data
data = [(1.0*v[0]/imW, 1.0*v[1]/imH) for v in values]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

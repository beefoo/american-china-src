# -*- coding: utf-8 -*-

import colorsys
import json
import math
from PIL import Image
import sys

# data config
OUTPUT_FILE = "letterTest.json"
PRECISION = 5
WIDTH = 5.0
HEIGHT = 5.0
DEPTH = .2
RESOLUTION = 0.025

im = Image.open("letterTest.png")
imgData = list(im.getdata())
imgW, imgH = im.size

matrix = []
verts = []
faces = []

cols = int(WIDTH / RESOLUTION)
rows = int(HEIGHT / RESOLUTION)

# generate verts
for row in range(rows+1):
    for col in range(cols+1):
        x = col * RESOLUTION
        y = row * RESOLUTION
        z = 0
        if 0 < col < cols and 0 < row < rows:
            ix = int(1.0 * col / cols * imgW)
            iy = int(1.0 * row / rows * imgH)
            i = int(iy * imgW + ix)
            rgb = imgData[i]
            hls = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
            z = -DEPTH * (1.0 - hls[1])
        verts.append((x,y,z))

# generate faces
for row in range(rows):
    for col in range(cols):
        v1 = row * (cols+1) + col
        v2 = v1 + 1
        v3 = v1 + cols + 2
        v4 = v1 + cols + 1
        faces.append((v1, v2, v3, v4))

# save data
data = [
    {"name": "LetterTest", "verts": verts, "edges": [], "faces": faces, "location": [-WIDTH*0.5, -HEIGHT*0.5, 0]}
]

with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

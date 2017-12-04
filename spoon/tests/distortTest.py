# -*- coding: utf-8 -*-

import math
import numpy as np
from PIL import Image, ImageDraw
from pprint import pprint
from scipy import interpolate
import sys

def lerp(a, b, mu):
    return (b-a) * mu + a

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def ellipse(vertices, center, r1, r2, z, distortCenter=False):
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
        e.append((u, v))

    if distortCenter:
        centerX = lerp(-1, 1, distortCenter)
        for i,vert in enumerate(e):
            x, y = vert
            if x <= 0:
                xp = norm(x, -1, 0)
                x = lerp(-1, centerX, xp)
            else:
                xp = norm(x, 0, 1)
                x = lerp(centerX, 1, xp)
            e[i] = (x, y)

    # convert to actual unit
    for i,vert in enumerate(e):
        u, v = vert
        u = u * r1 + center[0]
        v = v * r2 + center[1]
        e[i] = (u,v,z)

    return e

VERTICES_PER_EDGE_LOOP = 16
rx = 800.0
ry = 600.0
center = (1000.0, 1000.0, 0.0)
loop = ellipse(VERTICES_PER_EDGE_LOOP, center, rx, ry, 0, 0.4)

im = Image.new("RGB", (2000, 2000), (255,255,255))
draw = ImageDraw.Draw(im)
colors = [(0,0,0), (255,0,0), (0,255,0), (0,0,255), (255,0,255), (100,100,0), (0,255,255)]

for i,p1 in enumerate(loop):
    p0 = loop[i-1]
    color = colors[i % len(colors)]
    draw.line((p0[0], p0[1], p1[0], p1[1]), fill=color)
    # draw.text((p1[0], p1[1]), str(i), fill=color)

del draw
im.save("distortTest.png")

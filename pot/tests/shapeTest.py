# -*- coding: utf-8 -*-

import math
import numpy as np
from PIL import Image, ImageDraw
from pprint import pprint
from scipy import interpolate
import sys

def bspline(cv, n=100, degree=3, periodic=True):
    """ Calculate n samples on a bspline

        cv :      Array ov control vertices
        n  :      Number of samples to return
        degree:   Curve degree
        periodic: True - Curve is closed
                  False - Curve is open
    """

    # If periodic, extend the point array by count+degree+1
    cv = np.asarray(cv)
    count = len(cv)

    if periodic:
        factor, fraction = divmod(count+degree+1, count)
        cv = np.concatenate((cv,) * factor + (cv[:fraction],))
        count = len(cv)
        degree = np.clip(degree,1,degree)

    # If opened, prevent degree from exceeding count-1
    else:
        degree = np.clip(degree,1,count-1)


    # Calculate knot vector
    kv = None
    if periodic:
        kv = np.arange(0-degree,count+degree+degree-1)
    else:
        kv = np.clip(np.arange(count+degree+1)-degree,0,count-degree)

    # Calculate query range
    u = np.linspace(periodic,(count-degree),n)

    # Calculate result
    return np.array(interpolate.splev(u, (kv,cv.T,degree))).T.tolist()

def shape(points, width, height, vertices, center, z):
    loop = []
    hw = width * 0.5
    hh = height * 0.5

    if vertices > len(points):
        points = bspline(points, n=vertices+1, periodic=True)
        points = points[:-1]
        offset = vertices / 8
        a = points[(vertices-offset):]
        b = points[:(vertices-offset)]
        points = a + b

    for p in points:
        x = p[0] * width
        y = p[1] * height
        x =  x - hw + center[0]
        y =  y - hh + center[1]
        loop.append((x, y, z))
    return loop

WIDTH = 110.0
LENGTH = 160.0
HEIGHT = 125.0
EDGE_RADIUS = 4.0
EDGE_X = EDGE_RADIUS / LENGTH
EDGE_Y = EDGE_RADIUS / WIDTH
BODY1_X = 0.333
BODY1_W = 0.7
BODY1_Y = (1.0 - BODY1_W) * 0.5
BODY2_X = 0.667
BODY2_W = 0.95
BODY2_Y = (1.0 - BODY2_W) * 0.5
NOSE_X = 0.05
NOSE_W = 0.2
NOSE_Y = (1.0 - NOSE_W) * 0.5
NOSE_POINT_W = NOSE_W * 0.1667
NOSE_POINT_Y = (1.0 - NOSE_POINT_W) * 0.5
SHAPE = [
    (NOSE_X, NOSE_Y),       # top nose
    (BODY1_X, BODY1_Y),     # top body 1
    (BODY2_X, BODY2_Y),     # top body 2
    (1.0-EDGE_X, 0.0),      # top right, edge before
    (1.0, 0.0),             # top right
    (1.0, EDGE_Y),          # top right, edge after
    (1.0, 0.5),             # middle right
    (1.0, 1.0-EDGE_Y),      # bottom right, edge before
    (1.0, 1.0),             # bottom right
    (1.0-EDGE_X, 1.0),      # bottom right, edge after
    (BODY2_X, 1.0-BODY2_Y),     # bottom body 2
    (BODY1_X, 1.0-BODY1_Y),   # bottom body 1
    (NOSE_X, 1.0-NOSE_Y),   # bottom nose
    (0.0, 1.0-NOSE_POINT_Y),    # bottom nose point
    (0.0, 0.5),             # middle left (point of iron)
    (0.0, NOSE_POINT_Y),# top nose point
]

VERTICES_PER_EDGE_LOOP = 16 * 2**1
x = LENGTH*10
y = WIDTH*10
z = 0
center = (1000.0, 1000.0, 0.0)
loop1 = shape(SHAPE, x, y, 16, center, z)
loop2 = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)

im = Image.new("RGB", (2000, 2000), (255,255,255))
draw = ImageDraw.Draw(im)
colors = [(0,0,0), (255,0,0), (0,255,0), (0,0,255), (255,0,255), (100,100,0), (0,255,255)]

# for i,p1 in enumerate(loop1):
#     p0 = loop1[i-1]
#     color = colors[i % len(colors)]
#     draw.line((p0[0], p0[1], p1[0], p1[1]), fill=color)
#     draw.text((p1[0], p1[1]), str(i), fill=color)

for i,p1 in enumerate(loop2):
    p0 = loop2[i-1]
    color = colors[i % len(colors)]
    draw.line((p0[0], p0[1], p1[0], p1[1]), fill=color)
    draw.text((p1[0], p1[1]), str(i), fill=color)

del draw
im.save("shapeTest.png")

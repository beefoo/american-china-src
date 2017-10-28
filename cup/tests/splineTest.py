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

def roundedSquare(vertices, c, w, z, r):
    square = []
    hw = w * 0.5

    # top left -> top right
    y = c[1] - hw
    x = c[0] - hw
    square += [(x, y), (x + r, y), (c[0], y), (x + w - r, y)]
    # top right to bottom right
    x = c[0] + hw
    y = c[1] - hw
    square += [(x, y), (x, y+r), (x, c[1]), (x, y + w - r)]
    # bottom right to bottom left
    y = c[1] + hw
    x = c[0] + hw
    square += [(x, y), (x - r, y), (c[0], y), (x - w + r, y)]
    # bottom left to top left
    x = c[0] - hw
    y = c[1] + hw
    square += [(x, y), (x, y - r), (x, c[1]), (x, y - w + r)]

    # use b-spline for rounding
    rounded = bspline(square, vertices+1)
    rounded = rounded[:-1]
    offset = vertices / 8 - 1
    a = rounded[(vertices-offset):]
    b = rounded[:(vertices-offset)]
    rounded = a + b

    # add z
    rounded = [(r[0], r[1], z) for r in rounded]
    return rounded

square = roundedSquare(64, (0,0), 400, 0, 100)
square = [(s[0] + 300, s[1] + 300) for s in square]

im = Image.new("RGB", (600, 600), (255,255,255))
draw = ImageDraw.Draw(im)
colors = [(0,0,0), (255,0,0), (0,255,0), (0,0,255), (255,0,255), (100,100,0), (0,255,255)]

draw.point((100,100), fill=(0,0,0))
draw.point((500,100), fill=(0,0,0))
draw.point((500,500), fill=(0,0,0))
draw.point((100,500), fill=(0,0,0))

for i, p1 in enumerate(square):
    color = colors[i % len(colors)]
    p0 = square[i-1]
    draw.line((p0[0], p0[1], p1[0], p1[1]), fill=color)
    draw.text((p0[0], p0[1]), str(i), fill=color)

del draw
im.save("splineTest.png")

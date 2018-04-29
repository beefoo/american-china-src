# -*- coding: utf-8 -*-

import math
import numpy as np
from scipy import interpolate

def angleBetweenPoints(p1, p2):
    deltaX = p2[0] - p1[0]
    deltaY = p2[1] - p1[1]
    rad = math.atan2(deltaY, deltaX)
    return math.degrees(rad)

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

def circle(vertices, center, r, z):
    angle = 360.0 / vertices

    result = []
    for i in range(vertices):
        a = i * angle
        p = translatePoint(center, a, r)
        result.append((p[0], p[1], z))

    return result

def lerp(a, b, mu):
    return (b-a) * mu + a

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def roundP(vList, precision):
    rounded = []
    for v in vList:
        t = (round(v[0], precision), round(v[1], precision), round(v[2], precision))
        rounded.append(t)
    return rounded

def savitzkyGolay(y, window_size, order=3, deriv=0, rate=1):
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    y = np.array(y)
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * math.factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')

def translatePoint(p, degrees, distance):
    radians = math.radians(degrees)
    x2 = p[0] + distance * math.cos(radians)
    y2 = p[1] + distance * math.sin(radians)
    return (x2, y2)

class Mesh:

    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces = []
        self.edgeLoops = []

    def addEdgeLoop(self, loop):
        self.edgeLoops.append(loop)

    def addEdgeLoops(self, loops):
        for loop in loops:
            self.addEdgeLoop(loop)

    def closeEdgeLoop(self, loop, indexOffset, end=False):
        faces = []
        loopLen = len(loop)
        for i, v in enumerate(loop):
            a = i
            b = i+1
            if b >= loopLen:
                b = 0
            if end:
                faces.append((indexOffset+loopLen, indexOffset+a, indexOffset+b))
            else:
                faces.append((indexOffset, indexOffset+a+1, indexOffset+b+1))
        self.faces += faces

    def joinEdgeLoops(self, loopA, loopB, indexOffset):
        faces = []
        aLen = len(loopA)
        bLen = len(loopB)

        if aLen != bLen:
            print "Warning: length mismatch"

        # assume equal number of vertices
        for i in range(aLen):
            v1 = i
            v2 = i + 1
            v3 = i + 1 + aLen
            v4 = i + aLen
            if v2 >= aLen:
                v2 = 0
                v3 = aLen
            faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))

        self.faces += faces

    # join all the edge loop together
    def processEdgeloops(self):
        indexOffset = 0

        for i, edgeLoop in enumerate(self.edgeLoops):

            # add loop's vertices
            self.verts += edgeLoop

            # skip start
            if i <= 0:
                continue

            prev = self.edgeLoops[i-1]

            # if this is the first or last edge loop, add tris
            if len(prev) == 1:
                self.closeEdgeLoop(edgeLoop, indexOffset)

            elif len(edgeLoop) == 1:
                self.closeEdgeLoop(prev, indexOffset, end=True)

            else:
                self.joinEdgeLoops(prev, edgeLoop, indexOffset)

            indexOffset += len(prev)

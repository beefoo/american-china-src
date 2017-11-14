import math
import numpy as np
from PIL import Image, ImageDraw
from pprint import pprint
from scipy import interpolate
import sys

def angleBetweenPoints(p1, p2):
    deltaX = p2[0] - p1[0]
    deltaY = p2[1] - p1[1]
    rad = math.atan2(deltaY, deltaX)
    return math.degrees(rad)

def translatePoint(p, degrees, distance):
    radians = math.radians(degrees)
    x2 = p[0] + distance * math.cos(radians)
    y2 = p[1] + distance * math.sin(radians)
    return (x2, y2)

p1 = (200, 20)
p2 = (150, 40)
p3 = (100, 60)

angle = angleBetweenPoints(p1, p3)
normal = angle + 90
pn = translatePoint(p2, normal, 100)

im = Image.new("RGB", (600, 600), (255,255,255))
draw = ImageDraw.Draw(im)

xd = 150
yd = 220
draw.line((xd+p1[0], yd+p1[1], xd+p2[0], yd+p2[1]), fill=(255,0,0))
draw.line((xd+p2[0], yd+p2[1], xd+p3[0], yd+p3[1]), fill=(0,255,0))
draw.line((xd+p2[0], yd+p2[1], xd+pn[0], yd+pn[1]), fill=(0,0,255))

del draw
im.save("normalTest.png")

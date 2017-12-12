# -*- coding: utf-8 -*-

import json
import math
import os
from PIL import Image, ImageDraw
from pprint import pprint
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *

SCALE = 15
OFFSET_X = 900
OFFSET_Y = 1000

# START CONFIG

# cup config in mm
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 0 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 1
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
HALF_VERTICES_PER_EDGE_LOOP = VERTICES_PER_EDGE_LOOP / 2
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

CENTER = (0, 0, 0)

WIDTH = 110.0
LENGTH = 150.0
HEIGHT = 125.0
EDGE_RADIUS = 4.0
THICKNESS = 6.0
BASE_HEIGHT = 3.0
BASE_INSET_HEIGHT = 3.0
BODY_TOP_INSET_HEIGHT = 3.0

BASE_W = 0.9
BASE_L = 0.95
BASE_INSET_W = (BASE_W * 0.8) * WIDTH
BASE_INSET_L = (BASE_L * 0.8875) * LENGTH
BODY_BTM = 0.95
BODY_TOP = 0.85
BODY_TOP_INSET = BODY_TOP - 0.1

TOP_CENTER_OFFSET = (BODY_BTM - BODY_TOP) * 0.5
OUTER_TOP_CENTER = (LENGTH*TOP_CENTER_OFFSET, 0, 0)
TOP_CENTER = (LENGTH*TOP_CENTER_OFFSET*1.75, 0, 0)
INNER_TOP_CENTER = (LENGTH*TOP_CENTER_OFFSET, 0, 0)

BODY_HEIGHT = 0.475 * (HEIGHT-BASE_HEIGHT)
HANDLE_HEIGHT = (HEIGHT-BASE_HEIGHT) - BODY_HEIGHT
BODY_BASE_HEIGHT = BODY_HEIGHT * 0.2

T2 = THICKNESS*2
ER2 = EDGE_RADIUS*2

TOP_HOLE_EDGE = 4.0
TOP_HOLE_WIDTH = WIDTH*BODY_TOP_INSET*0.725-ER2
TOP_HOLE_LENGTH = LENGTH*BODY_TOP_INSET*0.575-ER2
TOP_HOLE_WIDTH_INNER = TOP_HOLE_WIDTH - 6.0
TOP_HOLE_LENGTH_INNER = TOP_HOLE_LENGTH - 6.0
TOP_HOLE_OUTER_HEIGHT = BODY_HEIGHT - 3.0
TOP_HOLE_INNER_HEIGHT = TOP_HOLE_OUTER_HEIGHT - 3.0

# Define the shape of the cross-section of the iron, clock-wise starting from top left
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

# Define the shape of the hole
HOLE_NOSE_W = NOSE_W * 2.0
HOLE_NOSE_Y = (1.0 - HOLE_NOSE_W) * 0.5
HOLE_NOSE_POINT_W = HOLE_NOSE_W * 0.25
HOLE_NOSE_POINT_Y = (1.0 - HOLE_NOSE_POINT_W) * 0.5
HOLE_EDGE_X = EDGE_X*4
HOLE_EDGE_Y = EDGE_Y*4
SHAPE_HOLE = [
    (NOSE_X, HOLE_NOSE_Y),       # top nose
    (BODY1_X, BODY1_Y),     # top body 1
    (BODY2_X, BODY2_Y),     # top body 2
    (1.0-HOLE_EDGE_X, 0.0),      # top right, edge before
    (1.0, 0.0),             # top right
    (1.0, HOLE_EDGE_Y),          # top right, edge after
    (1.0, 0.5),             # middle right
    (1.0, 1.0-HOLE_EDGE_Y),      # bottom right, edge before
    (1.0, 1.0),             # bottom right
    (1.0-HOLE_EDGE_X, 1.0),      # bottom right, edge after
    (BODY2_X, 1.0-BODY2_Y),     # bottom body 2
    (BODY1_X, 1.0-BODY1_Y),   # bottom body 1
    (NOSE_X, 1.0-HOLE_NOSE_Y),   # bottom nose
    (0.0, 1.0-HOLE_NOSE_POINT_Y),    # bottom nose point
    (0.0, 0.5),             # middle left (point of iron)
    (0.0, HOLE_NOSE_POINT_Y),# top nose point
]

# config for handle
HANDLE_VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**(SUBDIVIDE_X-1)
HANDLE_BOTTOM = BODY_HEIGHT
HANDLE_TOP = HEIGHT
HANDLE_SIDE_LENGTH = 7.0
HANDLE_SIDE_WIDTH = 9.0
HANDLE_SIDE_BASE_LENGTH = HANDLE_SIDE_LENGTH + 5.0
HANDLE_SIDE_BASE_WIDTH = HANDLE_SIDE_WIDTH + 5.0
HANDLE_SIDE_BASE_HEIGHT = 5.0
HANDLE_SIDE_BULGE_LENGTH_LEFT = 20.0
HANDLE_SIDE_BULGE_LENGTH_RIGHT = 20.0
HANDLE_SIDE_BLUGE_HEIGHT_LEFT = lerp(HANDLE_BOTTOM, HANDLE_TOP, 0.6)
HANDLE_SIDE_BLUGE_HEIGHT_RIGHT = lerp(HANDLE_BOTTOM, HANDLE_TOP, 0.6)
HANDLE_SIDE_BLUGE_MIDHEIGHT_LEFT = lerp(HANDLE_BOTTOM, HANDLE_TOP, 0.33)
HANDLE_SIDE_BLUGE_MIDHEIGHT_RIGHT = lerp(HANDLE_BOTTOM, HANDLE_TOP, 0.33)

HANDLE_TOP_NOTCH_LENGTH = 2.0
HANDLE_TOP_RADIUS_FROM = 6.0
HANDLE_TOP_NOTCH_RADIUS_FROM = HANDLE_TOP_RADIUS_FROM - 1.0
HANDLE_TOP_RADIUS_TO = 7.0
HANDLE_TOP_NOTCH_RADIUS_TO = HANDLE_TOP_RADIUS_TO - 0.75
HANDLE_TOP_CENTER_HEIGHT = HANDLE_TOP - HANDLE_TOP_RADIUS_TO
HTCH = HANDLE_TOP_CENTER_HEIGHT
HANDLE_EDGE_RADIUS = 2.0
HANDLE_TOP_SIDE_OFFSET = 8.0
HANDLE_TOP_CENTER_LENGTH = 8.0

BODY_TOP_INSET_EDGE_X_LEFT = -(LENGTH*BODY_TOP_INSET-EDGE_RADIUS) * 0.5 + OUTER_TOP_CENTER[0]
TOP_HOLE_X_LEFT = -(TOP_HOLE_LENGTH+TOP_HOLE_EDGE) * 0.5 + TOP_CENTER[0]
BODY_TOP_INSET_EDGE_X_RIGHT = (LENGTH*BODY_TOP_INSET-EDGE_RADIUS) * 0.5 + OUTER_TOP_CENTER[0]
TOP_HOLE_X_RIGHT = (TOP_HOLE_LENGTH+TOP_HOLE_EDGE) * 0.5 + TOP_CENTER[0]

HANDLE_LEFT_CENTER = ((BODY_TOP_INSET_EDGE_X_LEFT + TOP_HOLE_X_LEFT) * 0.425, 0, HANDLE_BOTTOM)
HANDLE_LEFT_CENTER_BULGE = (HANDLE_LEFT_CENTER[0]-HANDLE_SIDE_BULGE_LENGTH_LEFT, 0, HANDLE_SIDE_BLUGE_HEIGHT_LEFT)
HANDLE_RIGHT_CENTER = ((BODY_TOP_INSET_EDGE_X_RIGHT + TOP_HOLE_X_RIGHT) * 0.5, 0, HANDLE_BOTTOM)
HANDLE_RIGHT_CENTER_BULGE = (HANDLE_RIGHT_CENTER[0]+HANDLE_SIDE_BULGE_LENGTH_RIGHT, 0, HANDLE_SIDE_BLUGE_HEIGHT_RIGHT)
HANDLE_TOP_BULGE = 4.0

# END CONFIG

im = Image.new("RGB", (2000, 2000), (255,255,255))
draw = ImageDraw.Draw(im)
colors = [(0,0,0), (255,0,0), (0,255,0), (0,0,255), (255,0,255), (100,100,0), (0,255,255)]

loopFrom = shape(SHAPE, LENGTH*BODY_TOP_INSET-EDGE_RADIUS, WIDTH*BODY_TOP_INSET-EDGE_RADIUS, VERTICES_PER_EDGE_LOOP, OUTER_TOP_CENTER, BODY_HEIGHT)
loopTo = shape(SHAPE_HOLE, TOP_HOLE_LENGTH+TOP_HOLE_EDGE, TOP_HOLE_WIDTH+TOP_HOLE_EDGE, VERTICES_PER_EDGE_LOOP, TOP_CENTER, BODY_HEIGHT)
lerpCount = HALF_VERTICES_PER_EDGE_LOOP/4+1

leftHandleVertStart = VERTICES_PER_EDGE_LOOP - VERTICES_PER_EDGE_LOOP/4 + VERTICES_PER_EDGE_LOOP/16
leftHandleVertEnd = VERTICES_PER_EDGE_LOOP - VERTICES_PER_EDGE_LOOP/16
rightHandleVertStart = VERTICES_PER_EDGE_LOOP/4 + VERTICES_PER_EDGE_LOOP/16
rightHandleVertEnd = VERTICES_PER_EDGE_LOOP/2 - VERTICES_PER_EDGE_LOOP/16

LERP_EDGE_RADIUS = 1.5
# left handle lerp
L_LERP_LEFT_X = HANDLE_LEFT_CENTER[0] - HANDLE_SIDE_BASE_LENGTH * 0.5 - LERP_EDGE_RADIUS
L_LERP_RIGHT_X = HANDLE_LEFT_CENTER[0] + HANDLE_SIDE_BASE_LENGTH * 0.5 + LERP_EDGE_RADIUS
L_LERP_TOP_Y = HANDLE_LEFT_CENTER[1] - HANDLE_SIDE_BASE_WIDTH * 0.5 - LERP_EDGE_RADIUS
L_LERP_BOTTOM_Y = HANDLE_LEFT_CENTER[1] + HANDLE_SIDE_BASE_WIDTH * 0.5 + LERP_EDGE_RADIUS
# right handle lerp
R_LERP_LEFT_X = HANDLE_RIGHT_CENTER[0] - HANDLE_SIDE_BASE_LENGTH * 0.5 - LERP_EDGE_RADIUS
R_LERP_RIGHT_X = HANDLE_RIGHT_CENTER[0] + HANDLE_SIDE_BASE_LENGTH * 0.5 + LERP_EDGE_RADIUS
R_LERP_TOP_Y = HANDLE_RIGHT_CENTER[1] - HANDLE_SIDE_BASE_WIDTH * 0.5 - LERP_EDGE_RADIUS
R_LERP_BOTTOM_Y = HANDLE_RIGHT_CENTER[1] + HANDLE_SIDE_BASE_WIDTH * 0.5 + LERP_EDGE_RADIUS
loops = [loopFrom]
for i in range(lerpCount):
    mu = 1.0 * (i+1) / (lerpCount+1)
    loop = lerpEdgeloop(loopFrom, loopTo, mu)
    for j,v in enumerate(loop):
        # adjust right handle
        if rightHandleVertStart <= j <= rightHandleVertEnd:
            x, y, z = v
            # adjust top/bottom edge
            if j==rightHandleVertStart:
                y = R_LERP_TOP_Y
            elif j==rightHandleVertStart+1:
                y = R_LERP_TOP_Y + LERP_EDGE_RADIUS
            elif j==rightHandleVertEnd-1:
                y = R_LERP_BOTTOM_Y - LERP_EDGE_RADIUS
            elif j==rightHandleVertEnd:
                y = R_LERP_BOTTOM_Y
            # adjust left/right edge
            if i==0:
                x = R_LERP_RIGHT_X
            elif i==lerpCount-1:
                x = R_LERP_LEFT_X
            loop[j] = (x, y, z)
        # adjust left handle
        elif leftHandleVertStart-1 <= j <= leftHandleVertEnd+1:
            x, y, z = v
            # adjust left/right edge
            mu = 1.0 * i / (lerpCount-1)
            x = lerp(L_LERP_LEFT_X, L_LERP_RIGHT_X, mu)
            mu = norm(j, leftHandleVertStart, leftHandleVertEnd)
            if mu > 1.0:
                y = R_LERP_TOP_Y - 1.0
            elif mu < 0.0:
                y = R_LERP_BOTTOM_Y + 1.0
            else:
                y = lerp(R_LERP_BOTTOM_Y, R_LERP_TOP_Y, mu)
            loop[j] = (x, y, z)

    loops.append(loop)
loops.append(loopTo)

loop = roundedRect(HANDLE_VERTICES_PER_EDGE_LOOP, HANDLE_LEFT_CENTER, HANDLE_SIDE_BASE_LENGTH, HANDLE_SIDE_BASE_WIDTH, HANDLE_BOTTOM, HANDLE_EDGE_RADIUS)
loops.append(loop)

loop = roundedRect(HANDLE_VERTICES_PER_EDGE_LOOP, HANDLE_RIGHT_CENTER, HANDLE_SIDE_BASE_LENGTH, HANDLE_SIDE_BASE_WIDTH, HANDLE_BOTTOM, HANDLE_EDGE_RADIUS)
loop = rotateY(loop, HANDLE_RIGHT_CENTER, 180.0)
loops.append(loop)



pradius = 5
for i,loop in enumerate(loops):
    color = (0,0,0)
    isHandle = (len(loop)==HANDLE_VERTICES_PER_EDGE_LOOP)
    if isHandle:
        color = (0,255,0)
    for j,p1 in enumerate(loop):
        p0 = loop[j-1]
        pcolor = color
        lcolor = color
        if not isHandle and i > 0 and i < len(loops)-3 and (leftHandleVertStart < j <= leftHandleVertEnd or rightHandleVertStart < j <= rightHandleVertEnd):
            lcolor = (255,0,0)
        if not isHandle and i > 0 and i < len(loops)-3 and (leftHandleVertStart < j <= leftHandleVertEnd+1 or rightHandleVertStart < j <= rightHandleVertEnd+1):
            pcolor = (255,0,0)
        x0 = p0[0] * SCALE + OFFSET_X
        y0 = p0[1] * SCALE + OFFSET_Y
        x1 = p1[0] * SCALE + OFFSET_X
        y1 = p1[1] * SCALE + OFFSET_Y
        draw.line((x0, y0, x1, y1), fill=lcolor)
        draw.ellipse([(x0-pradius, y0-pradius), (x0+pradius, y0+pradius)], fill=pcolor)
        # draw.text((p1[0], p1[1]), str(i), fill=color)

del draw
im.save("holeTest.png")

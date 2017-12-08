# -*- coding: utf-8 -*-

import json
from lib import *
import math
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 8

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
TOP_CENTER = (LENGTH*TOP_CENTER_OFFSET*1.5, 0, 0)
INNER_TOP_CENTER = (LENGTH*TOP_CENTER_OFFSET, 0, 0)

BODY_HEIGHT = 0.475 * (HEIGHT-BASE_HEIGHT)
HANDLE_HEIGHT = (HEIGHT-BASE_HEIGHT) - BODY_HEIGHT
BODY_BASE_HEIGHT = BODY_HEIGHT * 0.2

T2 = THICKNESS*2
ER2 = EDGE_RADIUS*2

print "Check: %s > %s" % (BODY_BASE_HEIGHT-EDGE_RADIUS, EDGE_RADIUS)

# define pot: x, y, z
POT_OUTER = [
    (BASE_INSET_L-ER2, BASE_INSET_W-ER2, BASE_INSET_HEIGHT),                     # base inset edge
    (BASE_INSET_L, BASE_INSET_W, BASE_INSET_HEIGHT),                             # base inset
    (BASE_INSET_L, BASE_INSET_W, 0),                                             # base inner
    (LENGTH*BASE_L, WIDTH*BASE_W, 0),                                            # base outer bottom
    (LENGTH*BASE_L, WIDTH*BASE_W, BASE_HEIGHT),                                  # base outer top
    (LENGTH, WIDTH, BASE_HEIGHT),                                                # body bottom
    (LENGTH, WIDTH, BASE_HEIGHT+EDGE_RADIUS),                                    # base outer edge
    (LENGTH, WIDTH, BODY_BASE_HEIGHT-EDGE_RADIUS),                               # body base edge before
    (LENGTH, WIDTH, BODY_BASE_HEIGHT),                                           # body base top
    # (LENGTH*BODY_BTM, WIDTH*BODY_BTM, BODY_BASE_HEIGHT),                         # body bottom
    (LENGTH*BODY_BTM, WIDTH*BODY_BTM, BODY_BASE_HEIGHT+EDGE_RADIUS),             # body bottom edge after
    (LENGTH*BODY_BTM, WIDTH*BODY_BTM, BODY_BASE_HEIGHT+ER2),                     # body bottom edge after edge
    # (LENGTH*BODY_TOP, WIDTH*BODY_TOP, BODY_HEIGHT-EDGE_RADIUS),                  # body top edge before
    (LENGTH*BODY_TOP, WIDTH*BODY_TOP, BODY_HEIGHT-BODY_TOP_INSET_HEIGHT, OUTER_TOP_CENTER),               # body top
    (LENGTH*BODY_TOP_INSET, WIDTH*BODY_TOP_INSET, BODY_HEIGHT-BODY_TOP_INSET_HEIGHT, OUTER_TOP_CENTER),   # body top inset bottom
    (LENGTH*BODY_TOP_INSET, WIDTH*BODY_TOP_INSET, BODY_HEIGHT, OUTER_TOP_CENTER),                         # body top inset top
    (LENGTH*BODY_TOP_INSET-EDGE_RADIUS, WIDTH*BODY_TOP_INSET-EDGE_RADIUS, BODY_HEIGHT, OUTER_TOP_CENTER),          # body top inset top
]
print "Top inset length: %scm" % (LENGTH*BODY_TOP_INSET*0.1)

TOP_HOLE_EDGE = 4.0
TOP_HOLE_WIDTH = WIDTH*BODY_TOP_INSET*0.725-ER2
TOP_HOLE_LENGTH = LENGTH*BODY_TOP_INSET*0.575-ER2
TOP_HOLE_WIDTH_INNER = TOP_HOLE_WIDTH - 6.0
TOP_HOLE_LENGTH_INNER = TOP_HOLE_LENGTH - 6.0
TOP_HOLE_OUTER_HEIGHT = BODY_HEIGHT - 3.0
TOP_HOLE_INNER_HEIGHT = TOP_HOLE_OUTER_HEIGHT - 3.0
print "Top opening is %scm x %scm" % (TOP_HOLE_LENGTH_INNER*0.1, TOP_HOLE_WIDTH_INNER*0.1)
POT_TOP = [
    (TOP_HOLE_LENGTH+TOP_HOLE_EDGE, TOP_HOLE_WIDTH+TOP_HOLE_EDGE, BODY_HEIGHT),              # top hole edge
    (TOP_HOLE_LENGTH, TOP_HOLE_WIDTH, BODY_HEIGHT),                                      # top hole
    (TOP_HOLE_LENGTH, TOP_HOLE_WIDTH, TOP_HOLE_OUTER_HEIGHT),                            # top hole bottom
    (TOP_HOLE_LENGTH_INNER, TOP_HOLE_WIDTH_INNER, TOP_HOLE_OUTER_HEIGHT),                # top inner hole
    (TOP_HOLE_LENGTH_INNER, TOP_HOLE_WIDTH_INNER, TOP_HOLE_INNER_HEIGHT),                # top inner hole bottom
    (TOP_HOLE_LENGTH_INNER+ER2, TOP_HOLE_WIDTH_INNER+ER2, TOP_HOLE_INNER_HEIGHT),  # top inner hole bottom edge
]

INNER_BODY_TOP = TOP_HOLE_INNER_HEIGHT
INNER_BODY_BOTTOM = BODY_BASE_HEIGHT
POT_INNER = [
    (LENGTH*BODY_TOP-T2-ER2, WIDTH*BODY_TOP-T2-ER2, INNER_BODY_TOP, INNER_TOP_CENTER),     # inner body top edge
    (LENGTH*BODY_TOP-T2, WIDTH*BODY_TOP-T2, INNER_BODY_TOP, INNER_TOP_CENTER),             # inner body top
    (LENGTH*BODY_BTM-T2, WIDTH*BODY_BTM-T2, INNER_BODY_BOTTOM+ER2*2),     # inner body bottom edge before
    (LENGTH*BODY_BTM-T2, WIDTH*BODY_BTM-T2, INNER_BODY_BOTTOM),                 # inner body bottom
    (LENGTH*BODY_BTM-T2-ER2*4, WIDTH*BODY_BTM-T2-ER2*4, INNER_BODY_BOTTOM),         # inner body bottom edge after
]
potInnerLen = len(POT_INNER)

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

# build the mesh
mesh = Mesh()

# build the outer pot
for i,p in enumerate(POT_OUTER):
    if len(p)==4:
        x, y, z, center = p
    else:
        x, y, z = p
        center = CENTER

    if i <= 0:
        loops = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)
        mesh.addEdgeLoops(loops)
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)
        mesh.addEdgeLoop(loop)

# interpolate between outer pot and top hole; this is where the handle will be placed
loopFrom = mesh.edgeLoops[-1][:]
x, y, z = POT_TOP[0]
loopTo = shape(SHAPE_HOLE, x, y, VERTICES_PER_EDGE_LOOP, TOP_CENTER, z)
lerpCount = HALF_VERTICES_PER_EDGE_LOOP/4+1
HANDLE_LOOP_START = len(mesh.edgeLoops)
HANDLE_LOOP_END = HANDLE_LOOP_START + lerpCount
leftHandleVertStart = VERTICES_PER_EDGE_LOOP - VERTICES_PER_EDGE_LOOP/4 + VERTICES_PER_EDGE_LOOP/16
leftHandleVertEnd = VERTICES_PER_EDGE_LOOP - VERTICES_PER_EDGE_LOOP/16
rightHandleVertStart = VERTICES_PER_EDGE_LOOP/4 + VERTICES_PER_EDGE_LOOP/16
rightHandleVertEnd = VERTICES_PER_EDGE_LOOP/2 - VERTICES_PER_EDGE_LOOP/16
for i in range(lerpCount):
    mu = 1.0 * (i+1) / (lerpCount+2)
    loop = lerpEdgeloop(loopFrom, loopTo, mu)

    for j,v in enumerate(loop):
        # edge-edge-edge-edge-edge
        if i==0:
            if rightHandleVertStart <= j <= rightHandleVertEnd or leftHandleVertStart <= j <= leftHandleVertEnd:
                loop[j] = v # TODO
        # edge-edge-edge-edge-edge
        elif i >= lerpCount-1:
            if rightHandleVertStart <= j <= rightHandleVertEnd or leftHandleVertStart <= j <= leftHandleVertEnd:
                loop[j] = v # TODO
        # edge-hole-hole-hole-edge
        else:
            # this is a hole
            if rightHandleVertStart < j < rightHandleVertEnd or leftHandleVertStart < j < leftHandleVertEnd:
                loop[j] = False

            # this is the edge
            if j==rightHandleVertStart:
                loop[j] = v # TODO
            elif j==rightHandleVertEnd:
                loop[j] = v # TODO
            elif j==leftHandleVertStart:
                loop[j] = v # TODO
            elif j==leftHandleVertEnd:
                loop[j] = v # TODO

    mesh.addEdgeLoop(loop)

# build the top hole of the pot
for i,p in enumerate(POT_TOP):
    x, y, z = p
    loop = shape(SHAPE_HOLE, x, y, VERTICES_PER_EDGE_LOOP, TOP_CENTER, z)
    mesh.addEdgeLoop(loop)


# build the inner pot
for i,p in enumerate(POT_INNER):
    if len(p)==4:
        x, y, z, center = p
    else:
        x, y, z = p
        center = CENTER

    if i >= potInnerLen-1:
        loops = shapeMesh(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z, True)
        mesh.addEdgeLoops(loops)
    else:
        loop = shape(SHAPE, x, y, VERTICES_PER_EDGE_LOOP, center, z)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

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

HANDLE_LEFT_CENTER = ((BODY_TOP_INSET_EDGE_X_LEFT + TOP_HOLE_X_LEFT) * 0.45, 0, HANDLE_BOTTOM)
HANDLE_LEFT_CENTER_BULGE = (HANDLE_LEFT_CENTER[0]-HANDLE_SIDE_BULGE_LENGTH_LEFT, 0, HANDLE_SIDE_BLUGE_HEIGHT_LEFT)
HANDLE_RIGHT_CENTER = ((BODY_TOP_INSET_EDGE_X_RIGHT + TOP_HOLE_X_RIGHT) * 0.5, 0, HANDLE_BOTTOM)
HANDLE_RIGHT_CENTER_BULGE = (HANDLE_RIGHT_CENTER[0]+HANDLE_SIDE_BULGE_LENGTH_RIGHT, 0, HANDLE_SIDE_BLUGE_HEIGHT_RIGHT)
HANDLE_TOP_BULGE = 4.0

# handle left
# x, y, z, center
HANDLE_LEFT = [
    (HANDLE_SIDE_BASE_LENGTH, HANDLE_SIDE_BASE_WIDTH, HANDLE_BOTTOM, HANDLE_LEFT_CENTER),
    (HANDLE_SIDE_BASE_LENGTH, HANDLE_SIDE_BASE_WIDTH, HANDLE_BOTTOM+HANDLE_SIDE_BASE_HEIGHT, HANDLE_LEFT_CENTER),
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HANDLE_BOTTOM+HANDLE_SIDE_BASE_HEIGHT, HANDLE_LEFT_CENTER),
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HANDLE_SIDE_BLUGE_MIDHEIGHT_LEFT, HANDLE_LEFT_CENTER),
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HANDLE_SIDE_BLUGE_HEIGHT_LEFT, HANDLE_LEFT_CENTER_BULGE)
]

# handle top
HT_ER = EDGE_RADIUS
HT_NL = HANDLE_TOP_NOTCH_LENGTH
HT_SO = HANDLE_TOP_SIDE_OFFSET
HT_CL = HANDLE_TOP_CENTER_LENGTH
HANDLE_TOP = [
    # (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HTCH, (HANDLE_LEFT_CENTER[0]-HT_ER-HANDLE_TOP_BULGE, 0, HTCH), 'r'), # left rectangle edge
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HTCH, (HANDLE_LEFT_CENTER[0]-HT_ER, 0, HTCH), 'r'), # left rectangle edge
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HTCH, addZ(HANDLE_LEFT_CENTER, HTCH), 'r'), # left rectangle
    (HANDLE_TOP_RADIUS_FROM, HANDLE_TOP_RADIUS_FROM, HTCH, (HANDLE_LEFT_CENTER[0]+HT_SO, 0, HTCH), 'e'), # left ellipse over

    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]-HT_CL*0.5-HT_NL-HT_ER, 0, HTCH), 'e'), # left center edge
    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]-HT_CL*0.5-HT_NL, 0, HTCH), 'e'), # left center
    (HANDLE_TOP_NOTCH_RADIUS_TO, HANDLE_TOP_NOTCH_RADIUS_TO, HTCH, (TOP_CENTER[0]-HT_CL*0.5-HT_NL, 0, HTCH), 'e'), # left center notch down
    (HANDLE_TOP_NOTCH_RADIUS_TO, HANDLE_TOP_NOTCH_RADIUS_TO, HTCH, (TOP_CENTER[0]-HT_CL*0.5, 0, HTCH), 'e'), # left center notch over
    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]-HT_CL*0.5, 0, HTCH), 'e'), # left center notch up
    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]-HT_CL*0.5+HT_ER, 0, HTCH), 'e'), # left center notch edge

    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]+HT_CL*0.5-HT_ER, 0, HTCH), 'e'), # right center notch edge
    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]+HT_CL*0.5, 0, HTCH), 'e'), # right center notch up
    (HANDLE_TOP_NOTCH_RADIUS_TO, HANDLE_TOP_NOTCH_RADIUS_TO, HTCH, (TOP_CENTER[0]+HT_CL*0.5, 0, HTCH), 'e'), # right center notch over
    (HANDLE_TOP_NOTCH_RADIUS_TO, HANDLE_TOP_NOTCH_RADIUS_TO, HTCH, (TOP_CENTER[0]+HT_CL*0.5+HT_NL, 0, HTCH), 'e'), # right center notch down
    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]+HT_CL*0.5+HT_NL, 0, HTCH), 'e'), # right center
    (HANDLE_TOP_RADIUS_TO, HANDLE_TOP_RADIUS_TO, HTCH, (TOP_CENTER[0]+HT_CL*0.5+HT_NL+HT_ER, 0, HTCH), 'e'), # right center edge

    (HANDLE_TOP_RADIUS_FROM, HANDLE_TOP_RADIUS_FROM, HTCH, (HANDLE_RIGHT_CENTER[0]-HT_SO, 0, HTCH), 'e'), # right ellipse over
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HTCH, addZ(HANDLE_RIGHT_CENTER, HTCH), 'r'), # right rectangle
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HTCH, (HANDLE_RIGHT_CENTER[0]+HT_ER, 0, HTCH), 'r'), # right rectangle edge
    # (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HTCH, (HANDLE_RIGHT_CENTER[0]+HT_ER+HANDLE_TOP_BULGE, 0, HTCH), 'r'), # right rectangle edge
]

# handle right
HANDLE_RIGHT = [
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HANDLE_SIDE_BLUGE_HEIGHT_RIGHT, HANDLE_RIGHT_CENTER_BULGE),
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HANDLE_SIDE_BLUGE_MIDHEIGHT_RIGHT, addZ(HANDLE_RIGHT_CENTER, HANDLE_SIDE_BLUGE_MIDHEIGHT_RIGHT)),
    (HANDLE_SIDE_LENGTH, HANDLE_SIDE_WIDTH, HANDLE_BOTTOM+HANDLE_SIDE_BASE_HEIGHT, addZ(HANDLE_RIGHT_CENTER, HANDLE_BOTTOM+HANDLE_SIDE_BASE_HEIGHT)),
    (HANDLE_SIDE_BASE_LENGTH, HANDLE_SIDE_BASE_WIDTH, HANDLE_BOTTOM+HANDLE_SIDE_BASE_HEIGHT, addZ(HANDLE_RIGHT_CENTER, HANDLE_BOTTOM+HANDLE_SIDE_BASE_HEIGHT)),
    (HANDLE_SIDE_BASE_LENGTH, HANDLE_SIDE_BASE_WIDTH, HANDLE_BOTTOM, HANDLE_RIGHT_CENTER)
]

# build the mesh
hmesh = Mesh()

for h in HANDLE_LEFT:
    x, y, z, c = h
    loop = roundedRect(HANDLE_VERTICES_PER_EDGE_LOOP, c, x, y, z, HANDLE_EDGE_RADIUS)
    hmesh.addEdgeLoop(loop)

for h in HANDLE_TOP:
    x, y, z, c, t = h
    if t=="r":
        loop = roundedRect(HANDLE_VERTICES_PER_EDGE_LOOP, c, x, y, z, HANDLE_EDGE_RADIUS)
    else:
        loop = ellipse(HANDLE_VERTICES_PER_EDGE_LOOP, c, x, y, z)
    loop = rotateY(loop, c, 90.0)
    hmesh.addEdgeLoop(loop)

for h in HANDLE_RIGHT:
    x, y, z, c = h
    loop = roundedRect(HANDLE_VERTICES_PER_EDGE_LOOP, c, x, y, z, HANDLE_EDGE_RADIUS)
    loop = rotateY(loop, c, 180.0)
    hmesh.addEdgeLoop(loop)

hmesh.processEdgeloops()

# config for spout
SPOUT_VERTICES_PER_EDGE_LOOP = HANDLE_VERTICES_PER_EDGE_LOOP
SPOUT_EDGE = EDGE_RADIUS
SPOUT_INNER_WIDTH = 6.0
SPOUT_INNER_HEIGHT = 12.0
SPOUT_CORNER_RADIUS = 2.0
SPOUT_THICKNESS = 4.0
SPOUT_WIDTH = SPOUT_INNER_WIDTH + SPOUT_THICKNESS*2
SPOUT_HEIGHT = SPOUT_INNER_HEIGHT + SPOUT_THICKNESS*2
SPOUT_CENTER_HEIGHT = BODY_HEIGHT - SPOUT_HEIGHT * 0.5
SPOUT_TO_X = -LENGTH*0.5
SPOUT_FROM_X = -(LENGTH*BODY_TOP-T2)*0.5 # TODO: define this based on body
SPOUT_INNER_X = -(LENGTH*BODY_TOP-T2)*0.455 # TODO: define this based on body

SPOUT_ROTATE = 30.0
SPOUT_ROTATE_CENTER = ((SPOUT_FROM_X + SPOUT_TO_X) * 0.5, 0.0, SPOUT_CENTER_HEIGHT)
SPOUT_TRANSLATE = (0.0, 0.0, 6.0)

# x, y, z, center
SPOUT = [
    (SPOUT_WIDTH, SPOUT_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_FROM_X, 0, SPOUT_CENTER_HEIGHT)), # outer start
    (SPOUT_WIDTH, SPOUT_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_FROM_X-SPOUT_EDGE, 0, SPOUT_CENTER_HEIGHT)), # outer start edge
    (SPOUT_WIDTH, SPOUT_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_TO_X+SPOUT_EDGE, 0, SPOUT_CENTER_HEIGHT)), # outer end edge
    (SPOUT_WIDTH, SPOUT_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_TO_X, 0, SPOUT_CENTER_HEIGHT)), # outer end
    (SPOUT_INNER_WIDTH, SPOUT_INNER_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_TO_X, 0, SPOUT_CENTER_HEIGHT)), # inner end
    (SPOUT_INNER_WIDTH, SPOUT_INNER_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_TO_X+SPOUT_EDGE, 0, SPOUT_CENTER_HEIGHT)), # inner end edge
    (SPOUT_INNER_WIDTH, SPOUT_INNER_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_INNER_X-SPOUT_EDGE, 0, SPOUT_CENTER_HEIGHT)), # inner edge
    (SPOUT_INNER_WIDTH, SPOUT_INNER_HEIGHT, SPOUT_CENTER_HEIGHT, (SPOUT_INNER_X, 0, SPOUT_CENTER_HEIGHT)), # inner
]

# build the mesh
smesh = Mesh()

for h in SPOUT:
    x, y, z, c = h
    loop = roundedRect(SPOUT_VERTICES_PER_EDGE_LOOP, c, x, y, z, SPOUT_CORNER_RADIUS)
    loop = rotateY(loop, c, -90.0)
    loop = rotateY(loop, SPOUT_ROTATE_CENTER, SPOUT_ROTATE)
    loop = translateLoop(loop, SPOUT_TRANSLATE)
    smesh.addEdgeLoop(loop)

smesh.processEdgeloops()

# save data
data = [
    {
        "name": "Pot",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": range((VERTICES_PER_EDGE_LOOP/4)**2)
    }
    ,{
        "name": "Handle",
        "verts": roundP(hmesh.verts, PRECISION),
        "edges": [],
        "faces": hmesh.faces,
        "location": (0.0, 0.0, 0.0)
    },{
        "name": "Spout",
        "verts": roundP(smesh.verts, PRECISION),
        "edges": [],
        "faces": smesh.faces,
        "location": (0.0, 0.0, 0.0)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

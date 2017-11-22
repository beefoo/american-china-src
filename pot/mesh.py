# -*- coding: utf-8 -*-

import json
from lib import *
import math
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 8

# retrieve image map data
im = Image.open(IMAGE_MAP_FILE)
IMAGE_MAP_W, IMAGE_MAP_H = im.size
IMAGE_MAP = list(im.getdata())

# cup config in mm
BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 0 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 0
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

CENTER = (0, 0, 0)
WIDTH = 84.0
LENGTH = 125.0
HEIGHT = 200.0
EDGE_RADIUS = 4.0
THICKNESS = 4.0
DISPLACEMENT = (0, 3.0, -3.0)
BASE_INSET_HEIGHT = 3.0

# Define the shape of the cross-section of the iron, clock-wise starting from top left
EDGE_X = EDGE_RADIUS / LENGTH
EDGE_Y = EDGE_RADIUS / WIDTH
BODY_X = 0.333
BODY_W = 0.9
BODY_Y = (1.0 - BODY_W) * 0.5
BODY_EDGE_X = BODY_X + EDGE_X
NOSE_X = 0.1667
NOSE_W = 0.2
NOSE_Y = (1.0 - NOSE_W) * 0.5
NOSE_POINT_W = NOSE_W * 0.5
NOSE_POINT_Y = (1.0 - NOSE_POINT_W) * 0.5
SHAPE = [
    (NOSE_X, NOSE_Y),       # top nose
    (BODY_X, BODY_Y),       # top body
    (BODY_EDGE_X, 0.0),     # top body edge
    (1.0-EDGE_X, 0.0),      # top right, edge before
    (1.0, 0.0),             # top right
    (1.0, EDGE_Y),          # top right, edge after
    (1.0, 0.5),             # middle right
    (1.0, 1.0-EDGE_Y),      # bottom right, edge before
    (1.0, 1.0),             # bottom right
    (1.0-EDGE_X, 1.0),      # bottom right, edge after
    (BODY_EDGE_X, 1.0),     # bottom body edge
    (BODY_X, 1.0-BODY_Y),   # bottom body
    (NOSE_X, 1.0-NOSE_Y),   # bottom nose
    (0.0, NOSE_POINT_Y),    # bottom nose point
    (0.0, 0.5),             # middle left (point of iron)
    (0.0, 1.0-NOSE_POINT_Y),# top nose point
]

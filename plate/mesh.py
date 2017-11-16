# -*- coding: utf-8 -*-

import colorsys
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from pprint import pprint
from scipy import interpolate
import sys

# data config
OUTPUT_FILE = "mesh.json"
PRECISION = 8
IMAGE_MAP_FILE = "imgMap.png"

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

TOP_WIDTH = 152.0
HEIGHT = 20.0
EDGE_RADIUS = 4.0
THICKNESS = 4.0
DISPLACEMENT_DEPTH = 2.0
BASE_HEIGHT = 3.0

CENTER_WIDTH = TOP_WIDTH * 0.5
BASE_WIDTH = TOP_WIDTH * 0.6
BODY_HEIGHT = HEIGHT - BASE_HEIGHT

# -*- coding: utf-8 -*-

# Data source: https://earthquake.usgs.gov/earthquakes/events/1906calif/18april/got_seismogram.php

import csv
import json
import math
import numpy as np
import os
from pprint import pprint
from scipy import interpolate
import sys

# data config
OUTPUT_FILE = "mesh.json"
DATA_FILE = "data.csv"

BASE_VERTICES = 16 # don't change this as it will break rounded rectangles
SUBDIVIDE_Y = 0 # will subdivide base vertices B * 2^x
SUBDIVIDE_X = 0
VERTICES_PER_EDGE_LOOP = BASE_VERTICES * 2**SUBDIVIDE_X
print "%s vertices per edge loop" % VERTICES_PER_EDGE_LOOP

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
WIDTH = 115.0
HEIGHT = 50.0
BASE_WIDTH = 55.0
EDGE_RADIUS = 2.0
THICKNESS = 4.8

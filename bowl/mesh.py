# -*- coding: utf-8 -*-

# 690 miles of track =~ 1110 km = 37 x 5
# 3 laborers died for every 2 miles of track
# Change, Iris. The Chinese In America. p. 63
# ~1200 total workers died: http://web.stanford.edu/group/chineserailroad/cgi-bin/wordpress/faqs/
# 690 miles of track = https://www.gilderlehrman.org/sites/default/files/inline-pdfs/Transcontinental%20Railroad%20Fact%20Sheet.pdf

import csv
import json
from lib import *
import os
from pprint import pprint
import sys

# data config
OUTPUT_FILE = "mesh.json"
ROWS = 5
COLS = 37
VERTICES_PER_EDGE_LOOP = 16

# cup config in mm
CENTER = (0, 0, 0)
PRECISION = 8
WIDTH = 118.0
HEIGHT = 60.0
BASE_WIDTH = 55.0
BASE_HEIGHT = 9.0
EDGE_RADIUS = 4.0
THICKNESS = 5.0
BASE_EDGE_RADIUS = 2.0

# calculations
INSET_BASE_WIDTH = BASE_WIDTH - 8.0
INSET_BASE_HEIGHT = BASE_HEIGHT * 0.5
INNER_BASE_WIDTH = BASE_WIDTH - 6.0
BODY_HEIGHT = (HEIGHT - BASE_HEIGHT) * 0.1 + BASE_HEIGHT
BODY_WIDTH = WIDTH * 0.8
INNER_INSET_BASE_WIDTH = INSET_BASE_WIDTH * 0.5

BOWL = [
    [INSET_BASE_WIDTH - EDGE_RADIUS*2, INSET_BASE_HEIGHT],      # 0, start with base inset edge
    [INSET_BASE_WIDTH, INSET_BASE_HEIGHT],                      # 1, move out to base inset
    [INSET_BASE_WIDTH, INSET_BASE_HEIGHT*0.5],                  # 2, move down to base inset edge
    [INNER_BASE_WIDTH, 0],                                      # 3, move down and out to inner base
    [BASE_WIDTH, 0],                                            # 4, move out to outer base
    [BASE_WIDTH, BASE_EDGE_RADIUS],                             # 5, move up to outer base edge
    [BASE_WIDTH, BASE_HEIGHT],                                  # 6, move up to base top; START DISPLACEMENT HERE
    [BODY_WIDTH, BODY_HEIGHT],                                  # 7, move up and out to body
    [WIDTH, HEIGHT - EDGE_RADIUS],                              # 8, move up and out to outer top edge
    [WIDTH, HEIGHT],                                            # 9, move up to outer top
    [WIDTH-THICKNESS*2, HEIGHT],                                # 10, move in to inner top; STOP DISPLACEMENT HERE
    [WIDTH-THICKNESS*2, HEIGHT - EDGE_RADIUS],                  # 11, move in to inner top edge
    [BODY_WIDTH-THICKNESS*2, BODY_HEIGHT],                      # 12, move down and in to inner body
    [INNER_INSET_BASE_WIDTH, BASE_HEIGHT+THICKNESS],                  # 13, move down and in to inner base
    [INNER_INSET_BASE_WIDTH - EDGE_RADIUS*2, BASE_HEIGHT+THICKNESS]   # 14, move in to inner base edge
]
bowlLen = len(BOWL)

# build the mesh
mesh = Mesh()

# add the loops before the displacement
for i, d in enumerate(BOWL):
    w, z = tuple(d)
    r = w * 0.5
    if i <= 0:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoops(loops)
    elif i >= bowlLen-1:
        loops = ellipseMesh(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z, reverse=True)
        mesh.addEdgeLoops(loops)
    else:
        loop = ellipse(VERTICES_PER_EDGE_LOOP, CENTER, r, r, z)
        mesh.addEdgeLoop(loop)

print "Calculating faces..."
# generate faces from vertices
mesh.processEdgeloops()

# save data
data = [
    {
        "name": "Bowl",
        "verts": roundP(mesh.verts, PRECISION),
        "edges": [],
        "faces": mesh.faces,
        "location": CENTER,
        "flipFaces": range((VERTICES_PER_EDGE_LOOP/4)**2)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

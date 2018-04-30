# -*- coding: utf-8 -*-

# 690 miles of track =~ 1110 km = 10 × 111
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

# 1110 km
# 3 × 370 = 1,110
# 5 × 222 = 1,110
# 6 × 185 = 1,110
# 10 × 111 = 1,110
# 15 × 74 = 1,110
# 30 × 37 = 1,110
ROWS = 10
COLS = 111
VERTICES_PER_EDGE_LOOP = COLS

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
DISPLACE_AMOUNT = 1.25

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
    [BASE_WIDTH, BASE_HEIGHT],                                  # 6, move up to base top
    [BODY_WIDTH, BODY_HEIGHT],                                  # 7, move up and out to body, DISPLACE START
    [WIDTH, HEIGHT - EDGE_RADIUS],                              # 8, move up and out to outer top edge, DISPLACE END
    [WIDTH, HEIGHT],                                            # 9, move up to outer top
    [WIDTH-THICKNESS*2, HEIGHT],                                # 10, move in to inner top
    [WIDTH-THICKNESS*2, HEIGHT - EDGE_RADIUS],                  # 11, move in to inner top edge
    [BODY_WIDTH-THICKNESS*2, BODY_HEIGHT],                      # 12, move down and in to inner body
    [INNER_INSET_BASE_WIDTH, BASE_HEIGHT+THICKNESS],                  # 13, move down and in to inner base
    [INNER_INSET_BASE_WIDTH - EDGE_RADIUS*2, BASE_HEIGHT+THICKNESS]   # 14, move in to inner base edge
]

targetLoops = 120 # lower the number, the taller the holes
BOWL = bspline(BOWL, n=targetLoops)
bowlLen = len(BOWL)

displaceOffset = 0.515 # lower the number the lower the holes start/end
displaceStart = int(round(displaceOffset * (bowlLen-1)))
displaceEnd = displaceStart + ROWS
displaceIndexStart = 0
displaceIndexEnd = 0

# build the mesh
mesh = Mesh()

# add the loops
for i, d in enumerate(BOWL):
    w, z = tuple(d)
    r = w * 0.5

    # if displaceStart <= i <= displaceEnd:
    #     r *= 1.1

    loop = circle(VERTICES_PER_EDGE_LOOP, CENTER, r, z)

    # add center in the beginning
    if i==0:
        mesh.addEdgeLoop([(CENTER[0], CENTER[1], z)])
        mesh.addDisplaceLoop(0)

    mesh.addEdgeLoop(loop)
    displace = DISPLACE_AMOUNT if displaceStart <= i < displaceEnd else 0
    mesh.addDisplaceLoop(displace)

    # add center at the end
    if i==bowlLen-1:
        mesh.addEdgeLoop([(CENTER[0], CENTER[1], z)])
        mesh.addDisplaceLoop(0)

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
        "flipFaces": range(VERTICES_PER_EDGE_LOOP)
    }
]

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

# -*- coding: utf-8 -*-

import json
import math
from PIL import Image, ImageDraw
from pprint import pprint
import sys

OUTPUT_FILE = "imgMap.png"
TARGET_W = 2048
TARGET_H = 512
SIDES = 4
COLS_PER_SIDE = 3
ROWS_PER_SIDE = 3
IMAGE_SCALE = 0.35
WARP_INNER_X = 1.1
WARP_OUTER_X = 0.8

SIDE_WIDTH = TARGET_W / SIDES
SIDE_MARGIN_X = TARGET_H / 24.0
SIDE_MARGIN_Y = TARGET_H / 128.0
COL_MARGIN = TARGET_H * 0
COL_WIDTH = 1.0 * (SIDE_WIDTH - SIDE_MARGIN_X * 2 - COL_MARGIN * (COLS_PER_SIDE-1)) / COLS_PER_SIDE
ROW_HEIGHT = 1.0 * (TARGET_H - SIDE_MARGIN_Y * 2) / ROWS_PER_SIDE

imBase = Image.new('RGB', (TARGET_W, TARGET_H), (255,255,255))

# going from right to left
for i in range(SIDES):

    line = i+1
    char = 1

    for j in range(COLS_PER_SIDE):

        cx = TARGET_W - SIDE_WIDTH * i - SIDE_MARGIN_X - j * (COL_WIDTH + COL_MARGIN) - COL_WIDTH * 0.5
        rows = ROWS_PER_SIDE
        warpX = WARP_INNER_X
        if j % 2 == 0:
            rows = 2
            warpX = WARP_OUTER_X

        for k in range(rows):

            cy = SIDE_MARGIN_Y + ROW_HEIGHT * k + ROW_HEIGHT * 0.5
            filename = "chars/char_%s-%s.png" % (line, char)
            im = Image.open(filename)
            imgW, imgH = im.size
            tw = imgW * IMAGE_SCALE * warpX
            th = imgH * IMAGE_SCALE
            x = cx - tw * 0.5
            y = cy - th * 0.5

            im = im.resize((int(tw), int(th)))
            imBase.paste(im, (int(x), int(y)), im)

            char += 1

imBase.save(OUTPUT_FILE)
print "Saved %s" % OUTPUT_FILE

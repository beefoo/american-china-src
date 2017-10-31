# -*- coding: utf-8 -*-

import json
import math
from PIL import Image, ImageDraw
from pprint import pprint
import sys

OUTPUT_FILE = "imgMap.png"
TARGET_W = 2048
TARGET_H = 512
CHARS_LINES = 4
CHARS_PER_LINE = 7
IMAGE_SCALE = 0.25
MARGIN_X = TARGET_H / 4.0
MARGIN_Y = TARGET_H / 128.0
CENTER_MARGIN = MARGIN_X * 0.2

imBase = Image.new('RGB', (TARGET_W, TARGET_H), (255,255,255))
cols = 4
colWidth = 1.0 * TARGET_W / cols - MARGIN_X * 2
colHeight = 1.0 * TARGET_H - MARGIN_Y * 2
colX = MARGIN_X
colY = MARGIN_Y * 0.5
rowHeight = colHeight / cols
cellHeight = rowHeight
cellWidth = (colWidth - CENTER_MARGIN) * 0.5

# retrieve image data
x = colX
y = colY
for i in range(CHARS_LINES):
    y = colY + (rowHeight * 0.5)
    for j in range(CHARS_PER_LINE):
        line = CHARS_LINES-i
        char = j + 5
        if j > 2:
            char = j - 2
        filename = "chars/char_%s-%s.png" % (line, char)
        im = Image.open(filename)
        imgW, imgH = im.size
        tw = imgW * IMAGE_SCALE
        th = imgH * IMAGE_SCALE
        deltaX = x + round((cellWidth - tw) * 0.5)
        deltaY = y + round((cellHeight - th) * 0.5)
        im.thumbnail((tw, th))
        imBase.paste(im, (int(deltaX), int(deltaY)), im)
        y += rowHeight
        if char==7:
            x += cellWidth + CENTER_MARGIN
            y = colY
    x += cellWidth + (colX * 2)

imBase.save(OUTPUT_FILE)
print "Saved %s" % OUTPUT_FILE

# -*- coding: utf-8 -*-

# Data source:
    # USGS, Rupture Length and Slip
    # https://earthquake.usgs.gov/earthquakes/events/1906calif/virtualtour/earthquake.php

import json
import math
from pprint import pprint
from pykml import parser
import sys

INPUT_FILE = "data/DistributionOfSlip.kml"
OUTPUT_FILE = "data/DistributionOfSlip.json"

root = None

with open(INPUT_FILE) as f:
    root = parser.parse(f).getroot()

slippageFolder = root.Document.Folder[-2]
name = slippageFolder.name.text
print "Found folder: %s" % name

data = []
for placemark in slippageFolder.Placemark:
    slippage = float(placemark.name.text)
    (lon, lat, altitude) = tuple([float(c) for c in placemark.Point.coordinates.text.split(",")])
    data.append({
        "lon": lon,
        "lat": lat,
        "altitude": altitude,
        "slippageFeet": slippage
    })

print "Writing to file..."
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f)
    print "Wrote to file %s" % OUTPUT_FILE

# American China

_Under development. Coming mid 2018._ A porcelain dining set inspired by people, objects, and events in Chinese American history

## Table of contents

1. [Spoon](spoon/)
1. [Plate](plate/)
1. [Bowl](bowl/)
1. [Cup](cup/)
1. [Pot](pot/) with [lid](pot_lid/)
1. [Sauce dish](sauce_dish/)

## Requirements for generating new 3d models

1. [Python 2.7.x](https://www.python.org/downloads/)
1. [Blender 2.7.9+](https://www.blender.org/)
1. Some models require [Pillow](https://pillow.readthedocs.io/en/5.1.x/) for Python

## Workflow

Typically, this is how most of these work:

1. `python mesh.py` will generate a `mesh.json` file which contains the vertices and faces for the model
1. Open the `.blend` file and run the script (`Alt P`) which will run `blend.py` inside Blender. This will:
    1. Read the `mesh.json`
    1. Calculate the edges from the vertices and faces
    1. Apply filters such as subdivide and decimate
1. You will then see the model and you can add/modify filters as needed
1. You can export this into a format of your choosing, e.g. STL or OBJ

## Process

1. Generate mesh data by running `python mesh.py`. This will create a json file `mesh.json`.
2. Download, install, and run [Blender](https://www.blender.org/)
3. In Blender, open the file `spoon.blend`
4. In the text pane on the upper left, right click and select `Run script`. This will run the python script `blend.py` which adds the mesh data to the blender UI and applies subdivision and decimate modifiers
5. _(optional)_ Adjust and apply modifiers
6. Export the model to a format of choosing like `.stl` or `.obj`

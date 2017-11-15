## Process

1. _(optional)_ Analyze an image with seismic data by running `python imgToData.py -in data/seismic.png -out data/seismic.json`
2. Generate mesh data by running `python mesh.py` using seismic data produced by the previous step. This will create a json file `mesh.json`.
3. Download, install, and run [Blender](https://www.blender.org/)
4. In Blender, open the file `bowl.blend`
5. In the text pane on the upper left, right click and select `Run script`. This will run the python script `blend.py` which adds the mesh data to the blender UI and applies subdivision and decimate modifiers
6. _(optional)_ Adjust and apply modifiers
7. Export the model to a format of choosing like `.stl` or `.obj`

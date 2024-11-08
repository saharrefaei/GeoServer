
# DataUpload_Geoserver.py Script

This script allows you to upload GeoPackage and Shapefile data to a GeoServer, publish layers, and apply styles automatically.

## Requirements

To run this script, you'll need to install the following Python libraries:

### Required Libraries

- `requests`: For making HTTP requests to GeoServer. 
- `geopandas`: For handling geographic data and converting shapefiles to GeoPackage.
- `fiona`: For reading layers from GeoPackage and shapefile files.
- `tkinter`: For creating the graphical user interface (GUI) for user interaction.

### Installation

You can install all the necessary libraries using `pip`. Run the following command in your terminal:

```bash
pip install requests geopandas fiona

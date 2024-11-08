import requests
import os

# GeoServer details
geoserver_url = r"http://localhost:8080/geoserver" 
username = "sahar"
password = "sahar"

# Workspace details
workspace_name = "workspace"

# Create workspace
workspace_url = f"{geoserver_url}/rest/workspaces"
headers = {"Content-type": "text/xml"}
data = f"<workspace><name>{workspace_name}</name></workspace>"
requests.post(workspace_url, auth=(username, password), headers=headers, data=data)

# Store details
store_name = "python_store"

# Create store
store_url = f"{geoserver_url}/rest/workspaces/{workspace_name}/datastores"
data = f"<dataStore><name>{store_name}</name></dataStore>"
requests.post(store_url, auth=(username, password), headers=headers, data=data)

# Upload GeoPackage
geopackage_path = r"C:\Users\sahar\ELIA GROUP\GridBird - Python\GIS_Data\Geopackage_example.gpkg"  # Replace with your GeoPackage path
store_url = f"{geoserver_url}/rest/workspaces/{workspace_name}/datastores/{store_name}/file.gpkg"
with open(geopackage_path, "rb") as f:
    requests.put(store_url, auth=(username, password), headers=headers, data=f)

print("GeoPackage has been uploaded successfully.")


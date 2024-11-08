import requests
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import time
import geopandas as gpd
import fiona
import glob

def check_workspace(base_url, auth, workspace):
    url = f"{base_url}/rest/workspaces/{workspace}/layers"
    headers = {'Accept': 'application/json'}
    response = requests.get(url, auth=auth, headers=headers)
    if response.status_code == 200:
        layers = response.json()
        if 'layers' in layers and 'layer' in layers['layers']:
            return True, [layer['name'] for layer in layers['layers']['layer']]
        else:
            return False, []
    elif response.status_code == 404:
        return None, []
    else:
        print(f"Error checking workspace '{workspace}': {response.content}")
        return None, []

def create_workspace(base_url, auth, workspace):
    url = f"{base_url}/rest/workspaces"
    headers = {"Content-type": "text/xml"}
    data = f"<workspace><name>{workspace}</name></workspace>"
    response = requests.post(url, auth=auth, headers=headers, data=data)
    if response.status_code == 201:
        print(f"Workspace '{workspace}' created successfully.")
    elif response.status_code == 401:
        print("Unauthorized. Check your credentials.")
    else:
        print(f"Error creating workspace '{workspace}': {response.content}")

def create_datastore(base_url, auth, workspace, datastore_name):
    url = f"{base_url}/rest/workspaces/{workspace}/datastores"
    data = {
        "dataStore": {
            "name": datastore_name,
            "connectionParameters": {
                "entry": [
                    {"@key": "database", "$": datastore_name},
                    {"@key": "dbtype", "$": "geopkg"}
                ]
            }
        }
    }
    headers = {
        "Content-type": "application/json",
        'Accept': 'application/json'
    }
    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print(f"Datastore '{datastore_name}' created successfully.")
    elif response.status_code == 405:
        print(f"Datastore '{datastore_name}' already exists.")
    else:
        print(f"Error creating datastore '{datastore_name}': {response.content}")
    return response

def post_geopackage(base_url, auth, workspace, datastore, gpkg_path):
    url_gpkg = f"{base_url}/rest/workspaces/{workspace}/datastores/{datastore}/file.gpkg"
    with open(gpkg_path, "rb") as f:
        geopackage = f.read()
 
    headers = {"Content-type": "application/x-binary"}
    response = requests.put(url_gpkg, auth=auth, headers=headers, data=geopackage)
 
    if response.status_code in [200, 201]:
        print(f"GeoPackage '{gpkg_path}' uploaded successfully.")
    else:
        print(f"Error uploading GeoPackage '{gpkg_path}': {response.content}")
    return response

def publish_layer(base_url, auth, workspace, datastore, layer_name, layer_title):
    url = f"{base_url}/rest/workspaces/{workspace}/datastores/{datastore}/featuretypes"
    data = {
        "featureType": {
            "name": layer_name,
            "title": layer_title,
            "enabled": True
        }
    }
    headers = {
        "Content-type": "application/json",
        'Accept': 'application/json'
    }
    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(data))
 
    if response.status_code == 201:
        print(f"Layer '{layer_name}' published successfully.")
    elif response.status_code == 409:
        print(f"Layer '{layer_name}' already exists.")
    else:
        print(f"Error publishing layer '{layer_name}': {response.content}")
    return response


def add_style(base_url, auth, workspace, style_name, style_file):
    url = f"{base_url}/rest/workspaces/{workspace}/styles"
    headers = {"Content-type": "application/vnd.ogc.sld+xml"}
    with open(style_file, 'rb') as f:
        style_data = f.read()
    response = requests.post(url, auth=auth, headers=headers, data=style_data)
    if response.status_code == 201:
        print(f"Style '{style_name}' uploaded successfully.")
        return True  
    else:
        print(f"Error uploading style '{style_name}': {response.content}")
        return False  

def assign_style_to_layer(base_url, auth, workspace, layer_name, style_name):
    url = f"{base_url}/rest/layers/{workspace}:{layer_name}"
    headers = {"Content-type": "application/json", 'Accept': 'application/json'}
    data = {
        "layer": {
            "defaultStyle": {
                "name": style_name,
                "workspace": workspace
            }
        }
    }
    response = requests.put(url, auth=auth, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print(f"Style '{style_name}' assigned to layer '{layer_name}' successfully.")
    else:
        print(f"Error assigning style '{style_name}' to layer '{layer_name}': {response.content}")
        
def add_styles_geoserver(base_url, auth, workspace, sld_folder, layers):
    style_dict = {}
    sld_files = glob.glob(os.path.join(sld_folder, "*.sld"))

    for sld_file in sld_files:
        style_name = os.path.splitext(os.path.basename(sld_file))[0]
        style_dict[style_name] = sld_file

    print("Style Dictionary:", style_dict)

    for layer_name in layers:
        layer_name_without_extension = os.path.splitext(layer_name)[0]

        print(f"Checking layer: {layer_name} (without extension: {layer_name_without_extension})") 

        if layer_name_without_extension in style_dict:
            style_file = style_dict[layer_name_without_extension]
            if add_style(base_url, auth, workspace, layer_name_without_extension, style_file):
                assign_style_to_layer(base_url, auth, workspace, layer_name_without_extension, layer_name_without_extension)
            else:
                print(f"Error adding style '{layer_name_without_extension}' for layer '{layer_name_without_extension}'.")
        else:
            print(f"No matching style found for layer '{layer_name}' (without extension: '{layer_name_without_extension}').")




def read_layer_from_gpkg(path_to_gpkg):
    return [{"name": layer, "title": layer} for layer in fiona.listlayers(path_to_gpkg)]

def check_layer_exists(base_url, auth, workspace, layer_name):
    url = f"{base_url}/rest/layers/{workspace}:{layer_name}"
    headers = {'Accept': 'application/json'}
    response = requests.get(url, auth=auth, headers=headers)
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        print(f"Error checking layer '{layer_name}': {response.content}")
        return False

def load_all_layers_from_gpkg(base_url, auth, workspace, datastore, path_to_gpkg):
    layers = read_layer_from_gpkg(path_to_gpkg)
    existing_layers = check_workspace(base_url, auth, workspace)[1]
    skipped_layers = []

    for layer in layers:
        layer_name_without_extension = os.path.splitext(layer["name"])[0]
        if layer_name_without_extension in existing_layers:
            skipped_layers.append(layer_name_without_extension)
            print(f"Layer '{layer_name_without_extension}' already exists in workspace '{workspace}'. Skipping upload.")
            continue

        response = publish_layer(base_url, auth, workspace, datastore, layer_name_without_extension, layer["title"])
        if response.status_code == 201:
            print(f"Layer '{layer_name_without_extension}' published successfully.")
        else:
            print(f"Error publishing layer '{layer_name_without_extension}': {response.content}")

    return skipped_layers

def shp_to_gpkg(shp_path, gpkg_path):
    try:
        gdf = gpd.read_file(shp_path)
        print("Successfully read shapefile:", shp_path)
        
        if 'fid' in gdf.columns:
            gdf = gdf.drop(columns=['fid'])

        gdf.to_file(gpkg_path, driver="GPKG")
        print("Successfully converted to GeoPackage:", gpkg_path)
    except Exception as e:
        print(f"Error converting shapefile '{shp_path}' to GeoPackage: {e}")

 

def select_files(file_type):
    root = tk.Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(
        title=f"Select {file_type.upper()} Files",
        filetypes=((f"{file_type.upper()} files", f"*.{file_type.lower()}"), ("All files", "*.*"))
    )
    return file_paths

def check_datastore_exists(base_url, auth, workspace, datastore_name):
    url = f"{base_url}/rest/workspaces/{workspace}/datastores/{datastore_name}"
    headers = {'Accept': 'application/json'}
    response = requests.get(url, auth=auth, headers=headers)
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        print(f"Error checking datastore '{datastore_name}': {response.content}")
        return False

def upload_multiple_files(base_url, auth, workspace, file_type, datastore_name, conversion_func=None, sld_folder=None):
    file_paths = select_files(file_type)

    if not file_paths:
        print("No files selected.")
        return

    existing_layers = check_workspace(base_url, auth, workspace)[1]
    skipped_files = []

    for file_path in file_paths:
        print(f"Processing '{file_path}'...")  

        if file_type.lower() == "shp" and conversion_func:
            gpkg_path = os.path.splitext(file_path)[0] + ".gpkg"
            conversion_func(file_path, gpkg_path)
        else:
            gpkg_path = file_path

        layers = read_layer_from_gpkg(gpkg_path)
        skipped_layers = [layer["name"] for layer in layers if layer["name"] in existing_layers]

        if skipped_layers:
            skipped_files.append(file_path)
            messagebox.showwarning("Layers Skipped", f"The following layers in '{os.path.basename(file_path)}' were skipped because they already exist in the workspace: {', '.join(skipped_layers)}")
            continue

        unique_datastore_name = datastore_name
        counter = 1
        while check_datastore_exists(base_url, auth, workspace, unique_datastore_name):
            unique_datastore_name = f"{datastore_name}_{counter}"
            counter += 1

        create_datastore(base_url, auth, workspace, unique_datastore_name)
        post_geopackage(base_url, auth, workspace, unique_datastore_name, gpkg_path)
        skipped_layers = load_all_layers_from_gpkg(base_url, auth, workspace, unique_datastore_name, gpkg_path)

        if sld_folder:
            layers_in_gpkg = [layer["name"] for layer in read_layer_from_gpkg(gpkg_path)]
            print(f"Layers in GPKG: {layers_in_gpkg}") 
            add_styles_geoserver(base_url, auth, workspace, sld_folder, layers_in_gpkg)

    if skipped_files:
        messagebox.showwarning("Files Skipped", f"The following files were skipped because their layers already exist in the workspace: {', '.join(os.path.basename(f) for f in skipped_files)}")


def get_auth_from_user():
    root = tk.Tk()
    root.withdraw()
    username = simpledialog.askstring("Username", "Enter your GeoServer username:")
    password = simpledialog.askstring("Password", "Enter your GeoServer password:", show='*')
    return (username, password)

def main():
    global auth
    base_url = r"http://localhost:8080/geoserver" #replace with your host
    sld_folder = r"C:\Users\sahar\GIS_Data\styles" # replace with your style's files location

    auth = get_auth_from_user()

    workspace = simpledialog.askstring("Workspace", "Enter the workspace name:")
    if not workspace:
        print("Workspace name is required.")
        return

    exists, layer_names = check_workspace(base_url, auth, workspace)
    if exists is None:
        create_workspace(base_url, auth, workspace)
    elif exists and len(layer_names) > 0:
        if not messagebox.askyesno("Workspace Exists", f"The workspace '{workspace}' contains {len(layer_names)} layers. Are you sure you want to add new data to it?"):
            return

    datastore_name = simpledialog.askstring("Datastore Name", "Enter datastore name for all files:")
    if not datastore_name:
        print("Datastore name is required.")
        return

    start_total = time.time()

    if messagebox.askyesno("GeoPackage Upload", "Do you want to upload GeoPackage files?"):
        upload_multiple_files(base_url, auth, workspace, "gpkg", datastore_name, sld_folder=sld_folder)

    if messagebox.askyesno("Shapefile Upload", "Do you want to upload Shapefiles?"):
        upload_multiple_files(base_url, auth, workspace, "shp", datastore_name, shp_to_gpkg, sld_folder=sld_folder)

    end_total = time.time()
    print(f"Total time taken: {end_total - start_total} seconds")


if __name__ == "__main__":
    main()
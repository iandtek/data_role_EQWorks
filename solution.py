import pandas as pd
import numpy as np
from scipy import spatial
import math
import random
from folium import *
from folium.plugins import MarkerCluster, BeautifyIcon
import webbrowser
import os

data_sample = pd.read_csv("data/DataSample.csv")
poi_list = pd.read_csv("data/POIList.csv")

# 1. Cleanup
# A sample dataset of request logs is given in data/DataSample.csv. We consider records that have identical geoinfo and timest as suspicious. 
# Please clean up the sample dataset by filtering out those suspicious request records.

print("Step 1: Cleaning Data, Dropping duplicates...") 

without_duplicates = data_sample.drop_duplicates(["TimeSt","Country","Province","City","Latitude","Longitude"], keep='first')

print(f"Done! \nLength original dataset: {len(data_sample)}.\nLength dataset without duplicates: {len(without_duplicates)}.\n{len(data_sample) - len(without_duplicates)} duplicates found.")

# 2. Label
# Assign each request (from data/DataSample.csv) to the closest (i.e. minimum distance) POI (from data/POIList.csv).
# Note: a POI is a geographical Point of Interest.

print("Step 2: Labeling, finding closest POI for each request...")

pois = []
for index, row in poi_list.iterrows():
    pois.append([row['Latitude'], row['Longitude']])

def compute_nearest_point(point):
    distance, index = spatial.KDTree(pois).query(point)
    earth_radius = 6_371_000 #meters
    lat_point = point[0]
    lon_point = point[1]
    lat_poi = poi_list.iloc[index]["Latitude"]
    lon_poi = poi_list.iloc[index]["Longitude"]
    
    lat1 = math.radians(lat_point)
    lon1 = math.radians(lon_point)
    lat2 = math.radians(lat_poi)
    lon2 = math.radians(lon_poi)
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = earth_radius * c
    
    return (poi_list.iloc[index]["POIID"], distance)

pd.options.mode.chained_assignment = None
for index, row in without_duplicates.iterrows(): 
    computed_poi, computed_distance = compute_nearest_point([row["Latitude"], row["Longitude"]])
    without_duplicates.loc[index, "POI"] = computed_poi
    without_duplicates.loc[index, "Distance"] = computed_distance

print("Done!")

# 3. Analysis
# For each POI, calculate the average and standard deviation of the distance between the POI to each of its assigned requests.
# At each POI, draw a circle (with the center at the POI) that includes all of its assigned requests. 
# Calculate the radius and density (requests/area) for each POI.

print("Step 3: Analysis, calculating the average and standard deviation of the distance between the POI to each of its assigned requests...")

for poi_index, poi_row in poi_list.iterrows():
    average = without_duplicates[without_duplicates.POI == poi_row["POIID"]]["Distance"].mean()
    maximum = without_duplicates[without_duplicates.POI == poi_row["POIID"]]["Distance"].max()
    std = without_duplicates[without_duplicates.POI == poi_row["POIID"]]["Distance"].std()
    area = (math.pi * (maximum ** 2)) #In Square Meters
    density = without_duplicates[without_duplicates.POI == poi_row["POIID"]]["Distance"].count() / area
    count = without_duplicates[without_duplicates.POI == poi_row["POIID"]]["Distance"].count()

    poi_list.loc[poi_index, "Average"] = average if not math.isnan(average) else 0
    poi_list.loc[poi_index, "MaximumDistance"] = maximum if not math.isnan(maximum) else 0 #In meters
    poi_list.loc[poi_index, "StandardDeviation"] = std if not math.isnan(std) else 0 #In meters
    poi_list.loc[poi_index, "Density"] = density if not math.isnan(density) else 0 #In Requests / Square meters
    poi_list.loc[poi_index, "Count"] = int(count)

print("Done!")

# 4 Data Science/Engineering Tracks
# To visualize the popularity of each POI, they need to be mapped to a scale that ranges from -10 to 10. 
# Please provide a mathematical model to implement this, taking into consideration of extreme cases and outliers. 
# Aim to be more sensitive around the average and provide as much visual differentiability as possible. 
# Bonus: Try to come up with some reasonable hypotheses regarding POIs, state all assumptions, testing steps and conclusions. 
# Include this as a text file (with a name bonus) in your final submission.

print("Step 4: Calculating popularity...")
for index, row in poi_list.iterrows():
    total_count = len(without_duplicates)
    poi_count = len(without_duplicates[without_duplicates.POI == row["POIID"]])
    poi_list.loc[index, "Popularity"] = ((poi_count/((total_count+1)-poi_count)) * 20) - 10

print("Plotting Map...")
m = Map(location=[0, 0], zoom_start=2)

for index, row in poi_list.iterrows():
    color = "#%06x" % random.randint(0, 0xFFFFFF)
    if row["Count"] > 0:
        Circle(
            location = (row["Latitude"], row["Longitude"]),
            radius = int(row["MaximumDistance"]),
            color = color,
            fill_color = color
        ).add_to(m)
        Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=Popup(row["POIID"] + ", Popularity: " + "{0:.2f}".format(row["Popularity"]) + ", Count: " + "{0:.0f}".format(row["Count"]), sticky=True, show=True),
            icon=BeautifyIcon(background_color=color, icon='marker'),
            draggable=False
        ).add_to(m)    


marker_cluster = MarkerCluster().add_to(m)

for index, row in without_duplicates.iterrows():
    Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup= "Nearest POI: " + row["POI"],
        # icon=Icon(color='green', icon='ok-sign'),
        draggable=False
    ).add_to(marker_cluster)

outfp = "output/basemap.html"
m.save(outfp)

dirpath = os.getcwd()

print("Saving Output...")
without_duplicates.to_csv(r'output/DataSample.csv')
poi_list.to_csv(r'output/POIList.csv')

print("Opening Map...")
webbrowser.open(f"file://{dirpath}/{outfp}", new=2)
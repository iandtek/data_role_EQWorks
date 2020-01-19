import matplotlib.pyplot as plt
import networkx as nx
from pprint import pprint

task_ids_file = open("data/task_ids.txt", "r")
task_ids = task_ids_file.read().split(",")

relations = []
relations_lines = open("data/relations.txt", "r").read().splitlines()
for line in relations_lines:
    relations.append(tuple(line.split("->")))

G = nx.DiGraph()

# add nodes, labeled from tasks id:
map(G.add_node, task_ids)

# dependencies
G.add_edges_from(relations)

# Position
pos = nx.spring_layout(G,k=1,iterations=10)

# Calculate the paths 
paths = nx.all_simple_paths(G, source="73", target="36", cutoff=None) #Change here source to starting task and target to goal task

print("The pipeline dependency is:")
pprint(list(paths))

# Change default colors of the edge colors to different color each line so it's easier to 
# Differenciate each node and edges
colors = range(len(relations))

nx.draw_networkx_labels(G, pos)
nx.draw(G,pos, edge_color=colors)
plt.show()
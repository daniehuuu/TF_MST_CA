import networkx as nx
import pandas as pd
import random

# Function to generate a connected graph with n_nodes
def generate_connected_graph(n_nodes):
    # Create a random spanning tree to ensure connectivity
    G = nx.generators.random_tree(n_nodes)

    # Assign random integer weights between 1 and 200 to the spanning tree edges
    for u, v in G.edges():
        G[u][v]['weight'] = random.randint(1, 200)

    # Randomly add more edges to increase connectivity/density
    additional_edges = int(n_nodes * 1.5)  # Adjust the factor to control edge density
    edges_added = 0

    while edges_added < additional_edges:
        u = random.randint(0, n_nodes - 1)
        v = random.randint(0, n_nodes - 1)

        # Check that u and v are different nodes and not already connected
        if u != v and not G.has_edge(u, v):
            weight = random.randint(1, 200)  # Assign random positive weight
            G.add_edge(u, v, weight=weight)
            edges_added += 1  # Increment only when an edge is successfully added

    return G

# Generate a connected graph with 1500 nodes
connected_graph = generate_connected_graph(1500)

# Convert the graph's edges and weights to a DataFrame
edge_list = []
for u, v, data in connected_graph.edges(data=True):
    weight = data['weight']
    edge_list.append([u, v, weight])

df = pd.DataFrame(edge_list, columns=['Node1', 'Node2', 'Weight'])

# Save to CSV
df.to_csv('dataset.csv', index=False)


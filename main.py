import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

# Function to initialize the plot
def init():
    nx.draw_networkx_nodes(G, pos, node_size=50)  # Smaller nodes
    # No labels for nodes, just empty graph structure
    nx.draw_networkx_edges(G, pos, edgelist=G.edges, edge_color='lightgray')

# Function to update the plot at each step
def update(num):
    plt.clf()  # Clear the previous figure
    nx.draw_networkx_nodes(G, pos, node_size=50)  # Draw nodes as points
    # Draw all edges in light gray
    nx.draw_networkx_edges(G, pos, edgelist=G.edges, edge_color='lightgray')
    # Highlight the MST edges up to the current step
    nx.draw_networkx_edges(G, pos, edgelist=mst_edges[:num], edge_color='blue', width=2)

    # Calculate total weight of the MST up to this step
    current_total_weight = sum([G[u][v]['weight'] for u, v in mst_edges[:num]])

    # Display the total weight and connection status
    if num > 0:
        u, v = mst_edges[num-1]
        connection_status = f"Connecting nodes {u} and {v}"
    else:
        connection_status = "Starting Kruskal's Algorithm"

    plt.title(f"Kruskal's Algorithm: Step {num} | Total MST Weight: {current_total_weight} | {connection_status}")

# Kruskal's Algorithm with animation
def kruskal_with_animation(G):
    # Sort edges by weight
    edges = sorted(G.edges(data=True), key=lambda x: x[2]['weight'])
    uf = nx.utils.UnionFind()
    
    for edge in edges:
        u, v, data = edge
        if uf[u] != uf[v]:  # Check if they are in different components
            uf.union(u, v)  # Union the components
            mst_edges.append((u, v))  # Add the edge to the MST

# Generate a large random graph with 100+ nodes and random weights
def generate_large_graph(num_nodes=100, num_edges=300):
    G = nx.Graph()
    for i in range(num_edges):
        u = random.randint(0, num_nodes-1)
        v = random.randint(0, num_nodes-1)
        if u != v:
            weight = random.randint(1, 100)  # Random weight between 1 and 100
            G.add_edge(u, v, weight=weight)
    return G

# Create a large graph
G = generate_large_graph(1500, 4500)  # 100 nodes and 300 edges

# Variables to store positions and edges in the MST
pos = nx.spring_layout(G, seed=42, k=2.00)  # Adjust k to reduce overlap
mst_edges = []  # List to store MST edges

# Run Kruskal's algorithm (collect MST edges)
kruskal_with_animation(G)

# Create the animation
fig = plt.figure(figsize=(10, 8))
ani = animation.FuncAnimation(fig, update, frames=len(mst_edges)+1, init_func=init, interval=50, repeat=False)  # Faster interval (500ms)

# Show the animation
plt.show()

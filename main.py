import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Function to initialize the plot
def init():
    nx.draw_networkx_nodes(G, pos, node_size=700)
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

# Function to update the plot at each step
def update(num):
    plt.clf()  # Clear the previous figure
    nx.draw_networkx_nodes(G, pos, node_size=700)
    # Draw all edges in light gray
    nx.draw_networkx_edges(G, pos, edgelist=G.edges, edge_color='lightgray')
    # Highlight the MST edges up to the current step
    nx.draw_networkx_edges(G, pos, edgelist=mst_edges[:num], edge_color='blue', width=2)
    nx.draw_networkx_labels(G, pos)
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Kruskal's Algorithm: Step {}".format(num))

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

# Example graph
G = nx.Graph()
# Add weighted edges
G.add_edge('A', 'B', weight=5)
G.add_edge('A', 'E', weight=2)
G.add_edge('B', 'D', weight=3)
G.add_edge('B', 'C', weight=1)
G.add_edge('C', 'D', weight=1)
G.add_edge('C', 'F', weight=3)
G.add_edge('D', 'F', weight=2)
G.add_edge('D', 'E', weight=3)
G.add_edge('E', 'F', weight=2)

# Variables to store positions and edges in the MST
pos = nx.spring_layout(G)  # Positioning the graph nodes
mst_edges = []  # List to store MST edges

# Run Kruskal's algorithm (collect MST edges)
kruskal_with_animation(G)

# Create the animation
fig = plt.figure(figsize=(8, 6))
ani = animation.FuncAnimation(fig, update, frames=len(mst_edges)+1, init_func=init, interval=1000, repeat=False)

# Show the animation
plt.show()

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class KruskalAnimation:
    def __init__(self, G, pos, edges):
        self.G = G
        self.pos = pos
        self.mst_edges = edges
        self.fig = plt.figure(figsize=(10, 8))
        self.ani = None

        # Initialize the plot with the initial state of the graph
        self.init()

        # Create the animation
        self.ani = animation.FuncAnimation(
            self.fig, 
            self.update, 
            frames=len(self.mst_edges) + 1, 
            interval=50,  # Adjust interval if needed
            repeat=False
        )

    def init(self):
        nx.draw_networkx_nodes(self.G, self.pos, node_size=50)
        nx.draw_networkx_edges(self.G, self.pos, edgelist=self.G.edges, edge_color='lightgray')
        plt.title("Initial graph")
        plt.pause(5)


    def update(self, num):
        plt.clf()  # Clear the previous figure
        nx.draw_networkx_nodes(self.G, self.pos, node_size=50)
        nx.draw_networkx_edges(self.G, self.pos, edgelist=self.G.edges, edge_color='lightgray')
        nx.draw_networkx_edges(self.G, self.pos, edgelist=self.mst_edges[:num], edge_color='blue', width=2)

        current_total_weight = sum([self.G[u][v]['weight'] for u, v, _ in self.mst_edges[:num]])

        if num > 0:
            u, v, _ = self.mst_edges[num - 1]
            edge_weight = self.G[u][v]['weight']
            connection_status = f"Connecting nodes {u} and {v} with weight {edge_weight}"
        else:
            connection_status = "Starting Kruskal's Algorithm"

        plt.title(f"Kruskal's Algorithm: Step {num} | Total MST Weight: {current_total_weight}")
        plt.text(0.5, -0.1, connection_status, ha='center', va='center', transform=plt.gca().transAxes)

    def show(self):
        plt.show()

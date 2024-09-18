import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class KruskalAnimation:
    def __init__(self, G, pos):
        self.G = G
        self.pos = pos
        self.mst_edges = []  # List to store MST edges
        self.fig = plt.figure(figsize=(10, 8))
        self.ani = None
        
        # Run Kruskal's algorithm to collect MST edges
        self.kruskal_with_animation()
        
        # Create the animation
        self.ani = animation.FuncAnimation(
            self.fig, 
            self.update, 
            frames=len(self.mst_edges) + 1, 
            init_func=self.init, 
            interval=50,  # Faster interval (50ms)
            repeat=False
        )
    
    def kruskal_with_animation(self):
        # Sort edges by weight
        edges = sorted(self.G.edges(data=True), key=lambda x: x[2]['weight'])
        uf = nx.utils.UnionFind()
        
        for edge in edges:
            u, v, data = edge
            if uf[u] != uf[v]:  # Check if they are in different components
                uf.union(u, v)  # Union the components
                self.mst_edges.append((u, v))  # Add the edge to the MST
    
    def init(self):
        nx.draw_networkx_nodes(self.G, self.pos, node_size=50)  # Smaller nodes
        # No labels for nodes, just empty graph structure
        nx.draw_networkx_edges(self.G, self.pos, edgelist=self.G.edges, edge_color='lightgray')
    
    def update(self, num):
        plt.clf()  # Clear the previous figure
        nx.draw_networkx_nodes(self.G, self.pos, node_size=50)  # Draw nodes as points
        # Draw all edges in light gray
        nx.draw_networkx_edges(self.G, self.pos, edgelist=self.G.edges, edge_color='lightgray')
        # Highlight the MST edges up to the current step
        nx.draw_networkx_edges(self.G, self.pos, edgelist=self.mst_edges[:num], edge_color='blue', width=2)
        
        # Calculate total weight of the MST up to this step
        current_total_weight = sum([self.G[u][v]['weight'] for u, v in self.mst_edges[:num]])
        
        # Display the total weight and connection status
        if num > 0:
            u, v = self.mst_edges[num - 1]
            edge_weight = self.G[u][v]['weight']
            connection_status = "Connecting nodes {} and {} with weight {}".format(u,v,edge_weight)
        else:
            connection_status = "Starting Kruskal's Algorithm"
        
        plt.title(f"Kruskal's Algorithm: Step {num} | Total MST Weight: {current_total_weight} | {connection_status}")
        

    def show(self):
        plt.show()
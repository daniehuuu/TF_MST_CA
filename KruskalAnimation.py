import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class KruskalAnimation:
    def __init__(self, G, pos, edges):
        self.G = G
        self.pos = pos
        self.mst_edges = edges  # List to store MST edges
        self.fig = plt.figure(figsize=(10, 8))
        self.ani = None
        self.animation_rendered = False  # Flag to check if the animation was rendered

        # Create the animation and store it in self.ani
        self.ani = animation.FuncAnimation(
            self.fig, 
            self.update, 
            frames=len(self.mst_edges) + 1, 
            init_func=self.init, 
            interval=50,  # Faster interval (50ms)
            repeat=False
        )
        

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
        
        # Mark the animation as rendered
        self.animation_rendered = True
        
        # Calculate total weight of the MST up to this step
        current_total_weight = sum([self.G[u][v]['weight'] for u, v, _ in self.mst_edges[:num]])
        
        # Display the total weight and connection status
        if num > 0:
            u, v, _ = self.mst_edges[num - 1]
            edge_weight = self.G[u][v]['weight']
            connection_status = "Connecting nodes {} and {} with weight {}".format(u, v, edge_weight)
        else:
            connection_status = "Starting Kruskal's Algorithm"
        
        plt.title(f"Kruskal's Algorithm: Step {num} | Total MST Weight: {current_total_weight}")
        plt.text(0.5, -0.07, connection_status, ha='center', va='center', transform=plt.gca().transAxes)


        
    def show(self):
        """Show the animation and manage the rendering process."""
        try:
            # Keep a strong reference to the animation by assigning it to a variable
            anim_ref = self.ani  # This prevents the animation from being garbage collected.
            
            # Show the plot, ensuring the animation renders if possible
            plt.show()
        finally:
            if not self.animation_rendered:
                print("No animation rendered. Deleting figure.")
                plt.close('all')

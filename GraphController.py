import networkx as nx
import matplotlib.pyplot as plt
from tkinter import messagebox, Tk, Label, Frame, ttk
from file import read_graph_from_csv, export_graph_to_csv
from KruskalAnimation import KruskalAnimation

class GraphController:
    def __init__(self, fileIn, fileOut):
        self.G = read_graph_from_csv(fileIn)
        self.pos = None
        self.mst_edges = None  # Initialize mst_edges as None

    def show_data(self):
        
        root = Tk()
        root.title("Graph Data")
        style = ttk.Style(root)
        style.theme_use("clam")  
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("Treeview", rowheight=25, font=("Helvetica", 10))
        
        num_nodes = self.G.number_of_nodes()
        num_edges = self.G.number_of_edges()
        
        Label(root, text=f"Number of nodes: {num_nodes}", font=("Helvetica", 12)).pack(pady=5)
        Label(root, text=f"Number of edges: {num_edges}", font=("Helvetica", 12)).pack(pady=5)

        frame = Frame(root)
        frame.pack(pady=10)

        tree = ttk.Treeview(frame, columns=("Node", "Connections", "Total Weight", "Average Weight"), show="headings", height=10)
        tree.heading("Node", text="Node")
        tree.heading("Connections", text="Connections")
        tree.heading("Total Weight", text="Total Weight")
        tree.heading("Average Weight", text="Average Weight")
        tree.column("Node", anchor="center", width=80)
        tree.column("Connections", anchor="center", width=120)
        tree.column("Total Weight", anchor="center", width=120)
        tree.column("Average Weight", anchor="center", width=120)

        for node in sorted(self.G.nodes): 
            connections = self.G.degree(node) 
            total_weight = sum([self.G[node][neighbor]['weight'] for neighbor in self.G.neighbors(node)])  
            avg_weight = round(total_weight / connections, 1) if connections > 0 else 0  
            tree.insert("", "end", values=(node, connections, total_weight, avg_weight))

        tree.pack()
        root.mainloop()

    def getPos(self):
        if self.pos is None:
            messagebox.showinfo("Positioning", "Calculating graph layout. Please wait.")
            self.pos = nx.spring_layout(self.G, seed=42, k=2.00)
        return self.pos
    
    def show_visualization(self):
        pos = self.getPos()
        KruskalAnimation(self.G, pos).show()

    def show_mst(self):
        if self.mst_edges is None:
            self.mst_edges = self.kruskal()
        self.draw_mst(self.mst_edges)

    def kruskal(self):
        edges = sorted(self.G.edges(data=True), key=lambda x: x[2]['weight'])
        uf = nx.utils.UnionFind()
        mst_edges = []

        for edge in edges:
            u, v, data = edge
            if uf[u] != uf[v]:  # Check if they are in different components
                uf.union(u, v)  # Union the components
                mst_edges.append((u, v, data['weight']))  # Add the edge to the MST with weight

        return mst_edges

    def draw_mst(self, mst_edges):
        if (mst_edges is None) or (len(mst_edges) == self.G.number_of_nodes() - 1):
            mst_edges = self.kruskal()
        
        plt.figure(figsize=(10, 8))
        pos = self.getPos()
        nx.draw_networkx_nodes(self.G, pos, node_size=50)
        nx.draw_networkx_edges(self.G, pos, edgelist=self.G.edges, edge_color='lightgray')
        nx.draw_networkx_edges(self.G, pos, edgelist=[(u, v) for u, v, w in mst_edges], edge_color='blue', width=2)
        plt.title("Minimum Spanning Tree (MST)")
        plt.show()

    def export_mst_to_csv(self, fileOut):
        if self.mst_edges is None:
            self.mst_edges = self.kruskal()
        export_graph_to_csv(edges=self.mst_edges, file_path=fileOut)
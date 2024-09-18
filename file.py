import networkx as nx
import pandas as pd

def read_graph_from_csv(file_path):
    try:
        # Attempt to read the CSV file
        df = pd.read_csv(file_path)
        
        # Create an empty undirected graph
        G = nx.Graph()

        # Add edges to the graph from the DataFrame
        for index, row in df.iterrows():
            node1 = row['Node1']
            node2 = row['Node2']
            weight = row['Weight']
            G.add_edge(node1, node2, weight=weight)
        
        return G

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except PermissionError:
        print(f"Error: The file '{file_path}' is already open or you don't have permission to read it.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
"""
file_path = 'connected_graph_1500_nodes.csv'
graph = read_graph_from_csv(file_path)

if graph:
    print("Number of nodes:", graph.number_of_nodes())
    print("Number of edges:", graph.number_of_edges())
"""

import heapq
import json
import networkx as nx
class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, u):
        if self.parent[u] != u:
            self.parent[u] = self.find(self.parent[u])
        return self.parent[u]

    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u != root_v:
            if self.rank[root_u] > self.rank[root_v]:
                self.parent[root_v] = root_u
            elif self.rank[root_u] < self.rank[root_v]:
                self.parent[root_u] = root_v
            else:
                self.parent[root_v] = root_u
                self.rank[root_u] += 1


class MST:
    def __init__(self, graph):
        self.graph = graph
        self.mst = nx.Graph()
        self.total_amount = 0

    def prim_mst_distance(self):
        self.mst = nx.Graph()
        self.total_amount = 0
        start_node = next(iter(self.graph.nodes))
        visited = set([start_node])
        edges = [(data['distance'], start_node, neighbor) for neighbor, data in self.graph[start_node].items()]
        heapq.heapify(edges)
        
        while edges:
            distance, u, v = heapq.heappop(edges)
            if v not in visited:
                visited.add(v)
                self.mst.add_edge(u, v, distance=distance)
                self.total_amount += distance
                for neighbor, data in self.graph[v].items():
                    if neighbor not in visited:
                        heapq.heappush(edges, (data['distance'], v, neighbor))
                        
    def kruskal_mst_cost(self):
        self.mst = nx.Graph()
        self.total_amount = 0
        edges = [(data['cost'], u, v) for u, v, data in self.graph.edges(data=True)]
        edges.sort()
        
        uf = UnionFind(len(self.graph.nodes))
        node_index = {node: idx for idx, node in enumerate(self.graph.nodes)}
        
        for cost, u, v in edges:
            if uf.find(node_index[u]) != uf.find(node_index[v]):
                uf.union(node_index[u], node_index[v])
                self.mst.add_edge(u, v, cost=cost)
                self.total_amount += cost   
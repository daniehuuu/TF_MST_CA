import gmplot
import googlemaps
import pandas as pd
import networkx as nx
from scipy.spatial import distance_matrix
import json
import heapq

# Rutas a los archivos CSV y clave de API de Google Maps
graph_file_path = 'CAN.csv'
altitude_file_path = 'TB_UBIGEOS.csv'
api_key = 'AIzaSyBUu6qAVsHdnUJlFDwAeFyk3YQDgvanreA'

def clean_text(text):
    """Limpia caracteres mal codificados y reemplaza 'ñ' por 'n'."""
    if isinstance(text, str):
        text = text.encode('latin1').decode('utf-8', errors='ignore')
        text = text.replace('ñ', 'n').replace('Ñ', 'N')
    return text

def load_data(graph_file_path, altitude_file_path):
    try:
        graph_df = pd.read_csv(graph_file_path, delimiter=';', encoding='latin1')
        altitude_df = pd.read_csv(altitude_file_path, delimiter=';', encoding='latin1')
        
        required_columns_graph = ['UBIGEO_DISTRITO']
        required_columns_altitude = ['ubigeo_inei', 'distrito', 'latitud', 'longitud']
        
        # Elimina duplicados basados en el UBIGEO_DISTRITO
        graph_df = graph_df.drop_duplicates(subset=['UBIGEO_DISTRITO'])     
        
        # Verifica que existan las columnas requeridas en los archivos de datos
        if not all(column in graph_df.columns for column in required_columns_graph):
            raise ValueError("Graph data is missing required columns.")
        
        if not all(column in altitude_df.columns for column in required_columns_altitude):
            raise ValueError("Altitude data is missing required columns.")

        # Renombra columnas para unificar los nombres
        altitude_df.rename(columns={
            'ubigeo_inei': 'UBIGEO_DISTRITO',
            'latitud': 'latitude',
            'longitud': 'longitude',
            'distrito': 'district'
        }, inplace=True)
        
        altitude_df['district'] = altitude_df['district'].apply(clean_text)
          
        # Fusiona los DataFrames basados en el UBIGEO_DISTRITO
        merged_df = pd.merge(graph_df, altitude_df, on='UBIGEO_DISTRITO')
        
        return merged_df
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def create_graph(df, api_key):
    # Calcula la matriz de distancias entre las coordenadas
    coords = df[['latitude', 'longitude']].to_numpy()
    dist_matrix = distance_matrix(coords, coords)
    
    Grafo = nx.Graph()
    
    # Añade nodos al grafo con atributos de posición y distrito
    for i, row in df.iterrows():
        Grafo.add_node(i, pos=(row['longitude'], row['latitude']), district=row['district'])
    # print the number of nodes
    # print(f"Number of nodes: {Grafo.number_of_nodes()}")
    
    # Añade aristas al grafo basadas en las 3 distancias más cortas
    for i in range(len(dist_matrix)):
        # Ordena las distancias y selecciona los índices de las 3 distancias más cortas que no sean 0
        sorted_indices = [index for index in dist_matrix[i].argsort() if dist_matrix[i][index] != 0][:3]
        for nearest in sorted_indices:
            Grafo.add_edge(i, nearest, distance=dist_matrix[i][nearest])
            dist_matrix[nearest][i] = 0  # Establecer la conexión invertida a 0 para evitar duplicados
    
    # Inicializa el cliente de Google Maps
    gmaps = googlemaps.Client(key=api_key)

    """ To check the number of edges and the frequency of connections
    # how many edges
    print(f"Number of edges: {Grafo.number_of_edges()}")
    # Create a dictionary to store the frequency of each node's connections
    connection_frequencies = {}
    for node in Grafo.nodes():
        num_connections = len(list(Grafo.edges(node)))
        if num_connections in connection_frequencies:
            connection_frequencies[num_connections] += 1
        else:
            connection_frequencies[num_connections] = 1

    # Convert the dictionary to a DataFrame for better visualization
    frequency_df = pd.DataFrame(list(connection_frequencies.items()), columns=['Number of Connections', 'Frequency'])
    print(frequency_df)
    """

    # Define the lambda function to calculate the cost
    calculate_cost = lambda distance: distance * 1.03 if distance <= 1 else (distance * 1.07 if distance < 100 else distance * 1.13)

    edges_to_remove = []
    # Actualiza los pesos de las aristas con las distancias reales caminando
    for u, v, data in Grafo.edges(data=True):
        start = Grafo.nodes[u]['pos']
        end = Grafo.nodes[v]['pos']
        result = gmaps.distance_matrix(origins=[(start[1], start[0])], destinations=[(end[1], end[0])], mode="walking")
        
        if result['rows'][0]['elements'][0]['status'] == 'OK':
            distance = result['rows'][0]['elements'][0]['distance']['value'] / 1000  # Distancia en kilómetros
            data['distance'] = distance
            data['cost'] = calculate_cost(distance) 
        else:
            print(f"Error fetching distance between {u} and {v}: {result['rows'][0]['elements'][0]['status']}")
            edges_to_remove.append((u, v)) # Elimina la arista si no existe una distancia real
    Grafo.remove_edges_from(edges_to_remove)
    return Grafo

def save_graph_to_csv(graph, file_path):
    # Crear una lista para almacenar los datos de las aristas
    edge_data = []
    
    # Recorrer las aristas del grafo y extraer la información necesaria
    for u, v, data in graph.edges(data=True):
        edge_data.append({
            'distric 1:': graph.nodes[u]['district'],
            'lon1': graph.nodes[u]['pos'][0],
            'lat1': graph.nodes[u]['pos'][1],
            'distric 2:': graph.nodes[v]['district'],
            'lon2': graph.nodes[v]['pos'][0],
            'lat2': graph.nodes[v]['pos'][1],
            'distance': data['distance'],
            'cost': data['cost']
        })
    
    # Convertir la lista de datos en un DataFrame de pandas
    edge_df = pd.DataFrame(edge_data)
    
    # Guardar el DataFrame en un archivo CSV
    edge_df.to_csv(file_path, index=False)

def plot_map(df, api_key):
    # Crea el archivo HTML con la estructura básica del mapa
    with open("map.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                /* Asegura que el mapa ocupe todo el tamaño de la ventana */
                html, body, #map {
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                /* Estilo para el contenedor de información */
                #info {
                    position: absolute;
                    top: 120px;
                    left: 10px;
                    background-color: white;
                    padding: 10px;
                    border: 1px solid black;
                    border-radius: 5px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    z-index: 1000;
                    font-family: Arial, sans-serif;
                }
                #info h2 {
                    margin: 0 0 5px 0;
                    font-size: 16px;
                }
                #info p {
                    margin: 0;
                    font-size: 14px;
                }
            </style>
            <script src="https://maps.googleapis.com/maps/api/js?key=""" + api_key + """&callback=initMap" async defer></script>
            <script>
                function initMap() {
                    var map = new google.maps.Map(document.getElementById('map'), {
                        zoom: 10,
                        center: {lat: """ + str(df['latitude'].mean()) + """, lng: """ + str(df['longitude'].mean()) + """}
                    });

                    var infoWindow = document.getElementById('info');

                    var markers = [];
                    var locations = """ + df[['latitude', 'longitude', 'district']].to_json(orient='records') + """;

                    locations.forEach(function(location) {
                        var marker = new google.maps.Marker({
                            position: {lat: location.latitude, lng: location.longitude},
                            map: map,
                            icon: {
                                url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png", // URL of the marker icon
                                scaledSize: new google.maps.Size(20, 20) // Size of the marker icon
                            }
                        });

                        marker.addListener('click', function() {
                            infoWindow.innerHTML = '<h2>District: ' + location.district + '</h2>' +
                                                   '<p>Latitude: ' + location.latitude + '</p>' +
                                                   '<p>Longitude: ' + location.longitude + '</p>';
                        });

                        markers.push(marker);
                    });
                }
            </script>
        </head>
        <body>
            <div id="map"></div>
            <div id="info">Click on a marker to see the district information here.</div>
        </body>
        </html>
        """)

# Carga los datos y genera el mapa
#df = load_data(graph_file_path, altitude_file_path)
#if df is not None:
#    plot_map(df, api_key)

#g = create_graph(df, api_key)
#save_graph_to_csv(g, 'test.csv')

def create_original_graph_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        original_graph = nx.Graph()
        id = 0
        node_mapping = {}
        
        for _, row in df.iterrows():
            u = (row['lat1'], row['lon1'])
            v = (row['lat2'], row['lon2'])
            distance = row['distance']
            cost = row['cost']
            
            if u not in node_mapping:
                original_graph.add_node(id, pos=(row['lon1'], row['lat1']), district=row['distric 1:'])
                node_mapping[u] = id
                id += 1
            if v not in node_mapping:
                original_graph.add_node(id, pos=(row['lon2'], row['lat2']), district=row['distric 2:'])
                node_mapping[v] = id
                id += 1
            
            original_graph.add_edge(node_mapping[u], node_mapping[v], distance=distance, cost=cost)
        
        return original_graph
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Example usage
original_graph = create_original_graph_from_csv('test.csv')

# how many nodes
print(f"Number of nodes: {original_graph.number_of_nodes()}")
# how many edges
print(f"Number of edges: {original_graph.number_of_edges()}")

# plot the map with the connections 
# gmap = gmplot.GoogleMapPlotter(original_graph.nodes[0]['pos'][1], original_graph.nodes[0]['pos'][0], 10)
# for u, v, data in original_graph.edges(data=True):
#     gmap.marker(u[0], u[1], color='red')
#     gmap.marker(v[0], v[1], color='red')
#     gmap.plot([u[0], v[0]], [u[1], v[1]], 'blue', edge_width=2)
#
#gmap.draw("original_map.html")

# This func don't work
def plot_original_graph(graph, api_key):
    # Crea el archivo HTML con la estructura básica del mapa
    with open("original_map.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                /* Asegura que el mapa ocupe todo el tamaño de la ventana */
                html, body, #map {
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                /* Estilo para el contenedor de información */
                #info {
                    position: absolute;
                    top: 120px;
                    left: 10px;
                    background-color: white;
                    padding: 10px;
                    border: 1px solid black;
                    border-radius: 5px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    z-index: 1000;
                    font-family: Arial, sans-serif;
                }
                #info h2 {
                    margin: 0 0 5px 0;
                    font-size: 16px;
                }
                #info p {
                    margin: 0;
                    font-size: 14px;
                }
            </style>
            <script src="https://maps.googleapis.com/maps/api/js?key=""" + api_key + """&callback=initMap" async defer></script>
            <script>
                function initMap() {
                    var map = new google.maps.Map(document.getElementById('map'), {
                        zoom: 10,
                        center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
                    });

                    var infoWindow = document.getElementById('info');

                    var markers = [];
                    var edges = """ + json.dumps([{'start': graph.nodes[u]['pos'], 'end': graph.nodes[v]['pos']} for u, v in graph.edges()]) + """;

                    edges.forEach(function(edge) {
                        var start = new google.maps.LatLng(edge.start[1], edge.start[0]);
                        var end = new google.maps.LatLng(edge.end[1], edge.end[0]);

                        var line = new google.maps.Polyline({
                            path: [start, end],
                            geodesic: true,
                            strokeColor: '#FF0000',
                            strokeOpacity: 1.0,
                            strokeWeight: 2,
                            map: map
                        });

                        var markerStart = new google.maps.Marker({
                            position: start,
                            map: map,
                            icon: {
                                url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
                                scaledSize: new google.maps.Size(20, 20)
                            }
                        });

                        var markerEnd = new google.maps.Marker({
                            position: end,
                            map: map,
                            icon: {
                                url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
                                scaledSize: new google.maps.Size(20, 20)
                            }
                        });

                        markerStart.addListener('click', function() {
                            infoWindow.innerHTML = '<h2>District: ' + edge.start[2] + '</h2>' +
                                                   '<p>Latitude: ' + edge.start[1] + '</p>' +
                                                   '<p>Longitude: ' + edge.start[0] + '</p>';
                        });

                        markerEnd.addListener('click', function() {
                            infoWindow.innerHTML = '<h2>District: ' + edge.end[2] + '</h2>' +
                                                   '<p>Latitude: ' + edge.end[1] + '</p>' +
                                                   '<p>Longitude: ' + edge.end[0] + '</p>';
                        });

                        markers.push(markerStart);
                        markers.push(markerEnd);
                    });
                }
            </script>
        </head>
        <body>
            <div id="map"></div>
            <div id="info">Click on a marker to see the district information here.</div>
        </body>
        </html>
        """)

# Example usage
# plot_original_graph(original_graph, api_key) #This func don't work

class MaxComponent:
    def __init__(self, graph):
        self.graph = graph
        self.max_component = self.find_max_component()

    def find_max_component(self):
        visited = set()
        max_component = set()

        def dfs(node, component):
            stack = [node]
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    stack.extend(neighbor for neighbor in self.graph.neighbors(current) if neighbor not in visited)

        for node in self.graph.nodes():
            if node not in visited:
                component = set()
                dfs(node, component)
                if len(component) > len(max_component):
                    max_component = component

        return self.graph.subgraph(max_component)

    def draw_max_component(self, api_key):
        with open("max_component_map.html", "w", encoding="utf-8") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    html, body, #map {
                        height: 100%;
                        margin: 0;
                        padding: 0;
                    }
                    #info {
                        position: absolute;
                        top: 120px;
                        left: 10px;
                        background-color: white;
                        padding: 10px;
                        border: 1px solid black;
                        border-radius: 5px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                        z-index: 1000;
                        font-family: Arial, sans-serif;
                    }
                    #info h2 {
                        margin: 0 0 5px 0;
                        font-size: 16px;
                    }
                    #info p {
                        margin: 0;
                        font-size: 14px;
                    }
                </style>
                <script src="https://maps.googleapis.com/maps/api/js?key=""" + api_key + """&callback=initMap" async defer></script>
                <script>
                    function initMap() {
                        var map = new google.maps.Map(document.getElementById('map'), {
                            zoom: 10,
                            center: {lat: """ + str(self.max_component.nodes[0]['pos'][1]) + """, lng: """ + str(self.max_component.nodes[0]['pos'][0]) + """}
                        });

                        var infoWindow = document.getElementById('info');

                        var markers = [];
                        var edges = """ + json.dumps([{'start': self.max_component.nodes[u]['pos'], 'end': self.max_component.nodes[v]['pos']} for u, v in self.max_component.edges()]) + """;

                        edges.forEach(function(edge) {
                            var start = new google.maps.LatLng(edge.start[1], edge.start[0]);
                            var end = new google.maps.LatLng(edge.end[1], edge.end[0]);

                            var line = new google.maps.Polyline({
                                path: [start, end],
                                geodesic: true,
                                strokeColor: '#FF0000',
                                strokeOpacity: 1.0,
                                strokeWeight: 2,
                                map: map
                            });

                            var markerStart = new google.maps.Marker({
                                position: start,
                                map: map,
                                icon: {
                                    url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
                                    scaledSize: new google.maps.Size(20, 20)
                                }
                            });

                            var markerEnd = new google.maps.Marker({
                                position: end,
                                map: map,
                                icon: {
                                    url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
                                    scaledSize: new google.maps.Size(20, 20)
                                }
                            });

                            markerStart.addListener('click', function() {
                                infoWindow.innerHTML = '<h2>District: ' + edge.start[2] + '</h2>' +
                                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                                       '<p>Longitude: ' + edge.start[0] + '</p>';
                            });

                            markerEnd.addListener('click', function() {
                                infoWindow.innerHTML = '<h2>District: ' + edge.end[2] + '</h2>' +
                                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                                       '<p>Longitude: ' + edge.end[0] + '</p>';
                            });

                            markers.push(markerStart);
                            markers.push(markerEnd);
                        });
                    }
                </script>
            </head>
            <body>
                <div id="map"></div>
                <div id="info">Click on a marker to see the district information here.</div>
            </body>
            </html>
            """)

    def number_of_nodes(self):
        return self.max_component.number_of_nodes()

    def number_of_edges(self):
        return self.max_component.number_of_edges()

# Example usage
max_component1 = MaxComponent(original_graph)
print(f"Number of nodes in the max component: {max_component1.number_of_nodes()}")
print(f"Number of edges in the max component: {max_component1.number_of_edges()}")
max_component = max_component1.max_component

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
    def __init__(self, graph, api_key):
        self.graph = graph
        self.api_key = api_key
        self.mst = []
        self.total_cost = 0

    def prim_mst_distance(self):
        self.mst = []
        self.total_cost = 0
        start_node = next(iter(self.graph.nodes))
        visited = set([start_node])
        edges = [(data['distance'], start_node, neighbor) for neighbor, data in self.graph[start_node].items()]
        heapq.heapify(edges)
        
        while edges:
            distance, u, v = heapq.heappop(edges)
            if v not in visited:
                visited.add(v)
                self.mst.append((u, v, distance))
                self.total_cost += distance
                for neighbor, data in self.graph[v].items():
                    if neighbor not in visited:
                        heapq.heappush(edges, (data['distance'], v, neighbor))
        
        print(f"Prim MST by distance - Nodes: {len(visited)}, Edges: {len(self.mst)}, Total Distance: {self.total_cost}")
        self.draw_mst_html("prim_mst_distance.html", "distance")

    def kruskal_mst_cost(self):
        self.mst = []
        self.total_cost = 0
        edges = [(data['cost'], u, v) for u, v, data in self.graph.edges(data=True)]
        edges.sort()
        
        print(len(self.graph.nodes))
        uf = UnionFind(len(self.graph.nodes))
        node_index = {node: idx for idx, node in enumerate(self.graph.nodes)}
        print(f"Kruskal MST by cost - Nodes: {len(set(node_index.values()))}, Edges: {len(self.mst)}, Total Cost: {self.total_cost}")
        
        for cost, u, v in edges:
            if uf.find(node_index[u]) != uf.find(node_index[v]):
                uf.union(node_index[u], node_index[v])
                self.mst.append((u, v, cost))
                self.total_cost += cost

        print(f"Kruskal MST by cost - Nodes: {len(set(node_index.values()))}, Edges: {len(self.mst)}, Total Cost: {self.total_cost}")
        self.draw_mst_html("kruskal_mst_cost.html", "cost")

    def draw_mst_html(self, file_name, attribute):
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    html, body, #map {
                        height: 100%;
                        margin: 0;
                        padding: 0;
                    }
                    #info {
                        position: absolute;
                        top: 120px;
                        left: 10px;
                        background-color: white;
                        padding: 10px;
                        border: 1px solid black;
                        border-radius: 5px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                        z-index: 1000;
                        font-family: Arial, sans-serif;
                    }
                    #info h2 {
                        margin: 0 0 5px 0;
                        font-size: 16px;
                    }
                    #info p {
                        margin: 0;
                        font-size: 14px;
                    }
                </style>
                <script src="https://maps.googleapis.com/maps/api/js?key=""" + self.api_key + """&callback=initMap" async defer></script>
                <script>
                    function initMap() {
                        var map = new google.maps.Map(document.getElementById('map'), {
                            zoom: 10,
                            center: {lat: """ + str(self.graph.nodes[0]['pos'][1]) + """, lng: """ + str(self.graph.nodes[0]['pos'][0]) + """}
                        });

                        var infoWindow = document.getElementById('info');

                        var markers = [];
                        var edges = """ + json.dumps([{'start': self.graph.nodes[u]['pos'], 'end': self.graph.nodes[v]['pos']} for u, v, _ in self.mst]) + """; 

                        edges.forEach(function(edge) {
                            var start = new google.maps.LatLng(edge.start[1], edge.start[0]);
                            var end = new google.maps.LatLng(edge.end[1], edge.end[0]);

                            var line = new google.maps.Polyline({
                                path: [start, end],
                                geodesic: true,
                                strokeColor: '#FF0000',
                                strokeOpacity: 1.0,
                                strokeWeight: 2,
                                map: map
                            });

                            var markerStart = new google.maps.Marker({
                                position: start,
                                map: map,
                                icon: {
                                    url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
                                    scaledSize: new google.maps.Size(20, 20)
                                }
                            });

                            var markerEnd = new google.maps.Marker({
                                position: end,
                                map: map,
                                icon: {
                                    url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
                                    scaledSize: new google.maps.Size(20, 20)
                                }
                            });

                            markerStart.addListener('click', function() {
                                infoWindow.innerHTML = '<h2>District: ' + edge.start[2] + '</h2>' +
                                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                                       '<p>Longitude: ' + edge.start[0] + '</p>';
                            });

                            markerEnd.addListener('click', function() {
                                infoWindow.innerHTML = '<h2>District: ' + edge.end[2] + '</h2>' +
                                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                                       '<p>Longitude: ' + edge.end[0] + '</p>';
                            });

                            markers.push(markerStart);
                            markers.push(markerEnd);
                        });
                    }
                </script>
            </head>
            <body>
                <div id="map"></div>
                <div id="info">Click on a marker to see the district information here.</div>
            </body>
            </html>
            """)

# Example usage
mst = MST(max_component, api_key)
mst.kruskal_mst_cost()
input()
mst.prim_mst_distance()
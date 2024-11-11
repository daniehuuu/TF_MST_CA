import json
from mst import MST
from initial_dataset import GraphProcessor

api_key = 'AIzaSyBUu6qAVsHdnUJlFDwAeFyk3YQDgvanreA'

class MapProcessor:
    def __init__(self, data_file, api_key):
        self.data_file = data_file
        self.api_key = api_key
        self.load_data()

    def load_data(self):
        self.GProc = GraphProcessor(self.api_key, 'CAN.csv', 'TB_UBIGEOS.csv')
        df = self.GProc.load_data()
        self.initial_euclidian_graph = self.GProc.create_euclidian_measured_graph(df)
        self.real_weighted_graph = self.GProc.read_real_weighted_graph('dataset.csv')
        self.max_component = self.find_max_component()
        self.mst_processor = MST(self.max_component)
        self.mst_processor.prim_mst_distance()
        self.mst_distance_prim = self.mst_processor.mst
        self.mst_distance_total = self.mst_processor.total_amount
        self.mst_processor.kruskal_mst_cost()
        self.mst_cost_kruskal = self.mst_processor.mst
        self.mst_cost_total = self.mst_processor.total_amount
    
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
                    stack.extend(neighbor for neighbor in self.real_weighted_graph.neighbors(current) if neighbor not in visited)

        for node in self.real_weighted_graph.nodes():
            if node not in visited:
                component = set()
                dfs(node, component)
                if len(component) > len(max_component):
                    max_component = component

        return self.real_weighted_graph.subgraph(max_component)

    def plot_map(self, graph_type, file_name):
        # Decide which graph to plot based on the graph_type
        if graph_type == "ComponenteConexaMasGrande":
            graph = self.max_component  # The largest connected component
            script = self.get_maxcomponent_script(graph)   
        elif graph_type == "Euclidean":
            graph = self.initial_euclidian_graph  # Euclidean graph
            script = self.get_euclidean_script(graph)
        elif graph_type == "RealWeighted":
            graph = self.real_weighted_graph  # Real weighted graph
            script = self.get_real_weighted_script(graph)
        elif graph_type == "Original":
            graph = self.real_weighted_graph  # Original graph (no edges)
            script = self.get_original_script(graph)  # Aquí llamamos a get_original_script
        elif graph_type == "PrimMST":
            graph = self.mst_distance_prim  # Prim's MST
            script = self.get_prim_script(graph)  # Llamamos al script de Prim
        elif graph_type == "KruskalMST":
            graph = self.mst_cost_kruskal  # Kruskal's MST
            script = self.get_kruskal_script(graph)  
        else:
            raise ValueError("Unsupported graph type")

        # Generate the map HTML with the same style but with different scripts
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
                    """ + script + """
                </script>
            </head>
            <body>
                <div id="map"></div>
                <div id="info">Click on a marker to see the district information here.</div>
            </body>
            </html>
            """)

    def get_real_weighted_script(self, graph):
      """Genera el script específico para el grafo ponderado real, mostrando las conexiones, distancia en km y costo en miles de soles, y el total de nodos y aristas."""
      return """
      function initMap() {
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 10,
            center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
        });

        var infoWindow = document.getElementById('info');

        // Crear el contenedor de estadísticas en una esquina de la pantalla
        var statsContainer = document.createElement('div');
        statsContainer.style.position = 'absolute';
        statsContainer.style.top = '10px';
        statsContainer.style.right = '10px';
        statsContainer.style.padding = '10px';
        statsContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        statsContainer.style.border = '1px solid #ccc';
        statsContainer.style.borderRadius = '5px';
        statsContainer.style.fontFamily = 'inherit';  // Usar la misma fuente que el resto de la página
        statsContainer.innerHTML = '<h3>Stadistics</h3>' +
                                   '<p>Nodes: ' + """ + str(len(graph.nodes)) + """ + '</p>' +
                                   '<p>Edges: ' + """ + str(len(graph.edges)) + """ + '</p>';
        document.body.appendChild(statsContainer);

        var markers = [];
        var edges = """ + json.dumps([{
            'start': graph.nodes[u]['pos'],
            'start_district': graph.nodes[u]['district'],
            'end': graph.nodes[v]['pos'],
            'end_district': graph.nodes[v]['district'],
            'distance': graph[u][v]['distance'], 
            'cost': graph[u][v]['cost']  
        } for u, v in graph.edges()]) + """;  // Lista de aristas

        // Contar las conexiones por distrito
        var connectionsCount = {};

        edges.forEach(function(edge) {
            if (!connectionsCount[edge.start_district]) {
                connectionsCount[edge.start_district] = 0;
            }
            if (!connectionsCount[edge.end_district]) {
                connectionsCount[edge.end_district] = 0;
            }
            connectionsCount[edge.start_district]++;
            connectionsCount[edge.end_district]++;

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

            line.addListener('click', function() {
                var distance = edge.distance.toFixed(2);  // Distancia en km
                var cost = edge.cost.toFixed(2);  // Costo en miles de soles
                infoWindow.innerHTML = '<h2>Edge Information</h2>' +
                                       '<p>Start District: ' + edge.start_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>End District: ' + edge.end_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>Distance: ' + distance + ' km</p>' +
                                       '<p>Cost: ' + cost + ' mil soles</p>';
            });

            markerStart.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.start_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                       '<p>Longitude: ' + edge.start[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.start_district] + '</p>';
            });

            markerEnd.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.end_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                       '<p>Longitude: ' + edge.end[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.end_district] + '</p>';
            });

            markers.push(markerStart);
            markers.push(markerEnd);
        });
    }
    """




    def get_original_script(self, graph):
        """Genera el script específico para el grafo original (sin aristas)"""
        return """
        function initMap() {
            var map = new google.maps.Map(document.getElementById('map'), {
                zoom: 10,
                center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
            });

            var infoWindow = document.getElementById('info');

            var markers = [];
            var nodes = """ + json.dumps([{
                'position': node['pos'], 
                'district': node['district']
            } for node in graph.nodes.values()]) + """;  // Lista de nodos

            // Crear un marcador para cada nodo
            nodes.forEach(function(node) {
                var position = new google.maps.LatLng(node.position[1], node.position[0]);
                
                var marker = new google.maps.Marker({
                    position: position,
                    map: map,
                    icon: {
                        url: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png", 
                        scaledSize: new google.maps.Size(20, 20)
                    }
                });

                // Mostrar información del distrito cuando se haga clic en el marcador
                marker.addListener('click', function() {
                    infoWindow.innerHTML = '<h2>District: ' + node.district.replace(/ñ/g, 'n') + '</h2>' +  // Reemplazar todas las 'ñ' por 'n'
                                           '<p>Latitude: ' + node.position[1] + '</p>' +
                                           '<p>Longitude: ' + node.position[0] + '</p>';
                });

                markers.push(marker);
            });
        }
        """

    def get_euclidean_script(self, graph):
     """Genera el script para el grafo Euclidiano, mostrando la distancia en las aristas y la información en los marcadores, además del número de conexiones y el total de nodos y aristas."""
     return """
     function initMap() {
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 10,
            center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
        });

        var infoWindow = document.getElementById('info');

        // Crear el contenedor de estadísticas en una esquina de la pantalla
        var statsContainer = document.createElement('div');
        statsContainer.style.position = 'absolute';
        statsContainer.style.top = '10px';
        statsContainer.style.right = '10px';
        statsContainer.style.padding = '10px';
        statsContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        statsContainer.style.border = '1px solid #ccc';
        statsContainer.style.borderRadius = '5px';
        statsContainer.style.fontFamily = 'inherit';  // Usar la misma fuente que el resto de la página
        statsContainer.innerHTML = '<h3>Stadistics</h3>' +
                                   '<p>Nodes: ' + """ + str(len(graph.nodes)) + """ + '</p>' +
                                   '<p>Edges: ' + """ + str(len(graph.edges)) + """ + '</p>';
        document.body.appendChild(statsContainer);

        var markers = [];
        var edges = """ + json.dumps([{
            'start': graph.nodes[u]['pos'],
            'start_district': graph.nodes[u]['district'],
            'end': graph.nodes[v]['pos'],
            'end_district': graph.nodes[v]['district']
        } for u, v in graph.edges()]) + """;  // Lista de aristas

        // Contar las conexiones por distrito
        var connectionsCount = {};

        edges.forEach(function(edge) {
            // Contar las conexiones para cada distrito (inicio y fin)
            if (!connectionsCount[edge.start_district]) {
                connectionsCount[edge.start_district] = 0;
            }
            if (!connectionsCount[edge.end_district]) {
                connectionsCount[edge.end_district] = 0;
            }
            connectionsCount[edge.start_district]++;
            connectionsCount[edge.end_district]++;
        });

        // Función para calcular la distancia Euclidiana
        function calculateEuclideanDistance(start, end) {
            var lat1 = start[1], lon1 = start[0];
            var lat2 = end[1], lon2 = end[0];
            var R = 6371; // Radio de la Tierra en km
            var dLat = (lat2 - lat1) * Math.PI / 180;
            var dLon = (lon2 - lon1) * Math.PI / 180;
            var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                    Math.sin(dLon / 2) * Math.sin(dLon / 2);
            var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            return R * c; // Retorna la distancia en km
        }

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

            // Información al hacer clic en los marcadores
            markerStart.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.start_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                       '<p>Longitude: ' + edge.start[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.start_district] + '</p>';
            });

            markerEnd.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.end_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                       '<p>Longitude: ' + edge.end[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.end_district] + '</p>';
            });

            // Información al hacer clic en la arista (línea)
              line.addListener('click', function() {
                var distance = calculateEuclideanDistance(edge.start, edge.end).toFixed(2); // Calcular distancia
                  infoWindow.innerHTML = '<h2>Edge Information</h2>' +
                                        '<p>Start District: ' + edge.start_district.replace(/ñ/g, 'n') + '</p>' +
                                        '<p>End District: ' + edge.end_district.replace(/ñ/g, 'n') + '</p>' +
                                        '<p>Distance: ' + distance + '</p>' +
                                        '<p>Start District Connections: ' + connectionsCount[edge.start_district] + '</p>' +
                                        '<p>End District Connections: ' + connectionsCount[edge.end_district] + '</p>';
             });

             markers.push(markerStart);
             markers.push(markerEnd);
         });
     }
     """

    def get_maxcomponent_script(self, graph):
     """Genera el script específico para el componente más grande, mostrando la distancia en km y el costo en miles de soles en las aristas."""
     return """
    function initMap() {
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 10,
            center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
        });

        var infoWindow = document.getElementById('info');

        // Crear el contenedor de estadísticas en una esquina de la pantalla
        var statsContainer = document.createElement('div');
        statsContainer.style.position = 'absolute';
        statsContainer.style.top = '10px';
        statsContainer.style.right = '10px';
        statsContainer.style.padding = '10px';
        statsContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        statsContainer.style.border = '1px solid #ccc';
        statsContainer.style.borderRadius = '5px';
        statsContainer.style.fontFamily = 'inherit';  // Usar la misma fuente que el resto de la página
        statsContainer.innerHTML = '<h3>Statistics</h3>' +
                                   '<p>Nodes: ' + """ + str(len(graph.nodes)) + """ + '</p>' +
                                   '<p>Edges: ' + """ + str(len(graph.edges)) + """ + '</p>';
        document.body.appendChild(statsContainer);

        var markers = [];
        var edges = """ + json.dumps([{
            'start': graph.nodes[u]['pos'],
            'start_district': graph.nodes[u]['district'],
            'end': graph.nodes[v]['pos'],
            'end_district': graph.nodes[v]['district'],
            'distance': graph[u][v]['distance'],  # Distancia de la arista
            'cost': graph[u][v]['cost']  # Costo de la arista en miles de soles
        } for u, v in graph.edges()]) + """;  // Lista de aristas

        // Contar las conexiones por distrito
        var connectionsCount = {};

        edges.forEach(function(edge) {
            // Contar las conexiones para cada distrito (inicio y fin)
            if (!connectionsCount[edge.start_district]) {
                connectionsCount[edge.start_district] = 0;
            }
            if (!connectionsCount[edge.end_district]) {
                connectionsCount[edge.end_district] = 0;
            }
            connectionsCount[edge.start_district]++;
            connectionsCount[edge.end_district]++;

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

            // Información al hacer clic en los marcadores
            markerStart.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.start_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                       '<p>Longitude: ' + edge.start[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.start_district] + '</p>';
            });

            markerEnd.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.end_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                       '<p>Longitude: ' + edge.end[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.end_district] + '</p>';
            });

            // Información al hacer clic en la arista (línea)
            line.addListener('click', function() {
                var distance = edge.distance.toFixed(2);  // Distancia en km
                var cost = edge.cost.toFixed(2);  // Costo en miles de soles
                infoWindow.innerHTML = '<h2>Edge Information</h2>' +
                                       '<p>Start District: ' + edge.start_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>End District: ' + edge.end_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>Distance: ' + distance + ' km</p>' +
                                       '<p>Cost: ' + cost + ' mil soles</p>' +
                                       '<p>Start District Connections: ' + connectionsCount[edge.start_district] + '</p>' +
                                       '<p>End District Connections: ' + connectionsCount[edge.end_district] + '</p>';
            });

            markers.push(markerStart);
            markers.push(markerEnd);
        });
     }
     """

    
    def get_prim_script(self, graph):
     """Generates the script for Prim's graph, showing the distance and cost in the edges"""
     return """
     function initMap() {
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 10,
            center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
        });

        var infoWindow = document.getElementById('info');
        var markers = [];
        var edges = """ + json.dumps([{
            'start': graph.nodes[u]['pos'],
            'start_district': graph.nodes[u]['district'],
            'end': graph.nodes[v]['pos'],
            'end_district': graph.nodes[v]['district'],
            'distance': graph[u][v]['distance'],  
            'cost': graph[u][v]['cost']  
        } for u, v in graph.edges()]) + """;  // List of edges

        // Initialize the total cost counter
        var totalDistance = 0;

        // Count the connections by district
        var connectionsCount = {};

        edges.forEach(function(edge) {
            // Add the cost of each edge to the total cost
            totalDistance += edge.distance;

            // Count connections for each district (start and end)
            if (!connectionsCount[edge.start_district]) {
                connectionsCount[edge.start_district] = 0;
            }
            if (!connectionsCount[edge.end_district]) {
                connectionsCount[edge.end_district] = 0;
            }
            connectionsCount[edge.start_district]++;
            connectionsCount[edge.end_district]++;

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
                infoWindow.innerHTML = '<h2>District: ' + edge.start_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                       '<p>Longitude: ' + edge.start[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.start_district] + '</p>';
            });

            markerEnd.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.end_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                       '<p>Longitude: ' + edge.end[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.end_district] + '</p>';
            });

            // Show edge information
            line.addListener('click', function() {
                var distance = edge.distance.toFixed(2);  // Distance in km
                var cost = edge.cost.toFixed(2);  // Cost in thousands of soles
                infoWindow.innerHTML = '<h2>Edge Information</h2>' +
                                       '<p>Start District: ' + edge.start_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>End District: ' + edge.end_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>Distance: ' + distance + ' km</p>' +
                                       '<p>Cost: ' + cost + ' mil soles</p>';
            });

            markers.push(markerStart);
            markers.push(markerEnd);
        });

        // Create the statistics container in the top right corner
        var statsContainer = document.createElement('div');
        statsContainer.style.position = 'absolute';
        statsContainer.style.top = '10px';
        statsContainer.style.right = '10px';  // Positioning it to the right
        statsContainer.style.padding = '15px';
        statsContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
        statsContainer.style.border = '1px solid #ccc';
        statsContainer.style.borderRadius = '5px';
        statsContainer.style.fontFamily = 'Arial, sans-serif';  // Set a clearer font
        statsContainer.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';  // Added shadow for better visibility
        statsContainer.innerHTML = '<h3 style="margin: 0;">Statistics</h3>' +
                                   '<p style="margin: 5px 0;">Nodes: ' + """ + str(len(graph.nodes)) + """ + '</p>' +
                                   '<p style="margin: 5px 0;">Edges: ' + """ + str(len(graph.edges)) + """ + '</p>' +
                                   '<p style="margin: 5px 0;">Total Cost: ' + totalDistance.toFixed(2) + ' km</p>';
        document.body.appendChild(statsContainer);
    }
    """



    
   
    def get_kruskal_script(self, graph):
     """Generates the script for Kruskal's graph, showing the distance, the cost in edges, and the connections by node"""
     return """
     function initMap() {
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 10,
            center: {lat: """ + str(graph.nodes[0]['pos'][1]) + """, lng: """ + str(graph.nodes[0]['pos'][0]) + """}
        });

        var infoWindow = document.getElementById('info');
        var markers = [];
        var edges = """ + json.dumps([{
            'start': graph.nodes[u]['pos'],
            'start_district': graph.nodes[u]['district'],
            'end': graph.nodes[v]['pos'],
            'end_district': graph.nodes[v]['district'],
            'distance': graph[u][v]['distance'],  
            'cost': graph[u][v]['cost']  
        } for u, v in graph.edges()]) + """;  // List of edges

        // Initialize the total cost counter
        var totalCost = 0;

        // Count the connections by district
        var connectionsCount = {};

        edges.forEach(function(edge) {
            // Add the cost of each edge to the total cost
            totalCost += edge.cost;

            // Count connections for each district (start and end)
            if (!connectionsCount[edge.start_district]) {
                connectionsCount[edge.start_district] = 0;
            }
            if (!connectionsCount[edge.end_district]) {
                connectionsCount[edge.end_district] = 0;
            }
            connectionsCount[edge.start_district]++;
            connectionsCount[edge.end_district]++;

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
                infoWindow.innerHTML = '<h2>District: ' + edge.start_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.start[1] + '</p>' +
                                       '<p>Longitude: ' + edge.start[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.start_district] + '</p>';
            });

            markerEnd.addListener('click', function() {
                infoWindow.innerHTML = '<h2>District: ' + edge.end_district.replace(/ñ/g, 'n') + '</h2>' +
                                       '<p>Latitude: ' + edge.end[1] + '</p>' +
                                       '<p>Longitude: ' + edge.end[0] + '</p>' +
                                       '<p>Connections: ' + connectionsCount[edge.end_district] + '</p>';
            });

            // Show edge information
            line.addListener('click', function() {
                var distance = edge.distance.toFixed(2);  // Distance in km
                var cost = edge.cost.toFixed(2);  // Cost in thousands of soles
                infoWindow.innerHTML = '<h2>Edge Information</h2>' +
                                       '<p>Start District: ' + edge.start_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>End District: ' + edge.end_district.replace(/ñ/g, 'n') + '</p>' +
                                       '<p>Distance: ' + distance + ' km</p>' +
                                       '<p>Cost: ' + cost + ' mil soles</p>';
            });

            markers.push(markerStart);
            markers.push(markerEnd);
        });

        // Create the statistics container in the top right corner
        var statsContainer = document.createElement('div');
        statsContainer.style.position = 'absolute';
        statsContainer.style.top = '10px';
        statsContainer.style.right = '10px';  // Positioning it to the right
        statsContainer.style.padding = '15px';
        statsContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
        statsContainer.style.border = '1px solid #ccc';
        statsContainer.style.borderRadius = '5px';
        statsContainer.style.fontFamily = 'Arial, sans-serif';  // Set a clearer font
        statsContainer.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';  // Added shadow for better visibility
        statsContainer.innerHTML = '<h3 style="margin: 0;">Statistics</h3>' +
                                   '<p style="margin: 5px 0;">Total Nodes: ' + """ + str(len(graph.nodes)) + """ + '</p>' +
                                   '<p style="margin: 5px 0;">Total Edges: ' + """ + str(len(graph.edges)) + """ + '</p>' +
                                   '<p style="margin: 5px 0;">Total Cost: ' + totalCost.toFixed(2) + ' miles de soles</p>';
        document.body.appendChild(statsContainer);
    }
    """
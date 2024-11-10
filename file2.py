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
        self.real_weighted_graph = self.GProc.read_real_weighted_graph('dataset.csv') # Use create_real_weighted_graph() for the gm process 
        self.max_component = self.find_max_component()
        self.mst_processor = MST(self.max_component)
        self.mst_distance_prim = self.mst_processor.prim_mst_distance()
        self.mst_distance_total = self.mst_processor.total_amount
        self.mst_cost_kruskal = self.mst_processor.kruskal_mst_cost()
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

    def plot_map(self, graph, file_name):
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
            </body>q
            </html>
            """)

# Example usage
map_processor = MapProcessor('dataset.csv', api_key)
map_processor.plot_map(map_processor.real_weighted_graph, "test.html")
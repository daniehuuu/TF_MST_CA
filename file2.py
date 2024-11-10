import gmplot
import googlemaps
import pandas as pd
import networkx as nx
from scipy.spatial import distance_matrix

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
            Grafo.add_edge(i, nearest, weight=dist_matrix[i][nearest])
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
    calculate_cost = lambda weight: weight * 1.03 if weight <= 1 else (weight * 1.07 if weight < 100 else weight * 1.13)

    edges_to_remove = []
    # Actualiza los pesos de las aristas con las distancias reales caminando
    for u, v, data in Grafo.edges(data=True):
        start = Grafo.nodes[u]['pos']
        end = Grafo.nodes[v]['pos']
        result = gmaps.distance_matrix(origins=[(start[1], start[0])], destinations=[(end[1], end[0])], mode="walking")
        
        if result['rows'][0]['elements'][0]['status'] == 'OK':
            distance = result['rows'][0]['elements'][0]['distance']['value'] / 1000  # Distancia en kilómetros
            data['weight'] = distance
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
            'distance': data['weight'],
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
df = load_data(graph_file_path, altitude_file_path)
if df is not None:
    plot_map(df, api_key)

g = create_graph(df, api_key)
save_graph_to_csv(g, 'test.csv')
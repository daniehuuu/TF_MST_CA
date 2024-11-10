import gmplot
import pandas as pd
import networkx as nx
from scipy.spatial import distance_matrix

# Rutas a los archivos CSV y clave de API de Google Maps
graph_file_path = 'CAN.csv'
altitude_file_path = 'TB_UBIGEOS.csv'
api_key = 'AIzaSyBUu6qAVsHdnUJlFDwAeFyk3YQDgvanreA'

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
        
        # Fusiona los DataFrames basados en el UBIGEO_DISTRITO
        merged_df = pd.merge(graph_df, altitude_df, on='UBIGEO_DISTRITO')
        
        return merged_df
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def create_graph(df):
    # Calcula la matriz de distancias entre las coordenadas
    coords = df[['latitude', 'longitude']].to_numpy()
    dist_matrix = distance_matrix(coords, coords)
    Grafo = nx.Graph()
    
    # Añade nodos al grafo con atributos de posición y distrito
    for i, row in df.iterrows():
        Grafo.add_node(i, pos=(row['longitude'], row['latitude']), district=row['district'])
    
    # Añade aristas al grafo basadas en la matriz de distancias
    for i in range(len(dist_matrix)):
        nearest = dist_matrix[i].argsort()[1]  # Encuentra el nodo más cercano que no sea el mismo nodo
        Grafo.add_edge(i, nearest, weight=dist_matrix[i][nearest])
    
    return Grafo

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

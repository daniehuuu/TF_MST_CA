import pandas as pd
import networkx as nx
import googlemaps
from scipy.spatial import distance_matrix

class GraphProcessor:
    def __init__(self, api_key, graph_file_path, altitude_file_path):
        self.api_key = api_key
        self.graph_file_path = graph_file_path
        self.altitude_file_path = altitude_file_path
        self.euclidian_measured_graph = None
        self.real_weighted_graph = None

    def clean_text(self, text):
        """Limpia caracteres mal codificados y reemplaza 'ñ' por 'n'."""
        if isinstance(text, str):
            text = text.encode('latin1').decode('utf-8', errors='ignore')
            text = text.replace('ñ', 'n').replace('Ñ', 'N')
        return text

    def load_data(self):
        try:
            graph_df = pd.read_csv(self.graph_file_path, delimiter=';', encoding='latin1')
            altitude_df = pd.read_csv(self.altitude_file_path, delimiter=';', encoding='latin1')
            
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
            
            altitude_df['district'] = altitude_df['district'].apply(self.clean_text)
              
            # Fusiona los DataFrames basados en el UBIGEO_DISTRITO
            merged_df = pd.merge(graph_df, altitude_df, on='UBIGEO_DISTRITO')
            
            return merged_df
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def create_euclidian_measured_graph(self, df):
        # Calcula la matriz de distancias entre las coordenadas
        coords = df[['latitude', 'longitude']].to_numpy()
        dist_matrix = distance_matrix(coords, coords)
        
        Grafo = nx.Graph()
        
        # Añade nodos al grafo con atributos de posición y distrito
        for i, row in df.iterrows():
            Grafo.add_node(i, pos=(row['longitude'], row['latitude']), district=row['district'])
        
        # Añade aristas al grafo basadas en las 3 distancias más cortas
        for i in range(len(dist_matrix)):
            # Ordena las distancias y selecciona los índices de las 3 distancias más cortas que no sean 0
            sorted_indices = [index for index in dist_matrix[i].argsort() if dist_matrix[i][index] != 0][:3]
            for nearest in sorted_indices:
                Grafo.add_edge(i, nearest, distance=dist_matrix[i][nearest])
                dist_matrix[nearest][i] = 0  # Establecer la conexión invertida a 0 para evitar duplicados
        
        self.euclidian_measured_graph = Grafo
        return Grafo

    def create_real_weighted_graph(self):
        if self.euclidian_measured_graph is None:
            raise ValueError("Euclidian measured graph has not been created yet.")
        
        Grafo = self.euclidian_measured_graph.copy()
        
        # Inicializa el cliente de Google Maps
        gmaps = googlemaps.Client(key=self.api_key)

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
        
        self.real_weighted_graph = Grafo
        return Grafo

    def save_graph_to_csv(self, graph, file_path):
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
        
    def read_real_weighted_graph(self, file_path):
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

# Uso de la clase
# api_key = 'AIzaSyBUu6qAVsHdnUJlFDwAeFyk3YQDgvanreA'
# graph_file_path = 'CAN.csv'
# altitude_file_path = 'TB_UBIGEOS.csv'
# 
# processor = GraphProcessor(api_key, graph_file_path, altitude_file_path)
# df = processor.load_data()
# if df is not None:
#     g = processor.create_euclidian_measured_graph(df)
#     g = processor.create_real_weighted_graph()
#     processor.save_graph_to_csv(g, 'dataset.csv')

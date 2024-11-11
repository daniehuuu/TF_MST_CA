import tkinter as tk
from tkinter import ttk
import subprocess
from Map_Processor import MapProcessor

api_key = 'AIzaSyBUu6qAVsHdnUJlFDwAeFyk3YQDgvanreA'

app = tk.Tk()
app.title("Planificación de Redes de Fibra Óptica")
app.geometry("1000x800")  

bg_color = "#000000"
frame_color = "#1e1e1e"
label_color = "#ffffff"
highlight_color = "#00ff00"
button_bg_color = "#007acc"
button_fg_color = "#ffffff"

app.configure(bg=bg_color)

frame = ttk.Frame(app, padding="20", style="Custom.TFrame")
frame.place(relx=0.5, rely=0.5, anchor="center")

style = ttk.Style()
style.configure("Custom.TFrame", background=frame_color)
style.configure("Custom.TLabel", background=frame_color, foreground=label_color, font=("Helvetica", 12))
style.configure("Title.TLabel", background=frame_color, foreground=highlight_color, font=("Helvetica", 16, "bold"))

welcome_label = ttk.Label(frame, text="Planificación de Redes de Fibra Óptica", style="Title.TLabel")
welcome_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))  

author_label = ttk.Label(frame, text="Autores:", style="Custom.TLabel")
author_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))  

authors = [
    "u202213208 - Christian Renato Espinoza Saenz",
    "u202312230 - Daniel José Huapaya Vargas",
    "u202211846 - Joaquin David Rivadeneyra Ramos"
]

for i, author in enumerate(authors, start=2):
    author_label = ttk.Label(frame, text=author, style="Custom.TLabel")
    author_label.grid(row=i, column=0, columnspan=2, pady=5)

ttk.Label(frame, text="", style="Custom.TLabel").grid(row=len(authors) + 2, column=0, pady=10)

# Example usage
map_processor = MapProcessor('dataset.csv', api_key)


def plot_and_open(graph, filename):
    map_processor.plot_map(graph, filename)
    subprocess.Popen([filename], shell=True)

button0 = tk.Button(frame, text="Mostar Nodos", command=lambda: plot_and_open("Original", "original.html"), bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button0.grid(row=len(authors) + 3, column=0, columnspan=2, pady=5, padx=10)

button1 = tk.Button(frame, text="Mostrar Conexiones Aproximadas", command=lambda: plot_and_open("Euclidean", "euclidian.html"), bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button1.grid(row=len(authors) + 4, column=0, pady=5, padx=10)

button2 = tk.Button(frame, text="Mostrar con pesos reales", command=lambda: plot_and_open("RealWeighted", "real_weighted.html"), bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button2.grid(row=len(authors) + 4, column=1, pady=5, padx=10)

button3 = tk.Button(frame, text="Mostrar componente máxima", command=lambda: plot_and_open("ComponenteConexaMasGrande", "max_component.html"), bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button3.grid(row=len(authors) + 5, column=0, pady=5, padx=10)

button4 = tk.Button(frame, text="Mostrar MST Prim (Distancia)", command=lambda: plot_and_open("PrimMST", "mst_prim.html"), bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button4.grid(row=len(authors) + 5, column=1, pady=5, padx=10)

button5 = tk.Button(frame, text="Mostrar MST Kruskal (Costo)", command=lambda: plot_and_open("KruskalMST", "mst_kruskal.html"), bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button5.grid(row=len(authors) + 6, column=0, columnspan=2, pady=5, padx=10)
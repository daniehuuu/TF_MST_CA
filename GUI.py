import tkinter as tk
from tkinter import ttk
import subprocess
from GraphController import GraphController
import subprocess

excel_path = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"

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

graph_controller = GraphController(fileIn='dataset.csv', fileOut='mst.csv')

def open_program1():
    graph_controller.show_data()

def open_program2():
    graph_controller.show_visualization()

def open_dataset():
    subprocess.Popen([excel_path, "dataset.csv"])

def open_mst():
    graph_controller.show_mst()

def open_mst_csv():
    graph_controller.export_mst_to_csv('mst.csv')
    subprocess.Popen([excel_path, "mst.csv"])

button1 = tk.Button(frame, text="Mostrar datos", command=open_program1, bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button1.grid(row=len(authors) + 3, column=0, pady=5, padx=10)

button2 = tk.Button(frame, text="Abrir dataset.csv", command=open_dataset, bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button2.grid(row=len(authors) + 3, column=1, pady=5, padx=10)

button3 = tk.Button(frame, text="Mostrar visualización", command=open_program2, bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button3.grid(row=len(authors) + 4, column=0, columnspan=2, pady=5, padx=10)

button4 = tk.Button(frame, text="Mostrar MST", command=open_mst, bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button4.grid(row=len(authors) + 5, column=0, pady=5, padx=10)

button5 = tk.Button(frame, text="Mostrar MST CSV", command=open_mst_csv, bg=button_bg_color, fg=button_fg_color, font=("Helvetica", 12), padx=15, pady=5)
button5.grid(row=len(authors) + 5, column=1, pady=5, padx=10)

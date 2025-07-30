# main.py
import tkinter as tk
from gui import LoLScraperApp

if __name__ == "__main__":
    # Cria a janela principal do Tkinter
    janela = tk.Tk()
    
    # Instancia e executa a aplicação
    app = LoLScraperApp(janela)
    
    # Inicia o loop da interface gráfica
    janela.mainloop()
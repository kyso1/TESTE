# utils.py
import os
import json
import requests
from io import BytesIO
from PIL import Image, ImageTk, ImageDraw

def carregar_id_por_nome_campeao():
    """Carrega o mapeamento de nome de campeão para ID a partir de um JSON."""
    caminho_arquivo = os.path.join(os.path.dirname(__file__), 'icons.json')
    if not os.path.exists(caminho_arquivo):
        print("Aviso: arquivo 'icons.json' não encontrado.")
        return {}
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            id_para_nome = json.load(f)
        nome_para_id = {
            nome.lower().replace(' ', '').replace('.', ''): int(id_str)
            for id_str, nome in id_para_nome.items()
        }
        return nome_para_id
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao carregar 'icons.json': {e}")
        return {}

def criar_foto_arredondada(url: str, size: int):
    """Baixa uma imagem de uma URL, redimensiona e a torna circular."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img_data = response.content
        
        img = Image.open(BytesIO(img_data)).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        img.putalpha(mask)
        return ImageTk.PhotoImage(img)
    except (requests.exceptions.RequestException, IOError, Image.DecompressionBombError) as e:
        print(f"Erro ao criar imagem de {url}: {e}")
        return None
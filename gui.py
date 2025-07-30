# gui.py
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
import threading
from datetime import datetime
from io import BytesIO
import math

# Importa as funções dos outros módulos
from utils import carregar_id_por_nome_campeao, criar_foto_arredondada
from scraper import obter_dados_summoner

# Importações do Matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# --- Constantes de Estilo Modernas ---
BG_COLOR = "#0a0e13"
SECONDARY_BG = "#1e2328"
CARD_BG = "#1a1e22"
ACCENT_COLOR = "#c89b3c"
SECONDARY_ACCENT = "#463714"
TEXT_COLOR = "#f0e6d2"
SECONDARY_TEXT = "#a09b8c"
SUCCESS_COLOR = "#103c3c"
ERROR_COLOR = "#3c1518"
FONT_FAMILY = "Segoe UI"

class ModernScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # --- LÓGICA DE SCROLL REESCRITA E CORRIGIDA ---
        self.canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Este é o frame que vai conter todos os widgets e será rolável
        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")

        # Vincula a configuração da scroll region ao tamanho do frame interno
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Adiciona o frame ao canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # **A CORREÇÃO PRINCIPAL**: Força a largura do frame interno a ser igual à do canvas
        # Isso impede que o conteúdo "vaze" para fora da tela
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Empacotamento
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Vinculação do scroll do mouse
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        # Atualiza a largura do frame interno sempre que o canvas for redimensionado
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def _on_frame_configure(self, event):
        # Atualiza a região de rolagem do canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _on_mousewheel(self, event):
        # Lógica de scroll multiplataforma
        # Windows/macOS usam 'delta', Linux usa 'num'
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")


class LoLScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LoL Analytics Mobile")
        self.root.configure(bg=BG_COLOR)
        
        largura, altura = 410, 690  # Altura reduzida para caber melhor em telas menores
        self.root.geometry(f"{largura}x{altura}")
        self.root.resizable(False, False)

        self.id_por_nome_campeao = carregar_id_por_nome_campeao()

        self._configurar_estilo()
        self._criar_background()
        self._criar_widgets()

    def _configurar_estilo(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, 11))
        style.configure("Title.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, font=(FONT_FAMILY, 18, "bold"))
        style.configure("Subtitle.TLabel", background=BG_COLOR, foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 10))
        
        style.configure("Modern.TButton", background=ACCENT_COLOR, foreground=BG_COLOR, font=(FONT_FAMILY, 12, "bold"), borderwidth=0, focuscolor='none', relief="flat")
        style.map("Modern.TButton", background=[('active', '#d4af37'), ('pressed', '#b8941f')])
        
        style.configure("Modern.TEntry", fieldbackground=SECONDARY_BG, foreground=TEXT_COLOR, borderwidth=1, insertbackground=TEXT_COLOR, relief="flat")
        style.configure("Modern.TCombobox", fieldbackground=SECONDARY_BG, background=SECONDARY_BG, foreground=TEXT_COLOR, arrowcolor=ACCENT_COLOR, borderwidth=1, relief="flat")
        
        style.configure("TScrollbar", background=SECONDARY_BG, troughcolor=BG_COLOR, borderwidth=0, arrowcolor=ACCENT_COLOR)

    def _criar_background(self):
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        r1, g1, b1 = self.root.winfo_rgb(BG_COLOR)
        r2, g2, b2 = self.root.winfo_rgb(SECONDARY_BG)
        
        for i in range(height):
            r = (r1 * (height - i) + r2 * i) // (height * 256)
            g = (g1 * (height - i) + g2 * i) // (height * 256)
            b = (b1 * (height - i) + b2 * i) // (height * 256)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.bg_canvas.create_line(0, i, width, i, fill=color)

    def _criar_widgets(self):
        self.main_frame = ModernScrollableFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10)

        content = self.main_frame.scrollable_frame
        content.columnconfigure(0, weight=1)

        header_frame = ttk.Frame(content)
        header_frame.pack(fill="x", pady=(20, 30))
        ttk.Label(header_frame, text="LoL Analytics", style="Title.TLabel").pack()
        ttk.Label(header_frame, text="Análise de Jogador", style="Subtitle.TLabel").pack()

        input_frame = ttk.Frame(content, style="Card.TFrame")
        input_frame.pack(fill="x", pady=(0, 20), ipady=15)
        
        ttk.Label(input_frame, text="Nome de Invocador", font=(FONT_FAMILY, 11, "bold"), background=CARD_BG).pack(padx=20, pady=(10, 5))
        self.nome_entry = ttk.Entry(input_frame, width=30, style="Modern.TEntry", font=(FONT_FAMILY, 12), justify='center')
        self.nome_entry.pack(padx=20, pady=(0, 15), fill="x", ipady=5)

        ttk.Label(input_frame, text="Região", font=(FONT_FAMILY, 11, "bold"), background=CARD_BG).pack(padx=20, pady=(10, 5))
        self.regiao_combo = ttk.Combobox(input_frame, width=15, style="Modern.TCombobox", font=(FONT_FAMILY, 12), justify='center',
                                         values=["br", "na", "euw", "eune", "kr", "jp", "lan", "las", "oce", "tr", "ru"])
        self.regiao_combo.set("br")
        self.regiao_combo.pack(pady=(0, 20))
        
        self.buscar_btn = ttk.Button(content, text="Analisar Jogador", style="Modern.TButton", command=self.iniciar_busca)
        self.buscar_btn.pack(fill="x", ipady=10, pady=(0, 20))

        self.resultado_container = ttk.Frame(content)
        self.resultado_container.pack(fill="both", expand=True, pady=10)
        self.loading_frame = ttk.Frame(self.resultado_container)
        self.loading_label = ttk.Label(self.loading_frame, text="⏳ Analisando dados...", font=(FONT_FAMILY, 12))
        self.resultado_frame = None

    def iniciar_busca(self):
        nome = self.nome_entry.get().strip()
        regiao = self.regiao_combo.get()
        if not nome:
            self.mostrar_erro("⚠️ Por favor, preencha o nome do invocador.")
            return

        self.buscar_btn.config(state="disabled", text="Analisando...")
        self.mostrar_loading()
        
        thread = threading.Thread(target=self.worker_busca, args=(nome, regiao))
        thread.daemon = True
        thread.start()
        
    def mostrar_loading(self):
        self.limpar_resultados()
        self.loading_frame.pack(pady=50)
        self.loading_label.pack()
        
    def limpar_resultados(self):
        self.loading_frame.pack_forget()
        if self.resultado_frame:
            self.resultado_frame.destroy()
            
    def criar_frame_resultados(self):
        self.resultado_frame = ttk.Frame(self.resultado_container, style="TFrame")
        self.resultado_frame.pack(fill="both", expand=True)
        # Garante que o conteúdo dentro do frame de resultados também se expanda
        self.resultado_frame.columnconfigure(0, weight=1)

    def worker_busca(self, nome, regiao):
        dados = obter_dados_summoner(nome, regiao, self.id_por_nome_campeao)
        self.root.after(0, self.atualizar_ui, dados)

    def atualizar_ui(self, dados):
        self.limpar_resultados()
        self.criar_frame_resultados()
        
        if not dados or "erro" in dados:
            self.mostrar_erro(f"❌ {dados.get('erro', 'Invocador não encontrado.')}")
        else:
            self._preencher_dados(dados)
        
        self.buscar_btn.config(state="normal", text="Analisar Jogador")

    def _preencher_dados(self, dados):
        # Frame container para todo o perfil, para garantir o preenchimento
        profile_container = ttk.Frame(self.resultado_frame, style="TFrame")
        profile_container.pack(fill="x", expand=True)

        profile_card = ttk.Frame(profile_container, style="Card.TFrame")
        profile_card.pack(fill="x", pady=(0, 20), ipady=20)

        if dados.get("icone_url"):
            photo = criar_foto_arredondada(dados["icone_url"], 90)
            if photo:
                icone_label = ttk.Label(profile_card, image=photo, background=CARD_BG)
                icone_label.image = photo
                icone_label.pack(pady=(10, 15))

        nome_do_invocador = self.nome_entry.get().split('#')[0]
        ttk.Label(profile_card, text=nome_do_invocador, font=(FONT_FAMILY, 18, "bold"), background=CARD_BG).pack()

        if dados.get("elo"):
            elo_frame = ttk.Frame(profile_card, style="Card.TFrame")
            elo_frame.pack(pady=10)
            elo_name = dados['elo'].lower().split(' ')[0]
            elo_img_url = f"https://opgg-static.akamaized.net/images/medals_new/{elo_name}.png"
            elo_photo = criar_foto_arredondada(elo_img_url, 30)
            if elo_photo:
                elo_icon = ttk.Label(elo_frame, image=elo_photo, background=CARD_BG)
                elo_icon.image = elo_photo
                elo_icon.pack(side="left", padx=(0, 8))
            ttk.Label(elo_frame, text=dados['elo'], font=(FONT_FAMILY, 14, "bold"), background=CARD_BG, foreground=ACCENT_COLOR).pack(side="left")
        
        stats_data = [
            ("KDA Médio", dados.get('kda_medio', 'N/A'), SECONDARY_BG),
            ("Vitórias", f"{dados.get('vitorias', 'N/A')} ({dados.get('winrate', 'N/A')}%)", SUCCESS_COLOR),
            ("Ranking Global", f"#{dados.get('ranking', 'N/A')}", SECONDARY_ACCENT)
        ]
        for label, value, color in stats_data:
            stat_frame = tk.Frame(profile_container, bg=color)
            stat_frame.pack(fill="x", ipady=8, pady=3)
            ttk.Label(stat_frame, text=label, background=color, foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 9)).pack()
            ttk.Label(stat_frame, text=value, background=color, foreground=TEXT_COLOR, font=(FONT_FAMILY, 12, "bold")).pack()
        
        if dados.get("roles_data"):
            ttk.Label(profile_container, text="Frequência por Rota", font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(pady=(25, 10))
            self.plotar_grafico_radar(profile_container, dados["roles_data"])

        if dados.get("graph_data") and dados.get("rank_map"):
            ttk.Label(profile_container, text="Evolução do Ranking", font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(pady=(25, 10))
            self.plotar_grafico_elo(profile_container, dados["graph_data"], dados["rank_map"])

        if dados.get("campeoes"):
            ttk.Label(profile_container, text="Campeões Recentes", font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(pady=(25, 15))
            for champ in dados["campeoes"][:3]:
                self.criar_card_campeao_moderno(profile_container, champ)

    def plotar_grafico_radar(self, parent, roles_data):
        try:
            labels = [role['role'] for role in roles_data]
            values = [role['played'] for role in roles_data]
            if not labels or not any(values):
                ttk.Label(parent, text="Sem dados de rotas.", foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 10)).pack(pady=20)
                return

            num_vars = len(labels)
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            values_circular = values + values[:1]
            angles_circular = angles + angles[:1]

            fig, ax = plt.subplots(figsize=(3.1, 2.2), subplot_kw=dict(polar=True))
            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)
            ax.plot(angles_circular, values_circular, color=ACCENT_COLOR, linewidth=2)
            ax.fill(angles_circular, values_circular, color=ACCENT_COLOR, alpha=0.25)
            ax.set_yticklabels([])
            ax.set_xticks(angles)
            ax.set_xticklabels(labels, color=TEXT_COLOR, size=9)
            ax.spines['polar'].set_color(SECONDARY_TEXT)
            ax.tick_params(colors=SECONDARY_TEXT)
            plt.tight_layout(pad=0.8)

            buf = BytesIO()
            plt.savefig(buf, format='png', facecolor=BG_COLOR, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            photo = ImageTk.PhotoImage(Image.open(buf))
            graph_label = ttk.Label(parent, image=photo, background=BG_COLOR)
            graph_label.image = photo
            graph_label.pack(pady=(10, 20))
        except Exception as e:
            print(f"Erro ao gerar gráfico de radar: {e}")

    def plotar_grafico_elo(self, parent, graph_data_raw, rank_map):
        try:
            graph_data = [x for x in graph_data_raw if x[1] is not None]
            if len(graph_data) < 2:
                ttk.Label(parent, text="Sem dados suficientes para o gráfico de ranking.", foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 10)).pack(pady=20)
                return

            # Corrige timestamp (ms ou s)
            timestamps = []
            for x in graph_data:
                ts = x[0]
                if ts > 1e10:
                    ts = ts / 1000
                timestamps.append(datetime.fromtimestamp(ts))
            ranks_indices = [float(x[1]) for x in graph_data]

            plt.rcdefaults()
            fig, ax = plt.subplots(figsize=(3.6, 2.2), dpi=100)
            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)

            ax.plot(timestamps, ranks_indices, color=ACCENT_COLOR, linewidth=2, marker='o', markersize=4, markerfacecolor=ACCENT_COLOR, markeredgecolor=BG_COLOR)
            ax.set_title("Evolução do Ranking", fontsize=10, color=TEXT_COLOR, weight='bold')
            ax.set_ylabel("Elo", fontsize=9, color=SECONDARY_TEXT)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')

            # Ticks de ranking
            if rank_map and isinstance(rank_map, list) and len(rank_map) > 0 and isinstance(rank_map[0], dict):
                tick_positions = [i for i, r in enumerate(rank_map) if r.get('rankStr') == 'IV' or r.get('rankId') == 0]
                tick_labels = [r.get('tierRankString', str(i)) for i, r in enumerate(rank_map) if i in tick_positions]
                if len(tick_labels) > 5:
                    step = max(1, len(tick_labels) // 4)
                    tick_positions = tick_positions[::step]
                    tick_labels = tick_labels[::step]
                ax.set_yticks(tick_positions)
                ax.set_yticklabels(tick_labels, fontsize=8)
            else:
                ax.set_yticks([])

            ax.grid(True, linestyle='--', alpha=0.1, color=TEXT_COLOR)
            ax.tick_params(colors=SECONDARY_TEXT, which='both')
            for spine in ax.spines.values():
                spine.set_color(SECONDARY_BG)
            plt.tight_layout(pad=0.8)

            buf = BytesIO()
            plt.savefig(buf, format='png', facecolor=BG_COLOR, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            photo = ImageTk.PhotoImage(Image.open(buf))
            graph_label = ttk.Label(parent, image=photo, background=BG_COLOR)
            graph_label.image = photo
            graph_label.pack(pady=(10, 20))
        except Exception as e:
            print(f"Erro ao gerar gráfico de elo: {e}")

    def criar_card_campeao_moderno(self, parent, champ):
        champ_frame = ttk.Frame(parent, style="Card.TFrame")
        champ_frame.pack(fill="x", pady=5, ipady=10)
        champ_frame.columnconfigure(1, weight=1)
        
        champ_photo = criar_foto_arredondada(champ['icon_url'], 50)
        if champ_photo:
            icon_label = ttk.Label(champ_frame, image=champ_photo, background=CARD_BG)
            icon_label.image = champ_photo
            icon_label.grid(row=0, column=0, rowspan=2, padx=15, sticky="w")
        
        ttk.Label(champ_frame, text=champ['nome'], font=(FONT_FAMILY, 12, "bold"), background=CARD_BG).grid(row=0, column=1, sticky="w")
        stats_text = f"🎮 {champ['partidas']} partidas  •  🏆 {champ['winrate']}% WR"
        ttk.Label(champ_frame, text=stats_text, font=(FONT_FAMILY, 9), foreground=SECONDARY_TEXT, background=CARD_BG).grid(row=1, column=1, sticky="w")

    def mostrar_erro(self, mensagem):
        self.limpar_resultados()
        self.criar_frame_resultados()
        error_frame = tk.Frame(self.resultado_frame, bg=ERROR_COLOR)
        error_frame.pack(fill="x", ipady=20, pady=20)
        ttk.Label(error_frame, text=mensagem, foreground="white", font=(FONT_FAMILY, 11), background=ERROR_COLOR, wraplength=350, justify='center').pack()

def main():
    root = tk.Tk()
    LoLScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
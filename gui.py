# gui.py
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import threading
from datetime import datetime
from io import BytesIO
import requests
import math

# Importa as funções dos outros módulos
from utils import carregar_id_por_nome_campeao, criar_foto_arredondada
from scraper import obter_dados_summoner

# A importação do matplotlib é feita aqui, pois é uma dependência da GUI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np


# --- Constantes de Estilo Modernas ---
BG_COLOR = "#0a0e13"
SECONDARY_BG = "#1e2328"
CARD_BG = "#1e2328"
ACCENT_COLOR = "#c89b3c"
SECONDARY_ACCENT = "#463714"
TEXT_COLOR = "#f0e6d2"
SECONDARY_TEXT = "#a09b8c"
SUCCESS_COLOR = "#0f2027"
ERROR_COLOR = "#3c1518"
FONT_FAMILY = "Segoe UI"
BORDER_RADIUS = 8


class ModernScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Criar canvas e scrollbar
        self.canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configurar scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack elementos
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        self.bind_mousewheel()

    def bind_mousewheel(self):
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', bind_to_mousewheel)
        self.canvas.bind('<Leave>', unbind_from_mousewheel)


class GradientFrame(tk.Frame):
    def __init__(self, parent, color1, color2, width=400, height=100, **kwargs):
        super().__init__(parent, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.width = width
        self.height = height
        
        self.canvas = tk.Canvas(self, width=width, height=height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.draw_gradient()
        
    def draw_gradient(self):
        self.canvas.delete("gradient")
        
        # Criar gradiente vertical
        r1, g1, b1 = self.hex_to_rgb(self.color1)
        r2, g2, b2 = self.hex_to_rgb(self.color2)
        
        for i in range(self.height):
            ratio = i / self.height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.canvas.create_line(0, i, self.width, i, fill=color, tags="gradient")
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class ModernCard(tk.Frame):
    def __init__(self, parent, bg_color=CARD_BG, border_color=ACCENT_COLOR, **kwargs):
        super().__init__(parent, bg=bg_color, **kwargs)
        
        # Criar borda moderna
        self.configure(relief="flat", bd=0)
        
        # Frame interno para conteúdo
        self.content_frame = tk.Frame(self, bg=bg_color)
        self.content_frame.pack(fill="both", expand=True, padx=2, pady=2)


class LoLScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Android Studio")
        self.root.configure(bg=BG_COLOR)
        # Dimensões mobile (ex: 430x900, centralizado)
        largura, altura = 430, 900
        self.root.geometry(f"{largura}x{altura}")
        self.root.minsize(largura, altura)
        self.root.maxsize(largura, altura)
        # Centralizar na tela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.root.winfo_screenheight() // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
        # Ícone customizado
        try:
            self.root.iconphoto(True, tk.PhotoImage(file="icon.png"))
        except Exception:
            pass

        self.id_por_nome_campeao = carregar_id_por_nome_campeao()

        self._configurar_estilo()
        self._criar_background()
        self._criar_widgets()
        self._criar_marcadagua()

    def _criar_marcadagua(self):
        # Marca d'água no canto inferior direito
        try:
            marca_frame = tk.Frame(self.root, bg='', highlightthickness=0)
            marca_frame.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)
            # Ícone
            try:
                icon = tk.PhotoImage(file="icon.png")
                icon = icon.subsample(2, 2) if icon.width() > 32 else icon
                icon_label = tk.Label(marca_frame, image=icon, bg='', bd=0)
                icon_label.image = icon
                icon_label.pack(side='left', padx=(0, 4))
            except Exception:
                pass
            # Texto
            texto = tk.Label(marca_frame, text="Android Studio Dev", font=(FONT_FAMILY, 10, "bold"), fg="#ffffff", bg='', bd=0)
            texto.pack(side='left')
            # Transparência
            marca_frame.attributes = getattr(marca_frame, 'attributes', lambda *a, **k: None)
            try:
                marca_frame.attributes('-alpha', 0.5)
            except Exception:
                pass
            texto.configure(fg="#ffffff", bg='')
            texto.after(100, lambda: texto.configure(fg="#ffffff", bg=''))
        except Exception:
            pass

    def _configurar_estilo(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # Configurações gerais
        style.configure("TFrame", background=BG_COLOR, borderwidth=0)
        style.configure("Card.TFrame", background=CARD_BG, relief="flat")
        
        # Labels
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, 
                       font=(FONT_FAMILY, 11))
        style.configure("Title.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, 
                       font=(FONT_FAMILY, 16, "bold"))
        style.configure("Subtitle.TLabel", background=BG_COLOR, foreground=SECONDARY_TEXT, 
                       font=(FONT_FAMILY, 10))
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_COLOR, 
                       font=(FONT_FAMILY, 10))
        
        # Botões modernos
        style.configure("Modern.TButton", 
                       background=ACCENT_COLOR, 
                       foreground=BG_COLOR, 
                       font=(FONT_FAMILY, 11, "bold"),
                       borderwidth=0,
                       focuscolor='none',
                       relief="flat")
        style.map("Modern.TButton", 
                 background=[('active', '#d4af37'), ('pressed', '#b8941f')])
        
        # Campos de entrada
        style.configure("Modern.TEntry", 
                       fieldbackground=SECONDARY_BG, 
                       foreground=TEXT_COLOR, 
                       borderwidth=2,
                       insertbackground=TEXT_COLOR,
                       relief="flat")
        style.map("Modern.TEntry",
                 focuscolor=[('focus', ACCENT_COLOR)])
        
        # Combobox
        style.configure("Modern.TCombobox", 
                       fieldbackground=SECONDARY_BG, 
                       background=SECONDARY_BG, 
                       foreground=TEXT_COLOR, 
                       arrowcolor=ACCENT_COLOR,
                       borderwidth=2,
                       relief="flat")
        
        # Scrollbar
        style.configure("TScrollbar",
                       background=SECONDARY_BG,
                       troughcolor=BG_COLOR,
                       borderwidth=0,
                       arrowcolor=ACCENT_COLOR,
                       darkcolor=SECONDARY_BG,
                       lightcolor=SECONDARY_BG)

    def _criar_background(self):
        # Criar um canvas para o fundo com blend maior entre as cores
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.update_idletasks()
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self._draw_background_pattern(width, height)

    def _draw_background_pattern(self, width, height):
        # Gradiente principal com blend maior
        self.bg_canvas.configure(bg=BG_COLOR)
        steps = 200
        for i in range(steps):
            ratio = i / steps
            r1, g1, b1 = self._hex_to_rgb(BG_COLOR)
            r2, g2, b2 = self._hex_to_rgb(ACCENT_COLOR)
            r = int(r1 + (r2 - r1) * ratio * 0.5)
            g = int(g1 + (g2 - g1) * ratio * 0.5)
            b = int(b1 + (b2 - b1) * ratio * 0.5)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.bg_canvas.create_rectangle(0, int(i * height / steps), width, int((i + 1) * height / steps), fill=color, outline="")
        # Adicionar padrão hexagonal sutil
        hex_size = 60
        for x in range(0, width + hex_size, hex_size):
            for y in range(0, height + hex_size, hex_size):
                offset_x = (hex_size // 2) if (y // hex_size) % 2 else 0
                self.bg_canvas.create_polygon(
                    self._hexagon_points(x + offset_x, y, hex_size // 3),
                    outline=SECONDARY_BG, fill="", width=1
                )

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _hexagon_points(self, x, y, size):
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            points.extend([
                x + size * math.cos(angle),
                y + size * math.sin(angle)
            ])
        return points

    def _criar_widgets(self):
        # Frame principal com scroll, centralizado
        self.main_frame = ModernScrollableFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        content = self.main_frame.scrollable_frame

        # Header com título centralizado e visual mobile
        header_frame = ttk.Frame(content)
        header_frame.pack(fill="x", pady=(0, 18))

        title_label = ttk.Label(header_frame, text="Android Studio", style="Title.TLabel")
        title_label.pack(anchor="center", pady=(10, 0))

        subtitle_label = ttk.Label(header_frame, text="Player Analytics Dashboard", style="Subtitle.TLabel")
        subtitle_label.pack(anchor="center", pady=(0, 8))

        # Card de input centralizado
        input_card = ModernCard(content, relief="raised", bd=1)
        input_card.pack(pady=(0, 16), padx=8, fill="x")
        input_content = input_card.content_frame

        # Frame para inputs
        ttk.Label(input_content, text="Nome de Invocador", font=(FONT_FAMILY, 10, "bold")).pack(anchor="center", padx=10, pady=(16, 4))
        ttk.Label(input_content, text="Ex: Sandman#nunu", style="Subtitle.TLabel").pack(anchor="center", padx=10, pady=(0, 4))
        self.nome_entry = ttk.Entry(input_content, width=28, style="Modern.TEntry", font=(FONT_FAMILY, 11))
        self.nome_entry.pack(padx=10, pady=(0, 10), fill="x")

        # Frame para região
        region_frame = ttk.Frame(input_content)
        region_frame.pack(fill="x", padx=10, pady=(0, 12))
        ttk.Label(region_frame, text="Região", font=(FONT_FAMILY, 10, "bold")).pack(anchor="center", pady=(0, 4))
        self.regiao_combo = ttk.Combobox(region_frame, width=12, style="Modern.TCombobox", font=(FONT_FAMILY, 11), values=["br", "na", "euw", "eune", "kr", "jp", "lan", "las", "oce", "tr", "ru"])
        self.regiao_combo.set("br")
        self.regiao_combo.pack(anchor="center")

        # Botão de busca moderno centralizado
        button_frame = ttk.Frame(input_content)
        button_frame.pack(fill="x", padx=10, pady=(8, 12))
        self.buscar_btn = ttk.Button(button_frame, text="🔍 Analisar Jogador", style="Modern.TButton", command=self.iniciar_busca)
        self.buscar_btn.pack(fill="x", ipady=8)

        # Frame para resultados
        self.resultado_container = ttk.Frame(content)
        self.resultado_container.pack(fill="both", expand=True, pady=10)

        # Loading indicator (inicialmente escondido)
        self.loading_frame = ttk.Frame(self.resultado_container)
        self.loading_label = ttk.Label(self.loading_frame, text="⏳ Analisando dados...", font=(FONT_FAMILY, 12))

        # Frame real para resultados (será recriado quando necessário)
        self.resultado_frame = None

    def iniciar_busca(self):
        nome = self.nome_entry.get().strip()
        regiao = self.regiao_combo.get()
        
        if not nome or not regiao:
            self.mostrar_erro("⚠️ Por favor, preencha todos os campos.")
            return

        self.buscar_btn.config(state="disabled", text="🔄 Analisando...")
        self.mostrar_loading()
        
        thread = threading.Thread(target=self.worker_busca, args=(nome, regiao))
        thread.daemon = True
        thread.start()
        
    def mostrar_loading(self):
        self.limpar_resultados()
        self.loading_frame.pack(fill="x", pady=50)
        self.loading_label.pack()
        
    def limpar_resultados(self):
        # Esconder loading se estiver visível
        self.loading_frame.pack_forget()
        
        # Destruir frame de resultados anterior se existir
        if self.resultado_frame:
            self.resultado_frame.destroy()
            
    def criar_frame_resultados(self):
        """Cria um novo frame para os resultados"""
        self.resultado_frame = ttk.Frame(self.resultado_container)
        self.resultado_frame.pack(fill="both", expand=True)

    def worker_busca(self, nome, regiao):
        dados = obter_dados_summoner(nome, regiao, self.id_por_nome_campeao)
        self.root.after(0, self.atualizar_ui, dados)

    def atualizar_ui(self, dados):
        self.loading_frame.pack_forget()
        self.limpar_resultados()
        self.criar_frame_resultados()  # Criar novo frame para resultados
        
        if not dados or "erro" in dados:
            self.mostrar_erro(f"❌ {dados.get('erro', 'Invocador não encontrado ou perfil privado.')}")
        else:
            self._preencher_dados(dados)
        
        self.buscar_btn.config(state="normal", text="🔍 Analisar Jogador")

    def _preencher_dados(self, dados):
        # Card do perfil principal centralizado
        profile_card = ModernCard(self.resultado_frame, relief="raised", bd=1)
        profile_card.pack(pady=(0, 20))
        profile_content = profile_card.content_frame

        # Header do perfil centralizado
        header_frame = ttk.Frame(profile_content)
        header_frame.pack(fill="x", pady=20, padx=20)

        # Ícone do perfil
        if dados.get("icone_url"):
            icon_frame = ttk.Frame(header_frame)
            icon_frame.pack(side="left", padx=(0, 20))
            photo = criar_foto_arredondada(dados["icone_url"], 80)
            if photo:
                icone_label = ttk.Label(icon_frame, image=photo)
                icone_label.image = photo
                icone_label.pack()

        # Informações do perfil
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side="left", fill="both", expand=True)

        # Nome do jogador centralizado
        ttk.Label(info_frame, text=dados.get('nome', 'N/A'), font=(FONT_FAMILY, 16, "bold")).pack(anchor="center")

        # Elo com ícone
        if dados.get("elo"):
            elo_frame = ttk.Frame(info_frame)
            elo_frame.pack(anchor="center", pady=(5, 0))
            elo_name = dados['elo'].lower().split(' ')[0]
            elo_img_url = f"https://opgg-static.akamaized.net/images/medals_new/{elo_name}.png"
            elo_photo = criar_foto_arredondada(elo_img_url, 32)
            if elo_photo:
                elo_label = ttk.Label(elo_frame, image=elo_photo)
                elo_label.image = elo_photo
                elo_label.pack(side="left", padx=(0, 10))
            ttk.Label(elo_frame, text=dados['elo'], font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(side="left")

        # KDA médio (se presente)
        if dados.get('kda_medio'):
            kda_card = ModernCard(profile_content, bg_color=SECONDARY_BG)
            kda_card.pack(pady=(10, 10), fill="x")
            kda_label = ttk.Label(kda_card.content_frame, text=f"KDA Médio: {dados['kda_medio']}", font=(FONT_FAMILY, 13, "bold"), foreground=ACCENT_COLOR, background=SECONDARY_BG)
            kda_label.pack(anchor="center", pady=10)

        # Estatísticas em cards menores centralizados
        stats_frame = ttk.Frame(profile_content)
        stats_frame.pack(fill="x", pady=(0, 20), padx=20)
        stats_data = [
            ("🏆 Vitórias", f"{dados.get('vitorias', 'N/A')}", SUCCESS_COLOR),
            ("📊 Winrate", f"{dados.get('winrate', 'N/A')}%", ACCENT_COLOR),
            ("🌍 Ranking", f"#{dados.get('ranking', 'N/A')}", SECONDARY_ACCENT)
        ]
        for i, (label, value, color) in enumerate(stats_data):
            stat_frame = tk.Frame(stats_frame, bg=color, relief="flat")
            stat_frame.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            stats_frame.columnconfigure(i, weight=1)
            ttk.Label(stat_frame, text=label, background=color, foreground=TEXT_COLOR, font=(FONT_FAMILY, 9)).pack(pady=(10, 2))
            ttk.Label(stat_frame, text=value, background=color, foreground=TEXT_COLOR, font=(FONT_FAMILY, 12, "bold")).pack(pady=(0, 10))

        # Gráfico melhorado
        if dados.get("graph_data") and dados.get("rank_map"):
            graph_card = ModernCard(self.resultado_frame, relief="raised", bd=1)
            graph_card.pack(pady=(0, 20))
            ttk.Label(graph_card.content_frame, text="📈 Evolução do Ranking", font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(pady=(20, 10))
            self.plotar_grafico_moderno(graph_card.content_frame, dados["graph_data"], dados["rank_map"])

        # Gráfico de roles (rotas)
        if dados.get("roles_data") and len(dados["roles_data"]):
            roles_card = ModernCard(self.resultado_frame, relief="raised", bd=1)
            roles_card.pack(pady=(0, 20))
            ttk.Label(roles_card.content_frame, text="🗺️ Desempenho por Rota", font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(pady=(20, 10))
            self.plotar_grafico_roles(roles_card.content_frame, dados["roles_data"])

    def plotar_grafico_roles(self, parent, roles_data):
        # Gráfico de barras horizontal para winrate por rota
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from PIL import Image, ImageTk
        from io import BytesIO
        if not roles_data:
            ttk.Label(parent, text="Sem dados de rotas.", foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 10)).pack(pady=20)
            return
        roles = [r['role'] for r in roles_data]
        winrates = [r['winrate'] for r in roles_data]
        played = [r['played'] for r in roles_data]
        fig, ax = plt.subplots(figsize=(4.2, 2.2), dpi=100)
        fig.patch.set_facecolor(CARD_BG)
        ax.set_facecolor(CARD_BG)
        bars = ax.barh(roles, winrates, color=ACCENT_COLOR, edgecolor=SECONDARY_ACCENT, alpha=0.85)
        for i, bar in enumerate(bars):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f"{winrates[i]:.1f}%", va='center', ha='left', color=TEXT_COLOR, fontsize=9)
        ax.set_xlabel('Winrate (%)', color=TEXT_COLOR, fontsize=10)
        ax.set_xlim(0, max(winrates + [60]))
        ax.tick_params(colors=TEXT_COLOR, labelsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(SECONDARY_TEXT)
        ax.spines['left'].set_color(SECONDARY_TEXT)
        plt.tight_layout(pad=1.0)
        buf = BytesIO()
        plt.savefig(buf, format='png', facecolor=CARD_BG, bbox_inches='tight', dpi=100, transparent=False)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)
        photo = ImageTk.PhotoImage(image)
        graph_label = ttk.Label(parent, image=photo, background=CARD_BG)
        graph_label.image = photo
        graph_label.pack(pady=(10, 20))

        # Campeões mais jogados
        if dados.get("campeoes"):
            champs_card = ModernCard(self.resultado_frame, relief="raised", bd=1)
            champs_card.pack(pady=(0, 20))
            ttk.Label(champs_card.content_frame, text="⚔️ Campeões Mais Jogados", font=(FONT_FAMILY, 14, "bold"), foreground=ACCENT_COLOR).pack(pady=(20, 20))
            for i, champ in enumerate(dados["campeoes"][:5]):  # Limitar a 5 campeões
                self.criar_card_campeao_moderno(champs_card.content_frame, champ, i)

    def plotar_grafico_moderno(self, parent, graph_data_raw, rank_map):
        try:
            # Filtrar e processar dados
            graph_data = [(x[0], x[1]) for x in graph_data_raw if x[1] is not None and len(x) >= 2]
            if not graph_data or len(graph_data) < 2:
                ttk.Label(parent, text="📊 Dados insuficientes para gerar gráfico", 
                         foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 10)).pack(pady=20)
                return

            # Separar timestamps e ranks
            timestamps = []
            ranks_indices = []
            
            for timestamp, rank_idx in graph_data:
                try:
                    # Converter timestamp (pode estar em ms ou s)
                    if timestamp > 1e10:  # Se for maior que 10^10, está em ms
                        dt = datetime.fromtimestamp(timestamp / 1000)
                    else:
                        dt = datetime.fromtimestamp(timestamp)
                    
                    timestamps.append(dt)
                    ranks_indices.append(float(rank_idx))
                except (ValueError, OSError) as e:
                    print(f"Erro ao processar timestamp {timestamp}: {e}")
                    continue
            
            if len(timestamps) < 2:
                ttk.Label(parent, text="📊 Dados insuficientes para gerar gráfico", 
                         foreground=SECONDARY_TEXT, font=(FONT_FAMILY, 10)).pack(pady=20)
                return

            # Resetar estilo do matplotlib
            plt.rcdefaults()
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(5.5, 3.2), dpi=100)
            
            # Configurar cores do tema
            fig.patch.set_facecolor(CARD_BG)
            ax.set_facecolor(CARD_BG)
            
            # Plotar linha principal
            line_color = '#c89b3c'  # Dourado do LoL
            ax.plot(timestamps, ranks_indices, 
                   color=line_color, linewidth=2.5, alpha=0.9, zorder=3,
                   marker='o', markersize=4, markerfacecolor=line_color, 
                   markeredgecolor='white', markeredgewidth=0.5)
            
            # Configurar título e labels
            ax.set_title("Evolução do Ranking", fontsize=12, color=TEXT_COLOR, 
                        pad=15, weight='bold')
            ax.set_ylabel("Posição no Ranking", fontsize=10, color=TEXT_COLOR)
            ax.set_xlabel("Período", fontsize=10, color=TEXT_COLOR)
            
            # Configurar eixo X (datas)
            if len(timestamps) > 10:
                # Se há muitos pontos, mostrar menos datas
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(timestamps)//6)))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(timestamps)//6)))
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
            
            # Configurar eixo Y (ranks)
            if rank_map and len(rank_map) > 0:
                # Filtrar ranks válidos baseados nos dados reais
                min_rank = int(min(ranks_indices))
                max_rank = int(max(ranks_indices))
                
                # Criar ticks para ranks visíveis
                valid_ranks = []
                valid_labels = []
                
                for i, rank_info in enumerate(rank_map):
                    if min_rank <= i <= max_rank:
                        valid_ranks.append(i)
                        # Usar o nome do tier se disponível
                        if isinstance(rank_info, dict):
                            label = rank_info.get('tierRankString', f'Rank {i}')
                        else:
                            label = str(rank_info)
                        valid_labels.append(label)
                
                # Limitar número de ticks para evitar sobreposição
                if len(valid_ranks) > 8:
                    step = max(1, len(valid_ranks) // 6)
                    valid_ranks = valid_ranks[::step]
                    valid_labels = valid_labels[::step]
                
                if valid_ranks:
                    ax.set_yticks(valid_ranks)
                    ax.set_yticklabels(valid_labels, fontsize=8)
            else:
                # Fallback se não há rank_map
                ax.set_ylabel("Índice de Rank", fontsize=10, color=TEXT_COLOR)
            
            # Inverter eixo Y para que o melhor rank fique no topo (rank 0 = topo)
            if len(ranks_indices) > 1:
                if min(ranks_indices) < max(ranks_indices):
                    pass  # Não inverter, sentido padrão: menor valor no topo
                else:
                    ax.invert_yaxis()  # Inverter se os dados vierem invertidos
            
            # Grid sutil
            ax.grid(True, linestyle='-', alpha=0.1, color=TEXT_COLOR)
            ax.grid(True, linestyle='--', alpha=0.05, color=TEXT_COLOR, which='minor')
            
            # Configurar aparência dos eixos
            ax.tick_params(colors=TEXT_COLOR, which='both', labelsize=8)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color(SECONDARY_TEXT)
            ax.spines['left'].set_color(SECONDARY_TEXT)
            
            # Layout otimizado
            plt.tight_layout(pad=1.0)
            
            # Salvar imagem
            buf = BytesIO()
            plt.savefig(buf, format='png', facecolor=CARD_BG, 
                       edgecolor='none', bbox_inches='tight', dpi=100, 
                       transparent=False)
            plt.close(fig)
            buf.seek(0)
            
            # Exibir no tkinter
            image = Image.open(buf)
            photo = ImageTk.PhotoImage(image)
            graph_label = ttk.Label(parent, image=photo, background=CARD_BG)
            graph_label.image = photo
            graph_label.pack(pady=(10, 20))
            
        except Exception as e:
            print(f"Erro detalhado ao gerar gráfico: {e}")
            import traceback
            traceback.print_exc()
            
            error_label = ttk.Label(parent, text="⚠️ Erro ao gerar gráfico de ranking", 
                                   foreground="orange", font=(FONT_FAMILY, 10))
            error_label.pack(pady=20)

    def criar_card_campeao_moderno(self, parent, champ, index):
        # Card individual para cada campeão
        champ_card = tk.Frame(parent, bg=SECONDARY_BG, relief="flat")
        champ_card.pack(fill="x", padx=20, pady=5)
        
        # Frame interno
        champ_frame = ttk.Frame(champ_card)
        champ_frame.pack(fill="x", padx=15, pady=10)
        champ_frame.columnconfigure(1, weight=1)
        
        # Posição
        position_label = tk.Label(champ_frame, text=f"#{index + 1}", 
                                 bg=ACCENT_COLOR, fg=BG_COLOR, 
                                 font=(FONT_FAMILY, 10, "bold"),
                                 width=3, height=1)
        position_label.grid(row=0, column=0, rowspan=2, padx=(0, 15), sticky="w")
        
        # Ícone do campeão
        champ_photo = criar_foto_arredondada(champ['icon_url'], 40)
        if champ_photo:
            icon_label = ttk.Label(champ_frame, image=champ_photo, background=SECONDARY_BG)
            icon_label.image = champ_photo
            icon_label.grid(row=0, column=1, rowspan=2, padx=(0, 15), sticky="w")
        
        # Nome do campeão
        ttk.Label(champ_frame, text=champ['nome'], 
                 font=(FONT_FAMILY, 11, "bold"), 
                 foreground=TEXT_COLOR, background=SECONDARY_BG).grid(row=0, column=2, sticky="w")
        
        # Estatísticas
        stats_text = f"🎮 {champ['partidas']} partidas  •  🏆 {champ['winrate']}% WR  •  🏅 Rank #{champ['ranking']}"
        ttk.Label(champ_frame, text=stats_text, 
                 font=(FONT_FAMILY, 9), 
                 foreground=SECONDARY_TEXT, background=SECONDARY_BG).grid(row=1, column=2, sticky="w")

    def mostrar_erro(self, mensagem):
        if not self.resultado_frame:
            self.criar_frame_resultados()
            
        error_card = ModernCard(self.resultado_frame, bg_color=ERROR_COLOR)
        error_card.pack(fill="x", pady=20)
        
        ttk.Label(error_card.content_frame, text=mensagem, 
                 foreground="white", font=(FONT_FAMILY, 12), 
                 background=ERROR_COLOR, wraplength=400).pack(pady=30)


def main():
    root = tk.Tk()
    app = LoLScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
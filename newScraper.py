# # newScraper.py
# import requests
# from bs4 import BeautifulSoup
# import re
# import json
# from urllib.parse import quote

# # --- Novas importações para o Selenium ---
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options

# def obter_dados_summoner(nome_invocador: str, regiao: str, id_por_nome_campeao: dict):
#     """Busca e extrai todos os dados do perfil de um invocador usando Selenium para carregar a página completa."""
    
#     # --- Configuração do Selenium para rodar em segundo plano (headless) ---
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")  # Não abre uma janela do navegador
#     chrome_options.add_argument("--log-level=3") # Reduz a quantidade de logs no terminal
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
#     # Instala e gerencia o driver do Chrome automaticamente
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)
    
#     print("-" * 50)
#     print(f"Buscando dados para: {nome_invocador} na região {regiao.upper()}")

#     parts = nome_invocador.strip().split('#', 1)
#     game_name = parts[0]
#     tagline = parts[1] if len(parts) > 1 else None
#     encoded_game_name = quote(game_name)

#     if tagline:
#         nome_formatado = f"{encoded_game_name}-{tagline}"
#     else:
#         nome_formatado = encoded_game_name

#     url = f"https://www.leagueofgraphs.com/summoner/{regiao.lower()}/{nome_formatado.lower()}"
#     print(f"Acessando URL com Selenium: {url}")

#     try:
#         driver.get(url)
#         # --- A MÁGICA ACONTECE AQUI ---
#         # Espera até 10 segundos para que a tabela de roles (ou seu container) esteja presente na página
#         # Usamos o seletor CSS para encontrar o container que você nos mostrou.
#         wait = WebDriverWait(driver, 10)
#         wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tab-id='championsData-soloqueue'] table")))
        
#         print("[DIAGNÓSTICO] Tabela de roles carregada com sucesso!")
        
#         # Pega o HTML da página DEPOIS que o JavaScript foi executado
#         html_content = driver.page_source
        
#     except TimeoutException:
#         print("[DIAGNÓSTICO] ERRO: A tabela de roles não carregou a tempo. A página pode ter mudado ou o jogador não tem dados.")
#         driver.quit()
#         return {"erro": "Não foi possível carregar os dados das rotas do jogador."}
#     except Exception as e:
#         print(f"[DIAGNÓSTICO] Um erro inesperado ocorreu com o Selenium: {e}")
#         driver.quit()
#         return {"erro": "Ocorreu um erro ao carregar a página."}

#     # Fecha o navegador em segundo plano
#     driver.quit()

#     # Agora, usamos o BeautifulSoup para analisar o HTML completo que o Selenium nos deu
#     soup = BeautifulSoup(html_content, 'html.parser')
    
#     roles_data = []
#     roles_table_container = soup.find('div', {'data-tab-id': 'championsData-soloqueue'})
#     if roles_table_container:
#         roles_table = roles_table_container.find('table') 
#         if roles_table:
#             for row in roles_table.find_all('tr')[1:]:
#                 cols = row.find_all('td')
#                 if len(cols) >= 3:
#                     try:
#                         role_name = cols[0].find('div', class_='txt name').text.strip()
#                         played = int(cols[1]['data-sort-value'])
#                         winrate = round(float(cols[2]['data-sort-value']) * 100, 1)
#                         roles_data.append({"role": role_name, "played": played, "winrate": winrate})
#                     except (AttributeError, ValueError, KeyError, TypeError) as e:
#                         print(f"Erro ao processar linha da tabela: {e}")

#     # O resto do código permanece o mesmo, pois agora ele analisa o HTML correto
#     kda_medio = "N/A"
#     kda_div = soup.find('div', class_='kda')
#     if kda_div:
#         try:
#             kills = float(kda_div.find('span', class_='kills').text)
#             deaths = float(kda_div.find('span', class_='deaths').text)
#             assists = float(kda_div.find('span', class_='assists').text)
#             if deaths > 0:
#                 kda_val = (kills + assists) / deaths
#                 kda_medio = f"{kills:.1f} / {deaths:.1f} / {assists:.1f}   ({kda_val:.2f} KDA)"
#             else:
#                 kda_medio = f"{kills:.1f} / {deaths:.1f} / {assists:.1f}   (Perfeito)"
#         except (ValueError, AttributeError): pass

#     meta_desc = soup.find('meta', attrs={'name': 'twitter:description'})
#     if not meta_desc:
#         return {"erro": "Não foi possível encontrar os dados do perfil (meta tag)."}

#     dados = {
#         "campeoes": [], 
#         "kda_medio": kda_medio,
#         "roles_data": roles_data
#     }
    
#     descricao = meta_desc['content']
#     elo_match = re.search(r"([A-Za-z ]+\d*) - Wins: (\d+) \((\d+\.\d+)%\)", descricao)
#     if elo_match:
#         dados["elo"] = elo_match.group(1).strip()
#         dados["vitorias"] = elo_match.group(2)
#         dados["winrate"] = elo_match.group(3)

#     dados["ranking"] = (re.search(r"\(#([\d,]+)\)", descricao) or [None, None])[1]

#     meta_img = soup.find('meta', attrs={'name': 'twitter:image'})
#     if meta_img:
#         dados["icone_url"] = meta_img['content']
#         if dados["icone_url"].startswith('//'):
#             dados["icone_url"] = 'https:' + dados["icone_url"]

#     campeoes_matches = re.findall(r"/ ([^:]+): Wins: ([\d\.]+)% - Played: (\d+) \(#([\d,]+)\)", descricao)
#     for nome, win, played, rank in campeoes_matches:
#         nome_chave = nome.strip().lower().replace(' ', '').replace('.', '')
#         champ_id = id_por_nome_campeao.get(nome_chave)
#         icon_url = f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{champ_id}.png" if champ_id else None
#         dados["campeoes"].append({"nome": nome.strip(), "winrate": win, "partidas": played, "ranking": rank, "icon_url": icon_url})

#     # Os dados de gráfico de ranking precisam ser extraídos do HTML completo também
#     script_content = str(soup)
#     graphdata_match = re.search(r'const graphData\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
#     rankmap_match = re.search(r'const graphIntegerValues24\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
#     dados["graph_data"] = json.loads(graphdata_match.group(1)) if graphdata_match else None
#     dados["rank_map"] = json.loads(rankmap_match.group(1)) if rankmap_match else None

#     print("-" * 50)
#     return dados
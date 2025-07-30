# scraper.py
import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import quote

def obter_dados_summoner(nome_invocador: str, regiao: str, id_por_nome_campeao: dict):
    """Busca e extrai todos os dados do perfil de um invocador no League of Graphs."""
    
    print("-" * 50)
    print(f"Buscando dados para: {nome_invocador} na região {regiao.upper()}")
    
    parts = nome_invocador.strip().split('#', 1)
    game_name = parts[0]
    tagline = parts[1] if len(parts) > 1 else None
    encoded_game_name = quote(game_name)

    if tagline:
        nome_formatado = f"{encoded_game_name}-{tagline}"
    else:
        nome_formatado = encoded_game_name
    
    url = f"https://www.leagueofgraphs.com/summoner/{regiao.lower()}/{nome_formatado.lower()}"
    print(f"Acessando URL: {url}")
    
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR,pt;q=0.9"}

    try:
        resposta = requests.get(url, headers=headers, timeout=10)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERRO DE CONEXÃO: {e}")
        return {"erro": f"Erro de conexão: {e}"}

    soup = BeautifulSoup(resposta.text, 'html.parser')
    script_content = resposta.text
    
    roles_data = []

    # Tenta extrair dados da tabela HTML
    print("\n[DIAGNÓSTICO] Tentando extrair dados via tabela HTML...")
    roles_table_container = soup.find('div', {'data-tab-id': 'championsData-soloqueue'})
    if roles_table_container:
        # --- CORREÇÃO PRINCIPAL AQUI ---
        # Procura por QUALQUER tabela dentro do container, tornando o código mais robusto
        roles_table = roles_table_container.find('table') 
        
        if roles_table:
            for row in roles_table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3: # Mudado para 'maior ou igual' por segurança
                    try:
                        role_name = cols[0].find('div', class_='txt name').text.strip()
                        played = int(cols[1]['data-sort-value'])
                        winrate = round(float(cols[2]['data-sort-value']) * 100, 1)
                        
                        roles_data.append({
                            "role": role_name,
                            "played": played,
                            "winrate": winrate
                        })
                    except (AttributeError, ValueError, KeyError, TypeError) as e:
                        print(f"[DIAGNÓSTICO] Erro ao processar linha da tabela: {e}")
            if roles_data:
                print(f"[DIAGNÓSTICO] Sucesso! Dados da tabela extraídos. Roles: {[role['role'] for role in roles_data]}")
            else:
                print("[DIAGNÓSTICO] Tabela encontrada, mas não foi possível extrair dados das linhas.")
        else:
            print("[DIAGNÓSTICO] Container de roles encontrado, mas NENHUMA tabela foi encontrada dentro dele.")
    else:
        print("[DIAGNÓSTICO] Container 'championsData-soloqueue' não foi encontrado na página.")

    kda_medio = "N/A"
    kda_div = soup.find('div', class_='kda')
    if kda_div:
        try:
            kills = float(kda_div.find('span', class_='kills').text)
            deaths = float(kda_div.find('span', class_='deaths').text)
            assists = float(kda_div.find('span', class_='assists').text)
            
            if deaths > 0:
                kda_val = (kills + assists) / deaths
                kda_medio = f"{kills:.1f} / {deaths:.1f} / {assists:.1f}   ({kda_val:.2f} KDA)"
            else:
                kda_medio = f"{kills:.1f} / {deaths:.1f} / {assists:.1f}   (Perfeito)"
        except (ValueError, AttributeError): pass

    meta_desc = soup.find('meta', attrs={'name': 'twitter:description'})
    meta_img = soup.find('meta', attrs={'name': 'twitter:image'})
    
    graphdata_match = re.search(r'const graphData\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
    rankmap_match = re.search(r'const graphIntegerValues24\s*=\s*(\[.*?\]);', script_content, re.DOTALL)

    graph_data, rank_map = None, None

    if graphdata_match:
        try: graph_data = json.loads(graphdata_match.group(1))
        except json.JSONDecodeError: pass
    
    if rankmap_match:
        try: rank_map = json.loads(rankmap_match.group(1))
        except json.JSONDecodeError: pass
    
    if not meta_desc:
        return {"erro": "Não foi possível encontrar os dados do perfil. Pode ser privado ou inválido."}

    dados = {
        "campeoes": [], 
        "graph_data": graph_data, 
        "rank_map": rank_map,
        "kda_medio": kda_medio,
        "roles_data": roles_data
    }

    descricao = meta_desc['content']

    elo_match = re.search(r"([A-Za-z ]+\d*) - Wins: (\d+) \((\d+\.\d+)%\)", descricao)
    if elo_match:
        dados["elo"] = elo_match.group(1).strip()
        dados["vitorias"] = elo_match.group(2)
        dados["winrate"] = elo_match.group(3)

    dados["ranking"] = (re.search(r"\(#([\d,]+)\)", descricao) or [None, None])[1]

    if meta_img:
        dados["icone_url"] = meta_img['content']
        if dados["icone_url"].startswith('//'):
            dados["icone_url"] = 'https:' + dados["icone_url"]

    campeoes_matches = re.findall(r"/ ([^:]+): Wins: ([\d\.]+)% - Played: (\d+) \(#([\d,]+)\)", descricao)
    for nome, win, played, rank in campeoes_matches:
        nome_chave = nome.strip().lower().replace(' ', '').replace('.', '')
        champ_id = id_por_nome_campeao.get(nome_chave)
        icon_url = f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{champ_id}.png" if champ_id else None
        dados["campeoes"].append({
            "nome": nome.strip(), "winrate": win, "partidas": played,
            "ranking": rank, "icon_url": icon_url
        })
    print("-" * 50)
    return dados
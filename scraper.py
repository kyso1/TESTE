# scraper.py
import requests
from bs4 import BeautifulSoup
import re
import json

def obter_dados_summoner(nome_invocador: str, regiao: str, id_por_nome_campeao: dict):
    """Busca e extrai todos os dados do perfil de um invocador no League of Graphs."""
    nome_invocador = nome_invocador.strip().replace('#', ' ')
    nome_formatado = nome_invocador.replace(' ', '-').lower()
    url = f"https://www.leagueofgraphs.com/summoner/{regiao.lower()}/{nome_formatado}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR,pt;q=0.9"}

    try:
        resposta = requests.get(url, headers=headers, timeout=10)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro de conexão: {e}"}

    soup = BeautifulSoup(resposta.text, 'html.parser')

    roles_data = []
    roles_table_container = soup.find('div', {'data-tab-id': 'championsData-soloqueue'})
    if roles_table_container:
        roles_table = roles_table_container.find('table')
        
        # --- MUDANÇA: Adicionada verificação para garantir que a tabela existe ---
        if roles_table:
            # Pula a primeira linha (cabeçalho da tabela)
            for row in roles_table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) == 3:
                    try:
                        role_name = cols[0].find('div', class_='txt name').text.strip()
                        played = int(cols[1]['data-sort-value'])
                        winrate_raw = float(cols[2]['data-sort-value'])
                        winrate = round(winrate_raw * 100, 1)
                        
                        roles_data.append({
                            "role": role_name,
                            "played": played,
                            "winrate": winrate
                        })
                    except (AttributeError, ValueError, KeyError) as e:
                        print(f"Erro ao extrair dados da rota: {e}")
        # --- FIM DA MUDANÇA ---

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
        except (ValueError, AttributeError) as e:
            print(f"Erro ao extrair KDA: {e}")

    meta_desc = soup.find('meta', attrs={'name': 'twitter:description'})
    meta_img = soup.find('meta', attrs={'name': 'twitter:image'})
    
    script_content = resposta.text
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
    return dados
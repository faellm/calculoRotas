# DROP BOX
from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import folium

app = Flask(__name__)

# Dicionário com os bairros das cidades
bairros_por_cidade = {

    'Curitiba': [
        'Bairro 1 - Curitiba',
        'Bairro 2 - Curitiba',
        'Bairro 3 - Curitiba',
    ],

    'São José dos Pinhais': [
        'Academia',
        'Afonso Pena',
        'Águas Belas',
        'Área Institucional Aeroportuária',
        'Aristocrata',
        'Arujá',
        'Aviação',
        'Barro Preto',
        'Bom Jesus',
        'Boneca do Iguaçu',
        'Borda do Campo',
        'Cachoeira',
        'Campina do Taquaral',
        'Campo Largo da Roseira',
        'Centro',
        'Cidade Jardim',
        'Colônia Rio Grande',
        'Contenda',
        'Costeira',
        'Cristal',
        'Cruzeiro',
        'Del Rey',
        'Dom Rodrigo',
        'Guatupê',
        'Iná',
        'Ipê',
        'Itália',
        'Jurema',
        'Miringuava',
        'Ouro Fino',
        'Parque da Fonte',
        'Pedro Moro',
        'Quissisana',
        'Rio Pequeno',
        'Roseira de São Sebastião',
        'Santo Antônio',
        'São Cristóvão',
        'São Domingos',
        'São Marcos',
        'São Pedro',
        'Zacarias',
    ]
}

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        cidade = request.form['cidade']
        bairro = request.form['bairro']
        return generate_map(cidade, bairro)

    return render_template('teste_index.html')

def get_bairros(cidade):

    # Retornar os bairros específicos da cidade selecionada
    return bairros_por_cidade.get(cidade, [])

@app.route('/bairros', methods=['GET'])
def get_bairros_json():
    cidade = request.args.get('cidade')
    bairros = get_bairros(cidade)
    return jsonify({'bairros': bairros})

def generate_map(bairro, cidade,skip_axis='y'):

    # Obter o grafo de ruas do bairro usando o OSM
    G = ox.graph_from_place(bairro + ", " + cidade, network_type='drive')

     # Calcular uma sequência de nós que minimize a distância total percorrida
    rota = list(nx.approximation.traveling_salesman_problem(G.to_undirected(), cycle=True))

    # Adicionar a primeira aresta de volta ao último nó para formar um ciclo
    rota.append(rota[0])

    # Lista para armazenar a rota ótima, pulando um eixo específico
    rota_otima = [rota[0]]
    axis_val = G.nodes[rota[0]][skip_axis]  # Valor do eixo atual

    for i in range(1, len(rota)):
        # Verificar se o próximo nó possui o mesmo valor no eixo específico
        if G.nodes[rota[i]][skip_axis] != axis_val:
            axis_val = G.nodes[rota[i]][skip_axis]  # Atualizar o valor do eixo
            rota_otima.append(rota[i])

    # Obter as coordenadas dos pontos da rota ótima
    lats, lons = zip(*[(G.nodes[node]['y'], G.nodes[node]['x']) for node in rota_otima])

    # Calcular o centro do bairro
    centro_bairro = ox.geocode(bairro + ", " + cidade)

    # Crie um mapa Folium centrado no centro do bairro
    mapa = folium.Map(location=[centro_bairro[0], centro_bairro[1]], zoom_start=14)

    # Adicione as arestas (ruas) do grafo ao mapa
    edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

    for _, edge in edges.iterrows():
        linha = [(edge['geometry'].coords[0][1], edge['geometry'].coords[0][0]), 
                (edge['geometry'].coords[-1][1], edge['geometry'].coords[-1][0])]
        folium.PolyLine(locations=linha, color='blue').add_to(mapa)

    # Adicione a rota ótima em vermelho (caminho mais curto)
    coordenadas_rota = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in rota]
    folium.PolyLine(locations=coordenadas_rota, color='red').add_to(mapa)

    # Adicionar marcadores numerados para a rota ótima
    for i, coordenada in enumerate(coordenadas_rota):
        
        popup_text = f'Ponto {i+1}'
        icon = folium.DivIcon(html=f'<div style="font-size: 14px; font-weight: bold; background-color: yellow; border-radius: 50%; padding: 6px 12px;">{i+1}</div>')
        folium.Marker(location=coordenada, popup=popup_text, icon=icon).add_to(mapa)
        
    return mapa.get_root().render()

if __name__ == '__main__':
    app.run(debug=True)

# DROP BOX
from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import folium
from folium import plugins
from geopy.distance import distance
import math

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

def arrow_icon(color='red', icon_size=(10, 10), icon_anchor=(5, 5)):

    icon_url = f"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-{color}.png"
    return folium.CustomIcon(icon_url, icon_size=icon_size, icon_anchor=icon_anchor)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        cidade = request.form['cidade']
        bairro = request.form['bairro']
        map_html = generate_map(cidade, bairro)

        return render_template('map_template.html', map_html=map_html)
    
    return render_template('map_front.html')

def get_bairros(cidade):
    # Retornar os bairros específicos da cidade selecionada
    return bairros_por_cidade.get(cidade, [])

@app.route('/bairros', methods=['GET'])
def get_bairros_json():

    cidade = request.args.get('cidade')
    bairros = get_bairros(cidade)

    return jsonify({'bairros': bairros})

def calculate_bearing(lat1, lon1, lat2, lon2):

    # Calcular a direção entre os pontos utilizando a função atan2
    # O resultado está em radianos, então vamos converter para graus
    bearing = math.atan2(lon2 - lon1, lat2 - lat1)
    bearing = math.degrees(bearing)
    
    return bearing

def generate_map(bairro, cidade, skip_axis='y'):

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
    coordenadas_rota = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in rota_otima]

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

    # Adicionar a rota ótima em vermelho (caminho mais curto)
    folium.PolyLine(locations=coordenadas_rota, color='red').add_to(mapa)

    # Código para adicionar as setas de direcionamento nos nós da rota ótima
    for i in range(len(coordenadas_rota) - 1):
        coord_origem = coordenadas_rota[i]
        coord_destino = coordenadas_rota[i + 1]

        # Calcular a direção entre os pontos de origem e destino
        arrow_angle = calculate_bearing(coord_origem[0], coord_origem[1], coord_destino[0], coord_destino[1])

        # Adicionar o ícone com a seta de direcionamento na rota ótima
        plugins.AntPath(
            
            locations=[coord_origem, coord_destino],
            dash_array=[10, 20],
            weight=5,
            color='red',
            arrow_heads=True,
            arrowsize=0.7,

        ).add_to(mapa)

    # Adicionar marcadores nos nós da rota ótima com ícone de direção (setas)
    for i in range(len(coordenadas_rota) - 1):

        coord_origem = coordenadas_rota[i]
        coord_destino = coordenadas_rota[i + 1]

        # Calcular a direção entre os pontos de origem e destino
        arrow_angle = calculate_bearing(coord_origem[0], coord_origem[1], coord_destino[0], coord_destino[1])

        # Adicionar o marcador com o ícone de direção (seta)
        folium.Marker(
            
            location=coord_origem,
            icon=folium.DivIcon(
                html=f'<div style="transform: rotate({arrow_angle}deg);">'
                     f'<i class="fa fa-arrow-up fa-1x" style="color: yellow;"></i></div>',
                icon_size=(30, 30),
            ),
        ).add_to(mapa)

    # Adicionar marcador no ponto de partida com ícone de "seta para cima"
    folium.Marker(
        location=coordenadas_rota[0],
        icon=folium.DivIcon(
            html='<div style="transform: rotate(0deg);">'
                 '<i class="fa fa-arrow-up fa-3x" style="color: yellow;"></i></div>',
            icon_size=(30, 30),
        ),
    ).add_to(mapa)

    # Adicionar marcador no ponto de chegada com ícone de "seta para baixo"
    folium.Marker(
        location=coordenadas_rota[-1],
        icon=folium.DivIcon(
            html='<div style="transform: rotate(180deg);">'
                 '<i class="fa fa-arrow-up fa-3x" style="color: yellow;"></i></div>',
            icon_size=(30, 30),
        ),
    ).add_to(mapa)

     # Adicionar marcador no ponto de partida com ícone de "partida"
    folium.Marker(
        location=coordenadas_rota[0],
        icon=folium.DivIcon(
            html='<div style="transform: rotate(0deg);">'
                 '<i class="fa fa-flag fa-3x" style="color: green; fonte-size: 5px">Inicio/Fim</i></div>',
            icon_size=(30, 30),
        ),
    ).add_to(mapa)

    return mapa.get_root().render()

if __name__ == '__main__':
    app.run(debug=True)

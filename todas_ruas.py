from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import folium
from folium import plugins
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

def arrow_icon(color='blue', icon_size=(10, 10), icon_anchor=(5, 5)):
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

    # Calcular uma sequência de nós que minimize a distância total percorrida (TSP)
    rota = list(nx.approximation.traveling_salesman_problem(G.to_undirected(), cycle=True))

    # Obter as coordenadas dos pontos da rota
    coordenadas_rota = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in rota]

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

    # Código para adicionar as setas de direcionamento nos nós da rota
    for i in range(len(coordenadas_rota) - 1):
        coord_origem = coordenadas_rota[i]
        coord_destino = coordenadas_rota[i + 1]

        # Calcular a direção entre os pontos de origem e destino
        arrow_angle = calculate_bearing(coord_origem[0], coord_origem[1], coord_destino[0], coord_destino[1])

        # Adicionar o marcador com a seta de direcionamento na rota
        folium.Marker(
            location=coord_destino,
            icon=folium.DivIcon(
                html=f'<div style="transform: rotate({arrow_angle}deg);">'
                     '<i class="fa fa-arrow-up fa-3x" style="color: red;"></i></div>',
                icon_size=(30, 30),
            ),
        ).add_to(mapa)

    # Adicionar marcador no ponto de partida com ícone de "seta para cima"
    folium.Marker(
        location=coordenadas_rota[0],
        icon=folium.DivIcon(
            html='<div style="transform: rotate(0deg);">'
                 '<i class="fa fa-flag-checkered fa-3x" style="color: red;"></i></div>',
            icon_size=(30, 30),
        ),
    ).add_to(mapa)

    # Adicionar marcador no ponto de chegada com ícone de "seta para baixo"
    folium.Marker(
        location=coordenadas_rota[-1],
        icon=folium.DivIcon(
            html='<div style="transform: rotate(180deg);">'
                 '<i class="fa fa-flag-checkered fa-3x" style="color: red;"></i></div>',
            icon_size=(30, 30),
        ),
    ).add_to(mapa)

    return mapa.get_root().render()

if __name__ == '__main__':
    app.run(debug=True)

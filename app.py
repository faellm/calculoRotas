from flask import Flask, render_template, request
import osmnx as ox
import networkx as nx
import folium

app = Flask(__name__)

# Substitua 'your_mapbox_token' pelo seu token de acesso do Mapbox
mapbox_token = 'pk.eyJ1Ijoic3RoZWNhbWlsZSIsImEiOiJjbGs5enF3eHgwMjIxM2xuYXhmMWF2M3J3In0.GsOKW7BGbB3isNIHZx8pNg'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        bairro = request.form['bairro']
        cidade = request.form['cidade']
        return generate_map(bairro, cidade)
    
    return render_template('index.html')

def generate_map(bairro, cidade):

    # Obter o grafo de ruas do bairro usando o OSM
    G = ox.graph_from_place(bairro + ", " + cidade, network_type='drive')

    # Calcular uma sequência de nós que minimize a distância total percorrida
    rota = list(nx.approximation.traveling_salesman_problem(G.to_undirected(), cycle=True))

    # Adicionar a primeira aresta de volta ao último nó para formar um ciclo
    rota.append(rota[0])

    # Obter as coordenadas dos pontos da rota
    lats, lons = zip(*[(G.nodes[node]['y'], G.nodes[node]['x']) for node in rota])

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

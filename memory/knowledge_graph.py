import networkx as nx
import json
import os
from config import DATA_PATH

GRAPH_FILE = f"{DATA_PATH}/knowledge_graph.json"

def load_graph() -> nx.Graph:
    G = nx.Graph()
    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE) as f:
            data = json.load(f)
            G = nx.node_link_graph(data)
    return G

def save_graph(G: nx.Graph):
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(GRAPH_FILE, "w") as f:
        json.dump(nx.node_link_data(G), f, indent=2)

def update_graph(articles: list[dict]) -> nx.Graph:
    G = load_graph()
    for article in articles:
        entities = article.get("entities", [])
        source = article.get("source", "unknown")
        # add source node
        if not G.has_node(source):
            G.add_node(source, type="source")
        # add entity nodes and connect to source
        for entity in entities:
            if not G.has_node(entity):
                G.add_node(entity, type="entity")
            if G.has_edge(source, entity):
                G[source][entity]["weight"] += 1
            else:
                G.add_edge(source, entity, weight=1)
        # connect co-occurring entities
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                if G.has_edge(e1, e2):
                    G[e1][e2]["weight"] += 1
                else:
                    G.add_edge(e1, e2, weight=1)
    save_graph(G)
    print(f"[KnowledgeGraph] {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def get_entity_connections(entity: str, G: nx.Graph = None) -> list:
    if G is None:
        G = load_graph()
    if entity in G:
        return list(G.neighbors(entity))
    return []
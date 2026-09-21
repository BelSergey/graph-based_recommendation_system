import networkx as nx
from apps.interactions.models import Interaction


def build_interaction_graph(min_weight: float = 0.0) -> nx.Graph:
    """
    Строит bipartite-граф: узлы 'u_<id>' — пользователи, 'p_<id>' — товары.
    Вес ребра = сумма весов взаимодействий между парой.
    """
    graph = nx.Graph()

    interactions = Interaction.objects.select_related('user', 'product').all()

    for interaction in interactions:
        u_node = f'u_{interaction.user_id}'
        p_node = f'p_{interaction.product_id}'

        graph.add_node(u_node, bipartite=0, type='user')
        graph.add_node(p_node, bipartite=1, type='product')

        if graph.has_edge(u_node, p_node):
            graph[u_node][p_node]['weight'] += interaction.weight
        else:
            graph.add_edge(u_node, p_node, weight=interaction.weight)

    if min_weight > 0:
        edges_to_remove = [
            (u, v) for u, v, d in graph.edges(data=True)
            if d['weight'] < min_weight
        ]
        graph.remove_edges_from(edges_to_remove)

    return graph

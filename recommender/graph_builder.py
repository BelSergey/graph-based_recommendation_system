import networkx as nx
from interactions.models import Interaction
from django.db.models import Sum


def build_interaction_graph(min_weight: float = 0.0) -> nx.Graph:
    """Строит взвешенный двудольный граф из взаимодействий."""
    graph: nx.Graph = nx.Graph()

    aggregated = Interaction.objects.values("user_id", "product_id").annotate(
        total_weight=Sum("weight")
    )

    for row in aggregated:
        u_node = f"u_{row['user_id']}"
        p_node = f"p_{row['product_id']}"

        graph.add_node(u_node, bipartite=0, type="user")
        graph.add_node(p_node, bipartite=1, type="product")
        graph.add_edge(u_node, p_node, weight=float(row["total_weight"]))

    if min_weight > 0:
        edges_to_remove = [
            (u, v) for u, v, d in graph.edges(data=True) if d["weight"] < min_weight
        ]
        graph.remove_edges_from(edges_to_remove)

    return graph

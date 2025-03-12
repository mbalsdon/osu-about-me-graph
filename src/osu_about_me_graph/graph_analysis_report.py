from . import classes

import networkx

#################################################################################################################################################
#################################################################################################################################################

def create_nx_graph(mentions_graph: classes.DirectedGraph) -> networkx.MultiDiGraph:
    print("Creating base graph...")

    G = networkx.MultiDiGraph()

    edges = []
    for user, users_referred_to in mentions_graph.adj.items():
        G.add_node(user)
        for user_referred_to in users_referred_to:
            edges.append((user, user_referred_to))
    
    G.add_edges_from(edges)
    return G

#################################################################################################################################################
#################################################################################################################################################

def graph_analysis_report(mentions_graph: classes.DirectedGraph, analysis_report_filename: str, no_analysis_report: bool) -> None:
    """
    Generates a file containing results of graph analysis algorithms; e.g. betweenness centrality, PageRank, etc.
    """
    print(f"\n--- Generating graph analysis report for {len(mentions_graph.adj)} users...")

    if no_analysis_report:
        print(f"'No analysis' flag was set - exiting early...")
        return

    # Convert graph
    G = create_nx_graph(mentions_graph)

    # PageRank
    pagerank = networkx.pagerank(G, alpha=0.6)
    pagerank = sorted(pagerank.items(), key=lambda user: user[1], reverse=True)

    # Betweenness centrality
    betweenness_centrality = networkx.betweenness_centrality(G)
    betweenness_centrality = sorted(betweenness_centrality.items(), key=lambda user: user[1], reverse=True)

    # HITS
    (hits_hubs, hits_authorities) = networkx.hits(G)
    hits_hubs = sorted(hits_hubs.items(), key=lambda user: user[1], reverse=True)
    hits_authorities = sorted(hits_authorities.items(), key=lambda user: user[1], reverse=True)

    # (Louvain) Communities
    louvain_communities = networkx.community.louvain_communities(G, resolution=10)
    louvain_communities = sorted(louvain_communities, key=lambda community: len(community), reverse=True)
    louvain_communities = [community for community in louvain_communities if len(community) > 1]

    # Strongly connected components
    strongly_connected_components = networkx.strongly_connected_components(G)
    strongly_connected_components = sorted(list(strongly_connected_components), key=lambda component: len(component), reverse=True)
    strongly_connected_components = [component for component in strongly_connected_components if len(component) > 1]

    # Reciprocity
    reciprocity = networkx.reciprocity(G)

    # Build report
    lines = ["### Graph Analysis Report",]

    lines.extend(["\n---", "**PageRank**"])
    lines.append("\n```")
    for user in pagerank:
        lines.append(f"{user[0]} : {user[1]:.8f}")
    lines.append("```")

    lines.extend(["\n---", "**Betweenness Centrality**"])
    lines.append("\n```")
    for user in betweenness_centrality:
        lines.append(f"{user[0]} : {user[1]:.8f}")
    lines.append("```")

    lines.extend(["\n---", "**Hubs (HITS)**"])
    lines.append("\n```")
    for user in hits_hubs:
        lines.append(f"{user[0]} : {user[1]:.8f}")
    lines.append("```")

    lines.extend(["\n---", "**Authorities (HITS)**"])
    lines.append("\n```")
    for user in hits_authorities:
        lines.append(f"{user[0]} : {user[1]:.8f}")
    lines.append("```")

    lines.extend(["\n---", "**Communities (Louvain)**"])
    lines.append("\n```")
    for i, community in enumerate(louvain_communities):
        lines.append(f"Community {i + 1}:")
        for username in community:
            lines.append(f"    {username}")
    lines.append("```")

    lines.extend(["\n---", "**Strongly Connected Components**"])
    lines.append("\n```")
    for i, component in enumerate(strongly_connected_components):
        lines.append(f"Component {i + 1}:")
        for username in component:
            lines.append(f"    {username}")
    lines.append("```")

    lines.extend(["\n---", "**Reciprocity**"])
    lines.append("\n```")
    lines.append(f"{reciprocity}")
    lines.append("```")

    lines.append("\n---")

    # Print to file
    with open(analysis_report_filename, "w") as f:
        f.writelines(line + "\n" for line in lines)

#################################################################################################################################################
#################################################################################################################################################

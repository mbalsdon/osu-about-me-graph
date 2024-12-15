import classes

import networkx
import matplotlib.pyplot
import numpy

#################################################################################################################################################
#################################################################################################################################################

def generate_graph(mentions_graph: classes.UndirectedGraph, current_to_mentions: dict, image_filename: str) -> None:
    print("-- Generating graph...")

    G = networkx.Graph()
    G.add_edges_from((user, mentioned_user)
                     for user, mentions in mentions_graph.adj.items()
                     for mentioned_user in mentions)

    mentions_values = current_to_mentions.values()
    min_mentions = min(mentions_values)
    max_mentions = max(mentions_values)
    mention_range = max_mentions - min_mentions
    scale_factor = 1900 / mention_range if mention_range > 0 else 1900

    node_sizes = [100 + (current_to_mentions.get(node, min_mentions) - min_mentions) * scale_factor
                  for node in G.nodes()]

    figure = matplotlib.pyplot.figure(figsize=(50, 50), facecolor='black')
    ax = figure.add_subplot(111)
    ax.set_facecolor('black')

    pos = networkx.spring_layout(
        G,
        k=0.5,
        iterations=50,
        seed=727
    )

    batch_size = 1000
    edge_list = list(G.edges())

    for i in range(0, len(edge_list), batch_size):
        batch = edge_list[i:i + batch_size]
        for edge in batch:
            start = pos[edge[0]]
            end = pos[edge[1]]

            # Curved edges (TODO: flags)
            t = numpy.linspace(0, 1, 20)
            rad = 0.2
            rotation = numpy.arctan2(end[1] - start[1], end[0] - start[0])

            x = t * (end[0] - start[0]) + start[0]
            y = t * (end[1] - start[1]) + start[1]

            y += rad * numpy.sin(t * numpy.pi) * numpy.cos(rotation)
            x -= rad * numpy.sin(t * numpy.pi) * numpy.sin(rotation)

            # # Straight edges (TODO: flags)
            # x = numpy.array([start[0], end[0]])
            # y = numpy.array([start[1], end[1]])

            ax.plot(x, y, 'gray', alpha=0.5, linewidth=1.0)

        # Clear the plot cache periodically
        if i % (batch_size * 5) == 0:
            figure.canvas.flush_events()

    node_colors = numpy.random.rand(len(G.nodes()), 3)

    networkx.draw_networkx_nodes(
        G,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=1.0,
        edgecolors='black',
        linewidths=1.0,
        ax=ax
    )

    networkx.draw_networkx_labels(
        G,
        pos,
        font_size=6,
        font_weight='bold',
        font_color='white',
        ax=ax
    )

    ax.axis('off')
    figure.tight_layout()

    matplotlib.pyplot.savefig(image_filename, dpi=100, bbox_inches='tight', facecolor='black', edgecolor='none')
    matplotlib.pyplot.close()

#################################################################################################################################################
#################################################################################################################################################

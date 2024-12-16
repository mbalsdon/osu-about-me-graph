import classes

import networkx
import matplotlib.pyplot
import matplotlib.patches
import numpy

#################################################################################################################################################
#################################################################################################################################################

def get_rank_range(rank: int, num_users: int) -> int:
    """
    Get the range index (0-9) for a given rank.
    """
    num_ranges = 10
    range_size = (num_users + num_ranges - 1) // num_ranges
    return min((rank - 1) // range_size, num_ranges - 1)


def rank_to_color(rank: int, num_users: int) -> tuple[int, int, int]:
    """
    Map rank to RGB color according to gradient scheme.
    Colors are distributed evenly across the full gradient based on total number of users.
    Ranks within ranges of 100 will share the same color.
    """
    rank = max(1, min(num_users, rank))
    ranks_per_color = 100
    num_color_groups = (num_users + ranks_per_color - 1) // ranks_per_color
    color_step = max(1, 100 // num_color_groups)
    color_group = (rank - 1) // ranks_per_color
    color_index = (color_group * color_step) % 100

    # Muted Red to Muted Orange-Yellow (180,60,60) -> (180,150,60)
    if color_index < 25:
        return (180, 60 + color_index * 3.6, 60)
    # Muted Orange-Yellow to Muted Green (180,150,60) -> (60,180,60)
    elif color_index < 50:
        return (180 - (color_index - 25) * 4.8, 150 + (color_index - 25) * 1.2, 60)
    # Muted Green to Muted Teal (60,180,60) -> (60,180,180)
    elif color_index < 75:
        return (60, 180, 60 + (color_index - 50) * 4.8)
    # Muted Teal to Muted Blue (60,180,180) -> (60,60,180)
    else:
        return (60, 180 - (color_index - 75) * 4.8, 180)


def generate_graph(
        mentions_graph: classes.UndirectedGraph,
        current_to_mentions: dict,
        current_to_rank: dict,
        curve_edges: bool,
        image_filename: str
    ) -> None:
    """
    Generates graph.
    """
    print("-- Generating graph... This may take a while!")

    print("Building NetworkX graph from mentions data...")
    G = networkx.Graph()
    G.add_edges_from((user, mentioned_user)
                     for user, mentions in mentions_graph.adj.items()
                     for mentioned_user in mentions)

    num_users = len(current_to_rank)
    virtual_edges = []
    nodes_by_range = {}

    # Calculate normalized sizes for centrality weighting
    mentions_values = list(current_to_mentions.values())
    min_mentions = min(mentions_values)
    max_mentions = max(mentions_values)
    mention_range = max_mentions - min_mentions

    def get_normalized_size(mentions):
        return (mentions - min_mentions) / mention_range if mention_range > 0 else 1.0

    print("Adding virtual edges for rank-based clustering and size-based centrality...")
    # First, group nodes by rank range
    for node in G.nodes():
        rank = current_to_rank.get(node, num_users)
        rank_range = get_rank_range(rank, num_users)
        if rank_range not in nodes_by_range:
            nodes_by_range[rank_range] = []
        nodes_by_range[rank_range].append(node)

    # Add rank-based virtual edges
    for rank_range, nodes in nodes_by_range.items():
        for i, node in enumerate(nodes):
            for j in range(i + 1, min(i + 6, len(nodes))):
                virtual_edges.append((node, nodes[j], 250.0))  # Rank-based clustering weight

    # Add size-based virtual edges to center
    center_node = "CENTER"
    G.add_node(center_node)
    for node in G.nodes():
        if node != center_node:
            node_size = get_normalized_size(current_to_mentions.get(node, min_mentions))
            # Larger nodes get stronger attraction to center
            centrality_weight = 500.0 * (1.0 - node_size)  # Inverse relationship
            virtual_edges.append((node, center_node, centrality_weight))

    G.add_weighted_edges_from(virtual_edges)

    print(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges")

    print("Calculating node sizes based on mention counts...")
    scale_factor = 50000 / mention_range if mention_range > 0 else 50000

    print("Setting up matplotlib figure...")
    figure = matplotlib.pyplot.figure(figsize=(100, 100), facecolor="black")
    ax = figure.add_subplot(111)
    ax.set_facecolor("black")

    print("Calculating node positions using spring layout...")
    pos = networkx.spring_layout(
        G,
        k=2.5,  # Increase means more node spacing
        iterations=150,  # More iterations means better convergence
        weight="weight",
        seed=727
    )

    # Remove center node before drawing
    G.remove_node(center_node)
    del pos[center_node]

    print("Drawing edges...")
    batch_size = 1000
    edge_list = [e for e in G.edges() if G[e[0]][e[1]].get("weight", 1.0) == 1.0]
    total_batches = (len(edge_list) + batch_size - 1) // batch_size

    for i in range(0, len(edge_list), batch_size):
        batch = edge_list[i:i + batch_size]
        current_batch = i // batch_size + 1
        print(f"Processing edge batch {current_batch}/{total_batches} ({len(batch)} edges)")
        for edge in batch:
            start = pos[edge[0]]
            end = pos[edge[1]]

            rank1 = current_to_rank.get(edge[0], num_users)
            rank2 = current_to_rank.get(edge[1], num_users)
            edge_color = [x/250 for x in rank_to_color(min(rank1, rank2), num_users)]

            if curve_edges:
                t = numpy.linspace(0, 1, 20)
                rad = 0.2
                rotation = numpy.arctan2(end[1] - start[1], end[0] - start[0])

                x = t * (end[0] - start[0]) + start[0]
                y = t * (end[1] - start[1]) + start[1]

                y += rad * numpy.sin(t * numpy.pi) * numpy.cos(rotation)
                x -= rad * numpy.sin(t * numpy.pi) * numpy.sin(rotation)
            else:
                x = numpy.array([start[0], end[0]])
                y = numpy.array([start[1], end[1]])

            ax.plot(x, y, color=edge_color, alpha=0.5, linewidth=1.0)

        if i % (batch_size * 5) == 0:
            figure.canvas.flush_events()
            print("Cleared plot cache")

    print("Generating node colors based on ranks...")
    node_colors = []
    node_sizes = []
    node_labels = {}
    nodes = list(G.nodes())  # Get nodes in consistent order

    # Calculate base sizes for scaling
    max_label_size = 36
    min_label_size = 6
    base_node_size = 1000
    max_node_size = base_node_size + (max_mentions - min_mentions) * scale_factor

    for node in nodes:
        rank = current_to_rank.get(node, num_users)
        rgb_color = rank_to_color(rank, num_users)
        node_colors.append([x/250 for x in rgb_color])

        # Calculate node size
        node_size = base_node_size + (current_to_mentions.get(node, min_mentions) - min_mentions) * scale_factor
        node_sizes.append(node_size)

        # Calculate label size proportional to node size
        size_ratio = (node_size - base_node_size) / (max_node_size - base_node_size) if max_node_size > base_node_size else 0
        label_size = min_label_size + size_ratio * (max_label_size - min_label_size)
        node_labels[node] = label_size

    print("Drawing nodes...")
    networkx.draw_networkx_nodes(
        G,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=1.0,
        edgecolors="black",
        linewidths=1.0,
        ax=ax
    )

    print("Adding node labels...")
    # Group nodes by font size for batch drawing
    labels_by_size = {}
    for node, size in node_labels.items():
        size = max(min_label_size, round(size))  # Round to nearest integer and ensure minimum size
        if size not in labels_by_size:
            labels_by_size[size] = {}
        labels_by_size[size][node] = node

    # Draw labels in batches by size
    for font_size, node_dict in labels_by_size.items():
        networkx.draw_networkx_labels(
            G,
            pos,
            {node: label for node, label in node_dict.items()},
            font_size=font_size,
            font_weight="bold",
            font_color="white",
            ax=ax
        )

    print("Adding color legend...")
    ranks_per_color = 100  # Match the granularity used in rank_to_color
    legend_elements = []

    # Calculate how many users are in each color group
    users_per_group = (num_users + ranks_per_color - 1) // ranks_per_color

    for i in range(ranks_per_color):
        start_rank = i * users_per_group + 1
        end_rank = min((i + 1) * users_per_group, num_users)

        # Only add to legend if this group contains users
        if start_rank <= num_users:
            rgb_color = rank_to_color(start_rank, num_users)
            legend_elements.append(
                matplotlib.patches.Patch(
                    facecolor=[x/250 for x in rgb_color],
                    edgecolor='white',
                    label=f'Rank {start_rank}-{end_rank}',
                    linewidth=0.5
                )
            )

    # Calculate optimal number of columns based on number of legend elements
    num_elements = len(legend_elements)
    num_columns = max(1, min(5, (num_elements + 19) // 20))  # Up to 5 columns, minimum 20 items per column

    legend = ax.legend(
        handles=legend_elements,
        loc='upper right',
        bbox_to_anchor=(1.15, 1.15),
        frameon=True,
        facecolor='black',
        edgecolor='white',
        fontsize=24,  # Reduced font size to accommodate more entries
        title_fontsize=30,
        markerscale=4,
        borderpad=2.0,
        labelspacing=1.0,
        handletextpad=2.0,
        handlelength=3.0,
        ncol=num_columns,  # Use multiple columns
        columnspacing=4.0
    )

    legend.get_title().set_color('white')
    for text in legend.get_texts():
        text.set_color('white')
    legend.get_frame().set_linewidth(3.0)

    ax.axis("off")
    figure.tight_layout()

    print(f"Saving graph to {image_filename}...")
    matplotlib.pyplot.savefig(image_filename, dpi=100, bbox_inches="tight", facecolor="black", edgecolor="none", bbox_extra_artists=[legend])
    matplotlib.pyplot.close()

#################################################################################################################################################
#################################################################################################################################################

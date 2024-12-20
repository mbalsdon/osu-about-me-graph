import classes

import matplotlib.axes
import matplotlib.figure
import matplotlib.patches
import matplotlib.pyplot
import networkx
import PIL.Image
import PIL.ImageFile

import logging
import math
import os
import typing
import warnings

logger = logging.getLogger("osu-about-me-graph")

# Name that hopefully doesn't belong to another node
CENTER_NODE = "\!\@\#\$\%\^\&\*\(\) CENTER \!\@\#\$\%\^\&\*\(\)"

TEMP_LEGEND_FILENAME = "legend_temp.png"

#################################################################################################################################################
#################################################################################################################################################


def normalized_node_size(mentions_graph: classes.DirectedGraph, node: str) -> float:
    """
    Return normalized node size (from 0 to 1).
    """
    return mentions_graph.in_degrees[node] / max(mentions_graph.in_degrees.values())


def create_base_graph(mentions_graph: classes.DirectedGraph) -> networkx.MultiDiGraph:
    """
    Add "real" edges and nodes, i.e. those which will be drawn.
    """
    print("Creating base graph...")

    G = networkx.MultiDiGraph()

    edges = []
    for user, users_referred_to in mentions_graph.adj.items():
        G.add_node(user)
        for user_referred_to in users_referred_to:
            n = normalized_node_size(mentions_graph, user_referred_to)
            edges.append((user, user_referred_to, {"weight": 10.0 * (1.0 - (n**4)), "is_real": True}))

    G.add_edges_from(edges)
    return G


def add_rank_range_edges(G: networkx.MultiDiGraph, username_to_rank: dict, rank_range_size: int) -> None:
    """
    Add weighted invisible edges between nodes in the same rank range.
    """
    print(f"Grouping up nodes by rank range...")

    nodes_by_range = {}
    for node in G.nodes():
        rank = username_to_rank[node]
        rank_range = (rank - 1) // rank_range_size
        if rank_range not in nodes_by_range:
            nodes_by_range[rank_range] = []
        nodes_by_range[rank_range].append(node)

    virtual_edges = []
    for nodes in nodes_by_range.values():
        for i, node1 in enumerate(nodes):
            # This is the juicer - We only connect node i to (up to) the next x nodes ahead of it in the list.
            # This creates a sort of "swirly" effect on the graph where nodes in the same rank range are connected
            # to eachother in chains rather than a big clump.
            rank_connection_strength = len(nodes) // 10
            for j in range(i + 1, min(i + rank_connection_strength + 1, len(nodes))):
                node2 = nodes[j]
                virtual_edges.append((node1, node2, {"weight": 100.0, "is_real": False}))

    G.add_edges_from(virtual_edges)


def add_center_edges(G: networkx.MultiDiGraph, mentions_graph: classes.DirectedGraph) -> None:
    """
    Create a "center" node and create weighted invisible edges between it and every other node.
    """
    print("Grouping up nodes around the center...")

    G.add_node(CENTER_NODE)

    virtual_edges = []
    for node in G.nodes():
        if node != CENTER_NODE:
            n = normalized_node_size(mentions_graph, node)
            centrality_weight = 500.0 * (1.0 - (n**4))
            virtual_edges.append((node, CENTER_NODE, {"weight": centrality_weight, "is_real": False}))

    G.add_edges_from(virtual_edges)


def rank_to_color(rank: int, num_users: int, rank_range_size: int) -> tuple[int, int, int]:
    """
    Map rank to RGB color according to gradient scheme.
    Colors are distributed evenly across the full gradient based on total number of users.
    Ranks within specified range_size will share the same color.
    """
    num_color_groups = (num_users + rank_range_size - 1) // rank_range_size
    color_step = max(1, 100 // num_color_groups)
    color_group = (rank - 1) // rank_range_size
    color_index = (color_group * color_step) % 100

    # (180,60,60) -> (180,150,60)
    if color_index < 25:
        return (180, 60 + color_index * 3.6, 60)
    # (180,150,60) -> (60,180,60)
    elif color_index < 50:
        return (180 - (color_index - 25) * 4.8, 150 + (color_index - 25) * 1.2, 60)
    # (60,180,60) -> (60,180,180)
    elif color_index < 75:
        return (60, 180, 60 + (color_index - 50) * 4.8)
    # (60,180,180) -> (60,60,180)
    else:
        return (60, 180 - (color_index - 75) * 4.8, 180)


def calculate_node_properties(
        G: networkx.MultiDiGraph,
        username_to_mentions: dict,
        username_to_rank: dict,
        num_users: int,
        rank_range_size: int
    ) -> tuple[list[tuple[float, float, float]], list[float], dict]:
    """
    Calculate colors, sizes, and label properties for nodes.
    """
    print("Calculating node properties...")

    # Initialize containers
    node_colors = []
    node_sizes = []
    node_labels = {}
    nodes = list(G.nodes())

    # Calculate diameter scale factor to map from [0, max_mentions] to [min_diameter, max_diameter]
    min_diameter = 25
    max_diameter = 250
    max_mentions = max(username_to_mentions.values())
    diameter_scale_factor = (max_diameter - min_diameter) / max_mentions if max_mentions > 0 else 0

    for node in nodes:
        # Make center node invisible
        if node == CENTER_NODE:
            node_colors.append((0.0, 0.0, 0.0))
            node_sizes.append(0.0)
            node_labels[node] = 0.0

        else:
            # Calculate color based on rank
            rank = username_to_rank[node]
            rgb_color = rank_to_color(rank, num_users, rank_range_size)
            node_colors.append([x/255 for x in rgb_color])

            # Calculate diameter based on mentions (linear scaling)
            mention_count = username_to_mentions[node]
            diameter = min_diameter + (mention_count * diameter_scale_factor)

            # Convert diameter to area for NetworkX
            node_size = math.pi * ((diameter / 2) ** 2)
            node_sizes.append(node_size)

            # Calculate label size
            diameter_ratio = (diameter - min_diameter) / (max_diameter - min_diameter)
            label_size = 6 + (diameter_ratio * 30)
            node_labels[node] = label_size

    return node_colors, node_sizes, node_labels


def draw_real_edges(
        G: networkx.MultiDiGraph,
        pos: typing.Mapping,
        username_to_rank: dict,
        node_sizes: list[float],
        num_users: int,
        rank_range_size: int,
        ax: matplotlib.axes.Axes
    ) -> None:
    """
    Draw non-virtual edges.
    """
    print("Drawing edges...")
    real_edges = []
    real_edge_colors = []
    for edge_data in G.edges.data():
        if edge_data[2]["is_real"] and edge_data[0] != CENTER_NODE and edge_data[1] != CENTER_NODE:
            real_edges.append((edge_data[0], edge_data[1]))

            # If A mentions B, give the edge B's color
            mentioned_user_rank = username_to_rank[edge_data[1]]
            edge_color = rank_to_color(mentioned_user_rank, num_users, rank_range_size)
            real_edge_colors.append(tuple(x / 250 for x in edge_color))

    networkx.draw_networkx_edges(
        G,
        pos,
        edgelist=real_edges,
        edge_color=real_edge_colors,
        alpha=0.35,
        width=2.0,
        node_size=node_sizes,
        connectionstyle="arc3, rad=0.15",
        arrowsize=1,
        ax=ax
    )


def draw_real_nodes(
        G: networkx.MultiDiGraph,
        pos: typing.Mapping,
        node_sizes: list[float],
        node_colors: list[tuple[float, float, float]],
        ax: matplotlib.axes.Axes
    ) -> None:
    """
    Draw non-virtual nodes.
    """
    print("Drawing nodes...")
    networkx.draw_networkx_nodes(
        G,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.75,
        edgecolors="black",
        linewidths=1.0,
        ax=ax
    )


def draw_node_labels(
        G: networkx.MultiDiGraph,
        pos: typing.Mapping,
        node_labels: dict,
        ax: matplotlib.axes.Axes
    ) -> None:
    """
    Draw node labels.
    """
    print("Drawing labels...")
    labels_by_size = {}
    for node, size in node_labels.items():
        if size not in labels_by_size:
            labels_by_size[size] = {}
        labels_by_size[size][node] = node

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


def create_legend(figsize: tuple[int, int], num_users: int, rank_range_size: int) -> matplotlib.figure.Figure:
    """
    Create legend figure.
    Each entry is a color patch and the rank range associated with that color.
    """
    print(f"Creating legend...")

    # Build legend entries
    legend_elements = []
    num_groups = (num_users + rank_range_size - 1) // rank_range_size
    for i in range(num_groups):
        start_rank = i * rank_range_size + 1
        end_rank = min((i + 1) * rank_range_size, num_users)
        color = rank_to_color(start_rank, num_users, rank_range_size)

        legend_elements.append(
            matplotlib.patches.Patch(
                facecolor=[x/255 for x in color],
                edgecolor="white",
                label=f"Rank {start_rank} - {end_rank}",
                linewidth=0.5
            )
        )

    # Create legend
    legend_figure = matplotlib.pyplot.figure(figsize=figsize, facecolor="none")
    legend = legend_figure.legend(
        handles=legend_elements,
        loc="upper right",
        bbox_to_anchor=(1, 1),
        frameon=True,
        facecolor="black",
        edgecolor="white",
        fontsize=45,
        markerscale=9,
        ncol=max(1, (num_groups + 10 - 1) // 10) # ~10 rows per column
    )
    for text in legend.get_texts():
        text.set_color("white")
    legend.get_frame().set_linewidth(3.0)

    return legend_figure


def paste_onto(background_filename: str, foreground_filename: str) -> PIL.ImageFile.ImageFile:
    """
    Paste foreground image onto background image.
    """
    print(f"Pasting \"{foreground_filename}\" onto \"{background_filename}\"...")

    if logger.level != logging.DEBUG:
        warnings.filterwarnings("ignore", category=PIL.Image.DecompressionBombWarning)

    bg = PIL.Image.open(background_filename)
    fg = PIL.Image.open(foreground_filename)
    bg.paste(fg, (0, 0), fg)

    warnings.filterwarnings("default", category=PIL.Image.DecompressionBombWarning)

    return bg


#################################################################################################################################################
#################################################################################################################################################

def generate_graph(
        mentions_graph: classes.DirectedGraph,
        username_to_rank: dict,
        rank_range_size: int,
        image_filename: str
    ) -> None:
    """
    Generate and save graph image.
    """
    print("\n--- Generating graph...")

    if len(username_to_rank) != len(mentions_graph.adj):
        raise AssertionError(f"{len(username_to_rank)} != {len(mentions_graph.adj)}")
    num_users = len(username_to_rank)

    # Add nodes and edges
    G = create_base_graph(mentions_graph)
    add_rank_range_edges(G, username_to_rank, rank_range_size)
    add_center_edges(G, mentions_graph)

    # Calculate layout
    print("Calculating node positions...")
    pos = networkx.spring_layout(
        G,
        pos={CENTER_NODE: (0, 0)},
        fixed=[CENTER_NODE],
        k=2.5,
        iterations=250,
        weight="weight",
        seed=727
    )

    # Set up figure
    figure = matplotlib.pyplot.figure(figsize=(100, 100), facecolor="black")
    ax = figure.add_subplot(111)
    ax.set_facecolor("black")

    # Calculate values for drawing
    node_colors, node_sizes, node_labels = calculate_node_properties(
        G,
        mentions_graph.in_degrees,
        username_to_rank,
        num_users,
        rank_range_size
    )

    # Draw everything onto the figure
    draw_real_edges(G, pos, username_to_rank, node_sizes, num_users, rank_range_size, ax)
    draw_real_nodes(G, pos, node_sizes, node_colors, ax)
    draw_node_labels(G, pos, node_labels, ax)

    # Save graph
    ax.axis("off")
    print(f"Saving graph to {image_filename}...")
    matplotlib.pyplot.savefig(image_filename, dpi=100, facecolor="black", edgecolor="none")

    # Create and save legend (to temporary file)
    legend_figure = create_legend((100, 100), num_users, rank_range_size)
    legend_figure.savefig(TEMP_LEGEND_FILENAME, dpi=100, facecolor="none", edgecolor="none")

    # Combine graph/legend and save final result
    main_img = paste_onto(image_filename, TEMP_LEGEND_FILENAME)
    main_img.save(image_filename, format="PNG")

    # Clean up
    os.remove(TEMP_LEGEND_FILENAME)
    matplotlib.pyplot.close("all")

#################################################################################################################################################
#################################################################################################################################################

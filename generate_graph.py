import PIL.ImageFile
import classes

import numpy
import networkx
import matplotlib.pyplot
import matplotlib.figure
import matplotlib.patches
import matplotlib.axes
import PIL.Image

import typing
import os
import math

#################################################################################################################################################
#################################################################################################################################################

def create_base_graph(mentions_graph: classes.UndirectedGraph) -> networkx.Graph:
    """
    Create initial graph structure with basic edges.
    """
    print("Creating base graph...")
    G = networkx.Graph()
    G.add_edges_from(
        (user, mentioned_user)
        for user, mentions in mentions_graph.adj.items()
        for mentioned_user in mentions
    )

    return G


def add_virtual_edges(
        G: networkx.Graph,
        current_to_mentions: dict,
        current_to_rank: dict,
        rank_range_size: int
    ) -> tuple[networkx.Graph, str]:
    """
    Adds weighted virtual edges between nodes in the same rank range, so that
    nodes in the same rank range appear closer together.

    Also adds a "central node" with weighted virtual edges to every other node,
    so that nodes cluster around the center of the graph. Weights here are based
    on node size.
    * 
    """
    print("Adding virtual weighted edges...")
    counter = classes.ProgressCounter(0, len(G.nodes()) * 2)

    virtual_edges = []

    # Group nodes by rank range
    nodes_by_range = {}
    for node in G.nodes():
        rank = current_to_rank[node]
        rank_range = (rank - 1) // rank_range_size
        if rank_range not in nodes_by_range:
            nodes_by_range[rank_range] = []
        nodes_by_range[rank_range].append(node)

        counter.increment()
        counter.print_progress_bar()

    # Add rank range clustering edges
    for nodes in nodes_by_range.values():
        for i, node in enumerate(nodes):
            for j in range(i + 1, min(i + 6, len(nodes))):
                virtual_edges.append((node, nodes[j], 250.0))

    # Add center clustering edges
    center_node = "CENTER"
    G.add_node(center_node)
    for node in G.nodes():
        if node == center_node:
            continue

        # Larger nodes get weaker attraction to center (inverse relationship)
        normalized_node_size = current_to_mentions[node] / max(current_to_mentions.values())
        centrality_weight = 500.0 * (1.0 - normalized_node_size)
        virtual_edges.append((node, center_node, centrality_weight)) # (First node, second node, weight)

        counter.increment()
        counter.print_progress_bar()

    G.add_weighted_edges_from(virtual_edges)

    print("\n", end="")

    return G, center_node


def draw_curved_edge(start: numpy.ndarray, end: numpy.ndarray, edge_color: float, ax: matplotlib.axes.Axes):
    """
    Draw a curved edge between two points.
    """
    t = numpy.linspace(0, 1, 20) # Increase third value -> edges have smoother curvature
    rad = 0.2
    rotation = numpy.arctan2(end[1] - start[1], end[0] - start[0])

    # Calculate curved path
    x = t * (end[0] - start[0]) + start[0]
    y = t * (end[1] - start[1]) + start[1]

    # Apply curve transformation
    y += rad * numpy.sin(t * numpy.pi) * numpy.cos(rotation)
    x -= rad * numpy.sin(t * numpy.pi) * numpy.sin(rotation)

    ax.plot(x, y, color=edge_color, alpha=0.5, linewidth=1.0)


def draw_straight_edge(start: numpy.ndarray, end: numpy.ndarray, edge_color: list[float], ax: matplotlib.axes.Axes):
    """
    Draw a straight edge between two points.
    """
    x = numpy.array([start[0], end[0]])
    y = numpy.array([start[1], end[1]])

    ax.plot(x, y, color=edge_color, alpha=0.5, linewidth=1.0)


def draw_single_edge(
        edge: networkx.classes.reportviews.EdgeView,
        pos: typing.Mapping,
        current_to_rank: dict,
        num_users: int,
        rank_range_size: int,
        curve_edges: bool,
        ax: matplotlib.axes.Axes,
    ) -> None:
    """
    Draw a single edge.
    """
    start = pos[edge[0]]
    end = pos[edge[1]]

    # Color edge with color of whichever node/user is higher ranked (in the connection)
    rank1 = current_to_rank[edge[0]]
    rank2 = current_to_rank[edge[1]]
    edge_color = [x/250 for x in rank_to_color(min(rank1, rank2), num_users, rank_range_size)]

    if curve_edges:
        draw_curved_edge(start, end, edge_color, ax)
    else:
        draw_straight_edge(start, end, edge_color, ax)


def draw_edges(
        G: networkx.Graph,
        pos: typing.Mapping,
        current_to_rank: dict,
        num_users: int,
        rank_range_size: int,
        curve_edges: bool,
        ax: matplotlib.axes.Axes
    ) -> None:
    """
    Draw edges onto graph.
    """
    print("Drawing edges...")

    # Only process real edges (weight=1.0), excluding virtual edges
    edge_list = []
    for edge in G.edges():
        edge_attrs = G[edge[0]][edge[1]]
        if "weight" not in edge_attrs:
            edge_list.append(edge)

    # Batch edges so that we don't max out on memory
    counter = classes.ProgressCounter(0, len(edge_list))
    batch_size = 1000
    for i in range(0, len(edge_list), batch_size):
        batch = edge_list[i:i + batch_size]
        for edge in batch:
            draw_single_edge(edge, pos, current_to_rank, num_users, rank_range_size, curve_edges, ax)
            counter.increment()
            counter.print_progress_bar()

        # Periodically clear plot cache to manage memory
        if i % (batch_size * 5) == 0:
            matplotlib.pyplot.gcf().canvas.flush_events()

    print("\n", end="")


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
        G: networkx.Graph,
        current_to_mentions: dict,
        current_to_rank: dict,
        num_users: int,
        rank_range_size: int
    ) -> tuple[list[float], list[float], dict]:
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
    min_diameter = 30
    max_diameter = 300
    max_mentions = max(current_to_mentions.values())
    diameter_scale_factor = (max_diameter - min_diameter) / max_mentions if max_mentions > 0 else 0

    counter = classes.ProgressCounter(0, len(nodes))

    for node in nodes:
        # Calculate color based on rank
        rank = current_to_rank[node]
        rgb_color = rank_to_color(rank, num_users, rank_range_size)
        node_colors.append([x/250 for x in rgb_color])

        # Calculate diameter based on mentions (linear scaling)
        mention_count = current_to_mentions[node]
        diameter = min_diameter + (mention_count * diameter_scale_factor)

        # Convert diameter to area for NetworkX
        node_size = math.pi * ((diameter / 2) ** 2)
        node_sizes.append(node_size)

        # Calculate label size
        diameter_ratio = (diameter - min_diameter) / (max_diameter - min_diameter)
        label_size = 6 + (diameter_ratio * 30)
        node_labels[node] = label_size

        counter.increment()
        counter.print_progress_bar()

    print("\n", end="")
    return node_colors, node_sizes, node_labels


def draw_nodes_and_labels(
        G: networkx.Graph,
        pos: typing.Mapping,
        node_colors: list[float],
        node_sizes: list[float],
        node_labels: dict,
        ax: matplotlib.axes.Axes
    ):
    """
    Draw nodes and their labels with appropriate sizes and colors.
    """
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
    # Group labels by font size for efficient drawing
    labels_by_size = {}
    for node, size in node_labels.items():
        size = max(6, round(size))  # Ensure minimum size of 6pt
        if size not in labels_by_size:
            labels_by_size[size] = {}
        labels_by_size[size][node] = node

    # Draw labels in batches by font size
    for font_size, node_dict in labels_by_size.items():
        networkx.draw_networkx_labels(
            G, pos,
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
    print(f"Creating legend for {num_users} users with size {figsize}...")

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
    bg = PIL.Image.open(background_filename)
    fg = PIL.Image.open(foreground_filename)

    bg.paste(fg, (0, 0), fg)
    return bg


#################################################################################################################################################
#################################################################################################################################################

def generate_graph(
        mentions_graph: classes.UndirectedGraph,
        current_to_mentions: dict,
        current_to_rank: dict,
        curve_edges: bool,
        rank_range_size: int,
        image_filename: str
    ) -> None:
    """
    Generate and save graph image.
    """
    print("--- Generating graph...")

    # Create and enhance graph structure
    G = create_base_graph(mentions_graph)
    G, center_node = add_virtual_edges(G, current_to_mentions, current_to_rank, rank_range_size)

    # Calculate layout
    print("Calculating node positions...")
    pos = networkx.spring_layout(
        G,
        k=2.5, # Increase means more node spacing
        iterations=150, # Increase means better convergence
        weight="weight",
        seed=727
    )

    # Remove center node now that the graph is generated
    G.remove_node(center_node)
    del pos[center_node]

    # Set up visualization
    print("Setting up matplotlib figure...")
    figure = matplotlib.pyplot.figure(figsize=(100, 100), facecolor="black")
    ax = figure.add_subplot(111)
    ax.set_facecolor("black")

    # Draw graph elements
    num_users = len(current_to_rank)
    draw_edges(G, pos, current_to_rank, num_users, rank_range_size, curve_edges, ax)
    node_colors, node_sizes, node_labels = calculate_node_properties(
        G,
        current_to_mentions,
        current_to_rank,
        num_users,
        rank_range_size
    )
    draw_nodes_and_labels(G, pos, node_colors, node_sizes, node_labels, ax)

    # Finalize and save
    ax.axis("off")
    print(f"Saving graph to {image_filename}...")
    matplotlib.pyplot.savefig(
        image_filename,
        dpi=100,
        facecolor="black",
        edgecolor="none"
    )
    print("Graph generation complete!")

    # Create and save legend to temporary file same resolution as graph
    legend_figure = create_legend((100, 100), num_users, rank_range_size)
    legend_filename = "legend_temp.png"
    legend_figure.savefig(legend_filename, dpi=100, facecolor="none", edgecolor="none")

    # Combine images and save final result
    main_img = paste_onto(image_filename, legend_filename)
    main_img.save(image_filename, format="PNG")

    # Clean up
    os.remove(legend_filename)
    matplotlib.pyplot.close("all")

#################################################################################################################################################
#################################################################################################################################################

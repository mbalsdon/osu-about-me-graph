import ossapi

import argparse
import os

ARGS = None

#################################################################################################################################################
#################################################################################################################################################

def parse_arguments() -> None:
    parser = argparse.ArgumentParser(description="osu-about-me-graph Python CLI tool")

    # Add arguments
    parser.add_argument(
        "--big-nodes-closer",
        help="pull highly mentioned users closer to the center rather than pushing them away",
        action="store_true",
        required=False
    )

    parser.add_argument(
        "--no-graph",
        help="don't generate an image of the graph",
        action="store_true",
        required=False
    )

    parser.add_argument(
        "--no-legend",
        help="don't include a legend in the final image",
        action="store_true",
        required=False
    )

    parser.add_argument(
        "--save-json",
        help="save graph data to cytoscape-compatible json file",
        action="store_true",
        required=False
    )

    parser.add_argument(
        "--use-last-run",
        help="use osu!API player data fetched from a previous run",
        action="store_true",
        required=False
    )

    parser.add_argument(
        "--verbose",
        help="print verbose logs",
        action="store_true",
        required=False)



    parser.add_argument(
        "--arrow-size",
        help="size of arrows on edges in the graph [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--centrality-weight",
        help="gravity between all users and the center; higher means closer to the center [float]",
        type=float,
        required=False
    )

    parser.add_argument(
        "--dpi",
        help="dots/pixels per inch [int > 0]",
        type=int,
        required=False,
    )

    parser.add_argument(
        "--edge-curvature",
        help="how curved to make edges in the graph, in radians; 0 means straight [float >= 0]",
        type=float,
        required=False
    )

    parser.add_argument(
        "--edge-width",
        help="width of edges in the graph [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--env-path",
        help="path to environment variables file [filepath string]",
        type=str,
        required=False
    )

    parser.add_argument(
        "--fp-max-followers",
        help="maximum number of followers necessary to be included in false-positives report [int >= 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--fp-mentions-top-percentile",
        help="top percentile of mentions necessary to be included in false-positives report [float 0-100]",
        type=float,
        required=False
    )

    parser.add_argument(
        "--gamemode",
        help="osu! gamemode [osu, taiko, mania, catch]",
        type=str,
        required=False
    )

    parser.add_argument(
        "--image-width",
        help="width of the generated image, in inches [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--iterations",
        help="number of graph iterations; higher means better convergence [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--legend-font-size",
        help="font size of entries in the legend [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--max-label-size",
        help="maximum font size of node labels [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--min-label-size",
        help="minimum font size of node labels [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--max-node-diameter",
        help="maximum diameter of nodes in the graph [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--min-node-diameter",
        help="minimum diameter of nodes in the graph [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--num-users",
        help="number of users to pull [int 1-10000]",
        type=int,
        required=False,
    )

    parser.add_argument(
        "--rank-range-clustering-weight",
        help="gravity between users in the same rank; higher means closer together [float]",
        type=float,
        required=False
    )

    parser.add_argument(
        "--rank-range-connection-strength",
        help="how strongly to connect nodes in the same rank range; higher means stronger [float 0-1]",
        type=float,
        required=False
    )

    parser.add_argument(
        "--rank-range-size",
        help="size of each rank range; used for colouring and grouping [int > 0]",
        type=int,
        required=False
    )

    parser.add_argument(
        "--spring-force",
        help="spacing between nodes; higher means further apart [float]",
        type=float,
        required=False
    )

    parser.add_argument(
        "--start-rank",
        help="which rank to start pulling users at [int 1-10000]",
        type=int,
        required=False,
    )

    # Parse and store arguments
    global ARGS
    ARGS = parser.parse_args()

    # Set defaults
    if ARGS.arrow_size is None:
        ARGS.arrow_size = 10

    if ARGS.centrality_weight is None:
        ARGS.centrality_weight = 500.0

    if ARGS.dpi is None:
        ARGS.dpi = 100

    if ARGS.edge_curvature is None:
        ARGS.edge_curvature = 0.15

    if ARGS.edge_width is None:
        ARGS.edge_width = 2

    if ARGS.env_path is None:
        ARGS.env_path = os.path.join(os.getcwd(), ".env")

    if ARGS.fp_max_followers is None:
        ARGS.fp_max_followers = 1000

    if ARGS.fp_mentions_top_percentile is None:
        ARGS.fp_mentions_top_percentile = 5.0

    if ARGS.gamemode is None:
        ARGS.gamemode = "osu"

    if ARGS.image_width is None:
        ARGS.image_width = 100

    if ARGS.iterations is None:
        ARGS.iterations = 150

    if ARGS.legend_font_size is None:
        ARGS.legend_font_size = 50

    if ARGS.min_label_size is None:
        ARGS.min_label_size = 6

    if ARGS.max_label_size is None:
        ARGS.max_label_size = 30

    if ARGS.max_node_diameter is None:
        ARGS.max_node_diameter = 250

    if ARGS.min_node_diameter is None:
        ARGS.min_node_diameter = 25

    if ARGS.num_users is None:
        ARGS.num_users = 1000

    if ARGS.rank_range_clustering_weight is None:
        ARGS.rank_range_clustering_weight = 100.0

    if ARGS.rank_range_connection_strength is None:
        ARGS.rank_range_connection_strength = 0.1

    if ARGS.rank_range_size is None:
        ARGS.rank_range_size = 50

    if ARGS.spring_force is None:
        ARGS.spring_force = 2.5

    if ARGS.start_rank is None:
        ARGS.start_rank = 1

    # Parrot back to user
    print("\n--- Beginning execution with arguments:")
    for key, value in vars(ARGS).items():
        print(f"{key}: {value}")
    print("\n", end="")

    # Validate inputs
    do_exit = False
    error_messages = ""
    if ARGS.arrow_size <= 0:
        error_messages += "Arrow size must be greater than zero!\n"
        do_exit = True

    if ARGS.dpi <= 0:
        error_messages += "DPI must be greater than zero!\n"
        do_exit = True

    if ARGS.edge_curvature < 0:
        error_messages += "Edge curvature must be greater than or equal to zero!\n"
        do_exit = True

    if ARGS.edge_width <= 0:
        error_messages += "Edge width must be greater than zero!\n"
        do_exit = True

    if not os.path.exists(ARGS.env_path):
        error_messages += f"Could not find environment variable file at '{ARGS.env_path}'! You can specify its location with the --env-path flag.\n"
        do_exit = True

    if ARGS.fp_max_followers < 0:
        error_messages += "FP max followers must be greater than or equal to zero!\n"
        do_exit = True

    if ARGS.fp_mentions_top_percentile < 0 or ARGS.fp_mentions_top_percentile > 100:
        error_messages += "FP mentions top percentile must be within [0, 100]!\n"
        do_exit = True

    if ARGS.gamemode not in ["osu", "taiko", "mania", "catch"]:
        error_messages += "Gamemode must be one of osu, taiko, mania, or catch!\n"
        do_exit = True

    if ARGS.image_width <= 0:
        error_messages += "Image width must be greater than zero!\n"
        do_exit = True

    if ARGS.iterations <= 0:
        error_messages += "Iterations must be greater than zero!\n"
        do_exit = True

    if ARGS.legend_font_size <= 0:
        error_messages += "Legend font size must be greater than zero!\n"
        do_exit = True

    if ARGS.max_label_size <= 0:
        error_messages += "Maximum node label font size must be greater than zero!\n"
        do_exit = True

    if ARGS.max_label_size < ARGS.min_label_size:
        error_messages += "Maximum node label font size must be greater than or equal to minimum label font size!\n"
        do_exit = True

    if ARGS.min_label_size <= 0:
        error_messages += "Minimum node label font size must be greater than zero!\n"
        do_exit = True

    if ARGS.max_node_diameter <= 0:
        error_messages += "Maximum node diameter must be greater than zero!\n"
        do_exit = True

    if ARGS.max_node_diameter < ARGS.min_node_diameter:
        error_messages += "Maximum node diameter must be greater than or equal to minimum node diameter!\n"
        do_exit = True

    if ARGS.min_node_diameter <= 0:
        error_messages += "Minimum node diameter must be greater than zero!\n"
        do_exit = True

    if ARGS.num_users < 1 or ARGS.num_users > 10000:
        error_messages += "Number of users must be within [1, 10000]!\n"
        do_exit = True  

    if ARGS.start_rank < 1 or ARGS.start_rank > 10000:
        error_messages += "Start rank must be within [1, 10000]!\n"
        do_exit = True

    if ARGS.start_rank + ARGS.num_users - 1 > 10000:
        error_messages += f"Cannot pull users past rank 10000! Start rank = {ARGS.start_rank}, number of users = {ARGS.num_users}...\n"
        do_exit = True

    if ARGS.rank_range_size <= 0:
        error_messages += "Rank range size must be greater than zero!\n"
        do_exit = True

    if ARGS.rank_range_connection_strength < 0 or ARGS.rank_range_connection_strength > 1:
        error_messages += "Rank range connection strength must be within [0, 1]!\n"
        do_exit = True

    if do_exit:
        print("--- Please address the following errors before running again:")
        print(error_messages)
        print("Exiting...")
        exit(1)

    # Translate inputs
    if ARGS.gamemode == "taiko":
        ARGS.gamemode = ossapi.GameMode.TAIKO
    elif ARGS.gamemode == "mania":
        ARGS.gamemode = ossapi.GameMode.MANIA
    elif ARGS.gamemode == "catch":
        ARGS.gamemode = ossapi.GameMode.CATCH
    else:
        ARGS.gamemode = ossapi.GameMode.OSU

#################################################################################################################################################
#################################################################################################################################################

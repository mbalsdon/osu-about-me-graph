import args
from generate_graph import generate_graph
from parse_users import parse_users
from report_false_positives import report_false_positives
from scrape_users import scrape_users

import asyncio
import dotenv

import gc
import logging
import os
import time
import typing

logger = logging.getLogger("osu-about-me-graph")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

#################################################################################################################################################
#################################################################################################################################################

async def async_timer(func: typing.Callable[..., typing.Any], *args: typing.Any, **kwargs: typing.Any) -> tuple[typing.Any, float]:
    start = time.time()
    result = await func(*args, **kwargs)
    elapsed_min = (time.time() - start) / 60
    return result, elapsed_min


def sync_timer(func: typing.Callable[..., typing.Any], *args: typing.Any, **kwargs: typing.Any) -> tuple[typing.Any, float]:
    start = time.time()
    result = func(*args, **kwargs)
    elapsed_min = (time.time() - start) / 60
    return result, elapsed_min

#################################################################################################################################################
#################################################################################################################################################

async def main() -> None:
    args.parse_arguments()
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    dotenv.load_dotenv()

    save_filename = "users.pkl"
    report_filename = "false_positives.md"
    ignore_usernames_filename = "ignore_usernames.csv"
    image_filename = "user_network.png"

    big_nodes_closer = args.ARGS.big_nodes_closer
    no_graph = args.ARGS.no_graph
    no_legend = args.ARGS.no_legend
    use_last_run = args.ARGS.use_last_run
    verbose = args.ARGS.verbose

    arrow_size = args.ARGS.arrow_size
    centrality_weight_factor = args.ARGS.centrality_weight
    dpi = args.ARGS.dpi
    edge_curvature = args.ARGS.edge_curvature
    edge_width = args.ARGS.edge_width
    fp_max_followers = args.ARGS.fp_max_followers
    fp_mentions_top_percentile = args.ARGS.fp_mentions_top_percentile
    gamemode = args.ARGS.gamemode
    image_width = args.ARGS.image_width
    iterations = args.ARGS.iterations
    legend_font_size = args.ARGS.legend_font_size
    max_node_diameter = args.ARGS.max_node_diameter
    min_node_diameter = args.ARGS.min_node_diameter
    max_label_size = args.ARGS.max_label_size
    min_label_size = args.ARGS.min_label_size
    num_users = args.ARGS.num_users
    rank_range_clustering_weight = args.ARGS.rank_range_clustering_weight
    rank_range_connection_strength = args.ARGS.rank_range_connection_strength
    rank_range_size = args.ARGS.rank_range_size
    spring_force = args.ARGS.spring_force
    start_rank = args.ARGS.start_rank

    # Set log level
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Get API data
    users, scrape_min = await async_timer(
        scrape_users,
            start_rank,
            num_users,
            gamemode,
            use_last_run,
            save_filename
    )

    # Parse API data
    (mentions_graph, username_to_rank), parse_min = sync_timer(
        parse_users,
            users,
            ignore_usernames_filename
    )

    # Generate false-positives report
    _, report_min = sync_timer(
        report_false_positives,
            users,
            mentions_graph,
            fp_mentions_top_percentile,
            fp_max_followers,
            report_filename,
            ignore_usernames_filename
    )

    # Clean up before explode PC
    del users
    gc.collect()

    # Generate graph
    _, graphgen_min = sync_timer(
        generate_graph,
            mentions_graph,
            username_to_rank,
            spring_force,
            iterations,
            image_width,
            dpi,
            big_nodes_closer,
            centrality_weight_factor,
            min_node_diameter,
            max_node_diameter,
            min_label_size,
            max_label_size,
            edge_width,
            edge_curvature,
            arrow_size,
            rank_range_size,
            rank_range_connection_strength,
            rank_range_clustering_weight,
            legend_font_size,
            no_graph,
            no_legend,
            image_filename
    )

    # Print stuff
    print("\n--- Execution completed!\n")

    print(f"You can find the image at \"{image_filename}\"")
    print(f"Ignored usernames can be found at \"{ignore_usernames_filename}\"")
    print(f"Possible false-positives can be found at \"{report_filename}\"")
    print(f"Savefile located at \"{save_filename}\"\n")

    print(f"API scraping took {round(scrape_min, 4):.4f} minutes.")
    print(f"False-positive search took {round(report_min, 4):.4f} minutes.")
    print(f"User data parsing took {round(parse_min, 4):.4f} minutes.")
    print(f"Graph generation took {round(graphgen_min, 4):.4f} minutes.\n")


if __name__ == "__main__":
    asyncio.run(main())

#################################################################################################################################################
#################################################################################################################################################

# TODO

### readme
##### running:
####### cd /path/to/osu-about-me-graph
####### printf "OSU_API_CLIENT_ID=[your client ID here]\nOSU_API_CLIENT_SECRET=[your client secret here]" > .env
####### python3 -m venv venv
####### source venv/bin/activate
####### pip install ossapi networkx matplotlib asyncio aiohttp python-dotenv scipy numpy pillow
######### verify this
####### python3 src/main.py
##### rename conflicts
##### common-word-usernames (e.g. "Hello")

# FUTURE

### look into 2d interactive (plotly :cookiemonster:)
##### rmbr do for all gamemodes :-)
### look into 3d (also plotly :cookiemonster:)

### 2d interactive?

### executable?

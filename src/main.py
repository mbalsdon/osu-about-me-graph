from generate_graph import generate_graph
from parse_users import parse_users
from report_false_positives import report_false_positives
from scrape_users import scrape_users

import asyncio
import dotenv

import argparse
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
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    dotenv.load_dotenv()

    log_level = logging.DEBUG
    num_users = 1000
    use_last_run = False
    save_filename = "users.pkl"
    report_filename = "false_positives.md"
    ignore_usernames_filename = "ignore_usernames.csv"
    mentions_top_percentile = 5.0
    max_num_followers = 1000
    rank_range_size = 50
    image_filename = "user_network.png"

    # Set log level
    logger.setLevel(log_level)

    # Get API data
    users, scrape_min = await async_timer(
        scrape_users,
            num_users,
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
            mentions_top_percentile,
            max_num_followers,
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
            rank_range_size,
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

### flags
##### add:
####### log level (--verbose)
####### numplayers
####### starting rank
####### gamemode
####### dpi, figsize (width and length), spring-force (k; increase means more spacing), iterations (inncrease means better convergence), seed
####### use last run (maybe switch to specified savefilename input and output)
####### output image filename
####### num. vertices in edges
####### rank-based clustering weight (lower means closer together)
####### centrality weight (higher means closer together)
####### bigger nodes closer/farther from centre (bool)
####### legend (on/off)
####### commonword percentiles
######### add this to report
####### no graph (for reporting)
####### max/min node diameter
####### rank range size
####### rank_connection_strength (0 -> len(nodes); probably normalize to 0-1 for flag)
####### curvature rad (0.0 = straight)
####### arrow size
####### edge width
##### pick out good defaults; some gotta be calculated based on others

### look into 3d

### readme
##### running:
####### cd /path/to/osu-about-me-graph
####### printf "OSU_API_CLIENT_ID=[your client ID here]\nOSU_API_CLIENT_SECRET=[your client secret here]" > .env
####### python3 -m venv venv
####### source venv/bin/activate
####### pip install ossapi networkx matplotlib asyncio aiohttp python-dotenv scipy numpy pillow
####### python3 main.py
##### rename conflicts
##### common-word-usernames (e.g. "Hello")

# FUTURE

### 2d interactive?

### executable?

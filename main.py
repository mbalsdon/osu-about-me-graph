from scrape_users import scrape_users
from report_false_positives import report_false_positives
from parse_users import parse_users
from generate_graph import generate_graph

import dotenv
import asyncio

import time
import typing
import gc

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
    dotenv.load_dotenv()

    num_users = 1000
    use_last_run = True
    save_filename = "users.pkl"
    report_filename = "false_positives.txt"
    ignore_usernames_filename = "ignore_usernames.csv"
    mentions_top_percentile = 20
    max_num_followers = 300
    curve_edges = True
    image_filename = "user_network.png"

    # Get API data
    users, scrape_min = await async_timer(
        scrape_users,
            num_users,
            use_last_run,
            save_filename
    )

    # Parse API data
    (mentions_graph, username_to_mentions, username_to_rank), parse_min = sync_timer(
        parse_users,
            users,
            ignore_usernames_filename
    )

    # Generate false-positives report
    _, report_min = sync_timer(
        report_false_positives,
            users,
            username_to_mentions,
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
            username_to_mentions,
            username_to_rank,
            curve_edges,
            image_filename
    )

    # Print stuff
    print("--- Execution completed!\n")

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

### clean up graphgen
##### helper functions
##### logic cleanup
##### comments
### size scaling needs work
##### it scales w/ area but want diameter


### DirectedGraph
##### edge from A to B if A mentions B
##### improve report (who mentioned this + line)
##### graphgen options? undirected, directed with arrows, undirected only if both mention eachother

### flags
##### including:
####### numplayers
######### would change the graphgen math
####### gamemode
####### conflict resolution style
####### curved/straight edges
####### dpi, figsize (width and length), spring-force (k), iterations, seed
####### load dummy data
####### filename
####### edge num vertices
####### rank-based clustering weight
####### centrality weight
####### legend (on/off)
####### commonword percentiles
######### add this to report
###### no graph (for reporting)
##### can it be packaged into an executable or something

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

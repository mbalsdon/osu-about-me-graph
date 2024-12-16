from get_mentions import get_mentions
from generate_graph import generate_graph

import asyncio

import time

#################################################################################################################################################
#################################################################################################################################################

async def main() -> None:
    start = time.time()
    mentions_graph, current_to_mentions, current_to_rank = await get_mentions(1000, True) # TODO: False
    end = time.time()
    get_mentions_time_min = (end - start) / 60

    start = time.time()
    image_filename = "user_network.png"
    generate_graph(mentions_graph, current_to_mentions, current_to_rank, True, image_filename)
    end = time.time()
    generate_graph_time_min = (end - start) / 60

    print("Execution completed!\n")
    print(f"You can find the image at {image_filename}.")
    print(f"User data parsing took {get_mentions_time_min} minutes.")
    print(f"Graph generation took {generate_graph_time_min} minutes.")

if __name__ == "__main__":
    asyncio.run(main())

#################################################################################################################################################
#################################################################################################################################################

# TODO

### flags
##### including:
####### numplayers
######### would change the graphgen math
####### gamemode
####### conflict resolution style
####### curved/straight edges
####### dpi, figsize, spring-force (k), iterations, seed
####### load dummy data
####### filename
####### edge num vertices
####### rank-based clustering weight
####### centrality weight

### readme
##### running:
####### cd /path/to/osu-about-me-graph
####### printf "OSU_API_CLIENT_ID=[your client ID here]\nOSU_API_CLIENT_SECRET=[your client secret here]" > .env
####### python3 -m venv venv
####### source venv/bin/activate
####### pip install ossapi networkx matplotlib asyncio aiohttp python-dotenv scipy numpy
####### python3 main.py
##### rename conflicts
##### common-word-usernames (e.g. "Hello")

### commonwords
##### https://www.kaggle.com/datasets/rtatman/english-word-frequency ???
##### common osu words are pretty unique so ^^^ might not be helpful ("area", "wooting", "500", "horrible kids")
##### best way is probably to just compare follower_count/num_mentions, and report any discrepancies
##### read a manually written csv for usernames to ignore

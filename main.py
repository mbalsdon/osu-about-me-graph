from get_mentions import get_mentions
from generate_graph import generate_graph

import asyncio

import time

#################################################################################################################################################
#################################################################################################################################################

async def main() -> None:
    start = time.time()
    mentions_graph, current_to_mentions = await get_mentions(10000)
    end = time.time()
    get_mentions_time_min = (end - start) / 60

    start = time.time()
    image_filename = "user_network.png"
    generate_graph(mentions_graph, current_to_mentions, image_filename)
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

### save/loads
##### save+overwrite csv(?) data every time
##### load off by default, add as flag later

### visualization
##### edges go through nodes sometimes; can be misleading. some sort of color coding?
##### rank gradient 100 colors; 10,000/100; (250,0,0), (250,10,0), ..., (250,250,0), (240,250,0), ..., (0,250,0), (0,250,10), ..., (0,250,250), (0,240,250), ..., (0,0,250)
##### bigger node size range?
##### less distance between nodes?

### flags
##### numplayers
####### would change the graphgen math
##### gamemode
##### conflict resolution style
##### curved/straight edges
##### dpi, figsize, spring-force (k), iterations, seed
##### load dummy data
##### filename

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

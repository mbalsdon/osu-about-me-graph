from dotenv import load_dotenv
from ossapi import Ossapi, GameMode, RankingType, Cursor
import matplotlib.pyplot
import networkx
import numpy

import collections
import os
import time

#################################################################################################################################################
#################################################################################################################################################

# Adjacency list for an undirected graph
class UndirectedGraph:
    def __init__(self):
        self.adj = collections.defaultdict(set)

    def add_edge(self, u, v):
        self.adj[u].add(v)
        self.adj[v].add(u)

    def print_graph(self):
        if not self.adj:
            print("Graph is empty!")
            return

        print("Graph:")
        vertices = sorted(self.adj.keys())
        for vertex in vertices:
            neighbors = sorted(self.adj[vertex])
            print(f"    {vertex}: {neighbors}")

# Prefix tree node
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


# Prefix tree
class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    # Return set of names from trie that appear in document.
    def find_names_in_document(self, document: str) -> set[str]:
        document = document.lower()
        found_names = set()

        for i in range(len(document)):
            if i > 0 and document[i-1].isalnum():
                continue

            node = self.root
            j = i

            matched_name = None

            while j < len(document) and document[j] in node.children:
                node = node.children[document[j]]
                j += 1

                if node.is_end_of_word:
                    if j == len(document) or not document[j].isalnum():
                        matched_name = document[i:j]

            if matched_name:
                found_names.add(matched_name)

        return found_names

    # Return all words in the trie
    def get_all_words(self) -> list[str]:
        words = []
        def dfs(node: TrieNode, current_word: str) -> None:
            if node.is_end_of_word:
                words.append(current_word)
    
            for char, child in node.children.items():
                dfs(child, current_word + char)

        dfs(self.root, "")
        return sorted(words)

#################################################################################################################################################
#################################################################################################################################################

def main():
    scrape_start = time.time()

    # Load environment variables
    load_dotenv()
    client_id = os.getenv("OSU_API_CLIENT_ID")
    client_secret = os.getenv("OSU_API_CLIENT_SECRET")

    # osu!API v2 client
    osu = Ossapi(client_id, client_secret)

    # Mapping from past/current username (string) to current username (string)
    alias_to_current = {}

    # Mapping from current username (string) to "About me" page (string)
    current_to_aboutme = {}

    # Mapping from current username (string) to number of mentions by other users (number)
    current_to_mentions = {}

    # Undirected graph for users that mention each other
    mentions_graph = UndirectedGraph()

    # Prefix tree containing all aliases
    username_trie = Trie()

    # Get userIDs
    user_ids = []
    for i in range(1, 201):
        print(f"Getting user IDs for page {i} rankings...")
        rankings = osu.ranking(GameMode.OSU, RankingType.PERFORMANCE, cursor=Cursor(page=i))
        for user_statistics in rankings.ranking:
            user_ids.append(user_statistics.user.id)

    # Get user data
    for user_id in user_ids:
        print(f"Getting data for user with ID {user_id}...")

        # Skip users if they can't be found - might happen if they get restricted
        try:
            user = osu.user(user_id, mode=GameMode.OSU)
        except Exception as e:
            print(f'Unexpected error: {e} - skipping...')
            continue

        current_username = user.username.lower()
        about_me = user.page.raw

        # Populate alias -> username mapping. Note that someone's current username could be another person's past username. For example,
        # Cookiezi used to have the name "shigetora", but now someone else has that name. So, if someone references "shigetora" on their
        # profile, how do we know which one they're referring to? Here, we assume that the higher-ranked player is the one being referenced.
        # Since we fetch user data in order of rank, we just have to check that the current name hasn't already been added as a key. It
        # might be a more sophisticated approach in the future to resolve conflicts like this by comparing follower count instead.
        if current_username not in alias_to_current:
            alias_to_current[current_username] = current_username

        for pu in user.previous_usernames:
            previous_username = pu.lower()
            if previous_username not in alias_to_current:
                alias_to_current[previous_username] = current_username

        # Populate username -> mentions mapping
        current_to_mentions[current_username] = 0
        
        # Populate username -> "About me" mapping
        current_to_aboutme[current_username] = about_me

        # Populate prefix tree
        username_trie.insert(current_username)
        for previous_username in user.previous_usernames:
            username_trie.insert(previous_username)

    # Find referenced users in each "About me" page
    for current_username, about_me in current_to_aboutme.items():
        referenced_aliases = username_trie.find_names_in_document(about_me)
        for referenced_alias in referenced_aliases:

            # Find current username of the referenced user
            referenced_username = alias_to_current[referenced_alias.lower()]

            # Don't add self
            if current_username != referenced_username:

                # Increase number of mentions for referenced user
                current_to_mentions[referenced_username] += 1

                # Draw edge between about me page owner and who they referenced
                mentions_graph.add_edge(current_username, referenced_username)

    scrape_end = time.time()
    scrape_elapsed = scrape_end - scrape_start
    print(f'Finished scraping data! Time elapsed = {scrape_elapsed} seconds.')

    # Generate the graph
    graph_gen_start = time.time()
    print('Generating graph...')
    G = networkx.Graph()

    for user, mentions in mentions_graph.adj.items():
        G.add_node(user)
        for mentioned_user in mentions:
            G.add_edge(user, mentioned_user)

    mentions_values = list(current_to_mentions.values())
    min_mentions = min(mentions_values)
    max_mentions = max(mentions_values)
    mention_range = max_mentions - min_mentions

    node_sizes = { user: 100 + (count - min_mentions) * (1900 / mention_range) for user, count in current_to_mentions.items() }

    matplotlib.pyplot.figure(figsize=(30, 30), facecolor='black')
    matplotlib.pyplot.gca().set_facecolor('black')

    pos = networkx.spring_layout(
        G,
        k=0.1,
        iterations=25,
        seed=727
    )

    # TODO: curved edges profiling
    for edge in G.edges():
        start = pos[edge[0]]
        end = pos[edge[1]]

        rad = 0.2
        rotation = numpy.arctan2(end[1] - start[1], end[0] - start[0])

        t = numpy.linspace(0, 1, 100)
        x = t * (end[0] - start[0]) + start[0]
        y = t * (end[1] - start[1]) + start[1]

        y += rad * numpy.sin(t * numpy.pi) * numpy.cos(rotation)
        x -= rad * numpy.sin(t * numpy.pi) * numpy.sin(rotation)
        
        matplotlib.pyplot.plot(x, y, 'gray', alpha=0.5, linewidth=1.0)

    # TODO: straight edges profiling
    # for edge in G.edges():
    #     start, end = pos[edge[0]], pos[edge[1]]
    #     x = numpy.array([start[0], end[0]])
    #     y = numpy.array([start[1], end[1]])
    #     matplotlib.pyplot.plot(x, y, 'gray', alpha=0.3, linewidth=0.5)

    networkx.draw_networkx_nodes(
        G,
        pos,
        node_size=[node_sizes[node] for node in G.nodes()],
        node_color=numpy.random.rand(len(G.nodes()), 3),
        alpha=1.0,
        edgecolors='black',
        linewidths=1.0
    )

    networkx.draw_networkx_labels(
        G,
        pos,
        font_size=6,
        font_weight='bold',
        font_color='white'
    )

    matplotlib.pyplot.axis('off')
    matplotlib.pyplot.tight_layout()

    matplotlib.pyplot.savefig('user_network.png', dpi=100, bbox_inches='tight', facecolor='black', edgecolor='none')
    matplotlib.pyplot.close()

    graph_gen_end = time.time()
    graph_gen_elapsed = graph_gen_end - graph_gen_start
    print(f'Finished generating graph! Time elapsed = {graph_gen_elapsed} seconds.')


if __name__ == "__main__":
    main()


# TODO
### multithreaded
##### cant rely on ordering for conflict resolution; fetch and store all user data -> sort and populate on one thread?
##### scrape -> function (ret adjlist, mentioncounts), graphgen -> function (param adjlist, mentioncounts)

### memory
##### add memory profiling, try with/without edge curving
##### del'ing things?? when??
##### draw labels only for nodes with >X mentions?
##### increase system memory?
##### https://claude.ai/chat/0d9888e8-f687-4c1f-846b-6c9272b8776c

### visualization
##### edges go through nodes sometimes; can be misleading. some sort of color coding?
##### rank gradient 100 colors; 10,000/100; (250,0,0), (250,10,0), ..., (250,250,0), (240,250,0), ..., (0,250,0), (0,250,10), ..., (0,250,250), (0,240,250), ..., (0,0,250)
##### bigger node size range?
##### less distance between nodes?

### commonwords
##### https://www.kaggle.com/datasets/rtatman/english-word-frequency
##### do something with this ^ 🤷‍♂️
##### as angel pointed out, some words like "anime", "mal" are common w/ osu
##### get list of usernames found in top 10k freqlist?
##### confidence ratings based on nummentions, followercount, rank, freqlist pos?

### flags
##### numplayers
####### would change the graphgen math
##### gamemode
##### conflict resolution style
##### dpi, figsize, spring-force (k), iterations, seed

### readme
##### running:
####### cd /path/to/osu-about-me-graph
####### printf "OSU_API_CLIENT_ID=[your client ID here]\nOSU_API_CLIENT_SECRET=[your client secret here]" > .env
####### python3 -m venv venv
####### source venv/bin/activate
####### pip install ossapi networkx matplotlib asyncio aiohttp python-dotenv scipy
####### python3 main.py
##### rename conflicts
##### common-word-usernames (e.g. "Hello")

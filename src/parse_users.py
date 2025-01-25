import classes

import json
import os

#################################################################################################################################################
#################################################################################################################################################

def get_ignored_usernames(ignore_usernames_filename: str) -> list[str]:
    if not os.path.exists(ignore_usernames_filename):
        print(f"Could not find \"{ignore_usernames_filename}\" - no usernames will be ignored.")
        return

    with open(ignore_usernames_filename, "r") as f:
        ignored_usernames = [line.strip().lower() for line in f]
        return ignored_usernames


def save_to_json(mentions_graph: classes.DirectedGraph, current_to_rank: dict, current_to_about_me: dict, json_out_filename: str) -> None:
    nodes = []
    for username, rank in current_to_rank.items():
        nodes.append({
            "data": {
                "id": username,
                "label": username,
                "rank": rank,
                "about_me": current_to_about_me[username]
            }
        })

    edges = []
    for source_node, target_nodes in mentions_graph.adj.items():
        for target_node in target_nodes:
            edges.append({
                "data": {
                    "id": f"{source_node}*{target_node}",
                    "source": source_node,
                    "target": target_node,
                }
            })

    data = {
        "nodes": nodes,
        "edges": edges
    }

    with open(json_out_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, sort_keys=True)

#################################################################################################################################################
#################################################################################################################################################

def parse_users(
        users: list[dict],
        ignore_usernames_filename: str,
        save_json: bool,
        json_filename: str
    ) -> tuple[classes.DirectedGraph, dict]:
    """
    Parse user about me pages. Returns a tuple containing the following:
        * Undirected graph, where an edge exists between player A and B iff player A mentions player B.
        * Map from (current) username to number of mentions by other players.
        * Map from (current) username to global rank.
    Usernames found in specified csv file will not contribute to mention data for the associated user.
    """
    print(f"\n--- Parsing data for {len(users)} users...")
    alias_to_current = {}
    current_to_rank = {}
    current_to_about_me = {}
    mentions_graph = classes.DirectedGraph()
    username_trie = classes.Trie()

    # Get ignored usernames if they exist
    ignored_usernames = get_ignored_usernames(ignore_usernames_filename)
    ignored_username_hits = 0

    print("Building storage structures...")

    # Sort by follower count (descending), then rank (ascending) in the case of ties
    users = sorted(users, key=lambda user: (-user["follower_count"], user["global_rank"]), reverse=False)
    for user in users:
        # Populate username mapping with past and present usernames. Someone's current username could be
        # another's past username. To deal with these conflicts, pick user with higher follower count (or
        # rank during ties). We sorted the list as such above so we just have to check "not in".
        current_username = user["current_username"]
        if current_username not in alias_to_current:
            alias_to_current[current_username] = current_username

        previous_usernames = user["previous_usernames"]
        for previous_username in previous_usernames:
            if previous_username not in alias_to_current:
                alias_to_current[previous_username] = current_username

        current_to_rank[current_username] = user["global_rank"]
        current_to_about_me[current_username] = user["about_me"]

        if current_username in ignored_usernames:
            ignored_username_hits += 1
        else:
            username_trie.insert(current_username)

        for previous_username in previous_usernames:
            if previous_username in ignored_usernames:
                ignored_username_hits += 1
            else:
                username_trie.insert(previous_username)

    print(f"Found and ignored {ignored_username_hits} usernames!")

    print("Parsing 'About me' pages...")
    counter = classes.ProgressCounter(0, len(users))

    for user in users:
        current_username = user["current_username"]
        about_me = user["about_me"]

        mentions_graph.add_vertex(current_username)

        referenced_aliases = username_trie.find_names_in_document(about_me)
        for referenced_alias in referenced_aliases:
            referenced_username = alias_to_current[referenced_alias.lower()]

            if current_username != referenced_username:
                mentions_graph.add_edge(current_username, referenced_username)

        counter.increment()
        counter.print_progress_bar()

    print("\n", end="")

    if save_json:
        print(f"JSON flag was set; saving to {json_filename}...")
        save_to_json(mentions_graph, current_to_rank, current_to_about_me, json_filename)

    return mentions_graph, current_to_rank

#################################################################################################################################################
#################################################################################################################################################

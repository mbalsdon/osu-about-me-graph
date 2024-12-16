import classes

import os
import re

#################################################################################################################################################
#################################################################################################################################################

def get_ignored_usernames(ignore_usernames_filename: str) -> list[str]:
    if not os.path.exists(ignore_usernames_filename):
        print(f"Could not find \"{ignore_usernames_filename}\" - no usernames will be ignored.")
        return

    with open(ignore_usernames_filename, "r") as f:
        ignored_usernames = [line.strip().lower() for line in f]
        return ignored_usernames


def strip_bbcode(text: str):
    """
    Remove BBCode tag pairs while preserving the content between them.
    """
    # Pattern matches:
    # [tag]content[/tag]
    # [tag=value]content[/tag]
    # [tag=]content[/tag]
    pattern = r'\[([^]\s=]+)(?:=(?:[^\]]*)?)?\](.*?)\[/\1\]'

    # Keep processing until no more tag pairs are found
    while re.search(pattern, text, re.DOTALL | re.MULTILINE):
        text = re.sub(pattern, r'\2', text, flags=re.DOTALL | re.MULTILINE)

    return text

#################################################################################################################################################
#################################################################################################################################################

def parse_users(users: list[dict], ignore_usernames_filename: str) -> tuple[classes.UndirectedGraph, dict, dict]:
    """
    Parse user about me pages. Returns a tuple containing the following:
        * Undirected graph, where an edge exists between player A and B iff player A mentions player B.
        * Map from (current) username to number of mentions by other players.
        * Map from (current) username to global rank.
    Usernames found in specified csv file will not contribute to mention data for the associated user.
    """
    print(f"-- Parsing data for {len(users)} users...")
    alias_to_current = {}
    current_to_mentions = {}
    current_to_rank = {}
    mentions_graph = classes.UndirectedGraph()
    username_trie = classes.Trie()

    # Get ignored usernames if they exist
    ignored_usernames = get_ignored_usernames(ignore_usernames_filename)

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

        current_to_mentions[current_username] = 0
        current_to_rank[current_username] = user["global_rank"]

        if current_username in ignored_usernames:
            print(f"Ignored username {current_username}!")
        else:
            username_trie.insert(current_username)

        for previous_username in previous_usernames:
            if previous_username in ignored_usernames:
                print(f"Ignored username {previous_username}!")
            else:
                username_trie.insert(previous_username)

    for user in users:
        current_username = user["current_username"]
        about_me = strip_bbcode(user["about_me"])

        referenced_aliases = username_trie.find_names_in_document(about_me)
        for referenced_alias in referenced_aliases:
            referenced_username = alias_to_current[referenced_alias.lower()]

            if current_username != referenced_username:
                current_to_mentions[referenced_username] += 1
                mentions_graph.add_edge(current_username, referenced_username)

    return mentions_graph, current_to_mentions, current_to_rank

#################################################################################################################################################
#################################################################################################################################################

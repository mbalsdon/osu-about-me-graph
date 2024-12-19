import classes

import random

#################################################################################################################################################
#################################################################################################################################################

def find_bounded_substring(text: str, substring: str, delimiter: str) -> str:
    """
    Find the text containing substring bounded by delimiter.
    If no delimiter is found, extends to start/end of string.
    """
    pos = text.find(substring)
    if pos == -1:
        return None

    # Find previous delimiter or start of string
    start = text[:pos].rfind(delimiter)
    start = start + 1 if start != -1 else 0

    # Find next delimiter or end of string
    end = text[pos:].find(delimiter)
    end = pos + end if end != -1 else len(text)

    return text[start:end]

#################################################################################################################################################
#################################################################################################################################################

def report_false_positives(
        users: list[dict],
        mentions_graph: classes.DirectedGraph,
        mentions_top_percentile: int,
        max_num_followers: int,
        report_filename: str,
        ignore_usernames_filename: str
    ) -> None:
    """
    Generates a file containing users in the top X% of mentions with less than Y followers\n
    [If I ever have to read this code again](https://c.tenor.com/MT_m5VBtBWwAAAAd/tenor.gif)
    """
    print(f"\n--- Generating false-positives report for {len(users)} users...")

    username_to_followers = {}
    usernames = [u for u in list(mentions_graph.in_degrees.keys())]
    for username in usernames:
        username_to_followers[username] = next((u["follower_count"] for u in users if u["current_username"] == username), None)

    if (len(username_to_followers) != len(mentions_graph.in_degrees)):
        raise AssertionError(f"{len(username_to_followers)} != {len(mentions_graph.in_degrees)}")

    # Get top X% of mentions - by sorting (desc) and accessing first X% elements
    mentions_list_desc = [u[0] for u in sorted(mentions_graph.in_degrees.items(), key=lambda user: (-user[1], user[0]), reverse=False)]
    num_elmts = round(len(username_to_followers) * (mentions_top_percentile / 100))
    most_mentioned = mentions_list_desc[:num_elmts]

    # Get followcounts under threshold
    followers_under_threshold = [u[0] for u in username_to_followers.items() if u[1] <= max_num_followers]

    # Find users common to both lists (maintain order of mentions)
    possible_common_word_usernames = [username for username in most_mentioned if username in set(followers_under_threshold)]

    # Build report
    lines = [
        "### False Positives Report",
        "Some users have names that are also words commonly found in \"About me\" pages. Just to name a few:",
        "* Common words, e.g. \"About\", \"Skill\", \"Anime\"",
        "* Hardware peripherals, e.g. \"Wooting\", \"Razer\", \"RTX\"",
        "* PP barriers, e.g. \"400\", \"500\", \"600\"",
        "* Maps or parts of maps, e.g. \"Horrible Kids\", \"Freedom\" (from \"Freedom Dive\"), \"Daisuke\"",
        "",
        "There is no easy method or algorithm that will figure out when someone is referring to a user, as opposed to using a word. Here, we use number of mentions and follower count as a metric. The users below:",
        f"* Are in the top {mentions_top_percentile}% of mentions",
        f"* Have at most {max_num_followers} followers",
        "",
        "You can tweak these values and re-generate this report by running with additional flags, e.g.",
        "`TODO: flags`",
        "",
        "For each \"suspicious\" username, we also provide some random examples of how their name is being used on other profiles. This should ideally help you decide whether the username is being used as a mention or as a word.",
        "",
        f"In order to remove a user from graphs in the future, add their *alias* to `{ignore_usernames_filename}`. The file already contains some ignored usernames. Ignored usernames are omitted from the list below.",
        "",
        "By *alias*, we mean any current or past username. The script takes past usernames into account, so for example you may see someone with the username \"Mirei Hayasaka\" and wonder why they are mentioned so often. However, looking at their past usernames may reveal that they used to have the username \"About\". Note that the script will not ignore \"Mirei Hayasaka\" and all of their past usernames, only the specific username \"About\".",
        "",
        "---",
    ]

    for current_username in possible_common_word_usernames:
        previous_usernames = [user["previous_usernames"] for user in users if user["current_username"] == current_username][0]
        mentions = mentions_graph.in_degrees[current_username]
        followers = username_to_followers[current_username]

        lines.append(f"**Username:** '{current_username}'")
        lines.append(f"**Previous usernames:** {previous_usernames}")
        lines.append(f"**Number of mentions:** {mentions}")
        lines.append(f"**Number of followers:** {followers}")
        lines.append("")

        in_edges_list = list(mentions_graph.get_in_edges(current_username))
        random.shuffle(in_edges_list)

        num_iterations = min(10, len(in_edges_list))
        for i in range(0, num_iterations):
            in_edges = in_edges_list[i]
            mentioner_username = in_edges[0]
            about_me = [user["about_me"] for user in users if user["current_username"] == mentioner_username][0]

            usage_line = None
            aliases = [current_username] + previous_usernames
            for alias in aliases:
                usage_line = find_bounded_substring(about_me.lower(), alias, "\n")
                if usage_line != None:
                    lines.append(f"'{mentioner_username}' mentioned '{alias}' in the following line:")
                    lines.append(f"```\n{usage_line}\n```")
                    lines.append("")
                    break

            if usage_line == None:
                raise AssertionError(f"Could not find any mention of {aliases} in {mentioner_username}'s page!")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Print to file
    with open(report_filename, "w") as f:
        f.writelines(line + "\n" for line in lines)

    print(f"Found {len(possible_common_word_usernames)} possible false-positives!")

#################################################################################################################################################
#################################################################################################################################################

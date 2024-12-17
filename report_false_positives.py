#################################################################################################################################################
#################################################################################################################################################

def report_false_positives(
        users: list[dict],
        username_to_mentions: dict,
        mentions_top_percentile: int,
        max_num_followers: int,
        report_filename: str,
        ignore_usernames_filename: str
    ) -> None:
    """
    Generates a file containing users in the top X% of mentions with less than Y followers\n
    [If I ever have to read this code again](https://c.tenor.com/MT_m5VBtBWwAAAAd/tenor.gif)
    """
    print(f"--- Generating false-positives report for {len(users)} users...")

    username_to_followers = {}
    usernames = [u for u in list(username_to_mentions.keys())]
    for username in usernames:
        username_to_followers[username] = next((u["follower_count"] for u in users if u["current_username"] == username), None)

    if (len(username_to_followers) != len(username_to_mentions)):
        raise AssertionError(f"{len(username_to_followers)} != {len(username_to_mentions)}")

    # Get top X% of mentions - by sorting (desc) and accessing first X% elements
    mentions_list_desc = [u[0] for u in sorted(username_to_mentions.items(), key=lambda user: (-user[1], user[0]), reverse=False)]
    num_elmts = round(len(username_to_followers) * (mentions_top_percentile / 100))
    most_mentioned = mentions_list_desc[:num_elmts]

    # Get followcounts under threshold
    followers_under_threshold = [u[0] for u in username_to_followers.items() if u[1] <= max_num_followers]

    # Find users common to both lists (maintain order of mentions)
    possible_common_word_usernames = [username for username in most_mentioned if username in set(followers_under_threshold)]

    # Build report
    lines = [
        "Some users have names that are also words commonly found in 'About me' pages. Just to name a few:",
        "* Common words, e.g. 'about', 'skill', 'anime'",
        "* Hardware peripherals, e.g. 'wooting', 'razer', 'rtx'",
        "* PP barriers, e.g. '400', '500', '600'",
        "* Maps or parts of maps, e.g. 'horrible kids', 'freedom' (from 'freedom dive'), 'daisuke'",
        "",
        "There is no easy method or algorithm that will figure out when someone is referring to a user, as opposed to using a word.",
        "Here, we use number of mentions and follower count as a metric.",
        "The users below:",
        f"* Are in the top {mentions_top_percentile}% of mentions",
        f"* Have at most {max_num_followers} followers",
        "You can tweak these values and re-generate this report by running with additional flags, e.g.",
        "TODO --mentions-top-percentile 72 --max-num-followers 7 --use-last-run True --no-graph True",
        "",
        f"In order to remove them from graphs in the future, add their alias to '{ignore_usernames_filename}'.",
        "The file already contains some ignored usernames - these have been omitted from the list below.",
        "",
        "By alias, we mean any current or past username. The script takes past usernames into account, so for example you may see someone with the",
        "username 'Mirei Hayasaka' and wonder why they are mentioned so often. However, looking at their past usernames may reveal that they used to",
        "have the username 'About'. Note that the script will not ignore 'Mirei Hayasaka' and all of their past usernames, only the username 'About'.",
        "",
        "################################################################################################################################################################",
        "################################################################################################################################################################",
        ""
    ]

    for username in possible_common_word_usernames:
        previous_usernames = [user["previous_usernames"] for user in users if user["current_username"] == username][0]
        mentions = username_to_mentions[username]
        followers = username_to_followers[username]

        lines.append(f"Username: '{username}'")
        lines.append(f"Previous usernames: {previous_usernames}")
        lines.append(f"Number of mentions: {mentions}")
        lines.append(f"Number of followers: {followers}")
        lines.append("\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    # Print to file
    with open(report_filename, "w") as f:
        f.writelines(line + "\n" for line in lines)

    print(f"Found {len(possible_common_word_usernames)} possible false-positives!")

#################################################################################################################################################
#################################################################################################################################################

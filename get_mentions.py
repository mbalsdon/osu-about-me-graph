import classes

import dotenv
import ossapi
import asyncio
import aiohttp

import typing
import random
import math
import os
import pickle

#################################################################################################################################################
#################################################################################################################################################

class ProgressCounter:
    '''
    Simple class for progress bar prints.
    '''
    def __init__(self, i: int, total: int):
        self.i = i
        self.total = total

    def increment(self) -> None:
        self.i += 1

    def print_progress_bar(self) -> None:
        progress = self.i / self.total
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        percent = progress * 100
        print(f'\rProgress: [{bar}] {percent:.1f}% ({self.i}/{self.total})', end='', flush=True)

#################################################################################################################################################
#################################################################################################################################################

async def fetch_single_rankings_ids(osu: ossapi.OssapiAsync, page: int, counter: ProgressCounter) -> list[int]:
    retries = 0
    wait_sec = 1 + random.random()
    while True:
        try:
            rankings = await osu.ranking(ossapi.GameMode.OSU, ossapi.RankingType.PERFORMANCE, cursor=ossapi.Cursor(page=page))

            # Race condition here, but locks are expensive and printing is not critical
            counter.increment()
            counter.print_progress_bar()

            return [user_statistics.user.id for user_statistics in rankings.ranking]

        except ValueError as e:
            error_message = str(e).lower()

            # Exponential backoff if we get 429'ed. (https://en.wikipedia.org/wiki/Exponential_backoff)
            if "too many attempts" in error_message:
                wait_sec = (2 ** retries) + random.random()
                if (wait_sec >= 64):
                    wait_sec = 64 + random.random()

                retries += 1
                await asyncio.sleep(wait_sec)
                continue

            # Skip for other errors - may happen if for example someone gets restricted between the time
            # we grab their ID and the time we grab their data.
            return None

        # https://github.com/tybug/ossapi/issues/60#issuecomment-2544072157
        except (aiohttp.ContentTypeError, aiohttp.ClientError, aiohttp.ClientOSError, asyncio.TimeoutError) as e:
            await asyncio.sleep(wait_sec)
            continue


async def fetch_rankings_ids(osu: ossapi.OssapiAsync, num_pages: int) -> list[int]:
    print(f"Fetching user IDs for rankings pages 1-{num_pages} ...")
    counter = ProgressCounter(0, num_pages)
    tasks = [fetch_single_rankings_ids(osu, page, counter) for page in range(1, num_pages + 1)]
    results = await asyncio.gather(*tasks)
    user_ids = [id for ids in results for id in ids]
    print("\n", end="")
    return user_ids


async def fetch_single_user(osu: ossapi.OssapiAsync, user_id: int, counter: ProgressCounter) -> typing.Any:
    retries = 0
    wait_sec = 1 + random.random()
    while True:
        try:
            user = await osu.user(user_id, mode=ossapi.GameMode.OSU)

            # Race condition here, but locks are expensive and printing is not critical
            counter.increment()
            counter.print_progress_bar()

            return {
                "current_username": user.username.lower(),
                "previous_usernames": [pu.lower() for pu in user.previous_usernames],
                "about_me": user.page.raw,
                "follower_count": user.follower_count,
                "global_rank": user.statistics.global_rank
            }

        except ValueError as e:
            error_message = str(e).lower()

            # Exponential backoff if we get 429'ed. (https://en.wikipedia.org/wiki/Exponential_backoff)
            if "too many attempts" in error_message:
                wait_sec = (2 ** retries) + random.random()
                if (wait_sec >= 64):
                    wait_sec = 64 + random.random()

                retries += 1
                await asyncio.sleep(wait_sec)
                continue

            # Skip for other errors - may happen if for example someone gets restricted between the time
            # we grab their ID and the time we grab their data.
            return None

        # https://github.com/tybug/ossapi/issues/60#issuecomment-2544072157
        except (aiohttp.ContentTypeError, aiohttp.ClientError, aiohttp.ClientOSError, asyncio.TimeoutError) as e:
            await asyncio.sleep(wait_sec)
            continue


async def fetch_users(osu: ossapi.OssapiAsync, user_ids: list[typing.Any]) -> list[typing.Any]:
    print("Fetching user data...")
    counter = ProgressCounter(0, len(user_ids))
    tasks = [fetch_single_user(osu, user_id, counter) for user_id in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    print("\n", end="")
    return [user for user in results if user is not None]


def save_graph_data(filename: str, mentions_graph: classes.UndirectedGraph, current_to_mentions: dict) -> None:
    with open(filename, "wb") as f:
        pickle.dump({
            "mentions_graph": mentions_graph,
            "current_to_mentions": current_to_mentions
        }, f)


def load_graph_data(filename: str) -> tuple[classes.UndirectedGraph, dict]:
    with open(filename, "rb") as f:
        data = pickle.load(f)
        mentions_graph = data["mentions_graph"]
        current_to_mentions = data["current_to_mentions"]
        return mentions_graph, current_to_mentions


async def get_mentions(min_num_users: int, use_last_run: bool) -> tuple[classes.UndirectedGraph, dict]:
    '''
    Scrape user data from osu!API. Returns the following:
    * Undirected graph, where an edge exists between player A and B iff player A mentions player B.
    * Map, from username to number of mentions by other players.

    Takes past usernames into account.

    If use_last_run is set to True, ignores min_num_users and reads data from disk.
    '''

    # Load saved data if specified
    save_filename = "graph_data.pkl"
    if use_last_run:
        if not os.path.exists(save_filename):
            raise FileNotFoundError(f"Savefile {save_filename} could not be found.")
        return load_graph_data(save_filename)

    if min_num_users < 1 or min_num_users > 10000:
        raise ValueError(f"Number of users must be between 1-10000.")

    num_pages = math.ceil(min_num_users / 50)
    print(f"-- Parsing data for {num_pages * 50} users... This may take a while!")

    dotenv.load_dotenv()
    osu = ossapi.OssapiAsync(
        os.getenv("OSU_API_CLIENT_ID"),
        os.getenv("OSU_API_CLIENT_SECRET"))

    # Fetch user data and sort by follower count (descending) then rank (ascending)
    user_ids = await fetch_rankings_ids(osu, num_pages)
    users = await fetch_users(osu, user_ids)
    users = sorted(users, key=lambda user: (-user["follower_count"], user["global_rank"]), reverse=False)

    alias_to_current = {}
    current_to_mentions = {}
    mentions_graph = classes.UndirectedGraph()
    username_trie = classes.Trie()

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

        username_trie.insert(current_username)
        for previous_username in previous_usernames:
            username_trie.insert(previous_username)

    for user in users:
        current_username = user["current_username"]
        about_me = user["about_me"]

        referenced_aliases = username_trie.find_names_in_document(about_me)
        for referenced_alias in referenced_aliases:
            referenced_username = alias_to_current[referenced_alias.lower()]

            if current_username != referenced_username:
                current_to_mentions[referenced_username] += 1
                mentions_graph.add_edge(current_username, referenced_username)

    save_graph_data(save_filename, mentions_graph, current_to_mentions)
    return mentions_graph, current_to_mentions

#################################################################################################################################################
#################################################################################################################################################

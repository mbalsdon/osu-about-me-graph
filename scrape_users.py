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
    """
    Simple class for progress bar prints.
    """
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
        print(f"\rProgress: [{bar}] {percent:.1f}% ({self.i}/{self.total})", end="", flush=True)

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


async def fetch_single_user(osu: ossapi.OssapiAsync, user_id: int, counter: ProgressCounter) -> list[typing.Union[dict, None]]:
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


async def fetch_users(osu: ossapi.OssapiAsync, user_ids: list[typing.Union[dict, None]]) -> list[dict]:
    print("Fetching user data...")
    counter = ProgressCounter(0, len(user_ids))
    tasks = [fetch_single_user(osu, user_id, counter) for user_id in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    print("\n", end="")
    return [user for user in results if user is not None]


def save_users(filename: str, users: list[dict]):
    with open(filename, "wb") as f:
        pickle.dump({
            "users": users
        }, f)


def load_users(filename: str) -> list[dict]:
    with open(filename, "rb") as f:
        data = pickle.load(f)
        users = data["users"]
        return users

#################################################################################################################################################
#################################################################################################################################################

async def scrape_users(min_num_users: int, use_last_run: bool, save_filename: str) -> list[dict]:
    """
    Scrape user data from osu!API.\n
    Rounds min_num_users up to the nearest multiple of 50.\n
    If use_last_run is True, ignores min_num_users and reads data from save_filename.\n
    Returns list of users including:
        * "current_username": `str`
        * "previous_usernames": `list[str]`
        * "about_me": `str`
        * "follower_count": `int`
        * "global_rank": `int`
    """
    if use_last_run:
        print(f"-- Fetching save data from {save_filename}...")
        if not os.path.exists(save_filename):
            raise FileNotFoundError(f"Savefile {save_filename} could not be found!")
        return load_users(save_filename)

    if min_num_users < 1 or min_num_users > 10000:
        raise ValueError(f"Number of users must be between 1-10000!")

    num_pages = math.ceil(min_num_users / 50)
    print(f"-- Scraping osu!API data for {num_pages * 50} users... This may take a while!")

    osu = ossapi.OssapiAsync(
        os.getenv("OSU_API_CLIENT_ID"),
        os.getenv("OSU_API_CLIENT_SECRET"))

    user_ids = await fetch_rankings_ids(osu, num_pages)
    users = await fetch_users(osu, user_ids)

    save_users(save_filename, users)
    return users

#################################################################################################################################################
#################################################################################################################################################

import classes

import aiohttp
import asyncio
import ossapi

import logging
import math
import os
import pickle
import random
import typing

logger = logging.getLogger("osu-about-me-graph")

# osu!API v2 docs (https://osu.ppy.sh/docs/index.html#introduction) specify ratelimit of 1200 requests/min (0.05 requests/sec).
# Be nice to peppy by staying well under that.
MAX_REQUESTS_PER_SEC = 0.10

REQUEST_TIMEOUT_SEC = 5.0

#################################################################################################################################################
#################################################################################################################################################

async def fetch_single_rankings_ids(
        osu: ossapi.OssapiAsync,
        mode: ossapi.GameMode,
        page: int,
        initial_wait_sec: float,
        counter: classes.ProgressCounter
    ) -> list[int]:
    """
    Requests rankings from osu!API v2 and returns userIDs.
    Deals with server errors using [exponential backoff](https://en.wikipedia.org/wiki/Exponential_backoff).
    """
    await asyncio.sleep(initial_wait_sec)

    retries = 0
    wait_sec = 0.0

    while True:
        err_msg = ""
        try:
            # Sometimes ossapi client requests will hang
            rankings = await asyncio.wait_for(
                osu.ranking(
                    mode,
                    ossapi.RankingType.PERFORMANCE,
                    cursor=ossapi.Cursor(page=page)
                ),
                timeout=REQUEST_TIMEOUT_SEC
            )

            # Race condition here, but locks are expensive and printing is not critical
            counter.increment()
            counter.print_progress_bar()

            return [user_statistics.user.id for user_statistics in rankings.ranking]

        except ValueError as e:
            error_message = str(e).lower()

            # HTTP 429
            if "too many attempts" in error_message:
                err_msg = f"(Coroutine #{id(asyncio.current_task())}) Ratelimited!"
            else:
                raise e

        # https://github.com/tybug/ossapi/issues/60#issuecomment-2544072157
        except (aiohttp.ContentTypeError, aiohttp.ClientError, aiohttp.ClientOSError) as e:
            err_msg = f"(Coroutine #{id(asyncio.current_task())}) Something broke!"

        except asyncio.TimeoutError:
            err_msg = f"(Coroutine #{id(asyncio.current_task())}) Request timed out!"

        # Exponential backoff
        wait_sec = min(2**retries, 64) + random.random()
        retries += 1
        logger.debug(f"{err_msg} Waiting {wait_sec} seconds...")
        await asyncio.sleep(wait_sec)
        continue


async def fetch_rankings_ids(osu: ossapi.OssapiAsync, mode: ossapi.GameMode, first_page: int, num_pages: int) -> list[int]:
    print(f"Fetching user IDs for rankings pages {first_page}-{first_page + num_pages - 1} ...")
    counter = classes.ProgressCounter(0, num_pages)

    # Stay under ratelimit by firing request i at time = MAX_REQUESTS_PER_SEC * i (e.g. r1 at 0.0s, r2 at 0.1s, r3 at 0.2s, ...)
    tasks = [
        fetch_single_rankings_ids(osu, mode, page, MAX_REQUESTS_PER_SEC * i, counter)
        for i, page in enumerate(range(first_page, first_page + num_pages))
    ]
    results = await asyncio.gather(*tasks)
    user_ids = [id for ids in results for id in ids]
    print("\n", end="")
    return user_ids


async def fetch_single_user(
        osu: ossapi.OssapiAsync,
        mode: ossapi.GameMode,
        user_id: int,
        initial_wait_sec: float,
        counter: classes.ProgressCounter
    ) -> list[typing.Union[dict, None]]:
    """
    Requests user from osu!API v2.
    Deals with server errors using [exponential backoff](https://en.wikipedia.org/wiki/Exponential_backoff).
    """
    await asyncio.sleep(initial_wait_sec)

    retries = 0
    wait_sec = 0.0

    while True:
        err_msg = ""
        try:
            # Sometimes ossapi client requests will hang
            user = await asyncio.wait_for(
                osu.user(
                    user_id,
                    mode=mode
                ),
                timeout=REQUEST_TIMEOUT_SEC
            )

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

            # HTTP 429
            if "too many attempts" in error_message:
                err_msg = f"(Coroutine #{id(asyncio.current_task())}) Ratelimited!"

            # Skip for other errors - may happen if for example someone gets restricted between the time
            # we grab their ID and the time we grab their data.
            else:
                return None

        # https://github.com/tybug/ossapi/issues/60#issuecomment-2544072157
        except (aiohttp.ContentTypeError, aiohttp.ClientError, aiohttp.ClientOSError) as e:
            err_msg = f"(Coroutine #{id(asyncio.current_task())}) Something broke!"

        except asyncio.TimeoutError:
            err_msg = f"(Coroutine #{id(asyncio.current_task())}) Request timed out!"

        # Exponential backoff
        wait_sec = min(2**retries, 64) + random.random()
        retries += 1
        logger.debug(f"{err_msg} Waiting {wait_sec} seconds...")
        await asyncio.sleep(wait_sec)
        continue


async def fetch_users(osu: ossapi.OssapiAsync, mode: ossapi.GameMode, user_ids: list[typing.Union[dict, None]]) -> list[dict]:
    print("Fetching user data...")
    counter = classes.ProgressCounter(0, len(user_ids))

    # Stay under ratelimit by firing request i at time = MAX_REQUESTS_PER_SEC * i (e.g. r1 at 0.0s, r2 at 0.1s, r3 at 0.2s, ...)
    tasks = [
        fetch_single_user(osu, mode, user_id, MAX_REQUESTS_PER_SEC * i, counter)
        for i, user_id in enumerate(user_ids)
    ]
    results = await asyncio.gather(*tasks)
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
        print(f"Successfully loaded data for {len(users)} users!")
        return users

#################################################################################################################################################
#################################################################################################################################################

async def scrape_users(start_rank: int, num_users: int, gamemode: ossapi.GameMode, use_last_run: bool, save_filename: str) -> list[dict]:
    """
    Scrape user data from osu!API.
    If use_last_run is True, ignores num_users and reads data from save_filename.\n
    Returns list of users including:
        * "current_username": `str`
        * "previous_usernames": `list[str]`
        * "about_me": `str`
        * "follower_count": `int`
        * "global_rank": `int`
    """
    if use_last_run:
        print(f"\n--- Fetching save data from {save_filename}...")
        if not os.path.exists(save_filename):
            raise FileNotFoundError(f"Savefile {save_filename} could not be found!")
        return load_users(save_filename)

    if start_rank < 1 or start_rank > 10000:
        raise ValueError(f"Start rank must be between 1-10000!")
    if num_users < 1 or num_users > 10000:
        raise ValueError(f"Number of users must be between 1-10000!")

    first_page = math.floor((start_rank - 1) / 50) + 1
    num_pages = math.ceil((start_rank + num_users - 1) / 50)
    print(f"\n--- Scraping osu!API data for {num_users} users...")

    # Get rid of log spam caused by ossapi
    asyncio_default_log_level = logging.getLogger("asyncio").level
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    osu = ossapi.OssapiAsync(
        os.getenv("OSU_API_CLIENT_ID"),
        os.getenv("OSU_API_CLIENT_SECRET"))

    user_ids = await fetch_rankings_ids(osu, gamemode, first_page, num_pages)
    users = await fetch_users(osu, gamemode, user_ids)
    
    # Remove excess users
    num_remove_from_back = (50 - (num_users % 50)) % 50
    num_remove_from_front = (start_rank - 1) % 50
    print(f"Removing {num_remove_from_back + num_remove_from_front} excess users...")

    users = [u for u in sorted(users, key=lambda user: (user["global_rank"]), reverse=False)]
    if num_remove_from_front != 0:
        users = users[num_remove_from_front:]
    if num_remove_from_back != 0:
        users = users[:-num_remove_from_back]

    # Turn it back on now that we're done with the noisy stuff
    logging.getLogger("asyncio").setLevel(asyncio_default_log_level)

    save_users(save_filename, users)
    return users

#################################################################################################################################################
#################################################################################################################################################

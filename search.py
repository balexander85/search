"""Search the web for items and get magnet url for Transmission"""
from datetime import datetime

from search.sites import search_all_sites
from search.util import LOGGER, get_user_input


if __name__ == "__main__":
    user_input = get_user_input()
    start_time = datetime.now()

    all_results = search_all_sites(query=user_input)

    for counter, result in enumerate(all_results, start=1):
        LOGGER.info(f"{counter}) {result}")

    end_time = datetime.now()
    LOGGER.info(f"Search duration {end_time - start_time}")

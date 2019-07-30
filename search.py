"""Search the web for items and get magnet url for Transmission"""
from datetime import datetime

from sites import search_sites
from util import LOGGER, get_user_input, print_border


if __name__ == "__main__":
    user_input = get_user_input()
    start_time = datetime.now()

    for search_site in search_sites:
        print_border(search_site.__name__)
        site_results = search_site(query=user_input)
        for counter, site_result in enumerate(site_results, start=1):
            LOGGER.info(f"{counter}) {site_result}")

        LOGGER.info(f"Search duration {datetime.now() - start_time}")

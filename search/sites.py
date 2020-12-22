from asyncio import ensure_future, gather, get_event_loop, sleep
from datetime import datetime
from typing import List

from requests_html import HTML, Element
from search.results import Result
from search.util import LOGGER, get_first_element, format_comments, RequestsHtmlWrapper

NEED_TO_UPDATE = ["ThePirateBay"]


class BaseSite:
    """Parent class for searching websites."""

    SEARCH_URL_PATTERN = "/{}"
    WHITESPACE_PATTERN = "+"

    def __init__(
        self, protocol: str = "http", domain: str = "example", tdl: str = "com"
    ):
        """Construct URL with these base attributes.

        :param protocol: Protocol used for website.
        :param domain: Name of the domain where the web server belongs.
        :param tdl: Top Level Domain for website.
        """
        self.base_url: str = f"{protocol}://{domain}.{tdl}"
        LOGGER.info(f"Searching {self}")

    def __str__(self):
        return f"<{self.__class__.__name__} url='{self.base_url}'>"


class ThePirateBay(BaseSite):
    """Subclass for searching ThePirateBay domain."""

    SEARCH_URL_PATTERN = "/search/{}/0/99/0"
    WHITESPACE_PATTERN = "%20"
    RESULTS_TABLE = "table#searchResult"
    RESULTS_ROW = "div.detName"
    ITEM_NAME = "div.detName"
    ITEM_MAGNET_LINK = 'a[href^="magnet"]'
    ITEM_COMMENTS = "This torrent has {} comments."
    MEDIA_AND_CATEGORY_TYPE = "td.vertTh"
    SEEDERS_AND_LEACHERS = 'td[@align="right"]'
    UPLOADER_VIP = 'img[@alt="VIP"]'
    UPLOADER_TRUSTED = 'img[@alt="Trusted"]'
    PARSED_COMMENTS = "div.comment"

    def __init__(self, protocol: str, domain: str, tdl: str):
        super().__init__(protocol=protocol, domain=domain, tdl=tdl)

    def parse_row(self, obj: Element) -> dict:
        """Parse object for item information."""
        return {
            "name": get_first_element(obj, self.ITEM_NAME).text,
            "media_type": get_first_element(obj, self.MEDIA_AND_CATEGORY_TYPE)
            .find("a")[0]
            .text,
            "category": get_first_element(obj, self.MEDIA_AND_CATEGORY_TYPE)
            .find("a")[1]
            .text,
            "seeders": obj.find(self.SEEDERS_AND_LEACHERS)[0].text,
            "leachers": obj.find(self.SEEDERS_AND_LEACHERS)[1].text,
            "magnet_link": get_first_element(obj, self.ITEM_MAGNET_LINK).links.pop(),
            "file_size": get_first_element(obj, "font.detDesc").text.split(",")[1],
            "vip_status": get_first_element(obj, self.UPLOADER_VIP),
            "trusted": get_first_element(obj, self.UPLOADER_TRUSTED),
            "href": get_first_element(obj, "a.detLink").links.pop(),
            "uploader": (obj.find("font.detDesc")[0].text.split("by")[-1].strip()),
            "comment_count": (
                0
                if not obj.search(self.ITEM_COMMENTS)
                else obj.search(self.ITEM_COMMENTS).fixed[0]
            ),
        }

    async def _fetch_comments(self, result: Result):
        if result.comment_count >= 1:
            LOGGER.debug(f"_fetching comments: {result.__repr__()}")
            page_url: str = f"{self.base_url}{result.href}"
            LOGGER.debug(f"Await sleeping: {datetime.now()} {result.href}")
            await sleep(1)
            page = RequestsHtmlWrapper(url=page_url).html
            comments = page.find(selector=self.PARSED_COMMENTS)
            if comments:
                result.comments_section = format_comments(
                    [c.text.replace("\n", "") for c in comments]
                )

    def add_comments(self, results: List[Result]):
        """Return a list of comments for a result if available."""
        loop = get_event_loop()
        tasks = [ensure_future(self._fetch_comments(result)) for result in results]
        loop.run_until_complete(gather(*tasks, return_exceptions=True))
        loop.close()

    def search(self, query: str) -> List[Result]:
        """Base method for search."""
        search_url = self.base_url + self.SEARCH_URL_PATTERN.format(
            query.replace(" ", self.WHITESPACE_PATTERN)
        )
        LOGGER.info(f'Searching {search_url} for "{query}"')
        html: HTML = RequestsHtmlWrapper(url=search_url).html
        results_table: Element = get_first_element(
            html=html, locator=self.RESULTS_TABLE
        )
        if results_table:
            results: [Result] = [
                Result(self.parse_row(row))
                for row in results_table.find("tr")
                if row.find(self.RESULTS_ROW)
            ]
            # if results:
            #     self.add_comments(results)
            return results
        return []


# https://pirateproxys.com/
tpb_mirrors = [
    {"protocol": "https", "domain": "piratebay", "tdl": "live"},
    # {"protocol": "https", "domain": "thepiratebay", "tdl": "org"},
    # {"protocol": "https", "domain": "piratebay", "tdl": "icu"},
    # {"protocol": "https", "domain": "piratebayblocked", "tdl": "com"},
    # {"protocol": "https", "domain": "tpb", "tdl": "date"},
]
tpb_sites = [ThePirateBay(**tpb_instance) for tpb_instance in tpb_mirrors]

search_sites = [
    cls() for cls in BaseSite.__subclasses__() if cls.__name__ not in NEED_TO_UPDATE
]
search_sites.extend(tpb_sites)


def search_all_sites(query: str) -> List[Result]:
    all_results = []
    LOGGER.debug(msg=f"user_input: {query}")
    for search_site in search_sites:
        for result in search_site.search(query=query):
            all_results.append(result)
    set_results = set(all_results)
    sorted_results = sorted(set_results, key=lambda x: x.seeders, reverse=True)
    return sorted_results

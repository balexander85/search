"""Search the web for items and get magnet url for Transmission"""
from asyncio import ensure_future, gather, get_event_loop, sleep
from datetime import datetime
from typing import List

from requests_html import HTML, Element
from results import Result
from util import (
    LOGGER,
    get_first_element,
    get_user_input,
    format_comments,
    print_border,
    RequestsHtmlWrapper,
)

NEED_TO_UPDATE = ['']


class BaseSite:
    """Parent class for searching websites."""

    SEARCH_URL_PATTERN = '/{}'
    WHITESPACE_PATTERN = '+'

    def __init__(
            self,
            protocol: str = 'http',
            domain: str = 'example',
            tdl: str = 'com',
            query: str = None
    ):
        """Construct URL with these base attributes.

        :param protocol: Protocol used for website.
        :param domain: Name of the domain where the web server belongs.
        :param tdl: Top Level Domain for website.
        :param query: User's search query
        """
        print_border(self.__class__.__name__)
        self.base_url: str = f'{protocol}://{domain}.{tdl}'
        self.query: str = query
        self.request_wrapper: RequestsHtmlWrapper = RequestsHtmlWrapper(
            url=self.search_url
        )
        self.html: HTML = self.request_wrapper.html

    def __iter__(self) -> Result:
        """Iterate through each result found from search query."""
        for result in self.results:
            yield result

    @property
    def search_url(self) -> str:
        """Create search url with patch and whitespace replacement character"""
        LOGGER.info(f'Searching for "{self.query}"')
        return self.base_url + self.SEARCH_URL_PATTERN.format(
            self.query.replace(' ', self.WHITESPACE_PATTERN)
        )

    @property
    def results(self) -> List[dict]:
        """Abstract property which returns a list of results from search.

        Note: Will raise error if not implemented in subclass.
        """
        raise NotImplementedError(
            "Subclasses that use BaseSite must implement results property."
        )


class ThePirateBay(BaseSite):
    """Subclass for searching Thepiratebay domain."""

    SEARCH_URL_PATTERN = '/search/{}/0/99/0'
    WHITESPACE_PATTERN = '%20'
    RESULTS_TABLE = 'table#searchResult'
    RESULTS_ROW = 'div.detName'
    ITEM_NAME = 'div.detName'
    ITEM_MAGNET_LINK = 'a[href^="magnet"]'
    ITEM_COMMENTS = 'This torrent has {} comments.'
    MEDIA_AND_CATEGORY_TYPE = 'td.vertTh'
    SEEDERS_AND_LEACHERS = 'td[@align="right"]'
    UPLOADER_VIP = 'img[@alt="VIP"]'
    UPLOADER_TRUSTED = 'img[@alt="Trusted"]'
    PARSED_COMMENTS = 'div.comment'

    def __init__(
            self,
            protocol: str = "https",
            domain: str = "thepiratebay",
            tdl: str = "icu",
            query: str = None
    ):
        BaseSite.__init__(
            self, protocol=protocol, domain=domain, tdl=tdl, query=query
        )
        self.results_table: Element = get_first_element(
            html=self.html,
            locator=self.RESULTS_TABLE
        )

    def parse_row(self, obj: Element) -> dict:
        """Parse object for item information."""
        return {
            'name': get_first_element(obj, self.ITEM_NAME).text,
            'media_type': get_first_element(
                obj, self.MEDIA_AND_CATEGORY_TYPE).find('a')[0].text,
            'category': get_first_element(
                obj, self.MEDIA_AND_CATEGORY_TYPE).find('a')[1].text,
            'seeders': obj.find(self.SEEDERS_AND_LEACHERS)[0].text,
            'leachers': obj.find(self.SEEDERS_AND_LEACHERS)[1].text,
            'magnet_link': get_first_element(
                obj, self.ITEM_MAGNET_LINK).links.pop(),
            'file_size': get_first_element(
                obj, 'font.detDesc').text.split(',')[1],
            'vip_status': get_first_element(obj, self.UPLOADER_VIP),
            'trusted': get_first_element(obj, self.UPLOADER_TRUSTED),
            'href': get_first_element(obj, 'a.detLink').links.pop(),
            'uploader': (
                obj.find('font.detDesc')[0].text.split('by')[-1].strip()
            ),
            'comment_count': (
                0 if not obj.search(self.ITEM_COMMENTS)
                else obj.search(self.ITEM_COMMENTS).fixed[0]
            ),
        }

    async def _fetch_comments(self, result: Result):
        if result.comment_count >= 1:
            LOGGER.debug(
                f'_fetching comments: {result.__repr__()}'
            )
            page_url: str = f'{self.base_url}{result.href}'
            LOGGER.debug(f'Await sleeping: {datetime.now()} {result.href}')
            await sleep(1)
            page = self.request_wrapper.get_page(page_url=page_url)
            comments = page.find(selector=self.PARSED_COMMENTS)
            if comments:
                result.comments_section = format_comments(
                    [c.text.replace('\n', '') for c in comments]
                )

    def add_comments(self, results: List[Result]):
        """Return a list of comments for a result if available."""
        loop = get_event_loop()
        tasks = [
            ensure_future(self._fetch_comments(result))
            for result in results
        ]
        loop.run_until_complete(gather(*tasks, return_exceptions=True))
        loop.close()

    @property
    def results(self) -> List[Result]:
        """Returning results from this site."""
        if self.results_table:
            results: List[Result] = [
                Result(self.parse_row(row))
                for row in self.results_table.find("tr")
                if row.find(self.RESULTS_ROW)
            ]
            if results:
                self.add_comments(results)
            return results


if __name__ == '__main__':
    user_input = get_user_input()
    start_time = datetime.now()

    search_sites = [
        cls for cls in BaseSite.__subclasses__()
        if cls.__name__ not in NEED_TO_UPDATE
    ]

    for search_site in search_sites:
        site_results = search_site(query=user_input)
        for counter, site_result in enumerate(site_results, 1):
            print(f'{counter}) {site_result}')

        LOGGER.info(
            f'Search duration {datetime.now() - start_time}'
        )

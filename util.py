"""Functions to be used by search module
but not necessarily related to the searching itself.
"""
from logging import basicConfig, getLogger, INFO
from re import match as regex_match
from sys import argv, stdout
from typing import List, Union

from humanfriendly import parse_size
from requests_html import Element, HTML, HTMLResponse, HTMLSession
from retrying import retry

# Setting up logger
basicConfig(
    level=INFO,
    format="%(levelname)7s: %(message)s",
    stream=stdout,
)
LOGGER = getLogger("Search Logger")


def format_comments(comments: List[str]) -> List[str]:
    """Add #.) to each comment"""
    return [f'{i}.) {comment}' for i, comment in enumerate(comments, 1)]


def format_file_size(size: str) -> str:
    """Returns file size in a formatted string (i.e. 706 MiB)"""
    return '{} {}'.format(
        *regex_match(
            r'^.*?(?=(\d+.?\d*)).+?(?:(B|KiB|MiB|GiB|MB|GB))', size).groups()
    )


def format_file_size_to_int(size: str) -> int:
    """Returns file size in an integer value (i.e. 706 MiB => 740294656)"""
    return parse_size(size)


def get_first_element(html: Union[Element, HTML], locator: str) -> Element:
    """Wrapping the find method of the HTML object"""
    return html.find(selector=locator, first=True)


def get_user_input() -> str:
    """Get search query from user by command line or prompt"""
    try:
        return argv[1]
    except IndexError:
        return input('Enter search query:\n')


def print_border(name: str = None):
    """Print simple border to divide up output,
    if name print bottom border out too
    """
    print(158*'*')
    if name:
        print(f'{70*"#"}{name}{70*"#"}')
        print(158*"*")


def save_page(html: HTML, file_name: str = "test.html"):
    """Helper function to save page as an html file."""
    with open(file_name, "w") as f:
        f.write(html.html)


class RequestsHtmlWrapper:
    """A Wrapper class for the request_html library.

    Instances are generated when passing in a valid url then a request is made
    with that url and then the response attribute of the instance is set.

    This wrapper allows a user to make a request with a url and access the
    response object. In addition to accessing a response object with an
    instance, one is also able to access and parse the HTML object.

    Examples:
        URL is used to instantiate the class
        request_wrapper = HtmlRequestWrapper("https://www.example.com/")

        Use HTML tag with call function to get list of elements from HTML
        anchor_elements = request_wrapper("a")

        Access Requests response methods and attributes
        status_code = request_wrapper.response.status_code

        Access HTML object for the current response with the .html property
        html = request_wrapper.html

        Search for elements within the HTML object
        web_element = request_wrapper.html.find(locator)
    """

    def __init__(self, url: str, agent: str = 'Mozilla/5.0'):
        self.session: HTMLSession = HTMLSession()
        self.headers: dict = {
            'Content-Type': 'text/plain; charset=UTF-8',
            'User-Agent': agent
        }
        self.url: str = url
        self.cookies = None
        self.response: HTMLResponse = self.__response
        self.html: HTML = self.response.html

    def __repr__(self) -> str:
        return f'<Request_HTML_Wrapper url={self.url}>'

    def __call__(self, tag_name) -> List[Element]:
        """Shortcut method for HTMLResponse.html.find just like BeautifulSoup

        Returns:
            A list of elements for matching tag
        """
        return self.html.find(selector=tag_name)

    @property
    @retry(wait_fixed=500, stop_max_attempt_number=5)
    def __response(self) -> HTMLResponse:
        """Return HTMLResponse with the instance's url."""
        response: HTMLResponse = self.session.get(
            url=self.url, headers=self.headers, cookies=self.cookies
        )
        response.raise_for_status()
        return response

    def get_page(self, page_url: str) -> HTML:
        """Make request with given url and return html"""
        response: HTMLResponse = self.session.get(
            url=page_url, headers=self.headers, cookies=self.cookies
        )
        return response.html

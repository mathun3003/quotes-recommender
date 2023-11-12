import re
from typing import Any, Final, Generator

import scrapy
from scrapy.exceptions import StopDownload
from scrapy.http import Response

from src.core.constants import \
    QUOTE_NUM_LIKES_KEY, QUOTE_FEED_URL_KEY, QUOTE_TEXT_KEY, QUOTE_AUTHOR_KEY, \
    QUOTE_AVATAR_KEY, QUOTE_TAGS_KEY, QUOTE_AVATAR_IMG_KEY, USER_URLS_KEY

class GoodreadsSpider(scrapy.Spider):
    """Scraper to extract data from goodreads.com/quotes."""

    name = 'goodreads-spider'
    allowed_domains = ['goodreads.com'] 
    start_urls = [
        'https://www.goodreads.com/quotes'
    ]

    # filter masks for goodreads
    QUOTE_SELECTOR: Final[str] = 'div.quote'
    QUOTE_DETAILS: Final[str] = 'quoteDetails'
    QUOTE_FOOTER: Final[str] = 'quoteFooter'
    QUOTE_AVATAR: Final[str] = 'a.leftAlignedImage.quoteAvatar::attr(href)'
    QUOTE_AVATAR_IMG: Final[str] = 'a.leftAlignedImage.quoteAvatar img::attr(src)'
    QUOTE_TEXT: Final[str] = 'h1.quoteText::text'
    QUOTE_LIKES: Final[str] = 'span.uitext.smallText'
    QUOTE_FEED: Final[str] = 'a.smallText::attr(href)'
    QUOTE_AUTHOR_OR_TITLE: Final[str] = 'span.authorOrTitle::text'
    QUOTE_TAGS: Final[str] = 'div.greyText.smallText.left a::text'

    # user data
    USER_LIKE_FEED: Final[str] = 'div.elementList'
    USER_URL: Final[str] = 'a.leftAlignedImage::attr(href)'
    USER_LIKED_LINK: Final[str] = 'a.userName::attr(href)'

    # next page selector
    NEXT_SELECTOR: Final[str] = 'a.next_page::attr(href)'

    # regex
    NUM_LIKES_REGEX: Final[str] = r'\b\d+\b'  # removes non-digits from string
    def parse(self, response: Response, **kwargs: Any) -> Generator:
        """
        Function to select data from an object.
        :param response: web response from scrapy
        :param kwargs: additional kwargs
        :return: Generator object
        """
        for feed in response.css(self.QUOTE_FEED).extract():
            # extract number of likes, get the digit
            yield scrapy.Request(response.urljoin(feed), callback=self.parse_subpage)

        # get next page
        next_page = response.css(self.NEXT_SELECTOR).extract_first()
        # paginate if available
        if next_page:
            yield scrapy.Request(response.urljoin(next_page))

    def extract_id(self, username):
        USER_LIKED_ID_PATTERN = r'/user/show/(\d+)(?:-(\w+))?'
        match = re.match(USER_LIKED_ID_PATTERN, username)
        if match:
            user_id = match.group(1)
            username = match.group(2)
            return {user_id: username}
        else:
            return None
        
    def parse_subpage(self, response: Response) -> list[str]:
        """
        Function to crawl subpages from a starting url
        :param response: web response from scrapy
        :return: list user URLs
        """
        num_likes_list: list[str] = re.findall(self.NUM_LIKES_REGEX, response.css(self.QUOTE_LIKES).get())
        # raise exception if multiple values are found for regex matching
        if len(num_likes_list) > 1:
            raise StopDownload(fail=True)
        # raise exception if result is not a a digit
        if not (num_likes := num_likes_list[0]).isdigit():
            raise ValueError('num_likes is not a digit. Failed to convert to int.')
        else:
            # cast string to int
            num_likes = int(num_likes)
        
        user_ids = [self.extract_id(x) for x in response.css(self.USER_LIKED_LINK).extract()]
        # fetch subpage feed
        # yield results
        yield {
            # extract author
            QUOTE_AUTHOR_KEY: response.css(self.QUOTE_AUTHOR_OR_TITLE).get().strip(),
            # extract avatar jpg file from src
            QUOTE_AVATAR_IMG_KEY: response.css(self.QUOTE_AVATAR_IMG).extract(),
            QUOTE_AVATAR_KEY: response.urljoin(response.css(self.QUOTE_AVATAR).get()),
            # extract text
            QUOTE_TEXT_KEY: response.css(self.QUOTE_TEXT).get().strip().lstrip('“').rstrip('”'),
            # yield number of likes
            QUOTE_NUM_LIKES_KEY: num_likes,
            # yield quote feed url
            QUOTE_FEED_URL_KEY: response.url,
            # yield quote tags
            QUOTE_TAGS_KEY: response.css(self.QUOTE_TAGS).extract(),
            USER_URLS_KEY: user_ids
        }
        
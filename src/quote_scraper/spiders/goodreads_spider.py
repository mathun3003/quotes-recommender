from typing import Any, Final, Generator
import re

import scrapy
from scrapy.http import Response

from src.core.constants import QUOTE_NUM_LIKES


class GoodreadsSpider(scrapy.Spider):
    """Scraper to extract data from goodreads.com/quotes."""

    name = 'goodreads-spider'
    start_urls = [
        'https://www.goodreads.com/quotes'
    ]

    QUOTE_SELECTOR: Final[str] = 'dev.quote'
    QUOTE_DETAILS: Final[str] = 'quoteDetails'
    QUOTE_FOOTER: Final[str] = 'quoteFooter'
    QUOTE_AVATAR: Final[str] = 'quoteAvatar'
    QUOTE_TEXT: Final[str] = 'quoteText'
    QUOTE_LIKES: Final[str] = 'a.smallText::text'
    QUOTE_AUTHOR_OR_TITLE: Final[str] = 'authorOrTitle'
    NEXT_SELECTOR: Final[str] = ""  # TODO

    NUM_LIKES_REGEX: Final[str] = r'\b\d+\b'

    def parse(self, response: Response, **kwargs: Any) -> Generator:
        """
        Function to select data from an object.
        :param response: web response
        :param kwargs: additional kwargs
        :return:
        """
        for quote in response.css(self.QUOTE_SELECTOR):
            # TODO: yield quote
            yield {
                # TODO: raise exception if multiple values are found for regex matching
                # TODO: raise exception if result is not a a digit (i.e., string.isdigit() == False)
                QUOTE_NUM_LIKES: int(re.findall(self.NUM_LIKES_REGEX, response.css(self.QUOTE_LIKES).get())[0])
            }
            pass

        next_page = response.css(self.NEXT_SELECTOR).extract_first()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page)
            )

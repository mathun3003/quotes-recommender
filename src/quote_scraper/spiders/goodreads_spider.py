from typing import Any, Final, Generator
import re
import scrapy
from scrapy.http import Response
from src.core.constants import QUOTE_NUM_LIKES, QUOTE_TEXT, QUOTE_AUTHOR, QUOTE_TAGS


class GoodreadsSpider(scrapy.Spider):
    """Scraper to extract data from goodreads.com/quotes."""

    name = 'goodreads-spider'
    allowed_domains = ['goodreads.com'] 
    start_urls = [
        'https://www.goodreads.com/quotes'
    ]

    QUOTE_SELECTOR: Final[str] = 'div.quote'
    QUOTE_DETAILS: Final[str] = 'quoteDetails'
    QUOTE_FOOTER: Final[str] = 'quoteFooter'
    QUOTE_AVATAR: Final[str] = 'quoteAvatar'
    QUOTE_TEXT: Final[str] = 'quoteText'
    QUOTE_LIKES: Final[str] = 'a.smallText::text'
    QUOTE_AUTHOR_OR_TITLE: Final[str] = 'authorOrTitle'
    QUOTE_TAGS: Final[str] = 'div.greyText.smallText.left'
    NEXT_SELECTOR: Final[str] = "div.u-textAlignRight a.next_page"  # TODO

    NUM_LIKES_REGEX: Final[str] = r'\b\d+\b'

    def parse(self, response: Response, **kwargs: Any) -> Generator:
        """
        Function to select data from an object.
        :param response: web response
        :param kwargs: additional kwargs
        :return:
        """
        raw_quote_page = response.css(self.QUOTE_SELECTOR)

        for quote in raw_quote_page:

            yield {
                QUOTE_AUTHOR : quote.css(self.QUOTE_AUTHOR_OR_TITLE).get(),
                QUOTE_TEXT : quote.css(self.QUOTE_TEXT).get(),
                QUOTE_TAGS : quote.css(self.QUOTE_TAGS)[0].css('a::text').extract(),

                # TODO: raise exception if multiple values are found for regex matching
                # TODO: raise exception if result is not a a digit (i.e., string.isdigit() == False)
                QUOTE_NUM_LIKES: int(re.findall(self.NUM_LIKES_REGEX, response.css(self.QUOTE_LIKES).get())[0])
            }
            pass

        next_page = response.css(self.QUOTE_TAGS).attrib['href']
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page)
            )

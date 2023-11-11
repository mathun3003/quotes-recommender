import re
from typing import Any, Final, Generator

import scrapy
from scrapy.exceptions import StopDownload
from scrapy.http import Response

from src.core.constants import QUOTE_NUM_LIKES_KEY, QUOTE_FEED_URL_KEY, QUOTE_TEXT_KEY, QUOTE_AUTHOR_KEY, \
    QUOTE_AVATAR_KEY, QUOTE_TAGS_KEY, QUOTE_AVATAR_IMG_KEY


class GoodreadsSpider(scrapy.Spider):
    """Scraper to extract data from goodreads.com/quotes."""

    name = 'goodreads-spider'
    allowed_domains = ['goodreads.com'] 
    start_urls = [
        'https://www.goodreads.com/quotes'
    ]

    # quote data
    QUOTE_SELECTOR: Final[str] = 'div.quote'
    QUOTE_DETAILS: Final[str] = 'quoteDetails'
    QUOTE_FOOTER: Final[str] = 'quoteFooter'
    QUOTE_AVATAR: Final[str] = 'a.leftAlignedImage.quoteAvatar::attr(href)'
    QUOTE_AVATAR_IMG: Final[str] = 'a.leftAlignedImage.quoteAvatar img::attr(src)'
    QUOTE_TEXT: Final[str] = 'div.quoteText::text'
    QUOTE_LIKES: Final[str] = 'a.smallText::text'
    QUOTE_FEED: Final[str] = 'a.smallText::attr(href)'
    QUOTE_AUTHOR_OR_TITLE: Final[str] = 'span.authorOrTitle::text'
    QUOTE_TAGS: Final[str] = 'div.greyText.smallText.left a::text'

    # user data
    USER_LIKE_FEED: Final[str] = 'div.elementList'
    USER_URL: Final[str] = 'a.leftAlignedImage::attr(href)'

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
        for quote in response.css(self.QUOTE_SELECTOR):
            # extract number of likes, get the digit
            num_likes_list: list[str] = re.findall(self.NUM_LIKES_REGEX, quote.css(self.QUOTE_LIKES).get())
            # raise exception if multiple values are found for regex matching
            if len(num_likes_list) > 1:
                raise StopDownload(fail=True)
            # raise exception if result is not a a digit
            if not (num_likes := num_likes_list[0]).isdigit():
                raise ValueError('num_likes is not a digit. Failed to convert to int.')
            else:
                # cast string to int
                num_likes = int(num_likes)
            # extract like feed url
            quote_feed_list: list[str] = quote.css(self.QUOTE_FEED).extract()
            # raise exception if multiple values are found for this feed-link
            if len(quote_feed_list) > 1:
                raise StopDownload(fail=True)
            else:
                quote_feed = response.urljoin(quote_feed_list[0])
            # extract user data from a quote's feed
            # TODO: parse subpages
                # user_urls = scrapy.Request(quote_feed, callback=self.parse_subpage)

            # yield results
            yield {
                # extract author
                QUOTE_AUTHOR_KEY: quote.css(self.QUOTE_AUTHOR_OR_TITLE).get().strip(),
                # extract avatar jpg file from src
                QUOTE_AVATAR_IMG_KEY: quote.css(self.QUOTE_AVATAR_IMG).extract(),
                QUOTE_AVATAR_KEY: response.urljoin(quote.css(self.QUOTE_AVATAR).get()),
                # extract text
                QUOTE_TEXT_KEY: quote.css(self.QUOTE_TEXT).get().strip().lstrip('“').rstrip('”'),
                # yield number of likes
                QUOTE_NUM_LIKES_KEY: num_likes,
                # yield quote feed url
                QUOTE_FEED_URL_KEY: quote_feed,
                # yield quote tags
                QUOTE_TAGS_KEY: quote.css(self.QUOTE_TAGS).extract(),
                # TODO: USER_URLS_KEY: user_urls,
            }
        # get next page
        next_page = response.css(self.NEXT_SELECTOR).extract_first()
        # paginate if available
        if next_page:
            yield scrapy.Request(response.urljoin(next_page))

    def parse_subpage(self, response: Response) -> list[str]:
        """
        Function to crawl subpages from a starting url
        :param response: web response from scrapy
        :return: list user URLs
        """
        # fetch subpage feed
        subpage_feed = response.css(self.USER_LIKE_FEED)
        # return all user urls
        return [response.urljoin(user_url) for user_url in subpage_feed.css(self.USER_URL)]

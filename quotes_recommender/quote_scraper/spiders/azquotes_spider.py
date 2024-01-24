import re
from typing import Any, Final, Generator

import scrapy

from quotes_recommender.quote_scraper.constants import AZQUOTES_SPIDER_NAME
from quotes_recommender.quote_scraper.items import QuoteData, QuoteItem


class QuotesSpider(scrapy.Spider):
    """Scraper to extract data from azquotes.com/quotes."""

    name = AZQUOTES_SPIDER_NAME

    SELECTOR_AZ: Final[str] = "ul.authors a::attr(href)"
    SELECTOR_POP_AUTHORS: Final[str] = "div.profile.most-popular a::attr(href)"
    SELECTOR_QUOTE: Final[str] = "div.wrap-block"

    SELECTOR_ID: Final[str] = "a.title::attr(id)"
    SELECTOR_TEXT: Final[str] = "a.title::text"
    SELECTOR_AUTHOR: Final[str] = "a.title::attr(data-author)"
    SELECTOR_TAGS: Final[str] = "div.mytags a::text"
    SELECTOR_LIKES: Final[str] = "a.heart24::text"

    SELECTOR_NEXT_PAGE: Final[str] = "li.next a::attr(href)"

    QUOTE_ID_REGEX: Final[str] = r'\d+$'

    def start_requests(self):
        url = "https://www.azquotes.com/quotes/authors/a/"
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs: Any) -> Generator[QuoteItem, None, None]:
        """Scraping through the alphabet regarding quotes"""
        alphabet = response.css(self.SELECTOR_AZ).getall()
        for url in alphabet:
            yield response.follow(url=response.urljoin(url), callback=self.parse_pop_authors)

    def parse_pop_authors(self, response):
        """Scraping popular authors from every letter"""
        authors = response.css(self.SELECTOR_POP_AUTHORS).getall()

        for url in authors:
            yield response.follow(url=response.urljoin(url), callback=self.parse_author)

    def parse_author(self, response):
        """Scraping quotes from the author"""
        for quote in response.css(self.SELECTOR_QUOTE):
            id_attr = quote.css(self.SELECTOR_ID).get()
            id_number = re.search(self.QUOTE_ID_REGEX, id_attr).group() if id_attr else None

            if id_number is None:
                continue

            quote_result = QuoteItem.model_construct(
                id=int(id_number),
                data=QuoteData.model_construct(
                    author=quote.css(self.SELECTOR_AUTHOR).get(),
                    quote=quote.css(self.SELECTOR_TEXT).get(),
                    likes=int(quote.css(self.SELECTOR_LIKES).get()),
                    tags=[quote.lower() for quote in quote.css(self.SELECTOR_TAGS).getall()],
                ),
            )
            yield quote_result.model_dump()

        next_page = response.css(self.SELECTOR_NEXT_PAGE).get()
        if next_page:
            yield response.follow(url=response.urljoin(next_page), callback=self.parse_author)

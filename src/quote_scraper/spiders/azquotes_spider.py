import re
import scrapy
from typing import Final


class QuotesSpider(scrapy.Spider):
    name = "azquotes"

    SELECTOR_AZ: Final[str] = "ul.authors a::attr(href)"
    SELECTOR_POP_AUTHORS: Final[str] = "div.profile.most-popular a::attr(href)"
    SELECTOR_QUOTE: Final[str] = "div.wrap-block"

    SELECTOR_ID: Final[str] = "a.title::attr(id)"
    SELECTOR_TEXT: Final[str] = "a.title::text"
    SELECTOR_AUTHOR: Final[str] = "a.title::attr(data-author)"
    SELECTOR_TAGS: Final[str] = "div.mytags a::text"
    SELECTOR_LIKES: Final[str] = "a.heart24::text"

    SELECTOR_NEXT_PAGE: Final[str] = "li.next a::attr(href)"


    def start_requests(self):
        url = "https://www.azquotes.com/quotes/authors/a/"
        yield scrapy.Request(url = url, callback=self.parse_alphabet)
        

    def parse_alphabet(self, response):

        alpabeth = response.css(self.SELECTOR_AZ).getall()
        for url in alpabeth:
            yield response.follow(url=response.urljoin(url), callback = self.parse_pop_authors)

    def parse_pop_authors(self, response):

        authors = response.css(self.SELECTOR_POP_AUTHORS).getall()

        for url in authors:
            yield response.follow(url=response.urljoin(url), callback = self.parse_author)



    def parse_author(self, response):
        for quote in response.css(self.SELECTOR_QUOTE):

            id_attr = quote.css(self.SELECTOR_ID).get()
            id_number = re.search(r'\d+$', id_attr).group() if id_attr else None

            yield {
                "id": id_number,
                "text": quote.css(self.SELECTOR_TEXT).get(),
                "author": quote.css(self.SELECTOR_AUTHOR).get(),
                "tags": quote.css(self.SELECTOR_TAGS).getall(),
                "likes": quote.css(self.SELECTOR_LIKES).get()
            }

        next_page = response.css(self.SELECTOR_NEXT_PAGE).get()
        if next_page:
            yield response.follow(url=response.urljoin(next_page), callback = self.parse_author)


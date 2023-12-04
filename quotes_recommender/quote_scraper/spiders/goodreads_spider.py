import re
from typing import Any, Final, Generator

import scrapy
from scrapy.exceptions import StopDownload
from scrapy.http import Response

from quotes_recommender.quote_scraper.items import Quote, QuoteData, User


class GoodreadsSpider(scrapy.Spider):
    """Scraper to extract data from goodreads.com/quotes."""

    name = 'goodreads-spider'
    allowed_domains = ['goodreads.com']
    start_urls = ['https://www.goodreads.com/quotes']

    # CSS filter masks
    QUOTE_SELECTOR: Final[str] = 'div.quote'
    QUOTE_AVATAR: Final[str] = 'a.leftAlignedImage.quoteAvatar::attr(href)'
    QUOTE_AVATAR_IMG: Final[str] = 'a.leftAlignedImage.quoteAvatar img::attr(src)'
    QUOTE_TEXT: Final[str] = 'h1.quoteText::text'
    QUOTE_LIKES: Final[str] = 'span.uitext.smallText'
    QUOTE_FEED: Final[str] = 'a.smallText::attr(href)'
    QUOTE_AUTHOR_OR_TITLE: Final[str] = 'span.authorOrTitle::text'
    QUOTE_TAGS: Final[str] = 'div.greyText.smallText.left a::text'

    # User data
    USER_LIKE_FEED: Final[str] = 'div.elementList'
    USER_LIKED_LINK: Final[str] = 'a.userName::attr(href)'

    # Next page selector
    NEXT_SELECTOR: Final[str] = 'a.next_page::attr(href)'

    # Regex
    NUM_LIKES_REGEX: Final[str] = r'\b\d+\b'
    USER_LIKED_ID_PATTERN: Final[str] = r'/user\/show\/(\d+)-?([a-zA-Z0-9_-]+)'
    QUOTE_ID_PATTERN: Final[str] = r'/quotes/(\d+)-\w+'

    def parse(self, response: Response, **kwargs: Any) -> Generator[Quote, None, None]:
        """
        Function to select data from an object.
        :param response: web response from scrapy
        :param kwargs: additional kwargs
        :return: Generator object
        """
        for feed in response.css(self.QUOTE_FEED).extract():
            yield scrapy.Request(response.urljoin(feed), callback=self.parse_subpage)

        next_page = response.css(self.NEXT_SELECTOR).extract_first()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page))

    def extract_liked_user_id_name(self, to_be_extracted):
        """
        Function to extract the user_id and user_name via regexp. which
        returns the result in a dictionary format
        :param username: href link containing the ID and username information
        """
        match_user = re.match(self.USER_LIKED_ID_PATTERN, to_be_extracted)
        if match_user:
            user_id = match_user.group(1)
            user_name = match_user.group(2)
            return User(user_id=int(user_id), user_name=user_name)
        return None

    def parse_subpage(self, response: Response) -> Generator[dict, None, None]:
        """
        Function to crawl subpages from a starting url
        :param response: web response from scrapy
        :return: list user URLs
        """
        num_likes_list: list[str] = re.findall(self.NUM_LIKES_REGEX, response.css(self.QUOTE_LIKES).get())
        if len(num_likes_list) > 1:
            raise StopDownload(fail=True)
        if not num_likes_list[0].isdigit():
            raise ValueError('num_likes is not a digit. Failed to convert to int.')
        num_likes = int(num_likes_list[0])
        current_page_liking_users = [
            self.extract_liked_user_id_name(liked_user_link)
            for liked_user_link in response.css(self.USER_LIKED_LINK).extract()
        ]
        # Accumulate liking users across all pages
        liking_users = response.meta.get('liking_users', []) + current_page_liking_users
        next_user_page = response.css(self.NEXT_SELECTOR).extract_first()

        if next_user_page:  # "page=N" not in
            yield scrapy.Request(
                response.urljoin(next_user_page), callback=self.parse_subpage, meta={'liking_users': liking_users}
            )
        else:
            quote_id = re.search(self.QUOTE_ID_PATTERN, response.url)
            quote_result = Quote.model_construct(
                id=int(quote_id.group(1)) if quote_id else None,
                data=QuoteData.model_construct(
                    author_name=response.css(self.QUOTE_AUTHOR_OR_TITLE).get().strip(),
                    author_page=response.urljoin(response.css(self.QUOTE_AVATAR).get()),
                    avatar_img=response.css(self.QUOTE_AVATAR_IMG).extract_first(),
                    quote=response.css(self.QUOTE_TEXT).get().strip().lstrip('“').rstrip('”'),
                    num_likes=num_likes,
                    feed_url=response.url,
                    tags=response.css(self.QUOTE_TAGS).extract(),
                    liking_users=liking_users,
                ),
            )
            yield quote_result.model_dump()

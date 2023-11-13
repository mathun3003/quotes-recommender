# pylint: disable-all
# type: ignore

import logging

logger = logging.getLogger(__name__)


class GoodreadsToRedisPipeline:
    """Goodreads Scrapy Pipeline"""

    def process_item(self, item, spider):
        return item

    def open_spider(self) -> None:
        # TODO: establish document store connection
        return

# pylint: disable-all
# type: ignore

import logging
from itemadapter import ItemAdapter
logger = logging.getLogger(__name__)


class GoodreadsToRedisPipeline:
    """Goodreads Scrapy Pipeline"""

    def process_item(self, item, spider):
        print("Pipeline" + item['author'][0])
        adapter = ItemAdapter(item)
        return item

    def open_spider(self, spider) -> None:
        # TODO: establish document store connection
        return

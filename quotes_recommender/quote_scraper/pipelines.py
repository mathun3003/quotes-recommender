# pylint: disable=unused-argument
import logging

from quotes_recommender.ml_models.sentence_encoder import SentenceBERT
from quotes_recommender.quote_scraper.constants import GOODREADS_SPIDER_NAME
from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
from quotes_recommender.vector_store.vector_store_singleton import (
    QdrantVectorStoreSingleton,
)

logger = logging.getLogger(__name__)
model = SentenceBERT()


class QuotesToQdrantPipeline:
    """Scrapy Quotes Pipeline"""

    def __init__(self):
        """Initialize the pipeline."""
        self.vector_store = None
        self.user_store = None

    def process_item(self, item, spider):
        """Process a quote item and upsert the quote into the Qdrant vector store.
        :param item: An item containing quote data.
        :param spider: The Scrapy spider instance.
        """
        embeddings = model.encode_quote(item['data']['quote'])
        dups = self.vector_store.get_similarity_scores(query_embedding=embeddings)
        if dups:
            # Check for duplicates
            logger.warning("####### Duplicate found #######")
            return item
        # Check existence of author with image
        author_name = item['data']['author']
        sim_author = self.vector_store.get_entry_by_author(query_embedding=embeddings, author=author_name)
        avatar_image = sim_author.payload.get('avatar_img', None)
        item['data']['avatar_img'] = avatar_image
        self.vector_store.upsert_quotes([item], [embeddings])
        return item

    def open_spider(self, spider) -> None:
        """Open the spider and initialize the Qdrant vector store.
        :param spider: The Scrapy spider instance.
        """
        self.vector_store = QdrantVectorStoreSingleton().vector_store
        self.user_store = RedisUserStoreSingleton().user_store

    def close_spider(self, spider) -> None:
        """Close the spider.
        Registers user preferences in Redis of scraped users.
        :param spider: Scrapy spider instance
        :return None
        """
        # only run for goodreads spider
        if spider.name == GOODREADS_SPIDER_NAME:
            # init offset
            offset: int = 0
            # scroll all points
            while offset is not None:
                page_results, next_offset = self.vector_store.scroll_points(
                    payload_attributes=['liking_users'], limit=50, offset=offset
                )
                for point in page_results:
                    # get point ID
                    point_id = point.id
                    # collect each user ID
                    user_ids = [user.get('user_id', None) for user in point.payload.get('liking_users', None)]
                    # store user preferences
                    self.user_store.store_batch_likes(user_ids=user_ids, quote_id=point_id)

                # reset offset
                offset = next_offset

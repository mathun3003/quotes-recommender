import logging

from sentence_transformers import SentenceTransformer

from quotes_recommender.vector_store.vector_store_singleton import (
    QdrantVectorStoreSingleton,
)

logger = logging.getLogger(__name__)
model = SentenceTransformer('all-mpnet-base-v2')  # TODO Replace by its class


class QuotesToQdrantPipeline:
    """Scrapy Quotes Pipeline"""

    def __init__(self):
        """Initialize the pipeline."""
        self.vector_store = None

    def process_item(self, item, spider):  # pylint: disable=unused-argument
        """Process a quote item and upsert the quote into the Qdrant vector store.
        :param item (dict): An item containing quote data.
        :param spider: The Scrapy spider instance.
        """
        embeddings = model.encode(item['data']['quote'])
        dups = self.vector_store.get_similarity_scores(embeddings)

        if dups:
            logger.info("###############################")
            logger.warning("####### Duplicate found #######")
            logger.info(f"New: {item['data']['quote']}")
            logger.info(f"Exists: {dups}")
            logger.info("###############################")
        else:
            logger.info("###############################")
            logger.info("NO Dups found")

        # self.vector_store.upsert_quotes([item], [embeddings])
        return item

    def open_spider(self, spider) -> None:  # pylint: disable=unused-argument
        """Open the spider and initialize the Qdrant vector store.
        :param spider: The Scrapy spider instance.
        """
        self.vector_store = QdrantVectorStoreSingleton().vector_store

    def close_spider(self, spider) -> None:  # pylint: disable=unused-argument
        """Close the spider.
        Optionally performs cleanup operations when the spider is closed.
        :param The Scrapy spider instance.
        """
        # Optionally, add cleanup code here

import logging
from sentence_transformers import SentenceTransformer
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

logger = logging.getLogger(__name__)
model = SentenceTransformer('all-mpnet-base-v2')


class GoodreadsToQdrantPipeline:
    """Goodreads Scrapy Pipeline"""

    def __init__(self):
        """Initialize the pipeline."""
        self.vector_store = None

    def process_item(self, item, spider): # pylint: disable=unused-argument
        """Process a Goodreads item and upsert the quote into the Qdrant vector store.
        :param item (dict): A Goodreads item containing quote data.
        :param spider: The Scrapy spider instance.
        """
        embeddings = model.encode(item['data']['quote'])
        self.vector_store.upsert_quotes([item], [embeddings])
        return item

    def open_spider(self, spider) -> None: # pylint: disable=unused-argument
        """Open the spider and initialize the Qdrant vector store.
        :param spider: The Scrapy spider instance.
        """
        self.vector_store = QdrantVectorStoreSingleton().vector_store

    def close_spider(self, spider) -> None: # pylint: disable=unused-argument
        """Close the spider.
        Optionally performs cleanup operations when the spider is closed.
        :param The Scrapy spider instance.
        """
        # Optionally, add cleanup code here

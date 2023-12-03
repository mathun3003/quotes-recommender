from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
model = SentenceTransformer('all-mpnet-base-v2')

class GoodreadsToQdrantPipeline:
    """Goodreads Scrapy Pipeline"""

    def process_item(self, item, spider):
        embeddings = model.encode(item['data']['quote'])
        self.vector_store.upsert_quotes([item], [embeddings])
        return item

    def open_spider(self, spider) -> None:
        # Vector Store
        self.vector_store = QdrantVectorStoreSingleton().vector_store
        return

import logging
import json

from quotes_recommender.core.constants import TAG_MAPPING_PATH
from quotes_recommender.ml_models.sentence_encoder import SentenceBERT
from quotes_recommender.vector_store.vector_store_singleton import (
    QdrantVectorStoreSingleton,
)

logger = logging.getLogger(__name__)
model = SentenceBERT()


class QuotesToQdrantPipeline:
    """Scrapy Quotes Pipeline"""

    file = open(TAG_MAPPING_PATH, 'r')
    tag_mappings = json.load(file)

    def __init__(self):
        """Initialize the pipeline."""
        self.vector_store = None

    def process_item(self, item, spider):  # pylint: disable=unused-argument
        """Process a quote item and upsert the quote into the Qdrant vector store.
        :param item (dict): An item containing quote data.
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
        #Check for tag mappings
        mapped_tags = [self.tag_mappings.get(tag, tag) for tag in item['data']['tags']]
        item['data']['tags'] = list(set(mapped_tags))
        self.vector_store.upsert_quotes([item], [embeddings])
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
    file.close()

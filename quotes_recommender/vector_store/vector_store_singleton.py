from typing import Any

from quotes_recommender.utils.qdrant import QdrantConfig
from quotes_recommender.utils.singleton import Singleton
from quotes_recommender.vector_store.vector_store_qdrant import QdrantVectorStore


class QdrantDocumentStoreSingleton(Singleton):  # pylint: disable=too-few-public-methods
    """Singleton class for Qdrant database"""

    def init(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Init qdrant vector store"""

        self.vector_store = QdrantVectorStore(QdrantConfig(
            
        ))

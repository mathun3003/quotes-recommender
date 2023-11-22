from typing import Any

from src.utils.singleton import Singleton
from src.vector_store.vector_store_qdrant import QdrantVectorStore


class RedisDocumentStoreSingleton(Singleton):  # pylint: disable=too-few-public-methods
    """Singleton class for Qdrant database"""

    def init(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Init qdrant vector store"""

        self.vector_store = QdrantVectorStore(api_key="")

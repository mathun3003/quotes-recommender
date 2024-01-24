from typing import Any

from utils.qdrant import QdrantConfig
from utils.singleton import Singleton
from vector_store.vector_store_qdrant import QdrantVectorStore


class QdrantVectorStoreSingleton(Singleton):
    """Singleton class for Qdrant database"""

    def init(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Init qdrant vector store"""

        self.vector_store = QdrantVectorStore(QdrantConfig())

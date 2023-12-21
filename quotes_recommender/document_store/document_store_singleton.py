from typing import Any

from quotes_recommender.document_store.document_store_redis import RedisDocumentStore
from quotes_recommender.utils.redis import RedisConfig
from quotes_recommender.utils.singleton import Singleton


class RedisDocumentStoreSingleton(Singleton):  # pylint: disable=too-few-public-methods
    """Singleton class for Redis stack"""

    def init(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Init redis document store"""

        # get specified db index, choose 0 as default
        self.db_index = kwargs.get('db_name', 0)
        self.document_store = RedisDocumentStore(redis_config=RedisConfig())
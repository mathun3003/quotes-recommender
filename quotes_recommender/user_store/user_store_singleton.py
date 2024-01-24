from typing import Any

from user_store.user_store_redis import RedisUserStore
from utils.redis import RedisConfig
from utils.singleton import Singleton


class RedisUserStoreSingleton(Singleton):
    """Singleton class for Redis stack"""

    def init(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Init redis document store"""

        # get specified db index, choose 0 as default
        self.db_index = kwargs.get('db_name', 0)
        self.user_store = RedisUserStore(redis_config=RedisConfig())

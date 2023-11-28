import logging
from typing import Generator, Optional

import redis

from src.core.constants import TXT_ENCODING
from src.document_store.constants import DEFAULT_BATCH_SIZE
from src.utils.redis import RedisConfig

logger = logging.getLogger(__name__)


class RedisDocumentStore:  # pylint: disable=too-few-public-methods
    """Redis document store class for inserting, querying, and searching tasks"""

    def __init__(self, redis_config: RedisConfig, ping: bool = True) -> None:
        """
        Create a redis document store instance
        :param redis_config: RedisConfig object
        :param ping: ping connection
        """
        # raise error of no host or port was provided
        if redis_config.redis_url.host is None or redis_config.port is None:
            raise ConnectionError("No Redis host or port specified.")
        # get redis instance
        self.redis_instance = redis.Redis(
            host=str(redis_config.host),
            port=int(redis_config.port),
            db=redis_config.db,
            password=redis_config.password,
            username=redis_config.user,
        )
        # test connection
        if ping:
            if not self.redis_instance.ping():
                raise ConnectionError("Cannot connect to Redis.")
            logger.info('Connected to Redis.')

    def scan(
        self, search_str: str, batch_size: int = DEFAULT_BATCH_SIZE, type_filter: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Use SCAN_ITER function to receive key-value results for a search string
        :param search_str:
        :param batch_size:
        :param type_filter:
        :return: Generator object yielding batched results

        References:
            - https://redis.io/docs/interact/search-and-query/query/#mapping-common-sql-predicates-to-search-and-query
        """
        for key in self.redis_instance.scan_iter(search_str, batch_size, type_filter):
            yield key.decode(TXT_ENCODING)

import logging
from typing import Optional, Any, Mapping

import redis

from quotes_recommender.core.constants import TXT_ENCODING
from quotes_recommender.core.models import UserPreference
from quotes_recommender.user_store.constants import DEFAULT_BATCH_SIZE
from quotes_recommender.utils.redis import RedisConfig

logger = logging.getLogger(__name__)


class RedisUserStore:
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
        self._client = redis.Redis(
            host=str(redis_config.host),
            port=int(redis_config.port),
            db=redis_config.db,
            password=redis_config.password,
            username=redis_config.user,
        )
        # test connection
        if ping:
            if not self._client.ping():
                raise ConnectionError("Cannot connect to Redis.")
            logger.info('Connected to Redis.')

    def scan(
            self,
            search_str: Optional[str] = None,
            batch_size: int = DEFAULT_BATCH_SIZE,
            type_filter: Optional[str] = None,
            cursor: int = 0,
    ) -> list[Any]:
        """
        Use SCAN function to receive key-value results for a search string or type filter.
        :param search_str: Search string.
        :param batch_size: Number of returned results.
        :param type_filter: Filter by redis data types.
        :param cursor: Offset where to start searching.
        :return: Generator object yielding batched results

        References:
            - https://redis.io/docs/interact/search-and-query/query/#mapping-common-sql-predicates-to-search-and-query
        """
        hits = self._client.scan(cursor=cursor, match=search_str, count=batch_size, _type=type_filter)
        return [hit.decode(TXT_ENCODING) for hit in hits[1]]

    def get_user_credentials(self) -> Mapping[str, Any]:
        """
        Get all registered users and their credentials from redis.
        :return: usernames mapped to their corresponding credentials.
        """
        # init dict for credentials
        user_credentials: Mapping[str, Any] = {}
        # get all usernames
        usernames: list[str] = self.scan(type_filter='hash')
        # get credentials for every username
        for username in usernames:
            user_credentials[username] = {
                key.decode(TXT_ENCODING): value.decode(TXT_ENCODING)
                for key, value in self._client.hgetall(username).items()
            }
        return user_credentials

    def register_user(self, username: str, credentials: Mapping[str, str]) -> bool:
        """
        Creates a new hash for a new user
        :param username: The username of the new user.
        :param credentials: The credentials of the new user.
        :return: True if all fields were added, else False.
        """
        hash_key: str = f"user:{username}:credentials"
        added_fields = self._client.hset(name=hash_key, mapping=credentials)
        return True if added_fields == len(credentials) else False

    def get_user_preferences(self, username: str) -> list[UserPreference]:
        """
        Returns all preferences for a given user.
        :param username: The username of the logged-in user.
        :return: The list of user preferences.
        """
        base_hash_key: str = f"user:{username}:preferences"
        like_hash_key: str = f"{base_hash_key}:like"
        dislike_hash_key: str = f"{base_hash_key}:dislike"
        # TODO: convert to pipeline operation: https://stackoverflow.com/questions/19079441/get-multiple-sets
        likes = self._client.smembers(name=like_hash_key)
        dislikes = self._client.smembers(name=dislike_hash_key)
        return zip(
            [UserPreference(id=member, like=True) for member in likes],
            [UserPreference(id=member, like=False) for member in dislikes]
        )

    def set_user_preferences(self, username: str, preferences: list[UserPreference]) -> bool:
        """
        Sets the preferences of the logged-in user.
        :param username: The username of the logged-in user.
        :param preferences: The list of user preferences.
        :return: Whether operation was successful
        """
        # split user preferences up into likes/dislikes
        likes, dislikes = [], []
        for preference in preferences:
            if preference.like:
                likes.append(preference.id)
            elif not preference.like:
                dislikes.append(preference.id)
            else:
                raise ValueError(
                    f"User preference with id {preference.id} has wrong value for like attr: {preference.like}"
                )
        # build base hash key
        # TODO: create constants for hash keys
        base_hash_key: str = f"user:{username}:preferences"
        like_hash_key: str = f"{base_hash_key}:like"
        dislike_hash_key: str = f"{base_hash_key}:dislike"
        # TODO: convert to pipeline operation: https://stackoverflow.com/questions/19079441/get-multiple-sets
        num_likes_added: int = self._client.sadd(like_hash_key, *likes)
        num_dislikes_added: int = self._client.sadd(dislike_hash_key, *dislikes)
        # TODO: remove IDs from sets that are not part of the input list
        # TODO: rename function to 'sync_user_preferences'
        return True if ((num_likes_added + num_dislikes_added) == len(preferences)) else False
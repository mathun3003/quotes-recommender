import itertools
import logging
from typing import Optional, Any, Mapping

import redis

from quotes_recommender.core.constants import TXT_ENCODING
from quotes_recommender.core.models import UserPreference
from quotes_recommender.user_store.constants import DEFAULT_BATCH_SIZE
from quotes_recommender.user_store.models import PreferenceKey
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
        if redis_config.host is None or redis_config.port is None:
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

    def get_user_preferences(self, username: str) -> Optional[list[UserPreference]]:
        """
        Returns all preferences for a given user.
        :param username: The username of the logged-in user.
        :return: The list of user preferences.
        """
        # create hash keys from username
        hash_keys = PreferenceKey(username=username)
        likes = self._client.smembers(name=hash_keys.like_key)
        dislikes = self._client.smembers(name=hash_keys.dislike_key)
        return (
                [UserPreference(id=member, like=True) for member in likes] +
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
        # build hash keys
        hash_keys = PreferenceKey(username=username)
        if likes:
            # sync likes
            self._sync_preferences(
                preferences=likes, src_hash_key=hash_keys.dislike_key, dst_hash_key=hash_keys.like_key
            )
        if dislikes:
            # sync dislikes
            self._sync_preferences(
                preferences=dislikes, src_hash_key=hash_keys.like_key, dst_hash_key=hash_keys.dislike_key
            )
        # TODO: return True if everything went else False
        return True

    def _sync_preferences(self, preferences: list[int], src_hash_key: str, dst_hash_key: str) -> None:
        """
        Synchronizes the preferences for the logged-in user in order to keep mutually exclusiveness of
        preferences in Redis.
        :param preferences: Either like or dislike IDs.
        :param src_hash_key: Hash key of the source/opposite set of provided preferences
        (i.e., hash key for dislikes if likes were provided).
        :param dst_hash_key: Hash key of the destination/target set of provided preferences
        (i.e., hash key for likes if likes were provided).
        :return: True if any transaction was successful and false if not.
        """
        with self._client.pipeline() as pipe:
            # if at least a single preference is already a member of the opposite set
            # (i.e., if at least a single 1 is contained)
            if any((index_list := list(map(int, self._client.smismember(src_hash_key, preferences))))):
                # move it to the correct set (i.e, src set)
                for dislike in list(itertools.compress(preferences, index_list)):
                    pipe.smove(src_hash_key, dst_hash_key, dislike)
            # add remaining preferences (i.e., those with an index of 0) to the corresponding set (i.e., src set)
            # therefore, invert index_list items (0 -> 1, 1 -> 0)
            if any((inverted_index_list := [not idx for idx in index_list])):
                pipe.sadd(dst_hash_key, *list(itertools.compress(preferences, inverted_index_list)))
            pipe.execute()
            pipe.close()

    def delete_user_preference(self, hash_key: str, member: int) -> Optional[bool]:
        """
        Removes a member from a set if it is part of it.
        :param hash_key: The key of the set.
        :param member: The identifier of the member,
        :return: Whether the operation was successful.
        """
        # check if the member exists in the given set
        if self._client.sismember(hash_key, member):
            result = self._client.srem(hash_key, member)
            return True if result != 0 else False

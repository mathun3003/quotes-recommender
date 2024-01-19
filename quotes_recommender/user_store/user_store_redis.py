import itertools
import logging
from typing import Any, Mapping, Optional, Sequence

import redis

from quotes_recommender.core.constants import TXT_ENCODING
from quotes_recommender.user_store.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_SIMILAR_PREFERENCE,
)
from quotes_recommender.user_store.models import CredentialsKey, PreferenceKey
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

    def get_all_users(
        self,
        search_str: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> dict[str, list[int]]:
        """
        Use SSCAN function to receive key-value results for a search string.
        :param search_str: Search string.
        :param batch_size: Number of returned results.
        :return: Dictionary mapping each key to a list of its members

        References:
            - https://redis-py.readthedocs.io/en/stable/#redis.Redis.scan_iter
        """
        users_data = {}
        for key in self._client.scan_iter(match=search_str, count=batch_size):
            key_str = key.decode(TXT_ENCODING)
            members = [int(member.decode(TXT_ENCODING)) for member in self._client.smembers(key_str)]
            users_data[key_str] = members

        return users_data

    def get_most_similar_user(self, user: str, threshold: int = DEFAULT_SIMILAR_PREFERENCE) -> list[str]:
        """
        Get users with similar preferences to the given user.

        :param user: The username of the user for whom similar users are to be found.
        :param threshold: Minimum number of common preferences to consider a user similar.
        :return: List of usernames for users with similar preferences.
        """
        current_user_preferences = self.get_user_preferences(user)[0]
        all_users = self.get_all_users()
        similar_users = []

        for other_user, data in all_users.items():
            intersection_list = list(set(current_user_preferences).intersection(data))
            if len(intersection_list) >= threshold:
                similar_users.append(other_user)

        return similar_users

    def get_user_credentials(self) -> dict[Any, Any]:
        """
        Get all registered users and their credentials from redis.
        :return: usernames mapped to their corresponding credentials.
        """
        # init dict for credentials
        user_credentials: dict[Any, Any] = {}
        # get all usernames
        credential_hashes: list[str] = self.scan(type_filter='hash')
        # get credentials for every username
        for credential_hash in credential_hashes:
            # extract username from hash key
            username: str = credential_hash.split(':')[1]
            user_credentials[username] = {
                # get corresponding credentials
                key.decode(TXT_ENCODING): value.decode(TXT_ENCODING)
                for key, value in self._client.hgetall(credential_hash).items()
            }
        return user_credentials

    def register_user(self, username: str, credentials: Mapping[str | bytes, bytes | float | int | str]) -> bool:
        """
        Creates a new hash for a new user
        :param username: The username of the new user.
        :param credentials: The credentials of the new user.
        :return: True if all fields were added, else False.
        """
        hash_key: str = CredentialsKey(username=username).key
        added_fields = self._client.hset(name=hash_key, mapping=credentials)
        return added_fields == len(credentials)

    def get_user_preferences(self, username: str) -> tuple[list[int], list[int]]:
        """
        Returns all preferences for a given user.

        Unpack result to receive likes and dislikes separately:
        like_ids, dislike_ids = user_store.get_user_preferences(...)
        :param username: The username of the logged-in user.
        :return: Lists of liked and disliked quotes' IDs.
        """
        # create hash keys from username
        hash_keys = PreferenceKey(username=username)
        likes = self._client.smembers(name=hash_keys.like_key)
        dislikes = self._client.smembers(name=hash_keys.dislike_key)
        # return encoded likes and dislikes
        return (
            list(map(lambda x: int(x.decode(TXT_ENCODING)), likes)),
            list(map(lambda x: int(x.decode(TXT_ENCODING)), dislikes)),
        )

    def set_user_preferences(
        self,
        username: str,
        likes: Optional[Sequence[int | str] | set[int | str]] = None,
        dislikes: Optional[Sequence[int | str] | set[int | str]] = None,
    ) -> bool:
        """
        Sets the preferences of the logged-in user.
        :param username: The username of the logged-in user.
        :param likes: List of quote IDs of liked quotes.
        :param dislikes: List of quote IDs of disliked quotes.
        :return: Whether operation was successful
        """
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
        # TODO: return True if everything went right else False
        return True

    def _sync_preferences(
        self, preferences: Sequence[int | str] | set[int | str], src_hash_key: str, dst_hash_key: str
    ) -> None:
        """
        Synchronizes the preferences for the logged-in user in order to keep mutually exclusiveness of
        preferences in Redis.
        :param preferences: Either like or dislike IDs.
        :param src_hash_key: Hash key of the source/opposite set of provided preferences
        (i.e., hash key for dislikes if likes were provided).
        :param dst_hash_key: Hash key of the destination/target set of provided preferences
        (i.e., hash key for likes if likes were provided).
        :return: None
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

    def delete_user_preference(
        self,
        username: str,
        likes: Optional[Sequence[int | str] | set[int | str]] = None,
        dislikes: Optional[Sequence[int | str] | set[int | str]] = None,
    ) -> Optional[bool]:
        """
        Removes a member from a set if it is part of it.
        :param username: The username of the logged-in user.
        :param likes: List of quote IDs of liked quotes.
        :param dislikes: List of quote IDs of disliked quotes.
        :return: Whether the operation was successful.
        """
        if likes and dislikes:
            raise ValueError('Can only specify likes or dislikes to delete, not both.')
        if (not likes) and (not dislikes):
            raise ValueError('Either specify likes or dislikes.')
        # construct corresponding hash key
        hash_key: str = (
            PreferenceKey(username=username).like_key if likes else PreferenceKey(username=username).dislike_key
        )
        # check if the member exists in the given set
        if self._client.smismember(hash_key, likes if likes else dislikes):
            result = self._client.srem(hash_key, *likes if likes else dislikes)  # type: ignore
            return result != 0
        return False

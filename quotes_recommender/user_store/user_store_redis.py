import itertools
import logging
import operator
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

    def _get_all_users(
        self,
        search_str: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> dict[str, list[int]]:
        """
        Receive key-value results for all users.
        :param search_str: Search string.
        :param batch_size: Number of returned results.
        :return: Dictionary mapping each username to a list of its set members

        References:
            - https://redis-py.readthedocs.io/en/stable/#redis.Redis.scan_iter
        """
        # init user data dict
        users_data = {}
        # iterate over each key matching the search string
        for key in self._client.scan_iter(match=search_str, count=batch_size):
            # decode key
            key_str = key.decode(TXT_ENCODING)
            # parse set members
            members = list(map(lambda member: int(member.decode(TXT_ENCODING)), self._client.smembers(key_str)))
            # get username from hash key
            username: str = key_str.split(':')[1]
            # add results to users data dict
            users_data[username] = members
        # return dict
        return users_data

    def get_most_similar_user(self, user: str, threshold: int = DEFAULT_SIMILAR_PREFERENCE) -> Optional[str]:
        """
        Get user with most similar preferences to the given user based on set intersection.
        :param user: The username of the user for whom similar users are to be found.
        :param threshold: Minimum number of common preferences to consider a user similar.
        :return: username for user with most similar preferences.
        """
        current_user_preferences = self.get_user_preferences(user)[0]
        all_users = self._get_all_users(search_str='user:*:preferences:like')
        similar_users = {}
        for other_user, data in all_users.items():
            intersection_list = list(set(current_user_preferences).intersection(data))
            if (user != other_user) and (len(intersection_list) >= threshold):
                similar_users[other_user] = data
        # if no similar users were found
        if not similar_users:
            return None
        # get user with the greatest set intersection
        most_similar_user = max(similar_users.items(), key=operator.itemgetter(1))[0]
        # most_similar_user = next(iter(max_user))
        # return username of most similar user
        return most_similar_user

    def get_user_credentials(self) -> dict[Any, Any]:
        """
        Get all registered users and their credentials from redis.
        :return: usernames mapped to their corresponding credentials.
        """
        # init dict for credentials
        user_credentials: dict[Any, Any] = {}
        # get credentials for every username
        for credential_hash in self._client.scan_iter(match='user:*:credentials', _type='hash'):
            # extract username from hash key
            username: str = credential_hash.decode(TXT_ENCODING).split(':')[1]
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

    def store_likes_batch(self, user_ids: Sequence[str], quote_id: str | int) -> None:
        """
        Stores the likes of several users for a given quote ID in Redis.
        :param user_ids: List of user IDs.
        :param quote_id: The ID of the quote (point) which should be stored for each user.
        :return: None
        """
        # create hash keys from user ids
        hash_keys: list[str] = [PreferenceKey(username=str(user_id)).like_key for user_id in user_ids]
        with self._client.pipeline() as pipe:
            for hash_key in hash_keys:
                pipe.sadd(hash_key, quote_id)
            pipe.execute()
            pipe.close()

    def clean_up_user_store(self, threshold: int = DEFAULT_SIMILAR_PREFERENCE) -> None:
        """
        Cleans the user store by removing all sets having less than a specified number of elements.
        :param threshold: The minimum set size
        :return: None
        """
        # get all user sets
        user_data_all = self._get_all_users(search_str='user:*:preferences:like')
        # get registered users
        registered_users = list(self.get_user_credentials().keys())
        user_data_filtered = {key: value for key, value in user_data_all.items() if key not in registered_users}
        with self._client.pipeline() as pipe:
            # iter over all sets (except the one for the registered users)
            for username, like_set in user_data_filtered.items():
                # if the user has less than N likes
                if len(like_set) < threshold:
                    # re-construct hask key
                    hash_key: str = PreferenceKey(username=username).like_key
                    # delete key
                    pipe.delete(hash_key)
            pipe.execute()
            pipe.close()

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

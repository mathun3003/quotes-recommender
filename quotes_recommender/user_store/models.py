from pydantic import Field

from quotes_recommender.core.models import ForbidExtraModel


class BaseKey(ForbidExtraModel):
    """Base class defining a Redis hash key"""

    username: str = Field(description="The username of the logged-in user.")


class CredentialsKey(BaseKey):
    """Class defining a Redis hash key for user credentials."""

    @property
    def key(self) -> str:
        """
        Returning the Redis hash key containing the username.
        :return: Credentials Redis hash key
        """
        return f"user:{self.username}:credentials"


class PreferenceKey(BaseKey):
    """Class defining a Redis hash key for user preferences"""

    @property
    def _base_key(self) -> str:
        """
        Returning the Redis hash key containing the username.
        :return: Base Redis hash key.
        """
        return f"user:{self.username}:preferences"

    @property
    def like_key(self) -> str:
        """
        Returns a Redis Hash Key for a user's like.
        :return: Redis preference hash key.
        """
        return f"{self._base_key}:like"

    @property
    def dislike_key(self) -> str:
        """
        Returns a Redis Hash Key for a user's dislike.
        :return: Redis preference hash key.
        """
        return f"{self._base_key}:dislike"

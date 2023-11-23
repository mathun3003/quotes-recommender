from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

from quotes_recommender.core.constants import TXT_ENCODING


class RedisConfig(BaseSettings):
    """Redis settings config"""

    model_config = SettingsConfigDict(env_prefix='REDIS_', env_file_encoding=TXT_ENCODING)
    url: str = Field(default=None)
    user: str = Field(default=None)
    password: str = Field(min_length=0, default=None)
    host: str = Field(min_length=0, default='0.0.0.0')
    port: int = Field(min_length=0, default='6379')
    db: int = Field(ge=0, default=0)

    @property
    def redis_url(self) -> URL:
        """
        Returns yarl URL object of Redis string url.
        :return: yarl url object
        """
        return URL(self.url)

    @property
    def redis_url_with_creds(self) -> URL:
        """
        Returns yarl URL object of Redis string url with credentials
        :return: yarl URl object with credentials
        """
        return (
            self.redis_url.with_user(self.user).with_password(self.password).with_host(self.host).with_port(self.port)
        )

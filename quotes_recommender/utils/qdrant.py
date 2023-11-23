from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from quotes_recommender.core.constants import TXT_ENCODING


class QdrantConfig(BaseSettings):
    """Qdrant settings config"""

    model_config = SettingsConfigDict(env_prefix='QDRANT_', env_file_encoding=TXT_ENCODING)
    host: str = Field(min_length=0, default='0.0.0.0')
    port: int = Field(default='6333')
    api_key: Optional[str] = Field(..., description="API-Key of the database.")

    @property
    def http_url(self) -> str:
        return f'http://{self.host}:{self.port}'

    @property
    def https_url(self) -> str:
        return f'https://{self.host}:{self.port}'

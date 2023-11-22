import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Redis document store class for inserting, querying, and searching tasks"""

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key

    def get_content_based_recommendation(self) -> Any:
        """Get content-based recommendations"""
        # TODO

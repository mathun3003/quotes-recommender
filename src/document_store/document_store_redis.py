import logging

logger = logging.getLogger(__name__)


class RedisDocumentStore:
    """Redis document store class for inserting, querying, and searching tasks"""

    def __init__(self, db_name: int) -> None:
        self.redis = None

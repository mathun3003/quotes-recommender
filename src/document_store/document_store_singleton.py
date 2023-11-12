from src.utils.singleton import Singleton


class RedisDocumentStoreSingleton(Singleton):
    """Singleton class for Redis stack"""

    def init(self, *args, **kwds) -> None:  # pylint: disable=unused-argument
        """Init redis document store"""

        # get specified db index, choose 0 as default
        self.db_index = kwds.get('db_name', 0)
        self.document_stoer = RedisDocumentStore(
            db_name=self.db_index  # pylint: disable=attribute-defined-outside-init
        )
    
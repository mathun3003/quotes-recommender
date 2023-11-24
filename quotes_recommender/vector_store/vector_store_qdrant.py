import logging
from typing import Any
import requests

import numpy as np
import numpy.typing as npt
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import VectorParams, Distance, PointStruct, UpdateStatus
from requests import HTTPError

from quotes_recommender.quote_scraper.items import QuoteItem
from quotes_recommender.utils.qdrant import QdrantConfig
from quotes_recommender.vector_store.constants import DEFAULT_QUOTE_COLLECTION, DEFAULT_PAYLOAD_INDEX, \
    DEFAULT_EMBEDDING_SIZE

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Redis document store class for inserting, querying, and searching tasks"""

    def __init__(self, qdrant_config: QdrantConfig, on_disk: bool = True, timeout: float = 60.0, ping: bool = True,
                 use_https: bool = False) -> \
            None:
        """
        Init Qdrant vector store instance.
        :param qdrant_config: QdrantConfig instance.
        :param on_disk: Whether to store payloads on disk.
        :param timeout: Timeout after which the client declares a connection as aborted.
        :param ping: Whether to test the connection to Qdrant.
        """
        self.on_disk_payload = on_disk

        # raise error of no host or port was provided
        if qdrant_config.host is None or qdrant_config.port is None:
            raise ConnectionError("No Qdrant host or port specified.")

        # get qdrant client
        self.client = QdrantClient(
            url=qdrant_config.https_url if use_https else qdrant_config.http_url,
            api_key=qdrant_config.api_key,
            timeout=timeout
        )

        # test connection
        if ping:
            # use workaround instead of service API as it contains a bug
            response = requests.get(f'{qdrant_config.https_url if use_https else qdrant_config.http_url}/healthz')
            if not response.ok:
                raise ConnectionError("Cannot connect to Qdrant. Is the database running?")
            logger.info('Connected to Qdrant.')

        try:
            # try to fetch default collection
            self.client.get_collection(DEFAULT_QUOTE_COLLECTION)
        except UnexpectedResponse:
            self._create_default_collection_and_index()

    def _create_default_collection_and_index(self) -> None:
        """
        Creates a default collection and payload index.
        :return: None
        """
        # TODO: create HNSW index (?)
        # create default collection
        if not self.client.create_collection(
                collection_name=DEFAULT_QUOTE_COLLECTION,
                on_disk_payload=self.on_disk_payload,
                vectors_config=VectorParams(
                    size=DEFAULT_EMBEDDING_SIZE,
                    distance=Distance.COSINE,
                    on_disk=self.on_disk_payload
                )
        ):
            raise ConnectionError(f'Could not create {DEFAULT_QUOTE_COLLECTION} collection.')
        # create default index
        if not self.client.create_payload_index(
                collection_name=DEFAULT_QUOTE_COLLECTION,
                field_name=DEFAULT_PAYLOAD_INDEX,
                field_type='keyword'
        ):
            raise ConnectionError(f'Could not create {DEFAULT_PAYLOAD_INDEX} index on {DEFAULT_QUOTE_COLLECTION}.')

    def upsert_quotes(self, quotes: list[QuoteItem], embeddings: list[npt.NDArray[np.float64]],
                      collection_name: str = DEFAULT_QUOTE_COLLECTION, wait: bool = True) -> UpdateStatus:
        """
        Method to upsert quotes to the vector store.
        :param quotes: list of QuoteItems
        :param embeddings: list of quote embeddings
        :param collection_name: where to store the quotes.
        :param wait: Whether to wait for committed changes.
        :return: Status of the upsert request.
        """
        # construct points from inputs
        points = [PointStruct(
            id=quote.get('id'),
            vector=embedding,
            payload=quote.get('data'),
        ) for quote, embedding in zip(quotes, embeddings)]
        # upsert points
        response = self.client.upsert(
            collection_name=collection_name,
            points=points,
            wait=wait
        )
        # if upsert was not successful, raise an error
        if response.status.startswith('4'):
            raise HTTPError(f'Failing to upsert points: {response.status}')
        # return status
        return response.status

    def get_content_based_recommendation(self) -> Any:
        """Get content-based recommendations"""
        # TODO

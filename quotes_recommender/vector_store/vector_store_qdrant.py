import logging
from typing import Sequence, Optional, Any

import numpy as np
import numpy.typing as npt
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Distance, PointStruct, UpdateStatus, VectorParams, ScoredPoint, Filter, \
    FieldCondition, MatchAny, PayloadSelectorInclude, Record, RecommendStrategy
from requests import HTTPError

from quotes_recommender.quote_scraper.items import QuoteItem, ExtendedQuoteData
from quotes_recommender.utils.qdrant import QdrantConfig
from quotes_recommender.vector_store.constants import (
    DEFAULT_EMBEDDING_SIZE,
    DEFAULT_PAYLOAD_INDEX,
    DEFAULT_QUOTE_COLLECTION,
)

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Redis document store class for inserting, querying, and searching tasks"""

    def __init__(
            self, qdrant_config: QdrantConfig, on_disk: bool = True, timeout: float = 60.0, ping: bool = True
    ) -> None:
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
            url=qdrant_config.https_url if qdrant_config.use_https else qdrant_config.http_url,
            api_key=qdrant_config.api_key,
            timeout=timeout,
        )

        # test connection
        if ping:
            try:
                # use workaround instead of service API as it contains a bug
                response = requests.get(
                    f'{qdrant_config.https_url if qdrant_config.use_https else qdrant_config.http_url}/healthz', timeout=60
                )
            except ConnectionError as exc:
                logger.error("Cannot connect to Qdrant. Is the database running?")
                raise exc
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
                    size=DEFAULT_EMBEDDING_SIZE, distance=Distance.COSINE, on_disk=self.on_disk_payload
                ),
        ):
            raise ConnectionError(f'Could not create {DEFAULT_QUOTE_COLLECTION} collection.')
        # create default index
        if not self.client.create_payload_index(
                collection_name=DEFAULT_QUOTE_COLLECTION, field_name=DEFAULT_PAYLOAD_INDEX, field_type='keyword'
        ):
            raise ConnectionError(f'Could not create {DEFAULT_PAYLOAD_INDEX} index on {DEFAULT_QUOTE_COLLECTION}.')

    def upsert_quotes(
            self,
            quotes: list[QuoteItem],
            embeddings: Sequence[list[float]],
            collection_name: str = DEFAULT_QUOTE_COLLECTION,
            wait: bool = True,
    ) -> UpdateStatus:
        """
        Method to upsert quotes to the vector store.
        :param quotes: list of QuoteItems
        :param embeddings: list of quote embeddings
        :param collection_name: where to store the quotes.
        :param wait: Whether to wait for committed changes.
        :return: Status of the upsert request.
        """
        # Construct points from inputs
        points = [
            # TODO check for failure regarding pydantic attribute assignment
            PointStruct(
                id=quote['id'],  # type: ignore
                vector=embedding,
                payload=quote['data'],  # type: ignore
            )
            for quote, embedding in zip(quotes, embeddings)
        ]
        # upsert points
        response = self.client.upsert(collection_name=collection_name, points=points, wait=wait)
        # if upsert was not successful, raise an error
        if response.status.startswith('4'):
            raise HTTPError(f'Failing to upsert points: {response.status}')
        # return status
        return response.status

    def get_content_based_recommendation(
            self,
            query_embedding: npt.NDArray[np.float64],
            tags: Optional[list[str]] = None,
            limit: int = 10,
            score_threshold: Optional[float] = None,
            collection: str = DEFAULT_QUOTE_COLLECTION,
    ) -> list[Optional[ScoredPoint]]:
        """
        Get content-based recommendations for the specified query.
        :param query_embedding: The encoded user search string.
        :param tags: Tags that should be used for searching. Only those quotes are returned that are assigned to one of
        the specified tags (logical OR).
        :param limit: Max number of results that should be returned.
        :param score_threshold: Define a minimal score threshold for the result. If defined, less similar results will
        not be returned.
        :param collection: Collection used for the search.
        :return: Payload results of the matching quotes.

        Reference: https://qdrant.github.io/qdrant/redoc/index.html#tag/points/operation/search_points
        """
        # build the search query
        hits = self.client.search(
            collection_name=collection,
            query_vector=query_embedding,
            # fmt: off
            query_filter=Filter(
                # a quote must contain any of the specified tags to be considered a match
                must=[FieldCondition(key='tags', match=MatchAny(any=tags))]  # TODO: get from pydantic model
            ) if tags else None,
            # fmt: on
            limit=limit,
            score_threshold=score_threshold,
            # only select relevant payload fields
            with_payload=PayloadSelectorInclude(include=list(ExtendedQuoteData.model_fields.keys())),
        )
        # return payload results
        return hits

    def get_item_item_recommendations(
            self,
            negatives: Sequence[int],
            positives: Optional[Sequence[int]] = None,
            limit: int = 10,
            collection: str = DEFAULT_QUOTE_COLLECTION
    ) -> list[ScoredPoint]:
        """
        Use the Qdrant recommendations API to receive item-based recommendations.
        :param positives: IDs of positive examples to search for.
        :param negatives: IDs of negative examples to avoid.
        :param limit: Number of results.
        :param collection: Where to search for points.
        :return: List of recommendations.
        """
        recommendations = self.client.recommend(
            collection_name=collection,
            positive=positives,
            negative=negatives,
            limit=limit,
            with_payload=PayloadSelectorInclude(include=['author', 'avatar_img', 'tags', 'text']),  # TODO: get from pydantic model
            strategy=RecommendStrategy.BEST_SCORE,
            # TODO: adjust param for optimized search (https://qdrant.tech/documentation/concepts/explore/#best-score-strategy)
            # params={'ef': 64}
        )
        return recommendations

    def scroll_points(
            self,
            tags: Optional[list[str]] = None,
            offset: Optional[int] = None,
            limit: int = 20,
            collection: str = DEFAULT_QUOTE_COLLECTION
    ) -> tuple[list[Record], Optional[int | str | Any]]:
        """
        Scroll points from Qdrant.
        :param tags: Tag filters.
        :param offset: Offset where to start.
        :param limit: Number of results.
        :param collection: Where to search for points.
        :return: Page results and next page offset.
        """
        points = self.client.scroll(
            collection_name=collection,
            scroll_filter=Filter(
                must=[FieldCondition(key='tags', match=MatchAny(any=tags))]
            ) if tags else None,
            limit=limit,
            offset=offset,
            with_vectors=False,
            with_payload=PayloadSelectorInclude(include=['author', 'avatar_img', 'tags', 'text'])  # TODO: get from pydantic model
        )
        # return points and next_page_offset
        return points[0], points[1]

    def search_points(self, ids: Sequence[int | str], collection: str = DEFAULT_QUOTE_COLLECTION) -> list[Record]:
        """
        Searching points by IDs.
        :param ids: List or sequence of point IDs.
        :param collection: Where to search for points.
        :return: Points with payloads.
        """
        hits = self.client.retrieve(
            collection_name=collection,
            ids=ids,
            with_payload=PayloadSelectorInclude(include=['author', 'avatar_img', 'tags', 'text'])  # TODO: get from pydantic model
        )
        return hits

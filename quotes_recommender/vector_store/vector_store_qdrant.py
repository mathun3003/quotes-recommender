import logging
from typing import Optional, Optional, Sequence, Any

import numpy as np
import numpy.typing as npt
import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchText,
    PayloadSelectorInclude,
    PointStruct,
    RecommendStrategy,
    Record,
    ScalarQuantizationConfig,
    ScalarType,
    ScoredPoint,
    SearchParams,
    UpdateStatus,
    VectorParams, CountResult,
)
from requests import HTTPError

from quotes_recommender.quote_scraper.items import ExtendedQuoteData, QuoteItem
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
                requests.get(
                    f'{qdrant_config.https_url if qdrant_config.use_https else qdrant_config.http_url}/healthz',
                    timeout=60,
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
        # create default collection
        if not self.client.create_collection(
            collection_name=DEFAULT_QUOTE_COLLECTION,
            on_disk_payload=self.on_disk_payload,
            vectors_config=VectorParams(
                size=DEFAULT_EMBEDDING_SIZE, distance=Distance.COSINE, on_disk=self.on_disk_payload
            ),
            quantization_config=ScalarQuantizationConfig(type=ScalarType.INT8, always_ram=True),
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

    # pylint: disable=too-many-arguments
    def get_content_based_recommendation(
        self,
        query_embedding: npt.NDArray[np.float64],
        tags: Optional[list[str]] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        collection: str = DEFAULT_QUOTE_COLLECTION,
    ) -> Optional[list[ScoredPoint]]:
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
        collection: str = DEFAULT_QUOTE_COLLECTION,
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
            # TODO: get from pydantic model
            with_payload=PayloadSelectorInclude(include=['author', 'avatar_img', 'tags', 'text']),
            strategy=RecommendStrategy.BEST_SCORE,
            search_params=SearchParams(hnsw_ef=256, exact=True),
        )
        return recommendations

    def scroll_points(
        self,
        payload_attributes: list[str],
        tags: Optional[list[str]] = None,
        keyword: Optional[str] = None,
        offset: Optional[int] = None,
        limit: int = 20,
        collection: str = DEFAULT_QUOTE_COLLECTION,
    ) -> tuple[list[Record], Optional[int | str | Any]]:
        """
        Scroll points from Qdrant.
        :param payload_attributes: Which payload attributes to return for each point
        :param tags: Tag filters.
        :param keyword: Keyword filter.
        :param offset: Offset where to start.
        :param limit: Number of results.
        :param collection: Where to search for points.
        :return: Page results and next page offset.
        """
        # search for points
        points = self.client.scroll(
            collection_name=collection,
            scroll_filter=Filter(
                must=[FieldCondition(key='tags', match=MatchAny(any=tags))] if tags else None,
                should=[FieldCondition(key='text', match=MatchText(text=keyword))] if keyword else None,
            ),
            limit=limit,
            offset=offset,
            with_vectors=False,
            # TODO: get from pydantic model
            with_payload=PayloadSelectorInclude(include=payload_attributes),
        )
        # return points and next_page_offset
        return points[0], points[1]

    def get_point_count(self, collection: str = DEFAULT_QUOTE_COLLECTION) -> int:
        """
        Get the exact number of points for the given collection.
        :param collection: Collection name.
        :return: Number of exact point count.
        """
        # get count
        count: CountResult = self.client.count(collection_name=collection, exact=True)
        return count.count

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
            # TODO: get from pydantic model
            with_payload=PayloadSelectorInclude(include=['author', 'avatar_img', 'tags', 'text']),
        )
        return hits

    def get_similarity_scores(self, query_embedding: npt.NDArray[np.float64]) -> Optional[list[ScoredPoint]]:
        """
        Get similarity scores for the specified query.
        Used for determining tuples for data fusion.

        :param query_embedding: Encoded quote to be checked for duplicate detection.
        :param collection: Collection used for the search.
        :return: Payload results of duplicate quotes.

        Reference: https://qdrant.github.io/qdrant/redoc/index.html#tag/points/operation/search_points
        """
        dups = self.client.search(
            collection_name=DEFAULT_QUOTE_COLLECTION,
            query_vector=query_embedding,
            limit=1,
            score_threshold=0.9,
        )
        # return payload results
        return dups

    def get_entry_by_author(
        self,
        query_embedding: npt.NDArray[np.float64],
        author: str,
        collection: str = DEFAULT_QUOTE_COLLECTION,
    ) -> Optional[ScoredPoint]:
        """
        Get entry with the same author based on similarity scores for the specified query.
        :param author: Author to match.
        :param query_embedding: Encoded quote to be checked for duplicate detection.
        :param collection: Collection used for the search.
        :return: Payload results of quotes with the same author.

        Reference: https://qdrant.github.io/qdrant/redoc/index.html#tag/points/operation/search_points
        """
        # build the search query
        result = self.client.search(
            collection_name=collection,
            query_vector=query_embedding,
            # Add a condition to match the author
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key='author',
                        match=models.MatchValue(
                            value=author,
                        ),
                    )
                ]
            ),
            score_threshold=0,
        )
        # return payload results
        return result[0]

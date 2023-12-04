import json

from quotes_recommender.core.constants import TXT_ENCODING
from quotes_recommender.quote_scraper.items import Quote
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton
from tests.constants import TEST_VECTOR_SIZE, TEST_COLLECTION_NAME, TEST_DATA_PATH

vector_store = QdrantVectorStoreSingleton().vector_store


def test_upsert_quotes():
    # load test quote
    with open(TEST_DATA_PATH / "test_quote.json", "r", encoding=TXT_ENCODING) as test_quote:
        data = json.load(test_quote)
    # construct QuoteItem from data object
    quote = Quote(id=1, data=data)
    response = vector_store.upsert_quotes(
        quotes=[quote],
        embeddings=[[0.1] * TEST_VECTOR_SIZE],
        collection_name=TEST_COLLECTION_NAME
    )
    # check status
    assert response == "completed"

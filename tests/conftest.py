from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton
from tests.constants import TEST_COLLECTION_NAME, TEST_VECTOR_CONFIG

vector_store = QdrantVectorStoreSingleton().vector_store


def pytest_sessionstart(session):
    # create test collection
    vector_store.client.create_collection(TEST_COLLECTION_NAME, vectors_config=TEST_VECTOR_CONFIG, on_disk_payload=True)


def pytest_sessionfinish(session, exitstatus):
    # delete test collection
    vector_store.client.delete_collection(TEST_COLLECTION_NAME)

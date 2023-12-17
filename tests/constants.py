from pathlib import Path
from typing import Final

from qdrant_client.http.models import VectorParams, Distance

# paths
TEST_DATA_PATH = Path("tests") / "data"

TEST_COLLECTION_NAME: Final[str] = "test_collection"
TEST_VECTOR_SIZE: Final[int] = 768
TEST_VECTOR_CONFIG: Final[VectorParams] = VectorParams(
                    size=TEST_VECTOR_SIZE,
                    distance=Distance.COSINE,
                    on_disk=True
                )

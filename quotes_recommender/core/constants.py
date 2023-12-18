from pathlib import Path
from typing import Final

from yarl import URL

TXT_ENCODING: Final[str] = 'utf-8'
GOODREADS_QUOTES_URL: Final[URL] = URL("https://www.goodreads.com/quotes")

# Paths
DATA_PATH: Final[Path] = Path('data')
SENTENCE_ENCODER_PATH: Final[Path] = DATA_PATH / 'all-mpnet-base-v2'

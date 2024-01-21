import os
from pathlib import Path
from typing import Final

from yarl import URL

TXT_ENCODING: Final[str] = 'utf-8'

# URLs
GOODREADS_QUOTES_URL: Final[URL] = URL("https://www.goodreads.com/")

# Paths
DATA_PATH: Final[Path] = Path('data')
SENTENCE_ENCODER_PATH: Final[Path] = DATA_PATH / 'all-mpnet-base-v2'
LOGO_PATH: Final[Path] = Path('resources') / 'sagesnippet_logo.png'

script_dir = os.path.dirname(os.path.abspath(__file__))
TAG_MAPPING_PATH = os.path.join(script_dir, './short_tag_mapping.json')

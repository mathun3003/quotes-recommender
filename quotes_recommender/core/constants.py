from pathlib import Path
from typing import Final

TXT_ENCODING: Final[str] = 'utf-8'

# Paths
DATA_PATH: Final[Path] = Path('data')
SENTENCE_ENCODER_PATH: Final[Path] = DATA_PATH / 'all-mpnet-base-v2'

import logging
import platform
from typing import Any

import numpy as np
import numpy.typing as npt
import torch
from sentence_transformers import SentenceTransformer

from quotes_recommender.core.constants import SENTENCE_ENCODER_PATH
from quotes_recommender.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class SentenceBERTSingleton(Singleton):
    """Class loading the SentenceBERT model"""

    def init(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        """Load model from path or download it from HF"""
        # try to load model from path, otherwise download it from HF
        if not SENTENCE_ENCODER_PATH.exists():
            logger.info('Download SentenceBERT from HuggingFace Hub.')
        else:
            logger.info(f'Load SentenceBERT from path {SENTENCE_ENCODER_PATH}')
        self.model = SentenceBERT()


class SentenceBERT:
    """Class encapsulating the SentenceBERT model."""

    def __init__(self) -> None:
        """Loading the sentence encoder from path or from HF if not locally available."""
        self._sentence_bert = SentenceTransformer(str(SENTENCE_ENCODER_PATH))
        # find device for encoding
        # set default device
        self.device: str | torch.device = 'cpu'
        # check operating system
        if operating_sys := platform.system() == 'Darwin':
            # for Mac backends
            if torch.cuda.is_available():
                self.device = 'mps'
        else:
            if torch.cuda.is_available():
                # other backends
                self.device = 'cuda'

        logger.info(f'Using {self.device} on {operating_sys} for encoding.')

    def encode_quote(self, quote: str) -> npt.NDArray[np.float64]:
        """Encode a single quote by using the found device"""
        return self._sentence_bert.encode(sentences=quote, device=self.device, show_progress_bar=False)

import platform
import logging
from typing import Final

import requests
from bs4 import BeautifulSoup
import streamlit as st
import torch
from qdrant_client.http.models import Record
from sentence_transformers import SentenceTransformer

from quotes_recommender.core.constants import SENTENCE_ENCODER_PATH, GOODREADS_QUOTES_URL

logger = logging.getLogger(__name__)


def switch_opposite_button(button_key: str) -> None:
    """
    Deselects an opposite button if one of two corresponding (dis-)like buttons was clicked.
    :param button_key: The unique key of the button that has to be switched.
    :return: None
    """
    st.session_state[button_key] = False if st.session_state[button_key] is True else False


@st.cache_resource
def load_sentence_bert() -> SentenceTransformer:
    """
    Loads and caches SentenceBERT model.
    :return: None
    """
    """Loading the sentence encoder from path or from HF if not locally available."""
    sentence_bert = SentenceTransformer(str(SENTENCE_ENCODER_PATH))
    # find device for encoding
    # set default device
    device: str | torch.device = 'cpu'
    # check operating system
    if operating_sys := platform.system() == 'Darwin':
        # for Mac backends
        if torch.cuda.is_available():
            device = 'mps'
    else:
        if torch.cuda.is_available():
            # other backends
            device = 'cuda'

    logger.info(f'Using {device} on {operating_sys} for encoding.')
    return sentence_bert


def click_search_button() -> None:
    """
    Auxiliary function to add statefulness to the search button.
    :return: None
    """
    st.session_state.clicked_search_button = True


@st.cache_data
def extract_tag_filters() -> list[str]:
    """
    Fetches the quote tags from goodreads.com/quotes
    :return:
    """

    tag_selector: Final[str] = 'li.greyText'

    response = requests.get(str(GOODREADS_QUOTES_URL))

    if not response.ok:
        response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    options = [option.text.split()[0].strip() for option in soup.select(tag_selector)]
    return options


def display_quotes(quotes: list[Record], display_buttons: bool = False) -> None:
    """
    Auxiliary function to render quotes in streamlit.
    :param quotes: List of quotes from Qdrant.
    :param display_buttons: Whether to display (dis-)like buttons.
    :return: None
    """
    for quote in quotes:
        with st.container(border=True):
            left_quote_col, right_quote_col = st.columns(spec=[0.7, 0.3])
            with left_quote_col:
                st.markdown(f"""
                *„{quote.payload.get('text')}“*  
                **― {quote.payload.get('author')}**""")
                st.caption(f"Tags: {', '.join([tag.capitalize() for tag in quote.payload.get('tags')])}")
            with right_quote_col:
                if (img_link := quote.payload.get('avatar_img')) is not None:
                    st.image(img_link, use_column_width=True)
            if display_buttons:
                left_btn_col, right_btn_col = st.columns(spec=[0.2, 0.8])
                with left_btn_col:
                    like_btn = st.checkbox(
                        label=":thumbsup:",
                        help="Yes, I want to see more like this!",
                        key=f"quote_{quote.id}_like",
                        on_change=switch_opposite_button,
                        args=[f"quote_{quote.id}_dislike"]
                    )
                with right_btn_col:
                    dislike_btn = st.checkbox(
                        label=":thumbsdown:",
                        help="Yuk, show me less like this!",
                        key=f"quote_{quote.id}_dislike",
                        on_change=switch_opposite_button,
                        args=[f"quote_{quote.id}_like"]
                    )


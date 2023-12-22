import logging
import platform
from typing import Final, Optional

import requests
import streamlit as st
import torch
from bs4 import BeautifulSoup
from qdrant_client.http.models import Record
from sentence_transformers import SentenceTransformer

from quotes_recommender.core.constants import SENTENCE_ENCODER_PATH, GOODREADS_QUOTES_URL
from quotes_recommender.core.models import UserPreference
from quotes_recommender.user_store.models import PreferenceKey
from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton

user_store = RedisUserStoreSingleton().user_store
logger = logging.getLogger(__name__)


def switch_opposite_button(button_key: str, quote_id: int, hash_key: str) -> None:
    """
    Deselects an opposite button if one of two corresponding (dis-)like buttons was clicked.
    :param button_key: The unique key of the button that has to be switched.
    :param quote_id: The unique ID of the quote under which it is stored in Qdrant.
    :param hash_key: The preference hash key. Can either be a hash key for a like or dislike.
    :return: None
    """
    # set state of opposite checkbox to the negated value of the current checkbox
    st.session_state[button_key] = False if st.session_state[button_key] is True else False
    # remove opposite preference from Redis if available because a preference should only be available in one
    # set at a time
    if user_store.delete_user_preference(hash_key, member=quote_id) is False:
        st.toast('Failed to save preferences. Please try again later.', icon='🕠')


@st.cache_resource
def load_sentence_bert() -> SentenceTransformer:
    """
    Loading the sentence encoder from path or from HF if not locally available.
    :return: None
    """
    with st.spinner("Preparing query encoding. Hang on, we hurry up!"):
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


def display_quotes(quotes: list[Record], display_buttons: bool = False) -> Optional[list[UserPreference]]:
    """
    Auxiliary function to render quotes in streamlit.
    :param quotes: List of quotes from Qdrant.
    :param display_buttons: Whether to display (dis-)like buttons.
    :return: None
    """
    # set preference keys
    hash_keys = PreferenceKey(username=st.session_state['username'])
    # init likes/dislikes accumulators
    preferences: list[UserPreference] = []
    # display each quote
    for quote in quotes:
        with st.container(border=True):
            left_quote_col, right_quote_col = st.columns(spec=[0.7, 0.3])
            # display text, author, and tags on left hand side
            with left_quote_col:
                st.markdown(f"""
                *„{quote.payload.get('text')}“*  
                **― {quote.payload.get('author')}**""")
                st.caption(f"Tags: {', '.join([tag.capitalize() for tag in quote.payload.get('tags')])}")
            # display image on right hand side
            with right_quote_col:
                if (img_link := quote.payload.get('avatar_img')) is not None:
                    st.image(img_link, use_column_width=True)
            if display_buttons:
                # create unique keys for each checkbox
                like_key, dislike_key = f"{quote.id}-like", f"{quote.id}-dislike"
                # create columns
                left_btn_col, right_btn_col = st.columns(spec=[0.2, 0.8])
                # display checkboxes
                with left_btn_col:
                    # like button
                    like_btn = st.checkbox(
                        label=":thumbsup:",
                        help="Yes, I want to see more like this!",
                        key=like_key,
                        on_change=switch_opposite_button,
                        args=[dislike_key, quote.id, hash_keys.dislike_key]
                    )
                    if like_btn:
                        preferences.append(UserPreference(id=quote.id, like=True))
                with right_btn_col:
                    # dislike button
                    dislike_btn = st.checkbox(
                        label=":thumbsdown:",
                        help="Yuk, show me less like this!",
                        key=dislike_key,
                        on_change=switch_opposite_button,
                        args=[like_key, quote.id, hash_keys.like_key]
                    )
                    if dislike_btn:
                        preferences.append(UserPreference(id=quote.id, like=False))

    if display_buttons and preferences:
        return preferences

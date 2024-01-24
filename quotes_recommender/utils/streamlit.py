import json
import logging
from typing import Final, Optional, Sequence

import requests
import streamlit as st
from bs4 import BeautifulSoup
from qdrant_client.http.models import Record, ScoredPoint

from quotes_recommender.core.constants import TAG_MAPPING_PATH, TXT_ENCODING
from quotes_recommender.core.models import UserPreference
from quotes_recommender.ml_models.sentence_encoder import SentenceBERT
from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton

user_store = RedisUserStoreSingleton().user_store
logger = logging.getLogger(__name__)


def switch_opposite_button(button_key: str) -> None:
    """
    Deselects an opposite button if one of two corresponding (dis-)like buttons was clicked.
    :param button_key: The unique key of the button that has to be switched.
    :return: None
    """
    # set state of opposite checkbox to False
    st.session_state[button_key] = False


@st.cache_resource
def load_sentence_bert() -> SentenceBERT:
    """
    Loading the sentence encoder from path or from HF if not locally available.
    :return: None
    """
    with st.spinner("Preparing query encoding. Hang on, we hurry up!"):
        sentence_bert = SentenceBERT()
    return sentence_bert


def click_search_button() -> None:
    """
    Auxiliary function to add statefulness to the search button.
    :return: None
    """
    st.session_state.search_button_clicked = True


@st.cache_data
def get_tag_filters() -> list[str]:
    """
    Extracts quote tags from the tag mapping file located at TAG_MAPPING_PATH.
    :returns: A list of unique quote tags obtained from the mapping file.
    """
    with open(TAG_MAPPING_PATH, 'r') as file:
        tag_mapping_file = json.load(file)
    return list(set(tag_mapping_file.values()))


# pylint: disable=too-many-locals
def display_quotes(
    quotes: Sequence[Record | ScoredPoint],
    display_buttons: bool = False,
    ratings: Optional[list[UserPreference]] = None,
) -> Optional[tuple[list[int | str], list[int | str]]]:
    """
    Auxiliary function to render quotes in streamlit.

    Unpack results to receive liked and disliked quote IDs:
    likes, dislikes = display_quotes(...)
    :param quotes: List of quotes from Qdrant.
    :param display_buttons: Whether to display (dis-)like buttons.
    :param ratings: User ratings that should be displayed for each quote.
    :return: Lists of liked and disliked quote IDs.
    """
    if ratings and not display_buttons:
        raise ValueError(
            "User ratings can only be passed in combination with checkboxes. Set 'display_buttons' to True."
        )
    # init likes/dislikes accumulators
    likes, dislikes = [], []
    # display each quote
    for quote in quotes:
        if not quote.payload:
            raise ValueError(f"No payload found for quote {quote.id}")
        # init checkbox default values
        like_value, dislike_value = False, False
        # search for corresponding rating by ID
        if ratings:
            # find corresponding rating based on ID
            rating = next(filter(lambda r, quote_id=quote.id: r.id == quote_id, ratings), None)  # type: ignore
            # if a rating was found
            if rating:
                # set corresponding values
                like_value = rating.like
                dislike_value = not rating.like
        # construct quote container
        with st.container(border=True):
            left_quote_col, right_quote_col = st.columns(spec=[0.7, 0.3])
            # display text, author, and tags on left hand side
            with left_quote_col:
                st.markdown(
                    f"""
                *„{quote.payload['text']}“*
                **― {quote.payload['author']}**"""
                )
                st.caption(f"Tags: {', '.join([tag.capitalize() for tag in quote.payload['tags']])}")
            # display image on right hand side
            with right_quote_col:
                if img_link := quote.payload['avatar_img']:
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
                        args=[dislike_key],  # type: ignore
                        value=like_value,
                    )
                    if like_btn:
                        likes.append(quote.id)
                with right_btn_col:
                    # dislike button
                    dislike_btn = st.checkbox(
                        label=":thumbsdown:",
                        help="Yuk, show me less like this!",
                        key=dislike_key,
                        on_change=switch_opposite_button,
                        args=[like_key],  # type: ignore
                        value=dislike_value,
                    )
                    if dislike_btn:
                        dislikes.append(quote.id)

    if display_buttons:
        return likes, dislikes
    return None

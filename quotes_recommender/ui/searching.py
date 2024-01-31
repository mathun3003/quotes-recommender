import streamlit as st

from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
from quotes_recommender.utils.streamlit import (
    click_search_button,
    display_quotes,
    get_tag_filters,
    load_sentence_bert,
)
from quotes_recommender.vector_store.vector_store_singleton import (
    QdrantVectorStoreSingleton,
)

st.set_page_config(layout='centered')

try:
    user_store = RedisUserStoreSingleton().user_store
    vector_store = QdrantVectorStoreSingleton().vector_store
except AttributeError:
    st.rerun()
sentence_bert = load_sentence_bert()


# init state for search button
if 'search_button_clicked' not in st.session_state:
    st.session_state.search_button_clicked = False

st.title('Search for Quotes')
st.write(
    """
Here you can easily search for quotes.
Just specify what you are looking for or want to say and browse through the results.
In addition, you can specify in which quotes you are interested the most.
Therefore, filter the results by one or multiple tags.
"""
)
st.divider()

# specify user inputs
query = st.text_input(label="User query", placeholder="What are you looking for?")
tags = st.multiselect(label="Filters", options=get_tag_filters(), placeholder="Filter by tags.")
submitted = st.button(label="Search for Quotes", use_container_width=True, type="primary", on_click=click_search_button)
st.divider()

if submitted and st.session_state.search_button_clicked:
    # if no query was provided
    if not query or len(query.strip()) == 0:
        st.error('Please enter a search query.')
        st.stop()
    # perform search
    with st.spinner('Searching for quotes...', cache=True):
        quotes = vector_store.get_content_based_recommendation(
            query_embedding=sentence_bert.encode_quote(query), tags=tags
        )

    if not quotes:
        st.info("No quotes found. Please search for some other quotes or change filters.")
        st.stop()
    display_quotes(quotes, display_buttons=False)

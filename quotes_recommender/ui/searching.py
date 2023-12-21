import streamlit as st

from quotes_recommender.utils.streamlit import load_sentence_bert, click_search_button, extract_tag_filters, \
    display_quotes
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

vector_store = QdrantVectorStoreSingleton().vector_store
sentence_bert = load_sentence_bert()

# init state for search button
if 'clicked' not in st.session_state:
    st.session_state.clicked_search_button = False

st.title('Search for Quotes')
st.write("""
Here you can easily search for quotes. 
Just specify what you are looking for or want to say and browse through the results.
In addition, you can specify in which quotes you are interested the most. 
Therefore, filter the results by one or multiple tags. 
""")
st.divider()

# specify user inputs
query = st.text_input(label="User query", placeholder="What are you looking for?")
tags = st.multiselect(label="Filters", options=extract_tag_filters(), placeholder="Filter by tags.")
submitted = st.button(label="Search for Quotes", use_container_width=True, type="primary", on_click=click_search_button)
st.divider()

if submitted:
    if not query or len(query.strip()) == 0:
        st.error('Please enter a search query.')

    with st.spinner('Searching for quotes...'):
        quotes = vector_store.get_content_based_recommendation(
            query_embedding=sentence_bert.encode(query, show_progress_bar=False),
            tags=[tag.lower() for tag in tags]
        )

    if not quotes:
        st.info("No quotes found. Please search for some other quotes or change filters.")
    # display quotes
    display_quotes(quotes)

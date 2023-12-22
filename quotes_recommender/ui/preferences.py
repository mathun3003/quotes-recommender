import streamlit as st
import streamlit_authenticator as stauth

from quotes_recommender.core.models import UserPreference
from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
from quotes_recommender.utils.streamlit import switch_opposite_button, display_quotes, extract_tag_filters
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

vector_store = QdrantVectorStoreSingleton().vector_store
user_store = RedisUserStoreSingleton().user_store

# configure authenticator
authenticator = stauth.Authenticate(
    credentials={
        'usernames': user_store.get_user_credentials()
    },
    cookie_name='sage_snippet',
    key='authenticator-preferences-subpage'
)
# display logout button in sidebar
authenticator.logout('Logout', 'sidebar', key='logout_sidebar')

if st.session_state['authentication_status']:

    # Display logged in user on sidebar
    st.sidebar.write(f"Logged in as {st.session_state['name']}.")

    st.header('Your Preferences')
    st.subheader('Specify your interests')
    st.write("""
    In order to provide you the best possible recommendations, we need some information about your preferences and 
    interests. Please consider the following quotes and specify at least five quotes you like and not like. 
    You can also filter by tags and/or authors to .
    """)
    st.divider()
    # select by tags
    tags = st.multiselect(label="Filters", options=extract_tag_filters(), placeholder="Filter by tags.")
    with st.spinner('Loading quotes...'):
        # get quotes from vector store
        quotes, next_page_offset = vector_store.scroll_points(limit=10, tags=[tag.lower() for tag in tags])
    # display quotes with buttons
    st.divider()
    # display quotes and collect user preferences
    preferences = display_quotes(quotes, display_buttons=True)
    # write preferences to redis
    if preferences:
        if not user_store.set_user_preferences(username=st.session_state['username'], preferences=preferences):
            st.toast('Failed to save preferences. Please try again later.', icon='🕠')
else:
    st.info('🔔 Please login/register to specify preferences.')

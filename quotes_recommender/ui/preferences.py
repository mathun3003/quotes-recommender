import streamlit as st
import streamlit_authenticator as stauth

from quotes_recommender.core.models import UserPreference
from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
from quotes_recommender.utils.streamlit import display_quotes, extract_tag_filters
from quotes_recommender.vector_store.vector_store_singleton import (
    QdrantVectorStoreSingleton,
)

st.set_page_config(layout='centered')

try:
    vector_store = QdrantVectorStoreSingleton().vector_store
    user_store = RedisUserStoreSingleton().user_store
except AttributeError:
    st.rerun()

# configure authenticator
authenticator = stauth.Authenticate(
    credentials={'usernames': user_store.get_user_credentials()},
    cookie_name='sage_snippets',
    key='authenticator-preferences-subpage',
)

if st.session_state['authentication_status']:
    # Display logged in user on sidebar
    st.sidebar.write(f"Logged in as {st.session_state['name']}")
    authenticator.logout('Logout', 'sidebar', key='logout_sidebar')
    st.header('Your Preferences')
    st.subheader('Specify your interests')
    st.write(
        """
    In order to provide you the best possible recommendations, we need some information about your preferences and
    interests. Please consider the following quotes and specify at least five quotes you like and not like.
    You can also filter by tags or keywords to narrow down the displayed quotes.
    """
    )
    st.divider()
    with st.spinner('Loading filters...', cache=True):
        # select by tags
        tags = st.multiselect(
            label="Tags",
            options=extract_tag_filters(),
            help="Select one or multiple tags you would like to filter for.",
            placeholder="Filter by tags.",
        )
        # search by keyword
        keyword = st.text_input(
            label="Keyword", help="Type in a keyword you would like to filter for.", placeholder="Filter by keyword."
        )
    with st.spinner('Loading quotes...'):
        # get quotes from vector store
        quotes, _ = vector_store.scroll_points(limit=10, tags=[tag.lower() for tag in tags], keyword=keyword)
    # display quotes with buttons
    st.divider()
    # if no results were found
    if not quotes:
        # display error message
        st.info("❌ No quotes found for your filters. Please set different filters or remove some.")
    # get ratings (if any) for logged-in user
    likes, dislikes = user_store.get_user_preferences(st.session_state['username'])
    # construct UserPreference instances in order to display later
    like_ratings: list[UserPreference] = list(map(lambda x: UserPreference(id=x, like=True), likes))
    dislike_ratings: list[UserPreference] = list(map(lambda x: UserPreference(id=x, like=False), dislikes))
    # display quotes and collect user preferences
    set_likes, set_dislikes = display_quotes(  # type: ignore
        quotes, display_buttons=True, ratings=like_ratings + dislike_ratings
    )
    # write preferences to redis
    # if new likes were added
    if new_likes := set(set_likes).difference(set(likes)):
        # add them to redis
        if not user_store.set_user_preferences(username=st.session_state['username'], likes=new_likes):
            st.toast('Failed to save preferences. Please try again later.', icon='🕠')
    # if new dislikes were added
    elif new_dislikes := set(set_dislikes).difference(set(dislikes)):
        # add them to redis
        if not user_store.set_user_preferences(username=st.session_state['username'], dislikes=new_dislikes):
            st.toast('Failed to save preferences. Please try again later.', icon='🕠')
    # if no new likes were added, they have to be unselected
    elif (not new_likes) and (unset_likes := set(likes).difference(set_likes)):
        # delete them from redis
        if not user_store.delete_user_preference(username=st.session_state['username'], likes=list(unset_likes)):
            st.toast('Failed to save preferences. Please try again later.', icon='🕠')
    # if no new dislikes were added, they have to be unselected
    elif (not new_dislikes) and (unset_dislikes := set(dislikes).difference(set_dislikes)):
        # delete them from redis
        if not user_store.delete_user_preference(username=st.session_state['username'], dislikes=list(unset_dislikes)):
            st.toast('Failed to save preferences. Please try again later.', icon='🕠')

else:
    st.info('🔔 Please login/register to specify preferences.')

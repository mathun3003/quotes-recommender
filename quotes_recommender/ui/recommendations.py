import streamlit as st
import streamlit_authenticator as stauth

from utils.streamlit import display_quotes

from user_store.user_store_redis import RedisUserStore
from utils.redis import RedisConfig

from utils.qdrant import QdrantConfig
from vector_store.vector_store_qdrant import QdrantVectorStore

try:
    from user_store.user_store_singleton import (
        RedisUserStoreSingleton,
    )
    from vector_store.vector_store_singleton import (
        QdrantVectorStoreSingleton,
    )
except KeyError:
    st.rerun()

# set page layout
st.set_page_config(layout='wide')

# pylint: disable=duplicate-code
try:
    vector_store = QdrantVectorStore(qdrant_config=QdrantConfig())
    user_store = RedisUserStore(redis_config=RedisConfig())
except AttributeError:
    st.rerun()

# configure authenticator
authenticator = stauth.Authenticate(
    credentials={'usernames': user_store.get_user_credentials()},
    cookie_name='sage_snippets',
    key='authenticator-recommendations-subpage',
)

if st.session_state['authentication_status']:
    # display logout button in sidebar
    st.sidebar.write(f"Logged in as {st.session_state['name']}")
    authenticator.logout('Logout', 'sidebar', key='logout_sidebar')

    st.header('Your Recommendations')
    st.write(
        """
    Here you can see your recommendations. The more preferences you have specified, the more accurate your
    recommendations will get. It is recommended to have at least three likes and dislikes respectively in order to
    receive meaningful recommendations.
    """
    )
    st.divider()

    item_item_col, user_user_col = st.columns(2)

    # get ratings for logged-in user
    likes, dislikes = user_store.get_user_preferences(st.session_state['username'])
    if (not likes) and (not dislikes):
        st.info("🔔 You have not specified any preferences. Please specify any on the 'Set Preferences' page.")
        st.stop()
    else:
        with item_item_col:
            st.write('### Quotes you might also be interested in')
            # get item-item recommendations
            item_item_recommendations = vector_store.get_item_item_recommendations(positives=likes, negatives=dislikes)
            display_quotes(item_item_recommendations)
    with user_user_col:
        # get user-user recommendations
        with st.spinner('Hold tight! We are getting some recommendations for you... 🔍', cache=True):
            # get most similar user
            most_similar_user = user_store.get_most_similar_user(user=st.session_state['username'])
        # in case no similar user were found
        if not most_similar_user:
            st.info(
                """
            ⁉️ Oops, it seems you have a very special taste.
            Please provide more or other preferences in order to see further recommendations.
            """
            )
            st.stop()
        # get likes of most similar user
        most_similar_user_likes, _ = user_store.get_user_preferences(most_similar_user)
        # get non-symmetric set intersection
        user_user_quote_ids: list[int | str] = list(set(most_similar_user_likes).difference(likes))
        # get points
        user_user_recommendations = vector_store.search_points(user_user_quote_ids, limit=10)
        if not user_user_recommendations:
            st.info(
                """
            ⁉️ Oops, it seems you have a very special taste.
            Please provide more or other preferences in order to see further recommendations.
            """
            )
        # display recommendations
        st.write('### Similar users also liked')
        display_quotes(user_user_recommendations)

else:
    st.info('🔔 Please login/register to see your recommendations.')

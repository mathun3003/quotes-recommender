import streamlit as st
import streamlit_authenticator as stauth

from quotes_recommender.utils.streamlit import display_quotes

try:
    from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
    from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton
except KeyError:
    st.rerun()

# set page layout
st.set_page_config(layout='centered')

try:
    vector_store = QdrantVectorStoreSingleton().vector_store
    user_store = RedisUserStoreSingleton().user_store
except AttributeError:
    st.rerun()

# configure authenticator
authenticator = stauth.Authenticate(
    credentials={
        'usernames': user_store.get_user_credentials()
    },
    cookie_name='sage_snippet',
    key='authenticator-recommendations-subpage'
)

if st.session_state['authentication_status']:
    # display logout button in sidebar
    authenticator.logout('Logout', 'sidebar', key='logout_sidebar')

    # Display logged in user on sidebar
    st.sidebar.write(f"Logged in as {st.session_state['name']}")

    st.header('Your Recommendations')
    st.write("""
    Here you can see your recommendations. The more preferences you have specified, the more accurate your 
    recommendations will get. It is recommended to have at least three likes and dislikes respectively in order to
    receive meaningful recommendations.
    """)
    st.divider()

    # get ratings for logged-in user
    preferences = user_store.get_user_preferences(st.session_state['username'])
    if not preferences:
        st.info("🔔 You have not specified any preferences. Please specify any on the 'Set Preferences' page.")
        st.stop()
    else:
        # extract positives and negatives from preferences
        positives: list[int] = [preference.id for preference in list(filter(lambda p: p.like is True, preferences))]
        negatives: list[int] = [preferences.id for preferences in list(filter(lambda p: p.like is False, preferences))]
        # get recommendations
        recommendations = vector_store.get_item_item_recommendations(positives=positives, negatives=negatives)
        display_quotes(recommendations)
else:
    st.info('🔔 Please login/register to see your recommendations.')


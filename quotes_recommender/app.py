import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config
from streamlit_authenticator.exceptions import RegisterError

from quotes_recommender.core.models import UserPreference
from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
from quotes_recommender.utils.streamlit import display_quotes
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

try:
    vector_store = QdrantVectorStoreSingleton().vector_store
    user_store = RedisUserStoreSingleton().user_store
except AttributeError:
    st.rerun()

# TODO: add logging to streamlit app

# set page config
st.set_page_config(
    page_title='SageSnippets',
    page_icon='💬',
    menu_items={
        'About': '[Source Code](https://github.com/mathun3003/quotes-recommender)'
    },
    layout='wide'
)
# load pages
show_pages_from_config()

# set title
st.title('SageSnippets')
st.write('A Quote Recommender for Finding the Right Words to Express Your Thoughts')

# TODO: set description

# configure authenticator
authenticator = stauth.Authenticate(
    credentials={
        'usernames': user_store.get_user_credentials()
    },
    cookie_name='sage_snippet',
    key='authenticator-main-subpage'
)

login_tab, register_tab, forgot_password_tab = st.tabs(["Sign In", "Sign Up", "Reset Password"])

# Sign In tab
with (login_tab):
    authenticator.login(form_name='Login', location='main')
    # if login was successful
    if st.session_state['authentication_status']:
        # Display logged in user on sidebar
        st.sidebar.write(f"Logged in as {st.session_state['name']}")
        # display logout button in sidebar
        authenticator.logout('Logout', 'sidebar', key='logout_sidebar')
        # write welcome message
        st.write(f"## Welcome {st.session_state['name']} 👋")
        with st.spinner('Loading your preferences'):
            # get (dis-)likes (if any) of logged-in user
            like_preferences, dislike_preferences = user_store.get_user_preferences(st.session_state['username'])
        # if user has no preferences
        if (not like_preferences) and (not dislike_preferences):
            st.info("""You have no preferences specified. 
            Start defining your interests on the Preferences page.""")
        else:
            # display info message
            st.write("""
            Here you can see an overview of the quotes you have (dis-)liked. You can change (dis-)likes here at any time
            or add new (dis-)likes in the Preferences section.
            
            Based on your preferences, you can see recommendations on the [recommendations page](/Recommendations).
            """)
            st.divider()

            # fetch data from Qdrant
            liked_quotes, disliked_quotes = vector_store.search_points(like_preferences), \
                vector_store.search_points(dislike_preferences)
            # construct UserPreference instances in order to display later
            like_ratings: list[UserPreference] = [UserPreference(id=liked_quote.id, like=True)
                                                  for liked_quote in liked_quotes]
            dislike_ratings: list[UserPreference] = [UserPreference(id=disliked_quote.id, like=False)
                                                     for disliked_quote in disliked_quotes]

            # init accumulators for set likes and dislikes
            set_likes, set_dislikes = set(), set()
            # display preferences
            left_col, right_col = st.columns(2)
            with left_col:
                st.write('### Your Likes')
                if liked_quotes:
                    # get quote IDs of liked quotes for this session
                    set_likes_left, set_dislikes_left = display_quotes(liked_quotes,
                                                                       display_buttons=True,
                                                                       ratings=like_ratings)
                    # add user inputs to accumulators
                    set_likes.update(set_likes_left)
                    set_dislikes.update(set_dislikes_left)
                else:
                    st.info('You have no liked quotes.')
            with right_col:
                st.write('### Your Dislikes')
                if disliked_quotes:
                    # get quote IDs of disliked quotes for this session
                    set_likes_right, set_dislikes_right = display_quotes(disliked_quotes,
                                                                         display_buttons=True,
                                                                         ratings=dislike_ratings)
                    # add user inputs to accumulators
                    set_likes.update(set_likes_right)
                    set_dislikes.update(set_dislikes_right)
                else:
                    st.info('You have no disliked quotes.')

            # if new likes were added
            if new_likes := set_likes.difference(set(like_preferences)):
                # add them to redis
                if not user_store.set_user_preferences(username=st.session_state['username'], likes=new_likes):
                    st.toast('Failed to save preferences. Please try again later.', icon='🕠')
                else:
                    st.rerun()
            # if new dislikes were added
            elif new_dislikes := set_dislikes.difference(set(dislike_preferences)):
                # add them to redis
                if not user_store.set_user_preferences(username=st.session_state['username'], dislikes=new_dislikes):
                    st.toast('Failed to save preferences. Please try again later.', icon='🕠')
                else:
                    st.rerun()
            # if no new likes were added, they have to be unselected
            elif (not new_likes) and (unset_likes := set(like_preferences).difference(set_likes)):
                # delete them from redis
                if not user_store.delete_user_preference(username=st.session_state['username'], likes=unset_likes):
                    st.toast('Failed to save preferences. Please try again later.', icon='🕠')
                else:
                    st.rerun()
            # if no new dislikes were added, they have to be unselected
            elif (not new_dislikes) and (unset_dislikes := set(dislike_preferences).difference(set_dislikes)):
                # delete them from redis
                if not user_store.delete_user_preference(username=st.session_state['username'], dislikes=unset_dislikes):
                    st.toast('Failed to save preferences. Please try again later.', icon='🕠')
                else:
                    st.rerun()

    # if login was not successful
    elif st.session_state['authentication_status'] is False:
        st.error('❌ Username/password is incorrect')
    # if nothing was typed in
    elif st.session_state['authentication_status'] is None:
        st.warning('Please enter your username and password')

# Sign Up tab
with register_tab:
    try:
        if authenticator.register_user("Register", preauthorization=False):
            # get newly registered user from authenticator
            new_usernames: set[str] = \
                set(authenticator.credentials['usernames'].keys()) ^ set(user_store.get_user_credentials().keys())
            # register any new user
            for new_username in new_usernames:
                # get credentials
                new_credentials = authenticator.credentials['usernames'][new_username]
                # store in redis
                if not user_store.register_user(username=new_username, credentials=new_credentials):
                    st.error("Oops, you broke the internet... Please try again later.")
                    st.stop()
            st.success("You successfully registered for SageSnippets! 🎉")
            st.write("You can now log in via the 'Sign In' tab.")
    except RegisterError as register_error:
        st.error(register_error.message)

# Reset Password tab
with forgot_password_tab:
    # TODO: implement
    username_of_forgotten_password, email_of_forgotten_password, new_random_password = authenticator.forgot_password(
        'Forgot password')
    if username_of_forgotten_password:
        st.success('A new password has been sent to your email address 📫')
    elif not email_of_forgotten_password and username_of_forgotten_password is not None:
        st.error('Username not found')

import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config
from streamlit_authenticator.exceptions import RegisterError

from quotes_recommender.user_store.user_store_singleton import RedisUserStoreSingleton
from quotes_recommender.utils.streamlit import display_quotes
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

vector_store = QdrantVectorStoreSingleton().vector_store
user_store = RedisUserStoreSingleton().user_store


# set page config
st.set_page_config(
    page_title='SageSnippets',
    page_icon='💬',
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
with login_tab:
    authenticator.login(form_name='Login', location='main')
    # if login was successful
    if st.session_state['authentication_status']:
        # Display logged in user on sidebar
        st.sidebar.write(f"Logged in as {st.session_state['name']}.")
        # display logout button in sidebar
        authenticator.logout('Logout', 'sidebar', key='logout_sidebar')
        # write welcome message
        st.write(f"## Welcome {st.session_state['name']} 👋")
        with st.spinner('Loading your preferences'):
            # display (dis-)likes (if any) of logged-in user
            preferences = user_store.get_user_preferences(st.session_state['username'])
        # if user has no preferences
        if not preferences:
            st.info("""You have no preferences specified. 
            Start defining your interests within the [Preferences](/Preferences) page.""")
        else:
            # extract (dis-)likes from preferences
            likes = [preference.id for preference in preferences if preference.like]
            dislikes = [preference.id for preference in preferences if not preference.like]
            # TODO: fetch data from Qdrant
            # TODO: display quotes with (dis-)likes
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

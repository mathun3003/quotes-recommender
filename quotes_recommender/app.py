import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config
from streamlit_authenticator.exceptions import RegisterError

from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

vector_store = QdrantVectorStoreSingleton().vector_store


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
    # TODO: fetch credentials from DB
    credentials={
        'usernames': {
            'jsmith': {
                'email': 'test@web.de',
                'name': 'John Doe',
                'password': "$2b$12$TLdmvouH13w5dGD3i44WSOt5pVihi0lOUSaDszb.fIJ905TTz1WXi"  # 123
            }
        }
    },
    cookie_name='sage_snippet_cookie',
    key='bla'
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
    # if login was not successful
    elif st.session_state['authentication_status'] is False:
        st.error('❌ Username/password is incorrect')
    # if nothing was typed in
    elif st.session_state['authentication_status'] is None:
        st.warning('Please enter your username and password')

# Sign Up tab
with register_tab:
    # TODO: implement
    try:
        if authenticator.register_user("Register", preauthorization=False):
            st.success("You successfully registered for SageSnippets! 🎉")
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

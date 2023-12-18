import streamlit as st
import streamlit_authenticator as stauth

from quotes_recommender.utils.streamlit import switch_opposite_button
from quotes_recommender.vector_store.vector_store_singleton import QdrantVectorStoreSingleton

vector_store = QdrantVectorStoreSingleton().vector_store

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
# display logout button in sidebar
authenticator.logout('Logout', 'sidebar', key='logout_sidebar')

if st.session_state['authentication_status']:

    # Display logged in user on sidebar
    st.sidebar.write(f"Logged in as {st.session_state['name']}.")

    st.header('Your Preferences')
    st.subheader('Specify your preferences')
    st.write("""
    In order to provide you the best possible recommendations, we need some information about your preferences and 
    interests. Please consider the following quotes and specify at least five quotes you like and not like.
    """)
    st.divider()
    # get quotes from vector store
    quotes, next_page_offset = vector_store.scroll_points(limit=10)

    for quote in quotes:
        with st.container(border=True):
            left_quote_col, right_quote_col = st.columns(spec=[0.7, 0.3])
            with left_quote_col:
                st.markdown(f"""
                *„{quote.payload.get('text')}“*  
                **― {quote.payload.get('author')}**""")
                st.caption(f"Tags: {', '.join([tag.capitalize() for tag in quote.payload.get('tags')])}")
            with right_quote_col:
                if (img_link := quote.payload.get('avatar_img')) is not None:
                    st.image(quote.payload.get('avatar_img'), use_column_width=True)
            left_btn_col, right_btn_col = st.columns(spec=[0.2, 0.8])

            with left_btn_col:
                like_btn = st.checkbox(
                    label=":thumbsup:",
                    help="Yes, I want to see more like this!",
                    key=f"quote_{quote.id}_like",
                    on_change=switch_opposite_button,
                    args=[f"quote_{quote.id}_dislike"]
                )
            with right_btn_col:
                dislike_btn = st.checkbox(
                    label=":thumbsdown:",
                    help="Yuk, show me less like this!",
                    key=f"quote_{quote.id}_dislike",
                    on_change=switch_opposite_button,
                    args=[f"quote_{quote.id}_like"]
                )
else:
    st.info('🔔 Please login/register to specify preferences.')

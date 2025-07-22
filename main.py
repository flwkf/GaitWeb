import streamlit as st
st.markdown(
    """
    <style>
    .block-container {
        zoom: 0.75;
        -moz-transform: scale(0.75);
        -moz-transform-origin: top left;
    }
    </style>
    """,
    unsafe_allow_html=True
)
pages = {
    "Menu": [
        st.Page("dashboard.py", title="Dashboard"),
        st.Page("input.py", title="Update Database"),
    ]
}

pg = st.navigation(pages)
pg.run()

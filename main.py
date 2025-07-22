import streamlit as st
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        zoom: 0.95 !important;
    }
    </style>
""", unsafe_allow_html=True)

pages = {
    "Menu": [
        st.Page("dashboard.py", title="Dashboard"),
        st.Page("input.py", title="Update Database"),
    ]
}

pg = st.navigation(pages)
pg.run()

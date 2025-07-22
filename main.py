import streamlit as st

pages = {
    "Menu": [
        st.Page("dashboard.py", title="Dashboard"),
        st.Page("input.py", title="Update Database"),
    ]
}

pg = st.navigation(pages)
pg.run()

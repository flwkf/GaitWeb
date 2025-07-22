import streamlit as st
zoom_level = 0.75
st.markdown(f"""
    <style>
        .main {{
            transform: scale({zoom_level});
            transform-origin: top left;
            width: {100 / zoom_level}%;
        }}
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

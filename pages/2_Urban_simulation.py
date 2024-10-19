import streamlit as st
import const as const

st.set_page_config(**const.SET_PAGE_CONFIG)

with st.sidebar:
    st.page_link("Home.py", label="ホーム", icon="🏠")
    st.page_link("pages/1_Data_dashboard.py", label="データダッシュボード", icon="📊")
    st.page_link("pages/2_Urban_simulation.py", label="都市シミュレーション", icon="💻")

st.write("Under construction")
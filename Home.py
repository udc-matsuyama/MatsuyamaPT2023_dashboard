import streamlit as st
import const as const

st.set_page_config(**const.SET_PAGE_CONFIG)

with st.sidebar:
    st.page_link("Home.py", label="ホーム", icon="🏠")
    st.page_link("pages/1_Data_dashboard.py", label="データダッシュボード", icon="📊")
    st.page_link("pages/2_Urban_simulation.py", label="都市シミュレーション", icon="💻")

# メインページのコンテンツ
st.title('2023年松山都市圏パーソントリップ調査')
st.write("このページでは、松山都市圏の交通調査データを分析します。")
import streamlit as st
import const as const

st.set_page_config(**const.SET_PAGE_CONFIG)

with st.sidebar:
    st.page_link("Home.py", label="ホーム", icon="🏠")
    st.page_link("pages/1_Data_dashboard.py", label="データダッシュボード", icon="📊")
    st.page_link("pages/2_Urban_simulation.py", label="都市シミュレーション", icon="💻")

# メインページのコンテンツ
st.title('松山 都市データプラットフォーム')
st.markdown("""
            このページでは、松山都市圏の都市・交通データの分析ツールを提供します。
            ## 分析ツール
            """)
st.page_link("pages/1_Data_dashboard.py", label="データダッシュボード", icon="📊")
st.page_link("pages/2_Urban_simulation.py", label="都市シミュレーション", icon="💻")

st.markdown("""
            ## リンク
            - [松山アーバンデザインセンター](https://udcm.jp)
            - [松山アーバンデザインセンター スマートシティプロジェクト](https://udc-matsuyama.github.io)
            - [GitHub](https://github.com/udc-matsuyama)
            
            ## お問い合わせ・ご要望
            [こちらのGoogle Form](https://forms.gle/Hp8gevELD8EdYyft8)からお問い合わせください。
            """)


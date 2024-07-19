import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import geopandas as gpd

import const

st.set_page_config(**const.SET_PAGE_CONFIG)

# このファイルのディレクトリに移動
os.chdir(os.path.dirname(__file__))

# CSVファイルを読み込む
df3_path = 'data/3個人票.csv'
# df1
df1 = pd.read_csv("data/1世帯情報.csv", encoding='utf-8')

#df2
dtype_str= ['7_■1_現住所_住所（番地・番）', '8_■1_現住所_住所（号）', '勤務先・通学先・通園先の所在地_目標物', '勤務先・通学先・通園先の所在地_番地・番', '勤務先・通学先・通園先の所在地_号']
dtype_dict = {i: str for i in dtype_str}
df2 = pd.read_csv("data/2世帯個人.csv", encoding='utf-8', dtype=dtype_dict)

#df3
dtype_str= ['46_出発地_目標物', '47_出発地_番地・番', '48_出発地_号', '51_到着地_目標物', '52_到着地_番地・番', '53_到着地_号']
dtype_dict = {i: str for i in dtype_str}
df3 = pd.read_csv(df3_path, encoding='utf-8', dtype=dtype_dict)

# GeoJSONファイル
geojson_file_path = 'data/大ゾーン.geojson'
geo_data = gpd.read_file(geojson_file_path)

# 目的コード
purpose_dict = {1:"通勤", 2:"通学", 3:"帰宅", 4:"買い物", 5:"食事・社交・娯楽", 
                6:"観光・行楽・レジャー", 7:"通院", 8:"その他私用", 9:"送迎", 10:"販売・配達・仕入・購入先",
                11:"打ち合わせ・会議・集金・往診", 12:"作業・修理", 13:"農林漁業作業", 14:"その他の業務", 99:"無回答"}

mode_dict = {1: "徒歩", 2: "自転車", 3: "原動付自転車", 4: "自動二輪車", 5: "タクシー・ハイヤー", 
             6: "乗用車", 7: "軽自動車", 8: "貨物自動車", 9: "軽貨物車", 10: "自家用バス・貸切バス",
             11: "路線バス", 12: "鉄道（JR）", 13: "市内電車", 14: "郊外電車", 15: "船舶", 
             16: "航空機", 17: "その他", 18: "自動車（車種不明）", 99: "無回答"}

zone_dict = {'松山市1区':'市駅、大街道、松山城', '松山市2区':'大手町、本町', '松山市3区':'松山大・愛媛大・松山東高', '松山市4区':'いよ立花駅', '松山市5区':'市駅南側、JR西側',
             '松山市6区':'衣山', '松山市7区':'木屋町、山越', '松山市8区':'湯の山、北東山地', '松山市9区':'平井、梅本（東久米）', '松山市10区':'桑原・畑寺', 
             '松山市11区':'久米', '松山市12区':'恵原、南部山地', '松山市13区':'古川、石井、いよ立花の南', '松山市14区':'市坪、松山JCT', '松山市15区':'垣生、余戸、土居田',
             '松山市16区':'北斎院、空港線', '松山市17区':'三津浜駅、山西駅', '松山市18区':'久万ノ台、北部山地', '松山市19区':'伊予和気、堀江', '松山市20区':'興居島',
             '松山市21区':'空港', '松山市22区':'道後温泉、石手寺', '松山市23区':'JR松山駅', '松山市24区':'三津埠頭', '松山市25区':'松山観光港',
             '松山市26区':'中央卸売市場', '松山市27区':'伊予北条', '松山市28区':'中島',
             '伊予市1区':'郡中、伊予市駅', '伊予市2区':'伊予南部山地', '伊予市3区':'伊予西部山地',
             '東温市1区':'横河原駅、愛大医学部', '東温市2区':'東温市東部山地', '松前町':'松前町',
             '砥部町1区':'とべ動物園', '砥部町2区':'砥部南部山地'}


# タイトルと説明を追加
st.title('データ可視化ダッシュボード')
st.write('このダッシュボードでは、データの様々な視点からの分析を行います。')

# 上段の3列構成
col1, col2, col3 = st.columns(3)

with col1:
    # 地域選択フィルターを追加
    st.subheader('地域と平日/休日を選択')
    selected_area = st.selectbox('知りたい地域を選択してください', [f"{i} ({zone_dict[i]})" for i in zone_dict.keys()])
    selected_area = selected_area.split(' ')[0] # 選択された地域名のみ取得
    
    # 平日/休日選択ラジオボタン
    selected_day = st.radio('平日/休日を選択してください', ['平日', '休日'])
    selected_day = 1 if selected_day == '平日' else 2
    
    # Folium地図の作成
    m = folium.Map(location=[33.841936668807115, 132.75165552992496], zoom_start=12, tiles= "openstreetmap") # tiles= "cartodbpositron"

    # GeoJSONデータを透明なレイヤーとして追加
    style_function = lambda x: {
        'fillColor': '#transparent',
        'color': '#000000',
        'weight': 1.5,
        'fillOpacity': 0
    }
    
    # ホバー時の挙動
    highlight_function = lambda x: {
        'fillColor': '#ffaf00',
        'color': '#ffaf00',
        'weight': 2.5,
        'fillOpacity': 0.7
    }

    folium.GeoJson(
        geo_data,
        name="松山マップ",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(fields=['R05大ゾーン', 'CITY_NAME'], aliases=['大ゾーン', '都市名'])
    ).add_to(m)
    
    st_folium(m, height=500, use_container_width=True, returned_objects=[])
    
df3_selected = df3[(df3['ID'].isin(df2.loc[df2['居住大ゾーン']==selected_area, 'ID'])) & (df3['11_平休'] == selected_day)]

with col2:
    st.subheader('外出した人の割合')
    df3_selected

with col3:
    st.subheader('年齢別 外出した人の割合')
    age_groups = ['5～14歳', '15～24歳', '25～44歳', '45～64歳', '65～74歳', '75歳～']
    fig, ax = plt.subplots()
    for age_group in age_groups:
        data_age = filtered_data[filtered_data['年齢グループ'] == age_group]['外出した人の割合']
        ax.hist(data_age, bins=30, alpha=0.5, label=age_group)
    ax.legend(loc='best')
    st.pyplot(fig)

# 下段の4列構成
col4, col5, col6, col7 = st.columns(4)

with col4:
    st.subheader('トリップ数')
    fig, ax = plt.subplots()
    filtered_data['トリップ数'].dropna().hist(bins=30, ax=ax)
    st.pyplot(fig)

with col5:
    st.subheader('到着地の地図プロット')
    st.map(filtered_data[['到着地_緯度', '到着地_経度']].dropna())

with col6:
    st.subheader('移動距離のヒストグラム')
    fig, ax = plt.subplots()
    filtered_data['移動距離'].dropna().hist(bins=30, ax=ax)
    st.pyplot(fig)

with col7:
    st.subheader('滞在時間のヒストグラム')
    fig, ax = plt.subplots()
    filtered_data['滞在時間_分'].dropna().hist(bins=30, ax=ax)
    st.pyplot(fig)
# Streamlitアプリの実行
if __name__ == '__main__':
    st.run()

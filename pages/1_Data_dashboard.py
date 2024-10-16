# ライブラリのインポート
import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from shapely.geometry import Point

import const as const
import pages.lib.trip_od as trip_od

st.set_page_config(**const.SET_PAGE_CONFIG)
# ディレクトリが存在しない場合は作成
os.makedirs('data', exist_ok=True)

# --- サイドバーの設定 ---
with st.sidebar:
    st.page_link("Home.py", label="ホーム", icon="🏠")
    st.page_link("pages/1_Data_dashboard.py", label="データダッシュボード", icon="📊")
    st.page_link("pages/2_Urban_simulation.py", label="都市シミュレーション", icon="💻")


# --- データの読み込み---
# For remote server
# Secrets Managementからサービスアカウント情報を取得して辞書に再構築
service_account_info = {
    "type": st.secrets["SERVICE_ACCOUNT_TYPE"],
    "project_id": st.secrets["PROJECT_ID"],
    "private_key_id": st.secrets["PRIVATE_KEY_ID"],
    "private_key": st.secrets["PRIVATE_KEY"],
    "client_email": st.secrets["CLIENT_EMAIL"],
    "client_id": st.secrets["CLIENT_ID"],
    "auth_uri": st.secrets["AUTH_URI"],
    "token_uri": st.secrets["TOKEN_URI"],
    "auth_provider_x509_cert_url": st.secrets["AUTH_PROVIDER_X509_CERT_URL"],
    "client_x509_cert_url": st.secrets["CLIENT_X509_CERT_URL"]
}

# Google Drive APIのスコープ
SCOPES = ['https://www.googleapis.com/auth/drive']
# Google API認証用のサービスアカウント情報を使って認証を実行
credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

# Google Drive APIクライアントを作成
service = build('drive', 'v3', credentials=credentials)

# Google Driveからファイルを取得する関数
def download_file(file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    with open(file_name, 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%")
    return file_name

@st.cache_data(show_spinner='データを読み込んでいます。')
def load_data():
    # 1世帯情報.csvをダウンロード
    file_id = '1ntzZGqC5sXzvqg4nUCIpDiP_lGAqOvW4'
    file_name = 'data/1世帯情報.csv'
    downloaded_file = download_file(file_id, file_name)
    df1 = pd.read_csv(downloaded_file)
    # 2世帯個人.csvをダウンロード
    file_id = '1blEh9tQ_oRTNshrj4_4U7vXCZCNXclMk'
    file_name = 'data/2世帯個人.csv'
    downloaded_file = download_file(file_id, file_name)
    df2 = pd.read_csv(downloaded_file)
    # 3個人票.csvをダウンロード
    file_id = '1u4iLbvj-zW-Qp4OblGj03dqBTLqn5Zj7'
    file_name = 'data/3個人票.csv'
    downloaded_file = download_file(file_id, file_name)
    df3 = pd.read_csv(downloaded_file)
    # 大ゾーン.geojsonをダウンロード
    file_id = '1q1BXkA5sW-3YLYNo6tPCyBs1nJfY-mKC'
    file_name = 'data/大ゾーン.geojson'
    downloaded_file = download_file(file_id, file_name)
    geo_data = gpd.read_file(downloaded_file)

    return df1, df2, df3, geo_data

df1, df2, df3, geo_data = load_data()

geo_data["geometry"] = geo_data["geometry"].buffer(0)
geojson_file_path = 'data/大ゾーン.geojson'


'''
# For local
# CSVファイルを読み込む。
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
'''

# --- 辞書やヘルパー関数の定義 ---
# 目的コード
purpose_dict = {1:"通勤", 2:"通学", 3:"帰宅", 4:"買い物", 5:"食事・社交・娯楽", 
                6:"観光・行楽・レジャー", 7:"通院", 8:"その他私用", 9:"送迎", 10:"販売・配達・仕入・購入先",
                11:"打ち合わせ・会議・集金・往診", 12:"作業・修理", 13:"農林漁業作業", 14:"その他の業務", 99:"無回答"}

mode_dict = {1: "徒歩", 2: "自転車", 3: "原動付自転車", 4: "自動二輪車", 5: "タクシー・ハイヤー", 
             6: "乗用車", 7: "軽自動車", 8: "貨物自動車", 9: "軽貨物車", 10: "自家用バス・貸切バス",
             11: "路線バス", 12: "鉄道（JR）", 13: "市内電車", 14: "郊外電車", 15: "船舶", 
             16: "航空機", 17: "その他", 18: "自動車（車種不明）", 99: "無回答"}

zone_dict = {'松山市1区':'市駅、大街道、松山城', '松山市2区':'大手町、本町、味酒', '松山市3区':'愛媛大、松山東高、祝谷', '松山市4区':'いよ立花駅、朝生田', '松山市5区':'土橋、空港通、南江戸',
             '松山市6区':'衣山、宮田町', '松山市7区':'木屋町、山越、姫原', '松山市8区':'湯の山、北東山地', '松山市9区':'平井、梅本、東久米', '松山市10区':'桑原、畑寺、東野', 
             '松山市11区':'久米、南土居、高井', '松山市12区':'久谷、荏原、浄瑠璃', '松山市13区':'和泉南、古川北、石井、朝生田', '松山市14区':'市坪、松山IC、森松', '松山市15区':'垣生、余戸、土居田',
             '松山市16区':'北斎院、南斎院、北吉田', '松山市17区':'JR三津浜駅、山西、松ノ木', '松山市18区':'久万ノ台、谷町、北部山地', '松山市19区':'伊予和気、堀江', '松山市20区':'高浜、興居島',
             '松山市21区':'空港', '松山市22区':'道後温泉、石手寺', '松山市23区':'JR松山駅', '松山市24区':'三津埠頭', '松山市25区':'松山観光港',
             '松山市26区':'中央卸売市場', '松山市27区':'北条', '松山市28区':'中島',
             '伊予市1区':'郡中、伊予市駅', '伊予市2区':'伊予南部山地', '伊予市3区':'伊予西部山地',
             '東温市1区':'横河原駅、愛大医学部', '東温市2区':'東温市東部山地', '松前町':'松前町',
             '砥部町1区':'砥部町中心部、動物園', '砥部町2区':'砥部南部山地'}

def get_zone_from_lat_lon(lat:float, lon:float) -> str:
    for idx, row in geo_data.iterrows():
        if row['geometry'].contains(Point(lon, lat)):
            return row['R05大ゾーン']
    return "全地域"

@st.cache_data
def get_mode_df(df3_selected, purpose_list, mode_list_gaiyou, zone_dict):
    # ここで重い計算を行う
    mode_df = pd.DataFrame(columns=mode_list_gaiyou + ['samples'], index=zone_dict.keys())
    for d in zone_dict.keys():
        df_od = df3_selected.loc[(df3_selected['到着地大ゾーン'] == d) & (df3_selected['23_目的'].isin(purpose_list)), :]
        if len(df_od) > 10:
            for mode in mode_list_gaiyou:
                mode_df.loc[d, mode] = (df_od['代表交通手段_概要'] == mode).sum() / len(df_od)
            mode_df.loc[d, 'samples'] = len(df_od)
    mode_df = mode_df.loc[mode_df.sum(axis=1) != 0, :]
    mode_df = mode_df.sort_values('samples', ascending=False)[:5]
    return mode_df

@st.cache_data
def get_trip_od_purpose(purpose_list, ODzone_list, df3):
    return trip_od.trip_od_purpose(purpose_list, ODzone_list, df3)

@st.cache_data
def get_trip_plot_origin(df_trip, selected_area, geojson_file_path, purpose_code, title):
    return trip_od.plot_trip_origin(df_trip, selected_area, geojson_file_path, purpose_code, title)

@st.cache_data
def get_trip_plot_destination(df_trip, selected_area, geojson_file_path, purpose_code, title):
    return trip_od.plot_trip_destination(df_trip, selected_area, geojson_file_path, purpose_code, title)


# タイトルと説明を追加
st.title('2023年松山都市圏パーソントリップ調査')
#st.write('このダッシュボードでは、各地域に住んでいる人の移動に着目して分析を行います。')

# 上段の3列構成
col1, col2, col3 = st.columns(3, gap='small', vertical_alignment='top')

with col1:
    st.subheader('地図からゾーンを選ぶ')
    
    # 初期値をセッションに保存
    if "last_object_clicked" not in st.session_state:
        st.session_state["last_object_clicked"] = None
    if 'selected_zone' not in st.session_state:
        st.session_state['selected_zone'] = "全地域"
    
    # Folium地図の作成
    m = folium.Map(location=[33.841936668807115, 132.75165552992496], zoom_start=12, tiles="openstreetmap") # tiles= "cartodbpositron"
    # GeoJSONデータを透明なレイヤーとして追加
    '''
    style_function = lambda x: {
        'fillColor': '#transparent',
        'color': '#000000',
        'weight': 1.0,
        'fillOpacity': 0
    }
    '''
    # 各ゾーンのスタイルを動的に設定する関数
    def style_function(feature):
        zone_name = feature['properties']['R05大ゾーン']
        
        # クリックされたゾーンは黄色、それ以外は透明に
        if zone_name == st.session_state['selected_zone']:
            return {'fillColor': '#f08080', 'color': '#f08080', 'weight': 2.5, 'fillOpacity': 0.7}
        else:
            return {'fillColor': '#transparent', 'color': '#000000', 'weight': 1.0, 'fillOpacity': 0}

    
    # ホバー時の挙動
    highlight_function = lambda x: {
        'fillColor': '#ffaf00',
        'color': '#ffaf00',
        'weight': 2.5,
        'fillOpacity': 0.2
    }
    
    tooltip = folium.GeoJsonTooltip(
            fields=['R05大ゾーン', 'CITY_NAME'], 
            aliases=['大ゾーン', '都市名'],
            localize=True,
            sticky=True,
            labels=True,
            style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
            """,
            )

    area_info = folium.GeoJson(
        geo_data,
        name="松山マップ",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=tooltip
    )
    m.add_child(area_info) # レイヤーを地図に追加
    m.keep_in_front(area_info) # レイヤーを最前面に保持
    
    # 地図表示
    output = st_folium(m, height=400, use_container_width=True)
    if (
        output["last_object_clicked"]
        and output["last_object_clicked"] != st.session_state.get("last_object_clicked")
    ):
        st.session_state["last_object_clicked"] = output["last_object_clicked"]
        zone = get_zone_from_lat_lon(*output["last_object_clicked"].values())
        st.session_state["selected_zone"] = zone
        st.rerun()
    
with col2:
    # 地域選択フィルターを追加
    st.subheader('地域・属性・目的を選ぶ')
    selected_area = st.selectbox('知りたい地域を選んでください', 
                                 ["全地域"] + [f"{i} ({zone_dict[i]})" for i in zone_dict.keys()], 
                                 index=(["全地域"] + list(zone_dict.keys())).index(st.session_state['selected_zone']) if st.session_state['selected_zone'] in zone_dict else 0
                                 )
    
    selected_area = "全地域" if selected_area == "全地域" else selected_area.split(' ')[0] # 選択された地域名のみ取得
    
    # 平日/休日選択ラジオボタン
    selected_day_text = st.radio('平日/休日を選んでください', ['平日', '休日'], horizontal=True)
    selected_day = 1 if selected_day_text == '平日' else 2
    
    # 個人属性の選択ボタン
    age_dict = {'全て': (0, 130), '22歳以下': (0, 22), '23歳から39歳': (23, 39), '40歳から65歳': (40, 65), '66歳以上': (66, 130)}
    age = st.selectbox('年齢', list(age_dict.keys()))
    childcare = st.selectbox('18歳以下の子供の有無', ['全て', '子供あり'])
    car = st.selectbox('運転免許の有無', ['全て', '免許なし'])
    
    # ユーザーの選択をセッション状態に保存
    st.session_state['selected_area'] = selected_area
    st.session_state['selected_day'] = selected_day
    st.session_state['age'] = age
    st.session_state['childcare'] = childcare
    st.session_state['car'] = car
    
    # データのフィルタリングをキャッシュする
    @st.cache_data
    def filter_data(df2, df3, selected_area, selected_day, age, childcare, car):
        df3_selected = df3.copy()
        df2_selected = df2.copy()
        # 地域フィルタ
        if selected_area != "全地域":
            df3_selected = df3_selected[df3_selected['ID'].isin(df2[df2['居住大ゾーン'] == selected_area]['ID'])]
            df2_selected = df2_selected[df2_selected['居住大ゾーン'] == selected_area]
        # 平日/休日フィルタ
        df3_selected = df3_selected[df3_selected['11_平休'] == selected_day]
        # 年齢フィルタ
        age_range = age_dict[age]
        df2_selected = df2_selected[df2_selected['22_■3_年齢'].between(age_range[0], age_range[1])]
        df3_selected = df3_selected[df3_selected['ID'].isin(df2_selected['ID'])]
        # 子供の有無フィルタ
        if childcare == '子供あり':
            household_with_children = df2[df2['22_■3_年齢'] <= 18]['5_整理番号_市町村・ロット・SEQ'].unique()
            df2_selected = df2_selected[df2_selected['5_整理番号_市町村・ロット・SEQ'].isin(household_with_children)]
            df3_selected = df3_selected[df3_selected['ID'].isin(df2_selected['ID'])]
        # 運転免許フィルタ
        if car == '免許なし':
            df2_selected = df2_selected[df2_selected['27_■3_保有運転免許_①保有運転免許種類'].isin([4, 5])]
            df3_selected = df3_selected[df3_selected['ID'].isin(df2_selected['ID'])]

        return df2_selected, df3_selected

    df2_selected, df3_selected = filter_data(df2, df3, selected_area, selected_day, age, childcare, car)    
    # データ数
    st.write(f"該当するデータ: {len(df2_selected)}人, {len(df3_selected)}回の移動")

# 国勢調査の結果-------------------------------------------------------------------
with col3:
    st.subheader(f'{selected_area}の人口構成')
    
    if selected_area != '全地域':
        df = pd.read_csv('census_data/population_by_generation.csv',index_col=0)
        # グラフを描画
        fig, ax = plt.subplots()
        ax.bar(df.loc[selected_area,:].index,df.loc[selected_area,:],width=0.6)
        plt.xticks(rotation=45)
        st.pyplot(plt)
        
    elif selected_area == '全地域':
        PATH = 'census_data/census_population.csv'
        df_census = pd.read_csv(PATH, encoding='shift_jis',header=4)

        # 対象の地域のみ抽出
        df_census = df_census[(df_census['市区町村名'] == '松山市') | (df_census['市区町村名'] == '東温市')|
                (df_census['市区町村名'] == '伊予市')|(df_census['市区町村名'] == '松前町')|(df_census['市区町村名'] == '砥部町')]
        df_census = df_census[(df_census['男女'] == '総数')]
        # 地域階層レベル1に絞る
        df_census_level1 = df_census[(df_census['地域階層レベル'] == 1)]
        # 年齢を超細かく見ると...
        df_census_level1 = df_census_level1[['市区町村コード', '町丁字コード', '地域階層レベル','都道府県名', '市区町村名', '大字・町名', '字・丁目名', '総数',
                    '年齢「不詳」', '（再掲）15歳未満','（再掲）15〜64歳', '（再掲）65歳以上', '-','-.1']]
        df_census_level1_st = df_census_level1.loc[: , ["（再掲）15歳未満", "（再掲）15〜64歳",'（再掲）65歳以上','年齢「不詳」']].astype('int')
        df_census_level1_st=df_census_level1_st.rename(columns={'（再掲）15歳未満': '15歳未満','（再掲）15〜64歳': '15〜64歳','（再掲）65歳以上': '65歳〜','年齢「不詳」': '不明',}, 
                                                        index={0: '松山市',2576: '伊予市',2871: '東温市',3015: '松前町',3036: '砥部町'})
        df_sum = df_census_level1_st.sum()
        # グラフを描画
        fig, ax = plt.subplots()
        ax.bar(df_sum.index,df_sum)
        # Y軸ラベルを「万人」単位で表示
        # ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x/10000)}万人'))
        st.pyplot(plt)
# --------------------------------------------------------------------------------


st.subheader(f'選択した人の移動の基本情報')
st.write('<span style="color:green"> 小数字</span>は都市圏全体の平均値との差を表します。', unsafe_allow_html=True)
# 上段の3列構成
col4_1, col4_2, col4_3 = st.columns(3)
with col4_1:
    # 外出率
    out_rate = (df2_selected[f'{selected_day_text}外出'] * df2_selected['拡大係数']).mean(skipna=True)
    mean_out_rate = (df2[f'{selected_day_text}外出'] * df2['拡大係数']).mean(skipna=True)
    st.metric(label="外出した人の割合",
            value = f"{round(out_rate * 100, 1)} %",
            delta = f"{round((out_rate - mean_out_rate) * 100, 1)} %")
    
    # トリップ数（ネット）
    df2_net = df2_selected.loc[df2_selected[f'{selected_day_text}トリップ数']>0,:]
    trip_num = (df2_net[f'{selected_day_text}トリップ数'] * df2_net['拡大係数']).mean(skipna=True)
    df2_net = df2.loc[df2[f'{selected_day_text}トリップ数']>0,:]
    mean_trip_num = (df2_net[f'{selected_day_text}トリップ数'] * df2_net['拡大係数']).mean(skipna=True)
    st.metric(label="移動回数（外出した人）",
            value=round(trip_num, 2),
            delta = round(trip_num - mean_trip_num, 2))

with col4_2:
    # 手段
    # df3_selectedの割合計算
    counts_selected = df3_selected.groupby('代表交通手段_概要')['拡大係数'].sum()
    total_selected = df3_selected['拡大係数'].sum()
    ratio_selected = counts_selected.sort_index() / total_selected
    for i in set(['鉄道', '路面電車', 'バス', '自動車', '自転車', '徒歩']) - set(ratio_selected.index):
        ratio_selected[i] = 0

    # df3の割合計算
    counts_all = df3.groupby('代表交通手段_概要')['拡大係数'].sum()
    total_all = df3['拡大係数'].sum()
    ratio_all = counts_all.sort_index() / total_all

    st.metric(label="自動車利用率",
            value=f"{round(ratio_selected['自動車'] * 100, 1)} %",
            delta = f"{round((ratio_selected['自動車'] - ratio_all['自動車']) * 100, 1)} %")
    
    # 手段
    value = ratio_selected.loc[['鉄道', '路面電車', 'バス']].sum()
    mean = ratio_all.loc[['鉄道', '路面電車', 'バス']].sum()
    st.metric(label="公共交通利用率",
            value=f"{round(value * 100, 1)} %",
            delta = f"{round((value - mean) * 100, 1)} %")

with col4_3:
    # 手段
    st.metric(label="自転車利用率",
            value=f"{round(ratio_selected['自転車'] * 100, 1)} %",
            delta = f"{round((ratio_selected['自転車'] - ratio_all['自転車']) * 100, 1)} %")
    
    # 手段
    st.metric(label="徒歩率",
            value=f"{round(ratio_selected['徒歩'] * 100, 1)} %",
            delta = f"{round((ratio_selected['徒歩'] - ratio_all['徒歩']) * 100, 1)} %")



st.subheader(f'選択した人の目的・目的地ごとの交通手段')
# 目的の選択ボタン
st.write('目的を選んでください。')
purpose_list = st.multiselect('目的', [f"{i}" for i in purpose_dict.values()], default=[f"{i}" for i in purpose_dict.values()])

# mode_df を作成する
mode_list_gaiyou = ['徒歩', '自転車', '原付・二輪', 'タクシー', '自動車', 'バス', '鉄道', '路面電車', '船', '飛行機', 'その他']
color_mode_dict = {'徒歩': 'royalblue', '自転車': 'lightgreen', '原付・二輪': 'green', 'タクシー': 'wheat', '自動車': 'purple', 
                'バス': 'orange', '鉄道': 'red', '路面電車': 'pink', '船': 'lightgray', '飛行機': 'darkgray', 'その他': 'dimgray'}

# メインのコード内でキャッシュされた関数を呼び出す
mode_df = get_mode_df(df3_selected, [k for k, v in purpose_dict.items() if v in purpose_list], mode_list_gaiyou, zone_dict)


if len(mode_df) != 0:
    # データフレームをモルテン形式に変換
    melted_df = mode_df.reset_index().melt(id_vars=['index', 'samples'], value_vars=mode_list_gaiyou, var_name='交通手段', value_name='割合')
    melted_df = melted_df[melted_df['割合'] > 0]  # 0の行を削除
    melted_df = melted_df.rename(columns={'index': 'ゾーン'})
    melted_df['割合'] = melted_df['割合'].apply(lambda x: round(100 * x, 1))

    # y軸ラベルのカスタマイズ
    y_labels = {zone: f"{zone_dict[zone]}へ (n={mode_df.loc[zone, 'samples']})" for zone in mode_df.index}
    melted_df['ゾーンラベル'] = melted_df['ゾーン'].map(y_labels)
    
    # サンプル数順にゾーンラベルを並べる
    sorted_zones = melted_df[['ゾーンラベル', 'samples']].drop_duplicates().sort_values('samples', ascending=False)['ゾーンラベル'].tolist()

    # グラフの作成
    fig = px.bar(melted_df, 
                x='割合', 
                y='ゾーンラベル', 
                color='交通手段', 
                text='割合', 
                orientation='h',
                color_discrete_map=color_mode_dict,
                category_orders={'交通手段': mode_list_gaiyou, 'ゾーンラベル': sorted_zones})

    # テキスト表示のフォーマット設定
    fig.update_traces(textposition='inside', textfont_size=14)
    # グラフのレイアウトを更新
    fig.update_layout(title=f"{selected_area}({zone_dict[selected_area]})から出発する移動の交通手段" if selected_area != "全地域" else "全地域から移動の交通手段",
                    xaxis_title="割合 (%)",
                    yaxis_title="",
                    yaxis={'tickfont': {'size': 16}},
                    legend = {'title': '交通手段', 'title_font': {'size': 16}, 'font': {'size': 16}},
                    height=700)  # ソートをトータルで行う

    st.plotly_chart(fig)
else:
    st.write('<span style="color:red">データが少なすぎます。</span>', unsafe_allow_html=True)

# 下段の2列構成
col4, col5 = st.columns(2, gap='small', vertical_alignment='top')

with col4:
    st.subheader(f'{selected_area}に住む人がよく訪れる場所')
    if selected_area == "全地域":
        st.write('地域を選んでください。')
    else:
        #selected_purpose = st.multiselect('目的', [f"{i}" for i in purpose_dict.values()])
        purpose_o = st.selectbox('目的', [f"{i}" for i in purpose_dict.values()], key='origin')
        if len(purpose_o) == 0:
            st.write('目的を選んでください。')
        else:
            df_trip_o = get_trip_od_purpose(purpose_list=[k for k, v in purpose_dict.items() if v == purpose_o], ODzone_list=list(zone_dict.keys()), df3=df3)
        
        fig = get_trip_plot_origin(df_trip_o, selected_area, geojson_file_path, [k for k, v in purpose_dict.items() if v == purpose_o], title=purpose_o)
        # trip_od.plot_trip_origin(df_trip_o, selected_area, geojson_file_path, [k for k, v in purpose_dict.items() if v == purpose_o], title=purpose_o)
        st.pyplot(fig)
        # 上位5つの目的地を表示
        st.write('上位5つ')
        tbl_o = df_trip_o.loc[selected_area].sort_values(ascending=False)[:5].rename(index={k: f'{k} ({zone_dict[k]})' for k in zone_dict.keys()}).astype(int)
        st.markdown(f"""
                    1. {tbl_o.index[0]}  {tbl_o.iloc[0]}
                    1. {tbl_o.index[1]}  {tbl_o.iloc[1]}
                    1. {tbl_o.index[2]}  {tbl_o.iloc[2]}
                    1. {tbl_o.index[3]}  {tbl_o.iloc[3]}
                    1. {tbl_o.index[4]}  {tbl_o.iloc[4]}
                    """
        )
    
with col5:
    st.subheader(f'{selected_area}を訪れる人がどこから来るか')
    if selected_area == "全地域":
        st.write('地域を選んでください。')
    else:
        #selected_purpose = st.multiselect('目的', [f"{i}" for i in purpose_dict.values()])
        purpose_d = st.selectbox('目的', [f"{i}" for i in purpose_dict.values()], key='destination')
        if len(purpose_d) == 0:
            st.write('目的を選んでください。')
        else:
            df_trip_d = get_trip_od_purpose(purpose_list=[k for k, v in purpose_dict.items() if v == purpose_d], ODzone_list=list(zone_dict.keys()), df3=df3)
        
        fig = get_trip_plot_destination(df_trip_d, selected_area, geojson_file_path, [k for k, v in purpose_dict.items() if v == purpose_d], title=purpose_d)
        st.pyplot(fig)
        # 上位5つの出発地を表示
        st.write('上位5つ')
        tbl_d = df_trip_d[selected_area].sort_values(ascending=False)[:5].rename(index={k: f'{k} ({zone_dict[k]})' for k in zone_dict.keys()}).astype(int)
        st.markdown(f"""
                    1. {tbl_d.index[0]}  {tbl_d.iloc[0]}
                    1. {tbl_d.index[1]}  {tbl_d.iloc[1]}
                    1. {tbl_d.index[2]}  {tbl_d.iloc[2]}
                    1. {tbl_d.index[3]}  {tbl_d.iloc[3]}
                    1. {tbl_d.index[4]}  {tbl_d.iloc[4]}
                    """
        )
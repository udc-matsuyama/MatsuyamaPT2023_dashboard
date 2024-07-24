import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

import const
import trip_od

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
st.title('2023年松山都市圏パーソントリップ調査')
st.write('このダッシュボードでは、各地域に住んでいる人の移動に着目して分析を行います。')

# 上段の3列構成
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader('地図からゾーン名を確認')
    
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
    
    st_folium(m, height=400, use_container_width=True, returned_objects=[])
    

with col2:
    # 地域選択フィルターを追加
    st.subheader('地域と平日/休日を選択')
    selected_area = st.selectbox('知りたい地域を選択してください', [f"{i} ({zone_dict[i]})" for i in zone_dict.keys()])
    selected_area = selected_area.split(' ')[0] # 選択された地域名のみ取得
    
    # 平日/休日選択ラジオボタン
    selected_day_text = st.radio('平日/休日を選択してください', ['平日', '休日'])
    selected_day = 1 if selected_day_text == '平日' else 2
    
df3_selected = df3.loc[(df3['ID'].isin(df2.loc[df2['居住大ゾーン']==selected_area, 'ID'])) & (df3['11_平休'] == selected_day)]
df2_selected = df2.loc[df2['居住大ゾーン']==selected_area]

with col3:
    st.subheader('地域の基本情報')
    st.write('小数字は都市圏全体の平均値との差を表します。')
    # 上段の3列構成
    col3_1, col3_2 = st.columns(2)
    with col3_1:
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
    
    with col3_2:
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
        
        # 手段
        st.metric(label="自転車利用率",
                value=f"{round(ratio_selected['自転車'] * 100, 1)} %",
                delta = f"{round((ratio_selected['自転車'] - ratio_all['自転車']) * 100, 1)} %")
        
        # 手段
        st.metric(label="徒歩率",
                value=f"{round(ratio_selected['徒歩'] * 100, 1)} %",
                delta = f"{round((ratio_selected['徒歩'] - ratio_all['徒歩']) * 100, 1)} %")
    
    # 移動時間
    
    
    # 移動距離

# 下段の4列構成
col4, col5 = st.columns(2)

with col4:
    st.subheader('よく行く場所')
    #selected_purpose = st.multiselect('目的', [f"{i}" for i in purpose_dict.values()])
    purpose_o = st.selectbox('目的', [f"{i}" for i in purpose_dict.values()], key='origin')
    if len(purpose_o) == 0:
        st.write('目的を選択してください。')
    else:
        df_trip_o = trip_od.trip_od_purpose(purpose_list=[k for k, v in purpose_dict.items() if v == purpose_o], ODzone_list=list(zone_dict.keys()), df3=df3)
    
    fig = trip_od.plot_trip_origin(df_trip_o, selected_area, geojson_file_path, [k for k, v in purpose_dict.items() if v == purpose_o], title=purpose_o)
    st.pyplot(fig)
    
with col5:
    st.subheader('よく来る場所')
    #selected_purpose = st.multiselect('目的', [f"{i}" for i in purpose_dict.values()])
    purpose_d = st.selectbox('目的', [f"{i}" for i in purpose_dict.values()], key='destination')
    if len(purpose_d) == 0:
        st.write('目的を選択してください。')
    else:
        df_trip_d = trip_od.trip_od_purpose(purpose_list=[k for k, v in purpose_dict.items() if v == purpose_d], ODzone_list=list(zone_dict.keys()), df3=df3)
    
    fig = trip_od.plot_trip_destination(df_trip_d, selected_area, geojson_file_path, [k for k, v in purpose_dict.items() if v == purpose_d], title=purpose_d)
    st.pyplot(fig)


col6, col7 = st.columns(2)

with col6:
    st.subheader('目的地ごとの交通手段')   
    # mode_df を作成する
    mode_list_gaiyou = ['徒歩', '自転車', '原付・二輪', 'タクシー', '自動車', 'バス', '鉄道', '路面電車', '船', '飛行機', 'その他']
    color_mode_dict = {'徒歩': 'royalblue', '自転車': 'lightgreen', '原付・二輪': 'green', 'タクシー': 'wheat', '自動車': 'purple', 
                   'バス': 'orange', '鉄道': 'red', '路面電車': 'pink', '船': 'lightgray', '飛行機': 'darkgray', 'その他': 'dimgray'}
    mode_df = pd.DataFrame(columns=mode_list_gaiyou + ['samples'], index=zone_dict.keys())

    # mode_df を作成する
    for d in zone_dict.keys():
        df_od = df3.loc[(df3['出発地大ゾーン'] == selected_area) & (df3['到着地大ゾーン'] == d) & (df3['23_目的'] != 3), :]
        if len(df_od) > 10:  # トリップ数が少ない場合は無視
            for mode in mode_list_gaiyou:
                mode_df.loc[d, mode] = (df_od['代表交通手段_概要'] == mode).sum() / len(df_od)
                mode_df.loc[d, 'samples'] = len(df_od)

    # 0のところは削除
    mode_df = mode_df.loc[mode_df.sum(axis=1) != 0, :]

    if len(mode_df) != 0:
        # データフレームをモルテン形式に変換
        melted_df = mode_df.reset_index().melt(id_vars=['index', 'samples'], value_vars=mode_list_gaiyou, var_name='交通手段', value_name='割合')
        melted_df = melted_df[melted_df['割合'] > 0]  # 0の行を削除
        melted_df = melted_df.rename(columns={'index': 'ゾーン'})
        melted_df['割合'] = melted_df['割合'] * 100  # パーセント表示に変換

        # y軸ラベルのカスタマイズ
        y_labels = {zone: f"{zone_dict[zone]}へ (n={mode_df.loc[zone, 'samples']})" for zone in mode_df.index}
        melted_df['ゾーンラベル'] = melted_df['ゾーン'].map(y_labels)

        # グラフの作成
        fig = px.bar(melted_df, 
                    x='割合', 
                    y='ゾーンラベル', 
                    color='交通手段', 
                    text='割合', 
                    orientation='h',
                    color_discrete_map=color_mode_dict,
                    category_orders={'交通手段': mode_list_gaiyou})

        # テキスト表示のフォーマット設定
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')

        # グラフのレイアウトを更新
        fig.update_layout(title=f"{selected_area}({zone_dict[selected_area]})からの出発トリップの代表交通手段割合(帰宅を除く)",
                        xaxis_title="割合 (%)",
                        yaxis={'categoryorder':'total ascending'})  # ソートをトータルで行う

        st.plotly_chart(fig)


with col7:
    st.subheader('----')
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

import const

plt.rcParams['font.family'] = const.PLOT_FONT

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

def trip_od_purpose(purpose_list: list, ODzone_list: list, df3 : pd.DataFrame):
    mask = df3['23_目的'].isin(purpose_list)
    trip_od = df3[mask].groupby(['出発地大ゾーン', '到着地大ゾーン']).size().unstack().fillna(0)
    # なかった列の追加。トリップないので松山市25,26区は無視
    trip_od[list(set(ODzone_list) - set(trip_od.columns) - set(['松山市25区', '松山市26区']))] = 0
    # なかった行の追加。トリップないので松山市25,26区は無視
    for row in list(set(ODzone_list) - set(trip_od.index) - set(['松山市25区', '松山市26区'])):
        trip_od.loc[row] = 0
    
    # ゾーンの順番を揃える
    ODzone_order = {x: i for i, x in enumerate(ODzone_list)}
    trip_od = trip_od.sort_index(key=lambda x: x.map(ODzone_order), axis=0).sort_index(key=lambda x: x.map(ODzone_order),axis=1)
    return trip_od

def plot_trip_origin(trip_od: pd.DataFrame, selected_area: str, geojson_file_path:str, purpose_list: list, title = None):
    geo_data = gpd.read_file(geojson_file_path)
    
    # GeoJSONデータとデータフレームを地区名でマージ
    for idx in trip_od.index:
        geo_data = geo_data.merge(trip_od.loc[idx], left_on='R05大ゾーン', right_on='到着地大ゾーン', how='left')

    # 文字列から浮動小数に変換
    geo_data = geo_data.astype({x: float for x in trip_od.index})

    # 地図上で指定されたデータを可視化
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    geo_data.plot(column=selected_area, ax=ax, cmap='OrRd', legend=True, legend_kwds = {'shrink': 0.9}) # norm=norm, 
    # 対象地域を緑色で縁取る
    geo_data[geo_data['R05大ゾーン'] == selected_area].boundary.plot(ax=ax, edgecolor='lightgreen', linewidth=1)
    if title is None:
        plt.title(f"{selected_area}({zone_dict[selected_area]})からの出発トリップ({', '.join([purpose_dict[purpose] for purpose in purpose_list])})")
    else:
        plt.title(f"{selected_area}({zone_dict[selected_area]})からの出発トリップ({title})")
            
    return fig

def plot_trip_destination(trip_od: pd.DataFrame, selected_area: str, geojson_file_path:str, purpose_list: list, title = None):
    # GeoJSONファイルを読み込む
    geo_data = gpd.read_file(geojson_file_path)

    # GeoJSONデータとデータフレームを地区名でマージ
    for column in trip_od.columns:
        geo_data = geo_data.merge(trip_od[column], left_on='R05大ゾーン', right_on='出発地大ゾーン', how='left')

    # 文字列から浮動小数に変換
    geo_data = geo_data.astype({x: float for x in trip_od.columns})

    # 地図上で指定されたデータを可視化
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    geo_data.plot(column=selected_area, ax=ax, cmap='OrRd', legend=True, legend_kwds = {'shrink': 0.9}) # norm=norm, 
    # 対象地域を緑色で縁取る
    geo_data[geo_data['R05大ゾーン'] == selected_area].boundary.plot(ax=ax, edgecolor='lightgreen', linewidth=1)
    if title is None:
        plt.title(f"{selected_area}({zone_dict[selected_area]})への到着トリップ({', '.join([purpose_dict[purpose] for purpose in purpose_list])})")
    else:
        plt.title(f"{selected_area}({zone_dict[selected_area]})への到着トリップ({title})")
            
    return fig
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# このファイルのディレクトリに移動
os.chdir(os.path.dirname(__file__))

# CSVファイルを読み込む
file_path = 'data/3個人票_lonlat.csv'
data = pd.read_csv(file_path)

# タイトルと説明を追加
st.title('データ可視化ダッシュボード')
st.write('このダッシュボードでは、データの様々な視点からの分析を行います。')

# データのプレビューを表示
st.subheader('データのプレビュー')
st.write(data.head())

# 基本的な統計情報を表示
st.subheader('基本統計情報')
st.write(data.describe())

# カラム選択のセレクトボックスを追加
column = st.selectbox('表示するカラムを選択してください', data.columns)

# 選択されたカラムのヒストグラムを描画
st.subheader(f'{column}のヒストグラム')
fig, ax = plt.subplots()
data[column].dropna().hist(bins=30, ax=ax)
st.pyplot(fig)

# さらに具体的なグラフを追加
st.subheader('移動距離のヒストグラム')
fig, ax = plt.subplots()
data['移動距離'].dropna().hist(bins=30, ax=ax)
st.pyplot(fig)

# 地図上にプロット
st.subheader('到着地の地図プロット')
st.map(data[['到着地_緯度', '到着地_経度']].dropna())

# Streamlitアプリの実行
if __name__ == '__main__':
    st.run()

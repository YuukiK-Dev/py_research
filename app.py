import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. ページ設定
st.set_page_config(page_title="状況確認アプリ", layout="centered")

# 2. Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. データの読み込み（シート名を「シート1」に変更しました）
try:
    df = conn.read(worksheet="シート1", ttl=0)
except Exception:
    # 読み込めない場合は、見出しだけの空のデータを作ります
    df = pd.DataFrame(columns=["date", "time", "user_type", "status"])

st.title("🤝 状況確認アプリ")

# 4. 日本時間の取得
tokyo_tz = pytz.timezone('Asia/Tokyo')
now = datetime.now(tokyo_tz)

# 5. 記録ボタン
if st.button("😊 いい感じ", use_container_width=True):
    # 新しい1行を作成
    new_row = pd.DataFrame([{
        "date": now.strftime("%Y/%m/%d"),
        "time": now.strftime("%H:%M:%S"),
        "user_type": "当事者",
        "status": "いい感じ"
    }])
    
    # 今までのデータに新しい行をくっつける
    updated_df = pd.concat([df, new_row], ignore_index=True)
    
    # 「シート1」にすべてまとめて書き込む
    conn.update(worksheet="シート1", data=updated_df)
    
    st.balloons()
    st.success("スプレッドシートに記録しました！")

# 6. 最新の履歴を表示
st.divider()
st.subheader("最新の記録")
# 画面に最新の5件を表示します
display_df = updated_df if 'updated_df' in locals() else df
st.dataframe(display_df.tail(5), use_container_width=True, hide_index=True)

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. ページ設定
st.set_page_config(page_title="状況確認アプリ", layout="centered")

# 2. Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 既存データの読み込み
# 最初はデータがない場合があるため、エラーを回避する設定にしています
try:
    df = conn.read(worksheet="状況確認シート", ttl=0)
except Exception:
    df = pd.DataFrame(columns=["date", "time", "user_type", "status"])

st.title("🤝 状況確認アプリ")

# 4. 日本時間の取得（Asia/Tokyo）
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
    
    # 既存のデータに新しい行をくっつける
    updated_df = pd.concat([df, new_row], ignore_index=True)
    
    # スプレッドシート全体を更新（これが一番確実な方法です）
    conn.update(worksheet="状況確認シート", data=updated_df)
    
    st.balloons()
    st.success("スプレッドシートに記録しました！")

# 6. 最新の履歴を表示（直近5件）
st.divider()
st.subheader("最新の記録")
st.dataframe(updated_df.tail(5) if 'updated_df' in locals() else df.tail(5), use_container_width=True, hide_index=True)

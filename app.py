import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. 接続
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 読み込み
try:
    df = conn.read(worksheet="状況確認シート")
except:
    df = pd.DataFrame(columns=["date", "time", "user_type", "status"])

st.title("🤝 状況確認アプリ")

# 3. 日本時間
tokyo_tz = pytz.timezone('Asia/Tokyo')
now = datetime.now(tokyo_tz)

# 4. ボタン
if st.button("😊 いい感じ"):
    new_row = pd.DataFrame([{"date": now.strftime("%Y/%m/%d"), "time": now.strftime("%H:%M:%S"), "user_type": "当事者", "status": "いい感じ"}])
    conn.update(worksheet="状況確認シート", data=pd.concat([df, new_row], ignore_index=True))
    st.success("スプレッドシートに記録しました！")

# 5. 表示
st.divider()
st.dataframe(df.tail(5))

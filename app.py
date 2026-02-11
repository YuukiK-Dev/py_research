import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. ページ設定（必ず最初）
st.set_page_config(page_title="状況確認アプリ", layout="centered")

# （デバッグ：問題が解決したら消してOK）
st.write("connections keys:", list(st.secrets.get("connections", {}).keys()))
st.write("has service_account:", "service_account" in st.secrets.get("connections", {}).get("gsheets", {}))

# 2. Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🤝 状況確認アプリ")

# 3. 日本時間の取得
tokyo_tz = pytz.timezone("Asia/Tokyo")
now = datetime.now(tokyo_tz)

# 4. 記録ボタン
if st.button("😊 いい感じ", use_container_width=True):
    new_data = pd.DataFrame([{
        "date": now.strftime("%Y/%m/%d"),
        "time": now.strftime("%H:%M:%S"),
        "user_type": "当事者",
        "status": "いい感じ"
    }])

    try:
        df = conn.read(worksheet="シート1", ttl=0)
    except Exception:
        df = pd.DataFrame(columns=["date", "time", "user_type", "status"])

    df = pd.concat([df, new_data], ignore_index=True)
    conn.update(worksheet="シート1", data=df)

    st.success("記録しました！")
    st.rerun()  # 追加直後に表示を更新

# 5. 履歴を表示
st.divider()
st.subheader("最新の記録")

try:
    df = conn.read(worksheet="シート1", ttl=0)
    st.dataframe(df.tail(5), use_container_width=True, hide_index=True)
except Exception:
    st.info("まだ記録がありません。ボタンを押して最初のデータを登録しましょう！")

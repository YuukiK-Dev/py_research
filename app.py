import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. ページ設定（必ず最初）
st.set_page_config(page_title="状況確認アプリ", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #fff7fb 0%, #f2f7ff 100%);
}
            
h1, h2, h3, p, label {
    color: #334155 !important;
}

[data-testid="stMarkdownContainer"] {
    color: #334155 !important;
}

.stButton > button {
    background-color: #ffffff;
    border: 2px solid #f6b6d2;
    border-radius: 18px;
    padding: 14px;
    font-size: 18px;
    font-weight: bold;
    color: #4a5568;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}

.stButton > button:hover {
    background-color: #fff0f6;
    border-color: #ec8fbd;
}
</style>
""", unsafe_allow_html=True)

# （デバッグ：問題が解決したら消してOK）
# st.write("connections keys:", list(st.secrets.get("connections", {}).keys()))
# st.write("has service_account:", "service_account" in st.secrets.get("connections", {}).get("gsheets", {}))

# 2. Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🤝 状況確認アプリ")

# 3. 日本時間の取得
tokyo_tz = pytz.timezone("Asia/Tokyo")
now = datetime.now(tokyo_tz)

# 4. 記録ボタン (3つ)
st.subheader("今の気分を選んでね")

moods = {
    "😊 いい感じ":"いい感じ",
    "😐 ふつう":"ふつう",
    "😣 しんどい":"しんどい",
}

for label ,value in moods.items():
    if st.button(label,use_container_width=True):

        

        new_data = pd.DataFrame([{
            "date":now.strftime("%Y-%m-%d"),
            "time":now.strftime("%H:%M:%S"),
            "user_type":"当事者",
            "status":value

        }])

        try:
            df = conn.read(worksheet="シート1", ttl=0)
            df.columns=[c.strip() for c in df.columns]
            df=df.rename(columns={"Time":"time","Date":"date"})
            st.write("DEBUG columns:",df.columns.tolist())
        except Exception:
            df = pd.DataFrame(columns=["date","time","user_type","status"])

        df = df.loc[:,~df.columns.duplicated()]
        cols=["date", "time", "user_type", "status"]
        df = df.reindex(columns = cols)

        df = pd.concat([df, new_data], ignore_index=True)
        conn.update(worksheet="シート1", data=df)

        st.success("記録しました！")
        st.rerun()  # 追加直後に表示を更新

# 5. 履歴を表示
st.divider()
st.subheader("最新の記録")

try:
    df = conn.read(worksheet="シート1", ttl=0)

    df.columns=[c.strip() for c in df.columns]
    df=df.rename(columns={"Time":"time","Date":"date"})
    st.dataframe(df.tail(5), use_container_width=True, hide_index=True)
except Exception:
    st.info("まだ記録がありません。ボタンを押して最初のデータを登録しましょう！")

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz

# 1. ページ設定
st.set_page_config(page_title="状況確認アプリ", layout="centered")

# 2. Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🤝 状況確認アプリ")

# 3. 日本時間の取得
tokyo_tz = pytz.timezone('Asia/Tokyo')
now = datetime.now(tokyo_tz)

# 4. 記録ボタン
if st.button("😊 いい感じ", use_container_width=True):
    # 新しい1行のデータを作成
    new_data = pd.DataFrame([{
        "date": now.strftime("%Y/%m/%d"),
        "time": now.strftime("%H:%M:%S"),
        "user_type": "当事者",
        "status": "いい感じ"
    }])
    
    try:
        # 【重要】既存のデータに1行だけ「追加」する命令に変更しました
        conn.create(worksheet="シート1", data=new_data)
        st.balloons()
        st.success("スプレッドシートに記録しました！")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# 5. 履歴を表示
st.divider()
st.subheader("最新の記録")
try:
    df = conn.read(worksheet="シート1", ttl=0)
    st.dataframe(df.tail(5), use_container_width=True, hide_index=True)
except:
    st.info("まだ記録がありません。ボタンを押して最初のデータを登録しましょう！")

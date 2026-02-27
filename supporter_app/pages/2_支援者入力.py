import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="支援者：入力", layout="centered")
st.title("支援者：入力（supporter_log）")

conn = st.connection("gsheets", type=GSheetsConnection)

with st.form("supporter_input"):
    supporter = st.selectbox("支援者の種類", ["家族", "支援員", "教員", "その他"])
    seen_status = st.selectbox("当事者の状態", ["ok", "fuan", "shindoi"])
    action = st.text_input("対応（action）")
    memo = st.text_area("メモ")
    anxiety=st.slider("支援者の不安度 (0=なし~4=強い)",0,4,0)
    hesitation=st.radio("対応に困ったか?",["はい","いいえ"],horizontal=True)
    consult_need=st.radio("専門機関に相談したいと思ったか?",["はい","いいえ"],horizontal=True)
    urgency = st.selectbox("緊急度", [0, 1, 2], index=0)

    submitted = st.form_submit_button("保存")

if submitted:
    now = datetime.now()

    new_row = pd.DataFrame([{
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "supporter": supporter,
        "seen_status": seen_status,
        "action": action,
        "memo": memo,
        "anxiety": int(anxiety),
        "hesitation":hesitation,
        "consult_need":consult_need,
        "urgency": int(urgency),
        
    }])

    # 既存を読み込んで追記 → 全体を書き戻す（writeが無い環境向け）
    current = conn.read(worksheet="supporter_log", ttl=0)
    if current is None or len(current) == 0:
        combined = new_row
    else:
        current = current.loc[:, ~current.columns.duplicated()]
        combined = pd.concat([current, new_row], ignore_index=True)

    conn.update(worksheet="supporter_log", data=combined)
    st.success("保存しました（supporter_log に追記）")